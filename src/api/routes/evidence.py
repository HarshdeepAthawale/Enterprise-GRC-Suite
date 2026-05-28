from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.core.database import get_db
from src.api.deps import get_current_user
from src.models.user import User
from src.models.evidence import CollectedEvidence

router = APIRouter(prefix="/evidence", tags=["evidence"])


@router.get("/{evidence_id}")
async def get_evidence(evidence_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result = await db.execute(select(CollectedEvidence).where(CollectedEvidence.id == evidence_id))
    evidence = result.scalar_one_or_none()
    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence not found")

    return {
        "id": str(evidence.id),
        "framework_control_id": str(evidence.framework_control_id),
        "collector_type": evidence.collector_type,
        "collector_version": evidence.collector_version,
        "raw_data": evidence.raw_data,
        "structured_result": evidence.structured_result,
        "is_passing": evidence.is_passing,
        "pass_fail_reason": evidence.pass_fail_reason,
        "collected_at": evidence.collected_at.isoformat() if evidence.collected_at else None,
    }


@router.get("/{evidence_id}/raw")
async def get_raw_evidence(evidence_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result = await db.execute(select(CollectedEvidence).where(CollectedEvidence.id == evidence_id))
    evidence = result.scalar_one_or_none()
    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence not found")

    return evidence.raw_data
