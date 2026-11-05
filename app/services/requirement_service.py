from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.requirement import Requirement, RequirementVersion
from app.services.project_service import ProjectService
from app.services.audit_service import AuditService

class RequirementService:
    @staticmethod
    def create_requirement(
        db: Session,
        project_id: int,
        user_id: int,
        req_code: str,
        title: str,
        description: str,
        acceptance_notes: Optional[str] = None,
    ) -> Requirement:
        """Creates a requirement and its initial version (v1) anchored persistently."""
        ProjectService.require_owner(db, project_id, user_id)

        clean_code = req_code.strip().upper()
        existing = (
            db.query(Requirement)
            .filter(Requirement.project_id == project_id, Requirement.req_code == clean_code)
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Requirement with code '{clean_code}' already exists in this project",
            )

        req = Requirement(
            project_id=project_id,
            req_code=clean_code,
            title=title.strip(),
            description=description.strip(),
            status="active",
            version=1,
        )
        db.add(req)
        db.flush()

        # Create version 1
        v1 = RequirementVersion(
            requirement_id=req.requirement_id,
            version_no=1,
            body=description.strip(),
            acceptance_notes=acceptance_notes.strip() if acceptance_notes else None,
            created_by=user_id,
        )
        db.add(v1)
        db.flush()

        req.current_version_id = v1.version_id

        AuditService.log_event(
            db=db,
            project_id=project_id,
            actor_id=user_id,
            action="REQUIREMENT_CREATED",
            entity_type="requirement",
            entity_id=req.requirement_id,
            details=f"Created {clean_code}: '{req.title}' (Version 1)",
        )

        db.commit()
        db.refresh(req)
        return req

    @staticmethod
    def get_requirement(db: Session, requirement_id: int, user_id: int) -> Requirement:
        """Retrieves requirement after verifying project membership."""
        req = db.query(Requirement).filter(Requirement.requirement_id == requirement_id).first()
        if not req:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Requirement not found")
        ProjectService.require_member(db, req.project_id, user_id)
        return req

    @staticmethod
    def list_requirements(db: Session, project_id: int, user_id: int) -> List[Requirement]:
        """Lists all requirements for a project accessible to the user."""
        ProjectService.require_member(db, project_id, user_id)
        return (
            db.query(Requirement)
            .filter(Requirement.project_id == project_id)
            .order_by(Requirement.created_at.desc())
            .all()
        )

    @staticmethod
    def create_revision(
        db: Session,
        requirement_id: int,
        user_id: int,
        new_body: str,
        acceptance_notes: Optional[str] = None,
    ) -> RequirementVersion:
        """Creates an incremented version (v+1) for a requirement."""
        req = db.query(Requirement).filter(Requirement.requirement_id == requirement_id).first()
        if not req:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Requirement not found")
        ProjectService.require_owner(db, req.project_id, user_id)

        next_version_no = req.version + 1
        new_v = RequirementVersion(
            requirement_id=req.requirement_id,
            version_no=next_version_no,
            body=new_body.strip(),
            acceptance_notes=acceptance_notes.strip() if acceptance_notes else None,
            created_by=user_id,
        )
        db.add(new_v)
        db.flush()

        req.version = next_version_no
        req.current_version_id = new_v.version_id
        req.description = new_body.strip()

        AuditService.log_event(
            db=db,
            project_id=req.project_id,
            actor_id=user_id,
            action="REQUIREMENT_REVISED",
            entity_type="requirement",
            entity_id=req.requirement_id,
            details=f"Created revision version {next_version_no} for {req.req_code}",
        )

        db.commit()
        db.refresh(new_v)
        return new_v
