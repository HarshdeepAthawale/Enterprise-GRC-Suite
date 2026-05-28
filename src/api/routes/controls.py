from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from src.core.database import get_db
from src.api.deps import get_current_user
from src.models.user import User
from src.models.framework import FrameworkControl, ControlCatalog
from src.models.evidence import CollectedEvidence
from src.engine.evaluator import EvaluationEngine
from src.collectors.registry import COLLECTOR_REGISTRY, get_collector_config
from src.collectors.base import CollectorTarget

router = APIRouter(prefix="/controls", tags=["controls"])


@router.get("")
async def list_controls(
    framework_id: str | None = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = select(
        FrameworkControl.id,
        FrameworkControl.control_ref,
        FrameworkControl.name,
        FrameworkControl.description,
        ControlCatalog.catalog_ref.label("function_ref"),
        ControlCatalog.title.label("function_title"),
    ).join(ControlCatalog, ControlCatalog.id == FrameworkControl.catalog_id)

    if framework_id:
        query = query.where(ControlCatalog.standard_id == framework_id)

    result = await db.execute(query)
    rows = result.all()

    controls_list = []
    for row in rows:
        latest = await db.execute(
            select(CollectedEvidence)
            .where(CollectedEvidence.framework_control_id == row.id)
            .order_by(CollectedEvidence.collected_at.desc())
            .limit(1)
        )
        latest_evidence = latest.scalar_one_or_none()

        controls_list.append({
            "id": str(row.id),
            "control_ref": row.control_ref,
            "name": row.name,
            "description": row.description,
            "function_ref": row.function_ref,
            "function_title": row.function_title,
            "latest_status": latest_evidence.is_passing if latest_evidence else None,
            "last_checked": latest_evidence.collected_at.isoformat() if latest_evidence else None,
            "has_collector": row.control_ref in COLLECTOR_REGISTRY,
        })

    return controls_list


@router.get("/{control_id}")
async def get_control(control_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result = await db.execute(select(FrameworkControl).where(FrameworkControl.id == control_id))
    control = result.scalar_one_or_none()
    if not control:
        raise HTTPException(status_code=404, detail="Control not found")

    evidence_result = await db.execute(
        select(CollectedEvidence)
        .where(CollectedEvidence.framework_control_id == control_id)
        .order_by(CollectedEvidence.collected_at.desc())
        .limit(50)
    )
    evidence_list = evidence_result.scalars().all()

    return {
        "id": str(control.id),
        "control_ref": control.control_ref,
        "name": control.name,
        "description": control.description,
        "catalog_id": str(control.catalog_id),
        "implementation_examples": control.implementation_examples,
        "collectors": COLLECTOR_REGISTRY.get(control.control_ref, []),
        "evidence": [
            {
                "id": str(e.id),
                "collector_type": e.collector_type,
                "is_passing": e.is_passing,
                "pass_fail_reason": e.pass_fail_reason,
                "collected_at": e.collected_at.isoformat() if e.collected_at else None,
            }
            for e in evidence_list
        ],
    }


@router.post("/{control_id}/check")
async def trigger_check(
    control_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    control = await db.get(FrameworkControl, control_id)
    if not control:
        raise HTTPException(404, f"Control {control_id} not found")

    collector_classes = COLLECTOR_REGISTRY.get(control.control_ref, [])
    if not collector_classes:
        raise HTTPException(404, f"No collectors configured for {control.control_ref}")

    engine = EvaluationEngine()
    results = []
    for cls in collector_classes:
        collector = cls()
        config = await get_collector_config(db, collector.collector_type)
        target = CollectorTarget(
            control_ref=str(control_id),
            config=config,
        )
        evidence = await engine.run_check(db, collector, target, user.id)
        results.append({
            "evidence_id": str(evidence.id),
            "collector_type": evidence.collector_type,
            "is_passing": evidence.is_passing,
            "reason": evidence.pass_fail_reason,
            "collected_at": evidence.collected_at.isoformat() if evidence.collected_at else None,
        })

    return {"control": control.control_ref, "checks": len(results), "results": results}
