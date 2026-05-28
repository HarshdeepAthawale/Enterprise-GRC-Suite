"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-05-28
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "framework_standards",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("version", sa.String(20), nullable=False),
        sa.Column("source_url", sa.Text()),
        sa.Column("raw_import", JSONB()),
        sa.Column("imported_at", sa.DateTime()),
    )

    op.create_table(
        "control_catalogs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("standard_id", UUID(as_uuid=True), sa.ForeignKey("framework_standards.id"), nullable=False),
        sa.Column("catalog_ref", sa.String(50)),
        sa.Column("title", sa.String(255)),
        sa.Column("description", sa.Text()),
        sa.Column("parent_id", UUID(as_uuid=True), sa.ForeignKey("control_catalogs.id")),
        sa.Column("sort_order", sa.Integer(), default=0),
    )

    op.create_table(
        "framework_controls",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("catalog_id", UUID(as_uuid=True), sa.ForeignKey("control_catalogs.id"), nullable=False),
        sa.Column("control_ref", sa.String(50), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("implementation_examples", JSONB()),
    )

    op.create_table(
        "control_collector_mappings",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("framework_control_id", UUID(as_uuid=True), sa.ForeignKey("framework_controls.id"), nullable=False),
        sa.Column("collector_type", sa.String(100), nullable=False),
        sa.Column("collector_params_template", JSONB()),
        sa.Column("is_active", sa.Boolean(), default=True),
    )

    op.create_table(
        "users",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), unique=True, nullable=False, index=True),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("display_name", sa.String(100)),
        sa.Column("is_active", sa.Boolean(), default=True),
        sa.Column("role", sa.String(20), default="admin"),
        sa.Column("created_at", sa.DateTime()),
        sa.Column("updated_at", sa.DateTime()),
    )

    op.create_table(
        "evidence",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("framework_control_id", UUID(as_uuid=True), sa.ForeignKey("framework_controls.id"), nullable=False),
        sa.Column("collector_type", sa.String(50), nullable=False),
        sa.Column("collector_version", sa.String(20)),
        sa.Column("raw_data", JSONB(), nullable=False),
        sa.Column("structured_result", JSONB()),
        sa.Column("collected_at", sa.DateTime(), nullable=False),
        sa.Column("requested_by", UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("is_passing", sa.Boolean(), nullable=False),
        sa.Column("pass_fail_reason", sa.Text()),
    )

    op.create_table(
        "risk_matrices",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(100), default="Default 5x5"),
        sa.Column("likelihood_labels", JSONB()),
        sa.Column("impact_labels", JSONB()),
        sa.Column("matrix", JSONB()),
    )

    op.create_table(
        "risk_assessments",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("control_id", UUID(as_uuid=True), sa.ForeignKey("framework_controls.id")),
        sa.Column("evidence_id", UUID(as_uuid=True), sa.ForeignKey("evidence.id")),
        sa.Column("likelihood", sa.Integer()),
        sa.Column("impact", sa.Integer()),
        sa.Column("risk_score", sa.Integer()),
        sa.Column("risk_level", sa.String(20)),
        sa.Column("notes", sa.Text()),
        sa.Column("assessed_by", UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("assessed_at", sa.DateTime()),
    )


def downgrade() -> None:
    op.drop_table("risk_assessments")
    op.drop_table("risk_matrices")
    op.drop_table("evidence")
    op.drop_table("users")
    op.drop_table("control_collector_mappings")
    op.drop_table("framework_controls")
    op.drop_table("control_catalogs")
    op.drop_table("framework_standards")
