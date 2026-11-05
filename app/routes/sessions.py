from typing import List, Optional
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.session import (
    SessionResponse,
    InterpretationCreate,
    InterpretationResponse,
    ParticipationSummary,
)
from app.schemas.divergence import DivergenceResponse
from app.schemas.resolution import ResolutionCreate, ResolutionResponse
from app.services.auth_service import get_current_user
from app.services.session_service import SessionService
from app.services.divergence_service import DivergenceService
from app.services.resolution_service import ResolutionService

router = APIRouter(tags=["Sessions & Interpretations"])

@router.get("/api/sessions/{session_id}", response_model=SessionResponse)
def get_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieves session status and metadata."""
    session = SessionService.get_session(db, session_id, current_user.user_id)
    return SessionResponse(
        id=session.session_id,
        requirement_version_id=session.requirement_version_id,
        created_by=session.created_by,
        status=session.status,
        mode=session.mode,
        locked_at=session.locked_at,
        created_at=session.created_at,
    )

@router.get("/api/sessions/{session_id}/participation", response_model=ParticipationSummary)
def get_participation_summary(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Returns safe summary counts without leaking participant answers."""
    SessionService.get_session(db, session_id, current_user.user_id)
    summary = SessionService.get_participation_summary(db, session_id)
    return ParticipationSummary(
        session_id=summary["session_id"],
        status=summary["status"],
        mode=summary["mode"],
        total_submissions=summary["total_submissions"],
    )

