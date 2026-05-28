from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from src.collectors.base import EvidenceCollector, CollectorTarget
from src.models.evidence import CollectedEvidence


class EvaluationEngine:
    async def run_check(
        self,
        db: AsyncSession,
        collector: EvidenceCollector,
        target: CollectorTarget,
        user_id: UUID | None = None,
    ) -> CollectedEvidence:
        if not await collector.can_run(target):
            raise ValueError(f"Collector {collector.collector_type} cannot run with provided config")

        result = await collector.collect(target)

        evidence = CollectedEvidence(
            framework_control_id=UUID(target.control_ref),
            collector_type=result.collector_type,
            collector_version=result.collector_version,
            raw_data=result.raw_data,
            structured_result=result.structured_result,
            collected_at=datetime.utcnow(),
            requested_by=user_id,
            is_passing=result.is_passing,
            pass_fail_reason=result.reason,
        )
        db.add(evidence)
        await db.commit()
        await db.refresh(evidence)

        return evidence
