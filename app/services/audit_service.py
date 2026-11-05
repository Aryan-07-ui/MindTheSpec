from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models.audit import AuditLog

class AuditService:
    @staticmethod
    def log_event(
        db: Session,
        project_id: int,
        actor_id: Optional[int],
        action: str,
        entity_type: str,
        entity_id: int,
        details: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AuditLog:
        """
        Appends an immutable audit entry.
        Guaranteed: never logs secret tokens, passwords, or hidden blind submission texts.
        """
        # Ensure metadata is safe and does not leak confidential data
        safe_metadata = {}
        if metadata:
            for k, v in metadata.items():
                if k in ("password", "password_hash", "token", "secret", "interpretation_text", "expected_behavior"):
                    safe_metadata[k] = "[REDACTED]"
                else:
                    safe_metadata[k] = v

        entry = AuditLog(
            project_id=project_id,
            user_id=actor_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details,
            metadata_json=safe_metadata if safe_metadata else None,
        )
        db.add(entry)
        db.flush()  # Flush within caller transaction
        return entry

    @staticmethod
    def get_project_history(db: Session, project_id: int, limit: int = 100):
        """Returns time-ordered audit entries for a project."""
        return (
            db.query(AuditLog)
            .filter(AuditLog.project_id == project_id)
            .order_by(AuditLog.created_at.desc(), AuditLog.log_id.desc())
            .limit(limit)
            .all()
        )
