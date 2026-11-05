from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse, MemberAddRequest, MemberResponse
from app.schemas.requirement import RequirementCreate, RequirementResponse
from app.schemas.audit import AuditLogResponse
from app.services.auth_service import get_current_user
from app.services.project_service import ProjectService
from app.services.requirement_service import RequirementService
from app.services.audit_service import AuditService

router = APIRouter(prefix="/api/projects", tags=["Projects"])

@router.get("", response_model=List[ProjectResponse])
def list_projects(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Lists only projects accessible to the authenticated user."""
    projects = ProjectService.list_accessible_projects(db, current_user.user_id)
    return [
        ProjectResponse(
            id=p.project_id,
            title=p.project_name,
            description=p.description,
            owner_id=p.owner_id,
            status=p.status,
            created_at=p.created_at,
        )
        for p in projects
    ]

@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(
    payload: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Creates a new project with the authenticated user as owner."""
    p = ProjectService.create_project(db, payload.title, payload.description, current_user.user_id)
    return ProjectResponse(
        id=p.project_id,
        title=p.project_name,
        description=p.description,
        owner_id=p.owner_id,
        status=p.status,
        created_at=p.created_at,
    )

@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieves project details. Rejects non-members with 403."""
    p, role = ProjectService.require_member(db, project_id, current_user.user_id)
    return ProjectResponse(
        id=p.project_id,
        title=p.project_name,
        description=p.description,
        owner_id=p.owner_id,
        status=p.status,
        created_at=p.created_at,
    )

@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: int,
    payload: ProjectUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Updates project details. Rejects non-owners with 403."""
    p = ProjectService.update_project(
        db, project_id, current_user.user_id, payload.title, payload.description
    )
    return ProjectResponse(
        id=p.project_id,
        title=p.project_name,
        description=p.description,
        owner_id=p.owner_id,
        status=p.status,
        created_at=p.created_at,
    )

@router.delete("/{project_id}", status_code=status.HTTP_200_OK)
def delete_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Deletes project. Rejects non-owners with 403."""
    ProjectService.delete_project(db, project_id, current_user.user_id)
    return {"message": "Project deleted successfully", "project_id": project_id}

@router.get("/{project_id}/members", response_model=List[MemberResponse])
def list_project_members(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Lists all registered members of a project."""
    p, _ = ProjectService.require_member(db, project_id, current_user.user_id)
    return [
        MemberResponse(
            user_id=m.user_id,
            name=m.user.full_name if m.user else f"User {m.user_id}",
            email=m.user.email if m.user else "",
            role=m.role,
            joined_at=m.joined_at,
        )
        for m in p.members
    ]

@router.post("/{project_id}/members", response_model=MemberResponse, status_code=status.HTTP_201_CREATED)
def add_project_member(
    project_id: int,
    payload: MemberAddRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Owner adds or updates a member's role."""
    member = ProjectService.add_member(
        db, project_id, current_user.user_id, payload.email, payload.role
    )
    return MemberResponse(
        user_id=member.user_id,
        name=member.user.full_name,
        email=member.user.email,
        role=member.role,
        joined_at=member.joined_at,
    )

@router.delete("/{project_id}/members/{user_id}", status_code=status.HTTP_200_OK)
def remove_project_member(
    project_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Owner removes a member."""
    ProjectService.remove_member(db, project_id, current_user.user_id, user_id)
    return {"message": "Member removed successfully"}

@router.get("/{project_id}/requirements", response_model=List[RequirementResponse])
def list_requirements(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Lists all requirements for the project."""
    reqs = RequirementService.list_requirements(db, project_id, current_user.user_id)
    return [
        RequirementResponse(
            id=r.requirement_id,
            project_id=r.project_id,
            req_code=r.req_code,
            title=r.title,
            description=r.description,
            acceptance_criteria=r.acceptance_criteria,
            priority=r.priority,
            status=r.status,
            version=r.version,
            current_version_id=r.current_version_id,
            created_by=r.created_by,
            created_at=r.created_at,
        )
        for r in reqs
    ]

@router.post("/{project_id}/requirements", response_model=RequirementResponse, status_code=status.HTTP_201_CREATED)
def create_requirement(
    project_id: int,
    payload: RequirementCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Owner or analyst creates a requirement with initial version 1."""
    req = RequirementService.create_requirement(
        db=db,
        project_id=project_id,
        user_id=current_user.user_id,
        req_code=payload.req_code,
        title=payload.title,
        description=payload.description,
        acceptance_criteria=payload.acceptance_criteria or payload.acceptance_notes,
        priority=payload.priority or "medium",
    )
    return RequirementResponse(
        id=req.requirement_id,
        project_id=req.project_id,
        req_code=req.req_code,
        title=req.title,
        description=req.description,
        acceptance_criteria=req.acceptance_criteria,
        priority=req.priority,
        status=req.status,
        version=req.version,
        current_version_id=req.current_version_id,
        created_by=req.created_by,
        created_at=req.created_at,
    )

@router.get("/{project_id}/audit", response_model=List[AuditLogResponse])
def get_audit_trail(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Chronological project activity history."""
    ProjectService.require_member(db, project_id, current_user.user_id)
    logs = AuditService.get_project_history(db, project_id)
    return [
        AuditLogResponse(
            id=l.log_id,
            project_id=l.project_id,
            actor_id=l.user_id,
            action=l.action,
            entity_type=l.entity_type,
            entity_id=l.entity_id,
            details=l.details,
            metadata_json=l.metadata_json,
            created_at=l.created_at,
        )
        for l in logs
    ]
