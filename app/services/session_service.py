from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.requirement import Requirement, RequirementVersion
from app.models.session import InterpretationSession, Interpretation
from app.services.project_service import ProjectService
from app.services.audit_service import AuditService
from app.services.divergence_service import DivergenceService

class SessionService:
    @staticmethod
    def create_session(
        db: Session,
        requirement_id: int,
        user_id: int,
        version_id: Optional[int] = None,
        mode: str = "standard",
    ) -> InterpretationSession:
        """Owner creates a new blind interpretation session tied to a specific requirement version."""
        req = db.query(Requirement).filter(Requirement.requirement_id == requirement_id).first()
        if not req:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Requirement not found")

        ProjectService.require_owner(db, req.project_id, user_id)

        target_version_id = version_id or req.current_version_id
        if not target_version_id:
            # Fallback to latest version
            latest_v = (
                db.query(RequirementVersion)
                .filter(RequirementVersion.requirement_id == requirement_id)
                .order_by(RequirementVersion.version_no.desc())
                .first()
            )
            if not latest_v:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot start session: requirement has no version records",
                )
            target_version_id = latest_v.version_id

        session = InterpretationSession(
            requirement_version_id=target_version_id,
            created_by=user_id,
            status="collecting",  # Direct open collection
            mode=mode if mode in ("standard", "self_comparison") else "standard",
        )
        db.add(session)
        db.flush()

        AuditService.log_event(
            db=db,
            project_id=req.project_id,
            actor_id=user_id,
            action="SESSION_OPENED",
            entity_type="session",
            entity_id=session.session_id,
            details=f"Opened blind interpretation session #{session.session_id} for {req.req_code} (v{target_version_id})",
            metadata={"mode": session.mode},
        )
        db.commit()
        db.refresh(session)
        return session

    @staticmethod
    def get_session(db: Session, session_id: int, user_id: int) -> InterpretationSession:
        """Loads session and ensures the caller has project access."""
        session = db.query(InterpretationSession).filter(InterpretationSession.session_id == session_id).first()
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
        project_id = session.requirement_version.requirement.project_id
        ProjectService.require_member(db, project_id, user_id)
        return session

    @staticmethod
    def submit_interpretation(
        db: Session,
        session_id: int,
        user_id: int,
        perspective: str,
        expected_behavior: str,
        actor: Optional[str] = None,
        trigger_conditions: Optional[str] = None,
        delivery_hours: Optional[int] = None,
        constraints: Optional[str] = None,
        acceptance_criteria: Optional[str] = None,
    ) -> Interpretation:
        """
        Submits a structured interpretation during COLLECTING phase.
        Enforces:
        - Atomic rejection if session is LOCKED / ANALYZED / RESOLVED.
        - One submission per user per standard session (unless self_comparison mode).
        - Safe audit logging without storing the sensitive interpretation body.
        """
        session = db.query(InterpretationSession).filter(InterpretationSession.session_id == session_id).first()
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

        project_id = session.requirement_version.requirement.project_id
        ProjectService.require_member(db, project_id, user_id)

        if session.status != "collecting":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Submissions are closed. Session is currently {session.status.upper()}.",
            )

        # In standard mode, enforce single submission per user
        if session.mode == "standard":
            existing = (
                db.query(Interpretation)
                .filter(Interpretation.session_id == session_id, Interpretation.user_id == user_id)
                .first()
            )
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="You have already submitted an interpretation for this session.",
                )
        else:
            # Self-comparison mode allows multiple named perspectives from one user
            existing = (
                db.query(Interpretation)
                .filter(
                    Interpretation.session_id == session_id,
                    Interpretation.user_id == user_id,
                    Interpretation.perspective == perspective.strip(),
                )
                .first()
            )
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Perspective '{perspective}' has already been submitted for this session.",
                )

        # Validate delivery_hours if supplied
        if delivery_hours is not None and delivery_hours <= 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="delivery_hours must be a positive integer",
            )

        interp = Interpretation(
            session_id=session_id,
            requirement_id=session.requirement_version.requirement_id,
            user_id=user_id,
            perspective=perspective.strip(),
            actor=actor.strip() if actor else None,
            expected_behavior=expected_behavior.strip(),
            trigger_conditions=trigger_conditions.strip() if trigger_conditions else None,
            delivery_hours=delivery_hours,
            constraints=constraints.strip() if constraints else None,
            acceptance_criteria=acceptance_criteria.strip() if acceptance_criteria else None,
        )
        db.add(interp)
        db.flush()

        # Audit log metadata only (NO confidential body text)
        AuditService.log_event(
            db=db,
            project_id=project_id,
            actor_id=user_id,
            action="INTERPRETATION_SUBMITTED",
            entity_type="interpretation",
            entity_id=interp.interpretation_id,
            details=f"Submitted blind interpretation as '{interp.perspective}'",
            metadata={"session_id": session_id, "perspective": interp.perspective},
        )

        db.commit()
        db.refresh(interp)
        return interp

    @staticmethod
    def get_session_interpretations(
        db: Session, session_id: int, user_id: int
    ) -> List[Interpretation]:
        """
        CRITICAL SERVER-SIDE BLIND VISIBILITY ENFORCEMENT:
        - When session is DRAFT or COLLECTING:
          Returns ONLY the calling user's own submission.
          Other stakeholders' answers are NEVER returned in JSON, HTML, or logs.
          Owner has NO privilege to see others' hidden answers prior to lock.
        - When session is LOCKED, ANALYZED, or RESOLVED:
          Returns all submissions to authorized project members.
        """
        session = SessionService.get_session(db, session_id, user_id)

        if session.status in ("draft", "collecting"):
            return (
                db.query(Interpretation)
                .filter(Interpretation.session_id == session_id, Interpretation.user_id == user_id)
                .all()
            )
        else:
            return (
                db.query(Interpretation)
                .filter(Interpretation.session_id == session_id)
                .order_by(Interpretation.submitted_at.asc())
                .all()
            )

    @staticmethod
    def get_single_interpretation(
        db: Session, interpretation_id: int, user_id: int
    ) -> Interpretation:
        """
        Direct IDOR protection: prevents fetching another user's interpretation by direct ID before lock.
        """
        interp = db.query(Interpretation).filter(Interpretation.interpretation_id == interpretation_id).first()
        if not interp:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interpretation not found")

        project_id = interp.requirement.project_id
        ProjectService.require_member(db, project_id, user_id)

        if interp.session.status in ("draft", "collecting") and interp.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. Interpretation answers are strictly confidential until session lock.",
            )
        return interp

    @staticmethod
    def get_participation_summary(db: Session, session_id: int) -> Dict[str, Any]:
        """Returns safe summary counts without leaking participant content."""
        session = db.query(InterpretationSession).filter(InterpretationSession.session_id == session_id).first()
        if not session:
            return {"total_submissions": 0, "status": "unknown"}
        count = db.query(Interpretation).filter(Interpretation.session_id == session_id).count()
        return {
            "session_id": session_id,
            "status": session.status,
            "mode": session.mode,
            "total_submissions": count,
        }

    @staticmethod
    def lock_session(db: Session, session_id: int, user_id: int) -> InterpretationSession:
        """
        Owner-only atomic lock:
        - Freezes submissions.
        - Triggers deterministic divergence detection.
        - Transitions session state: COLLECTING -> LOCKED -> ANALYZED.
        """
        session = db.query(InterpretationSession).filter(InterpretationSession.session_id == session_id).first()
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

        project_id = session.requirement_version.requirement.project_id
        ProjectService.require_owner(db, project_id, user_id)

        if session.status != "collecting":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Cannot lock session in '{session.status}' state.",
            )

        now = datetime.now(timezone.utc)
        session.status = "locked"
        session.locked_at = now
        db.flush()

        # Run divergence analysis immediately in the same transaction
        findings = DivergenceService.analyze_session(db, session)
        session.status = "analyzed"

        AuditService.log_event(
            db=db,
            project_id=project_id,
            actor_id=user_id,
            action="SESSION_LOCKED",
            entity_type="session",
            entity_id=session.session_id,
            details=f"Locked session #{session.session_id}. Analyzed {len(findings)} divergence findings.",
            metadata={"findings_count": len(findings)},
        )

        db.commit()
        db.refresh(session)
        return session
