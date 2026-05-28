import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from src.models.base import Base


class RiskMatrix(Base):
    __tablename__ = "risk_matrices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), default="Default 5x5")
    likelihood_labels = Column(JSONB)
    impact_labels = Column(JSONB)
    matrix = Column(JSONB)


class RiskAssessment(Base):
    __tablename__ = "risk_assessments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    control_id = Column(UUID(as_uuid=True), ForeignKey("framework_controls.id"))
    evidence_id = Column(UUID(as_uuid=True), ForeignKey("evidence.id"))
    likelihood = Column(Integer)
    impact = Column(Integer)
    risk_score = Column(Integer)
    risk_level = Column(String(20))
    notes = Column(Text)
    assessed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    assessed_at = Column(DateTime, default=datetime.utcnow)
