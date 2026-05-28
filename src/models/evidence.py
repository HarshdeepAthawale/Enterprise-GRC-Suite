import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from src.models.base import Base


class CollectedEvidence(Base):
    __tablename__ = "evidence"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    framework_control_id = Column(UUID(as_uuid=True), ForeignKey("framework_controls.id"), nullable=False)
    collector_type = Column(String(50), nullable=False)
    collector_version = Column(String(20))
    raw_data = Column(JSONB, nullable=False)
    structured_result = Column(JSONB)
    collected_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    requested_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    is_passing = Column(Boolean, nullable=False)
    pass_fail_reason = Column(Text)
