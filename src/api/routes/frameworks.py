from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from src.core.database import get_db
from src.api.deps import get_current_user
from src.models.user import User
from src.models.framework import FrameworkStandard, ControlCatalog, FrameworkControl

router = APIRouter(prefix="/frameworks", tags=["frameworks"])


@router.get("")
async def list_frameworks(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result = await db.execute(
        select(
            FrameworkStandard.id,
            FrameworkStandard.name,
            FrameworkStandard.version,
            FrameworkStandard.imported_at,
            func.count(FrameworkControl.id).label("control_count"),
        )
        .select_from(FrameworkStandard)
        .outerjoin(ControlCatalog, ControlCatalog.standard_id == FrameworkStandard.id)
        .outerjoin(FrameworkControl, FrameworkControl.catalog_id == ControlCatalog.id)
        .group_by(FrameworkStandard.id)
    )
    rows = result.all()
    return [
        {
            "id": str(row.id),
            "name": row.name,
            "version": row.version,
            "control_count": row.control_count,
            "imported_at": row.imported_at.isoformat() if row.imported_at else None,
        }
        for row in rows
    ]


@router.get("/{framework_id}")
async def get_framework(framework_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result = await db.execute(select(FrameworkStandard).where(FrameworkStandard.id == framework_id))
    framework = result.scalar_one_or_none()
    if not framework:
        raise HTTPException(status_code=404, detail="Framework not found")

    cats_result = await db.execute(
        select(ControlCatalog).where(
            ControlCatalog.standard_id == framework_id,
            ControlCatalog.parent_id.is_(None),
        ).order_by(ControlCatalog.sort_order)
    )
    functions = cats_result.scalars().all()

    return {
        "id": str(framework.id),
        "name": framework.name,
        "version": framework.version,
        "imported_at": framework.imported_at.isoformat() if framework.imported_at else None,
        "functions": [
            {
                "id": str(fn.id),
                "catalog_ref": fn.catalog_ref,
                "title": fn.title,
            }
            for fn in functions
        ],
    }
