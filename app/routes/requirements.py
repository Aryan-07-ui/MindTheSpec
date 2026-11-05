from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.requirement import RequirementResponse, VersionResponse, RevisionCreate
from app.schemas.session import SessionCreate, SessionResponse
from app.services.auth_service import get_current_user
from app.services.requirement_service import RequirementService
from app.services.session_service import SessionService

router = APIRouter(prefix="/api/requirements", tags=["Requirements"])

@router.get("/{requirement_id}", response_model=RequirementResponse)
def get_requirement(
    requirement_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieves requirement detail."""
    r = RequirementService.get_requirement(db, requirement_id, current_user.user_id)
    return RequirementResponse(
        id=r.requirement_id,
        project_id=r.project_id,
        req_code=r.req_code,
        title=r.title,
        description=r.description,
        status=r.status,
        version=r.version,
        current_version_id=r.current_version_id,
        created_at=r.created_at,
    )

@router.get("/{requirement_id}/versions", response_model=List[VersionResponse])
def list_versions(
    requirement_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Lists historical requirement versions."""
    r = RequirementService.get_requirement(db, requirement_id, current_user.user_id)
    return [
        VersionResponse(
            id=v.version_id,
            version_no=v.version_no,
            body=v.body,
            acceptance_notes=v.acceptance_notes,
            created_by=v.created_by,
            created_at=v.created_at,
        )
        for v in r.versions
    ]

@router.post("/{requirement_id}/sessions", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
def create_session(
    requirement_id: int,
    payload: SessionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Owner starts a new blind interpretation session tied to this requirement."""
    session = SessionService.create_session(
        db=db,
        requirement_id=requirement_id,
        user_id=current_user.user_id,
        version_id=payload.version_id,
        mode=payload.mode,
    )
    return SessionResponse(
        id=session.session_id,
        requirement_version_id=session.requirement_version_id,
        created_by=session.created_by,
        status=session.status,
        mode=session.mode,
        locked_at=session.locked_at,
        created_at=session.created_at,
    )

@router.post("/{requirement_id}/revisions", response_model=VersionResponse, status_code=status.HTTP_201_CREATED)
def create_revision(
    requirement_id: int,
    payload: RevisionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Owner creates an updated version of the requirement."""
    v = RequirementService.create_revision(
        db=db,
        requirement_id=requirement_id,
        user_id=current_user.user_id,
        new_body=payload.body,
        acceptance_notes=payload.acceptance_notes,
    )
    return VersionResponse(
        id=v.version_id,
        version_no=v.version_no,
        body=v.body,
        acceptance_notes=v.acceptance_notes,
        created_by=v.created_by,
        created_at=v.created_at,
    )
