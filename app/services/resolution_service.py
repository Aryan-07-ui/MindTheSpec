from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.session import InterpretationSession
from app.models.resolution import Resolution
from app.models.divergence import Divergence
from app.services.project_service import ProjectService
from app.services.audit_service import AuditService

class ResolutionService:
    @staticmethod
    def record_resolution(
        db: Session,
        session_id: int,
        user_id: int,
        statement: str,
        rationale: str,
    ) -> Resolution:
        """
        Owner records an official binding resolution.
        - Preserves all historical interpretations unaltered.
        - Marks session as RESOLVED.
        - Marks open divergences as resolved.
        - Records immutable audit log.
        """
        session = db.query(InterpretationSession).filter(InterpretationSession.session_id == session_id).first()
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

        project_id = session.requirement_version.requirement.project_id
        ProjectService.require_owner(db, project_id, user_id)

        if session.status not in ("locked", "analyzed", "resolved"):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cannot resolve an unlocked session. Session must be locked first.",
            )

        existing = db.query(Resolution).filter(Resolution.session_id == session_id).first()
        if existing:
            # Update resolution
            existing.statement = statement.strip()
            existing.rationale = rationale.strip()
            existing.decided_by = user_id
            resolution = existing
            action = "RESOLUTION_REVISED"
        else:
            resolution = Resolution(
                session_id=session_id,
                statement=statement.strip(),
                rationale=rationale.strip(),
                decided_by=user_id,
            )
            db.add(resolution)
            action = "RESOLUTION_RECORDED"

        session.status = "resolved"

        # Update divergences review status
        divergences = db.query(Divergence).filter(Divergence.session_id == session_id).all()
        for div in divergences:
            div.review_status = "resolved"

        AuditService.log_event(
            db=db,
            project_id=project_id,
            actor_id=user_id,
            action=action,
            entity_type="resolution",
            entity_id=session.session_id,
            details=f"Recorded official resolution: '{statement.strip()[:80]}...'",
        )

        db.commit()
        db.refresh(resolution)
        return resolution

    @staticmethod
    def get_resolution(db: Session, session_id: int, user_id: int) -> Optional[Resolution]:
        """Fetches the resolution for a session if the caller is an authorized member."""
        session = db.query(InterpretationSession).filter(InterpretationSession.session_id == session_id).first()
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

        project_id = session.requirement_version.requirement.project_id
        ProjectService.require_member(db, project_id, user_id)

        return db.query(Resolution).filter(Resolution.session_id == session_id).first()
