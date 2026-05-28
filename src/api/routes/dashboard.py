from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from src.core.database import get_db
from src.api.deps import get_current_user
from src.models.user import User

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary")
async def dashboard_summary(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result = await db.execute(text("""
        SELECT DISTINCT ON (e.framework_control_id)
            fc.control_ref,
            fc.name,
            e.is_passing,
            e.collected_at,
            e.id as evidence_id,
            cc.catalog_ref as function_ref,
            cc.title as function_title
        FROM evidence e
        JOIN framework_controls fc ON e.framework_control_id = fc.id
        JOIN control_catalogs cc ON fc.catalog_id = cc.id
        ORDER BY e.framework_control_id, e.collected_at DESC
    """))
    rows = result.fetchall()

    total = len(rows)
    passing = sum(1 for r in rows if r.is_passing)
    failing = total - passing

    by_function = {}
    for r in rows:
        fn_ref = r.function_ref
        if fn_ref not in by_function:
            by_function[fn_ref] = {"ref": fn_ref, "title": r.function_title, "total": 0, "passing": 0}
        by_function[fn_ref]["total"] += 1
        if r.is_passing:
            by_function[fn_ref]["passing"] += 1

    for fn in by_function.values():
        fn["pass_rate"] = round((fn["passing"] / fn["total"] * 100), 1) if fn["total"] > 0 else 0

    return {
        "total_controls": total,
        "passing": passing,
        "failing": failing,
        "pass_rate": round((passing / total * 100), 1) if total > 0 else 0,
        "last_updated": max(r.collected_at for r in rows).isoformat() if rows else None,
        "by_function": sorted(by_function.values(), key=lambda x: x["ref"]),
        "failing_controls": [
            {
                "control_ref": r.control_ref,
                "name": r.name,
                "reason": "",
                "collected_at": r.collected_at.isoformat() if r.collected_at else None,
                "evidence_id": str(r.evidence_id),
            }
            for r in rows if not r.is_passing
        ],
    }


@router.get("/heatmap")
async def dashboard_heatmap(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result = await db.execute(text("""
        SELECT DISTINCT ON (e.framework_control_id)
            fc.control_ref,
            fc.name,
            e.is_passing,
            cc.catalog_ref as function_ref,
            cc.title as function_title
        FROM evidence e
        JOIN framework_controls fc ON e.framework_control_id = fc.id
        JOIN control_catalogs cc ON fc.catalog_id = cc.id
        ORDER BY e.framework_control_id, e.collected_at DESC
    """))
    rows = result.fetchall()

    heatmap = {}
    for r in rows:
        fn_ref = r.function_ref
        if fn_ref not in heatmap:
            heatmap[fn_ref] = {"function_ref": fn_ref, "function_title": r.function_title, "controls": []}
        heatmap[fn_ref]["controls"].append({
            "control_ref": r.control_ref,
            "name": r.name,
            "passing": r.is_passing,
        })

    return list(heatmap.values())