@router.post("/api/sessions/{session_id}/interpretations", response_model=InterpretationResponse, status_code=status.HTTP_201_CREATED)
def submit_interpretation(
    session_id: int,
    payload: InterpretationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Submits a structured interpretation during the open/collecting phase."""
    interp = SessionService.submit_interpretation(
        db=db,
        session_id=session_id,
        user_id=current_user.user_id,
        perspective=payload.perspective,
        expected_behavior=payload.expected_behavior,
        assumptions=payload.assumptions,
        acceptance_criteria=payload.acceptance_criteria,
        edge_cases=payload.edge_cases,
        notes=payload.notes,
        actor=payload.actor,
        trigger_conditions=payload.trigger_conditions,
        delivery_hours=payload.delivery_hours,
        constraints=payload.constraints,
    )
    return InterpretationResponse(
        id=interp.interpretation_id,
        session_id=interp.session_id,
        user_id=interp.user_id,
        perspective=interp.perspective,
        actor=interp.actor,
        expected_behavior=interp.expected_behavior,
        assumptions=interp.assumptions,
        trigger_conditions=interp.trigger_conditions,
        delivery_hours=interp.delivery_hours,
        constraints=interp.constraints,
        acceptance_criteria=interp.acceptance_criteria,
        edge_cases=interp.edge_cases,
        notes=interp.notes,
        submitted_at=interp.submitted_at,
    )

@router.get("/api/sessions/{session_id}/interpretations", response_model=List[InterpretationResponse])
def get_session_interpretations(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    SERVER-SIDE BLIND ACCESS:
    - Pre-lock: returns ONLY current user's submission.
    - Post-lock / Post-reveal: returns all submissions to authorized members.
    """
    interps = SessionService.get_session_interpretations(db, session_id, current_user.user_id)
    return [
        InterpretationResponse(
            id=i.interpretation_id,
            session_id=i.session_id,
            user_id=i.user_id,
            perspective=i.perspective,
            actor=i.actor,
            expected_behavior=i.expected_behavior,
            assumptions=i.assumptions,
            trigger_conditions=i.trigger_conditions,
            delivery_hours=i.delivery_hours,
            constraints=i.constraints,
            acceptance_criteria=i.acceptance_criteria,
            edge_cases=i.edge_cases,
            notes=i.notes,
            submitted_at=i.submitted_at,
        )
        for i in interps
    ]

@router.get("/api/interpretations/{interpretation_id}", response_model=InterpretationResponse)
def get_interpretation_by_id(
    interpretation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Direct ID lookup with IDOR & blind protection."""
    interp = SessionService.get_single_interpretation(db, interpretation_id, current_user.user_id)
    return InterpretationResponse(
        id=interp.interpretation_id,
        session_id=interp.session_id,
        user_id=interp.user_id,
        perspective=interp.perspective,
        actor=interp.actor,
        expected_behavior=interp.expected_behavior,
        assumptions=interp.assumptions,
        trigger_conditions=interp.trigger_conditions,
        delivery_hours=interp.delivery_hours,
        constraints=interp.constraints,
        acceptance_criteria=interp.acceptance_criteria,
        edge_cases=interp.edge_cases,
        notes=interp.notes,
        submitted_at=interp.submitted_at,
    )

@router.post("/api/sessions/{session_id}/lock", response_model=SessionResponse)
def lock_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Locks session, freezing submissions and computing deterministic divergences."""
    session = SessionService.lock_session(db, session_id, current_user.user_id)
    return SessionResponse(
        id=session.session_id,
        requirement_version_id=session.requirement_version_id,
        created_by=session.created_by,
        status=session.status,
        mode=session.mode,
        locked_at=session.locked_at,
        created_at=session.created_at,
    )

@router.post("/api/sessions/{session_id}/reveal", response_model=SessionResponse)
def reveal_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Reveals session interpretations and divergences to team members."""
    session = SessionService.reveal_session(db, session_id, current_user.user_id)
    return SessionResponse(
        id=session.session_id,
        requirement_version_id=session.requirement_version_id,
        created_by=session.created_by,
        status=session.status,
        mode=session.mode,
        locked_at=session.locked_at,
        created_at=session.created_at,
    )

@router.get("/api/sessions/{session_id}/divergences", response_model=List[DivergenceResponse])
def get_divergences(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieves divergence findings after session is locked/analyzed/revealed."""
    session = SessionService.get_session(db, session_id, current_user.user_id)
    if session.status in ("draft", "open", "collecting"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Divergence findings are confidential until session lock.",
        )
    findings = DivergenceService.get_session_divergences(db, session_id)
    return [
        DivergenceResponse(
            id=d.divergence_id,
            session_id=d.session_id,
            field_name=d.field_name,
            kind=d.kind,
            category=d.category or d.kind,
            severity=d.severity or "medium",
            evidence_json=d.evidence_json,
            review_status=d.review_status,
            fingerprint=d.fingerprint,
            created_at=d.created_at,
        )
        for d in findings
    ]

@router.post("/api/divergences/{divergence_id}/resolve", status_code=status.HTTP_200_OK)
def resolve_individual_divergence(
    divergence_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Marks an individual divergence item as resolved."""
    div = ResolutionService.resolve_divergence(db, divergence_id, current_user.user_id, "resolved")
    return {"message": "Divergence marked as resolved", "divergence_id": div.divergence_id, "review_status": div.review_status}

@router.post("/api/sessions/{session_id}/resolution", response_model=ResolutionResponse, status_code=status.HTTP_201_CREATED)
def record_resolution(
    session_id: int,
    payload: ResolutionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Owner records the final resolution and rationale."""
    res = ResolutionService.record_resolution(
        db=db,
        session_id=session_id,
        user_id=current_user.user_id,
        statement=payload.statement,
        rationale=payload.rationale,
    )
    return ResolutionResponse(
        id=res.resolution_id,
        session_id=res.session_id,
        statement=res.statement,
        rationale=res.rationale,
        decided_by=res.decided_by,
        decided_at=res.decided_at,
    )

@router.get("/api/sessions/{session_id}/resolution", response_model=Optional[ResolutionResponse])
def get_resolution(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Fetches the official resolution for a session."""
    res = ResolutionService.get_resolution(db, session_id, current_user.user_id)
    if not res:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No resolution recorded yet")
    return ResolutionResponse(
        id=res.resolution_id,
        session_id=res.session_id,
        statement=res.statement,
        rationale=res.rationale,
        decided_by=res.decided_by,
        decided_at=res.decided_at,
    )

@router.get("/api/sessions/{session_id}/export/csv")
def export_session_csv(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    FR-15: Authenticated CSV export of divergence findings and resolutions.
    Enforces formula injection defense and strictly denies exporting pre-lock hidden submissions.
    """
    session = SessionService.get_session(db, session_id, current_user.user_id)
    if session.status in ("draft", "open", "collecting"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSV export is restricted until session lock and analysis completion.",
        )

    import io
    import csv

    output = io.StringIO()
    writer = csv.writer(output)

    def sanitize(val):
        if val is None:
            return ""
        s = str(val)
        if s and s[0] in ("=", "+", "-", "@", "\t", "\r"):
            return f"'{s}"
        return s

    # Write Session Metadata
    writer.writerow(["MindTheSpec Divergence Export"])
    writer.writerow(["Session ID", sanitize(session.session_id)])
    writer.writerow(["Requirement Code", sanitize(session.requirement_version.requirement.req_code)])
    writer.writerow(["Requirement Title", sanitize(session.requirement_version.requirement.title)])
    writer.writerow(["Status", sanitize(session.status)])
    writer.writerow([])

    # Write Resolution
    res = ResolutionService.get_resolution(db, session_id, current_user.user_id)
    if res:
        writer.writerow(["Official Resolution"])
        writer.writerow(["Decided At", sanitize(res.decided_at)])
        writer.writerow(["Decision Statement", sanitize(res.statement)])
        writer.writerow(["Rationale", sanitize(res.rationale)])
        writer.writerow([])

    # Write Divergences
    writer.writerow(["Divergence ID", "Category", "Field", "Severity", "Review Status", "Summary", "Explanation"])
    divergences = DivergenceService.get_session_divergences(db, session_id)
    for d in divergences:
        writer.writerow([
            sanitize(d.divergence_id),
            sanitize(d.category or d.kind),
            sanitize(d.field_name),
            sanitize(d.severity or "medium"),
            sanitize(d.review_status),
            sanitize(d.evidence_json.get("summary", "")),
            sanitize(d.evidence_json.get("explanation", "")),
        ])
    writer.writerow([])

    # Write Disclosed Stakeholder Submissions
    writer.writerow(["Participant", "Perspective", "Delivery Hours", "Actor", "Expected Behavior", "Assumptions", "Acceptance Criteria", "Edge Cases", "Notes"])
    interps = SessionService.get_session_interpretations(db, session_id, current_user.user_id)
    for i in interps:
        writer.writerow([
            sanitize(i.user.full_name if i.user else i.user_id),
            sanitize(i.perspective),
            sanitize(i.delivery_hours),
            sanitize(i.actor),
            sanitize(i.expected_behavior),
            sanitize(i.assumptions),
            sanitize(i.acceptance_criteria),
            sanitize(i.edge_cases),
            sanitize(i.notes),
        ])

    from fastapi.responses import Response
    csv_bytes = output.getvalue().encode("utf-8")
    filename = f"mindthespec_session_{session_id}_report.csv"
    return Response(
        content=csv_bytes,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
