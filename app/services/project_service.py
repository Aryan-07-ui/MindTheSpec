from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.project import Project, ProjectMember
from app.models.user import User
from app.services.audit_service import AuditService

class ProjectService:
    @staticmethod
    def get_user_role(db: Session, project_id: int, user_id: int) -> Optional[str]:
        """Returns the member role or None if the user is not a member."""
        member = (
            db.query(ProjectMember)
            .filter(ProjectMember.project_id == project_id, ProjectMember.user_id == user_id)
            .first()
        )
        if member:
            return member.role
        project = db.query(Project).filter(Project.project_id == project_id).first()
        if project and project.owner_id == user_id:
            return "owner"
        return None

    @staticmethod
    def require_member(db: Session, project_id: int, user_id: int) -> tuple[Project, str]:
        """Ensures the user has at least membership access to the project."""
        project = db.query(Project).filter(Project.project_id == project_id).first()
        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
        role = ProjectService.get_user_role(db, project_id, user_id)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to view or access this project",
            )
        return project, role

    @staticmethod
    def require_owner(db: Session, project_id: int, user_id: int) -> Project:
        """Ensures the user is the project owner."""
        project, role = ProjectService.require_member(db, project_id, user_id)
        if role != "owner" and project.owner_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the project owner can perform this operation",
            )
        return project

    @staticmethod
    def list_accessible_projects(db: Session, user_id: int) -> List[Project]:
        """Returns only projects the user owns or belongs to as a member."""
        member_project_ids = (
            db.query(ProjectMember.project_id)
            .filter(ProjectMember.user_id == user_id)
            .scalar_subquery()
        )
        return (
            db.query(Project)
            .filter(
                or_(
                    Project.owner_id == user_id,
                    Project.project_id.in_(member_project_ids),
                )
            )
            .order_by(Project.created_at.desc())
            .all()
        )

    @staticmethod
    def create_project(db: Session, title: str, description: Optional[str], owner_id: int) -> Project:
        """Creates a project and registers the owner as an initial member."""
        project = Project(
            project_name=title.strip(),
            description=description.strip() if description else None,
            owner_id=owner_id,
            status="active",
        )
        db.add(project)
        db.flush()

        # Add owner to project_members table
        owner_member = ProjectMember(
            project_id=project.project_id,
            user_id=owner_id,
            role="owner",
        )
        db.add(owner_member)

        # Audit log event
        AuditService.log_event(
            db=db,
            project_id=project.project_id,
            actor_id=owner_id,
            action="PROJECT_CREATED",
            entity_type="project",
            entity_id=project.project_id,
            details=f"Created project '{project.project_name}'",
        )

        db.commit()
        db.refresh(project)
        return project

    @staticmethod
    def add_member(db: Session, project_id: int, owner_id: int, email: str, role: str) -> ProjectMember:
        """Adds an existing registered user to the project as a member."""
        ProjectService.require_owner(db, project_id, owner_id)
        valid_roles = ("analyst", "developer", "tester", "observer")
        if role not in valid_roles:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid role '{role}'. Allowed: {', '.join(valid_roles)}",
            )
        target_user = db.query(User).filter(User.email == email.strip().lower()).first()
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No user found with email '{email}'",
            )
        existing = (
            db.query(ProjectMember)
            .filter(ProjectMember.project_id == project_id, ProjectMember.user_id == target_user.user_id)
            .first()
        )
        if existing:
            existing.role = role
            member = existing
            action = "MEMBER_ROLE_UPDATED"
        else:
            member = ProjectMember(project_id=project_id, user_id=target_user.user_id, role=role)
            db.add(member)
            action = "MEMBER_ADDED"

        AuditService.log_event(
            db=db,
            project_id=project_id,
            actor_id=owner_id,
            action=action,
            entity_type="user",
            entity_id=target_user.user_id,
            details=f"Assigned role '{role}' to {target_user.full_name} ({target_user.email})",
        )
        db.commit()
        return member

    @staticmethod
    def remove_member(db: Session, project_id: int, owner_id: int, user_id: int):
        """Removes a member from the project."""
        project = ProjectService.require_owner(db, project_id, owner_id)
        if user_id == project.owner_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot remove project owner from membership",
            )
        member = (
            db.query(ProjectMember)
            .filter(ProjectMember.project_id == project_id, ProjectMember.user_id == user_id)
            .first()
        )
        if not member:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")
        db.delete(member)
        AuditService.log_event(
            db=db,
            project_id=project_id,
            actor_id=owner_id,
            action="MEMBER_REMOVED",
            entity_type="user",
            entity_id=user_id,
            details=f"Removed member user ID {user_id}",
        )
        db.commit()
