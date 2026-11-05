from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func, UniqueConstraint
from sqlalchemy.orm import relationship
from app.models.base import Base

class InterpretationSession(Base):
    __tablename__ = "interpretation_sessions"

    session_id = Column(Integer, primary_key=True, autoincrement=True)
    requirement_version_id = Column(Integer, ForeignKey("requirement_versions.version_id"), nullable=False, index=True)
    created_by = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    status = Column(String(20), nullable=False, default="open")  # open/collecting, locked, revealed/analyzed, resolved
    mode = Column(String(20), nullable=False, default="standard")  # standard, self_comparison
    locked_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    @property
    def id(self):
        return self.session_id

    requirement_version = relationship("RequirementVersion", back_populates="sessions")
    creator = relationship("User")
    interpretations = relationship("Interpretation", back_populates="session", cascade="all, delete-orphan")
    divergences = relationship("Divergence", back_populates="session", cascade="all, delete-orphan")
    resolution = relationship("Resolution", back_populates="session", uselist=False, cascade="all, delete-orphan")


class Interpretation(Base):
    __tablename__ = "interpretations"

    interpretation_id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey("interpretation_sessions.session_id", ondelete="CASCADE"), nullable=False, index=True)
    requirement_id = Column(Integer, ForeignKey("requirements.requirement_id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    perspective = Column(String(100), nullable=False)
    actor = Column(String(100), nullable=True)
    expected_behavior = Column(Text, nullable=False)
    trigger_conditions = Column(Text, nullable=True)
    delivery_hours = Column(Integer, nullable=True)
    constraints = Column(Text, nullable=True)
    acceptance_criteria = Column(Text, nullable=True)
    interpretation_text = Column(Text, nullable=True)
    assumptions = Column(Text, nullable=True)
    edge_cases = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    submitted_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("session_id", "user_id", "perspective", name="uq_session_user_perspective"),
    )

    @property
    def id(self):
        return self.interpretation_id

    session = relationship("InterpretationSession", back_populates="interpretations")
    requirement = relationship("Requirement", back_populates="interpretations")
    user = relationship("User", back_populates="interpretations")
