from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey, func, UniqueConstraint
from sqlalchemy.orm import relationship
from app.models.base import Base

class Resolution(Base):
    __tablename__ = "resolutions"

    resolution_id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey("interpretation_sessions.session_id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    statement = Column(Text, nullable=False)
    rationale = Column(Text, nullable=False)
    decided_by = Column(Integer, ForeignKey("users.user_id"), nullable=False, index=True)
    decided_at = Column(DateTime, server_default=func.now())

    @property
    def id(self):
        return self.resolution_id

    session = relationship("InterpretationSession", back_populates="resolution")
    decider = relationship("User")
