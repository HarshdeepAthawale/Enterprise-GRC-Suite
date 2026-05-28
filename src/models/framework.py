import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, Integer, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from src.models.base import Base


class FrameworkStandard(Base):
    __tablename__ = "framework_standards"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    version = Column(String(20), nullable=False)
    source_url = Column(Text)
    raw_import = Column(JSONB)
    imported_at = Column(DateTime, default=datetime.utcnow)

    catalogs = relationship("ControlCatalog", back_populates="standard", cascade="all, delete-orphan")


class ControlCatalog(Base):
    __tablename__ = "control_catalogs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    standard_id = Column(UUID(as_uuid=True), ForeignKey("framework_standards.id"), nullable=False)
    catalog_ref = Column(String(50))
    title = Column(String(255))
    description = Column(Text)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("control_catalogs.id"))
    sort_order = Column(Integer, default=0)

    standard = relationship("FrameworkStandard", back_populates="catalogs")
    children = relationship("ControlCatalog", backref="parent", remote_side=[id])
    controls = relationship("FrameworkControl", back_populates="catalog", cascade="all, delete-orphan")


class FrameworkControl(Base):
    __tablename__ = "framework_controls"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    catalog_id = Column(UUID(as_uuid=True), ForeignKey("control_catalogs.id"), nullable=False)
    control_ref = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    implementation_examples = Column(JSONB)

    catalog = relationship("ControlCatalog", back_populates="controls")


class ControlCollectorMapping(Base):
    __tablename__ = "control_collector_mappings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    framework_control_id = Column(UUID(as_uuid=True), ForeignKey("framework_controls.id"), nullable=False)
    collector_type = Column(String(100), nullable=False)
    collector_params_template = Column(JSONB)
    is_active = Column(Boolean, default=True)
