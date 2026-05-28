from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from src.core.database import get_db
from src.api.deps import get_current_user
from src.models.user import User
from src.collectors.registry import COLLECTOR_REGISTRY, COLLECTOR_METADATA

router = APIRouter(prefix="/collectors", tags=["collectors"])


@router.get("")
async def list_collectors(user: User = Depends(get_current_user)):
    return [
        {
            "type": meta["type"],
            "description": meta.get("description", ""),
            "version": meta.get("version", "1.0.0"),
            "controls": meta.get("controls", []),
        }
        for meta in COLLECTOR_METADATA
    ]


class CollectorConfigRequest(BaseModel):
    config: dict


@router.post("/{collector_type}/config")
async def save_collector_config(
    collector_type: str,
    req: CollectorConfigRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if collector_type not in {m["type"] for m in COLLECTOR_METADATA}:
        raise HTTPException(status_code=404, detail=f"Unknown collector: {collector_type}")

    from src.models.framework import ControlCollectorMapping
    result = await db.execute(
        select(ControlCollectorMapping)
        .where(
            ControlCollectorMapping.collector_type == collector_type,
            ControlCollectorMapping.is_active == True,
        )
        .limit(1)
    )
    mapping = result.scalar_one_or_none()

    if mapping:
        mapping.collector_params_template = req.config
    else:
        mapping = ControlCollectorMapping(
            collector_type=collector_type,
            collector_params_template=req.config,
            is_active=True,
        )
        db.add(mapping)

    await db.commit()
    return {"collector_type": collector_type, "status": "config saved"}
