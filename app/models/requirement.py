from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func, UniqueConstraint
from sqlalchemy.orm import relationship
from app.models.base import Base

class Requirement(Base):
    __tablename__ = "requirements"

    requirement_id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.project_id", ondelete="CASCADE"), nullable=False, index=True)
    req_code = Column(String(50), nullable=False, default="REQ-001")
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    acceptance_criteria = Column(Text, nullable=True)
    priority = Column(String(20), nullable=False, default="medium")  # low, medium, high, critical
    status = Column(String(20), nullable=False, default="active")  # draft, active, resolved, archived
    created_by = Column(Integer, ForeignKey("users.user_id"), nullable=True)
    version = Column(Integer, nullable=False, default=1)
    current_version_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("project_id", "req_code", name="uq_project_req_code"),
    )

    @property
    def id(self):
        return self.requirement_id

    project = relationship("Project", back_populates="requirements")
    creator = relationship("User", foreign_keys=[created_by])
    versions = relationship("RequirementVersion", back_populates="requirement", cascade="all, delete-orphan", order_by="RequirementVersion.version_no")
    interpretations = relationship("Interpretation", back_populates="requirement")


class RequirementVersion(Base):
    __tablename__ = "requirement_versions"

    version_id = Column(Integer, primary_key=True, autoincrement=True)
    requirement_id = Column(Integer, ForeignKey("requirements.requirement_id", ondelete="CASCADE"), nullable=False, index=True)
    version_no = Column(Integer, nullable=False, default=1)
    body = Column(Text, nullable=False)
    acceptance_notes = Column(Text, nullable=True)
    created_by = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("requirement_id", "version_no", name="uq_req_version_no"),
    )

    @property
    def id(self):
        return self.version_id

    requirement = relationship("Requirement", back_populates="versions")
    creator = relationship("User")
    sessions = relationship("InterpretationSession", back_populates="requirement_version")
