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
        acceptance_criteria: Optional[str] = None,
        acceptance_notes: Optional[str] = None,
        priority: str = "medium",
    ) -> Requirement:
        """Creates a requirement and its initial version (v1) anchored persistently."""
        project, role = ProjectService.require_member(db, project_id, user_id)
        if role not in ("owner", "analyst"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only project owners and analysts can create requirements",
            )

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

        valid_priorities = ("low", "medium", "high", "critical")
        clean_priority = priority.strip().lower() if priority else "medium"
        if clean_priority not in valid_priorities:
            clean_priority = "medium"

        crit = (acceptance_criteria or acceptance_notes or "").strip() or None

        req = Requirement(
            project_id=project_id,
            req_code=clean_code,
            title=title.strip(),
            description=description.strip(),
            acceptance_criteria=crit,
            priority=clean_priority,
            status="active",
            created_by=user_id,
            version=1,
        )
        db.add(req)
        db.flush()

        # Create version 1
        v1 = RequirementVersion(
            requirement_id=req.requirement_id,
            version_no=1,
            body=description.strip(),
            acceptance_notes=crit,
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
            details=f"Created {clean_code}: '{req.title}' (Version 1, Priority: {clean_priority})",
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
    def update_requirement(
        db: Session,
        requirement_id: int,
        user_id: int,
        title: Optional[str] = None,
        description: Optional[str] = None,
        acceptance_criteria: Optional[str] = None,
        priority: Optional[str] = None,
        status_val: Optional[str] = None,
    ) -> Requirement:
        """Updates requirement metadata. Permitted for owners and analysts."""
        req = db.query(Requirement).filter(Requirement.requirement_id == requirement_id).first()
        if not req:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Requirement not found")

        project, role = ProjectService.require_member(db, req.project_id, user_id)
        if role not in ("owner", "analyst"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only project owners and analysts can update requirements",
            )

        if title is not None:
            clean_title = title.strip()
            if len(clean_title) < 2:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Title too short")
            req.title = clean_title

        if description is not None:
            clean_desc = description.strip()
            if len(clean_desc) < 5:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Description too short")
            req.description = clean_desc

        if acceptance_criteria is not None:
            req.acceptance_criteria = acceptance_criteria.strip() if acceptance_criteria.strip() else None

        if priority is not None:
            clean_priority = priority.strip().lower()
            if clean_priority in ("low", "medium", "high", "critical"):
                req.priority = clean_priority

        if status_val is not None:
            clean_status = status_val.strip().lower()
            if clean_status in ("draft", "active", "resolved", "deprecated"):
                req.status = clean_status

        AuditService.log_event(
            db=db,
            project_id=req.project_id,
            actor_id=user_id,
            action="REQUIREMENT_UPDATED",
            entity_type="requirement",
            entity_id=req.requirement_id,
            details=f"Updated requirement {req.req_code}: '{req.title}'",
        )

        db.commit()
        db.refresh(req)
        return req

    @staticmethod
    def delete_requirement(db: Session, requirement_id: int, user_id: int):
        """Deletes a requirement. Restricted to project owner."""
        req = db.query(Requirement).filter(Requirement.requirement_id == requirement_id).first()
        if not req:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Requirement not found")

        ProjectService.require_owner(db, req.project_id, user_id)

        AuditService.log_event(
            db=db,
            project_id=req.project_id,
            actor_id=user_id,
            action="REQUIREMENT_DELETED",
            entity_type="requirement",
            entity_id=req.requirement_id,
            details=f"Deleted requirement {req.req_code}: '{req.title}'",
        )

        db.delete(req)
        db.commit()

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

        project, role = ProjectService.require_member(db, req.project_id, user_id)
        if role not in ("owner", "analyst"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only project owners and analysts can revise requirements",
            )

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
        if acceptance_notes:
            req.acceptance_criteria = acceptance_notes.strip()

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
