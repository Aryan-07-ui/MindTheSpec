from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func, JSON, UniqueConstraint
from sqlalchemy.orm import relationship
from app.models.base import Base

class Divergence(Base):
    __tablename__ = "divergences"

    divergence_id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey("interpretation_sessions.session_id", ondelete="CASCADE"), nullable=False, index=True)
    field_name = Column(String(100), nullable=False)
    kind = Column(String(50), nullable=False, default="structured_mismatch")
    evidence_json = Column(JSON, nullable=False)
    review_status = Column(String(20), nullable=False, default="open")  # open, resolved, ignored
    fingerprint = Column(String(64), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("session_id", "fingerprint", name="uq_session_fingerprint"),
    )

    @property
    def id(self):
        return self.divergence_id

    session = relationship("InterpretationSession", back_populates="divergences")
    divergence_interpretations = relationship("DivergenceInterpretation", back_populates="divergence", cascade="all, delete-orphan")


class DivergenceInterpretation(Base):
    __tablename__ = "divergence_interpretations"

    divergence_id = Column(Integer, ForeignKey("divergences.divergence_id", ondelete="CASCADE"), primary_key=True)
    interpretation_id = Column(Integer, ForeignKey("interpretations.interpretation_id", ondelete="CASCADE"), primary_key=True)

    divergence = relationship("Divergence", back_populates="divergence_interpretations")
    interpretation = relationship("Interpretation")
