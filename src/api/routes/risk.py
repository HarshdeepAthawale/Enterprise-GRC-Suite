from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from src.core.database import get_db
from src.api.deps import get_current_user
from src.models.user import User
from src.models.risk import RiskMatrix, RiskAssessment

router = APIRouter(prefix="/risk", tags=["risk"])


@router.get("/matrix")
async def get_risk_matrix(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result = await db.execute(select(RiskMatrix).order_by(RiskMatrix.id).limit(1))
    matrix = result.scalar_one_or_none()
    if not matrix:
        return {"message": "No risk matrix configured. Run seed data."}
    return {
        "id": str(matrix.id),
        "name": matrix.name,
        "likelihood_labels": matrix.likelihood_labels,
        "impact_labels": matrix.impact_labels,
        "matrix": matrix.matrix,
    }


class MatrixUpdate(BaseModel):
    name: str | None = None
    likelihood_labels: list[str] | None = None
    impact_labels: list[str] | None = None
    matrix: list[list[int]] | None = None


@router.put("/matrix")
async def update_risk_matrix(
    req: MatrixUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(select(RiskMatrix).order_by(RiskMatrix.id).limit(1))
    matrix = result.scalar_one_or_none()
    if not matrix:
        matrix = RiskMatrix()
        db.add(matrix)

    if req.name is not None:
        matrix.name = req.name
    if req.likelihood_labels is not None:
        matrix.likelihood_labels = req.likelihood_labels
    if req.impact_labels is not None:
        matrix.impact_labels = req.impact_labels
    if req.matrix is not None:
        matrix.matrix = req.matrix

    await db.commit()
    await db.refresh(matrix)
    return {"id": str(matrix.id), "name": matrix.name}


class RiskAssessmentCreate(BaseModel):
    control_id: str
    evidence_id: str
    likelihood: int
    impact: int
    notes: str | None = None


@router.post("/assess")
async def create_risk_assessment(
    req: RiskAssessmentCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    risk_score = req.likelihood * req.impact
    if risk_score >= 16:
        risk_level = "critical"
    elif risk_score >= 10:
        risk_level = "high"
    elif risk_score >= 5:
        risk_level = "medium"
    else:
        risk_level = "low"

    assessment = RiskAssessment(
        control_id=req.control_id,
        evidence_id=req.evidence_id,
        likelihood=req.likelihood,
        impact=req.impact,
        risk_score=risk_score,
        risk_level=risk_level,
        notes=req.notes,
        assessed_by=user.id,
    )
    db.add(assessment)
    await db.commit()
    await db.refresh(assessment)

    return {
        "id": str(assessment.id),
        "risk_score": risk_score,
        "risk_level": risk_level,
        "likelihood": req.likelihood,
        "impact": req.impact,
    }
