import asyncio
from sqlalchemy import select
from src.scheduler.worker import app
from src.models.framework import FrameworkControl, ControlCollectorMapping
from src.collectors.registry import COLLECTOR_REGISTRY
from src.collectors.base import CollectorTarget
from src.engine.evaluator import EvaluationEngine
from src.core.database import async_session


@app.task
def run_all_controls():
    asyncio.run(_run_all_controls())


async def _run_all_controls():
    engine = EvaluationEngine()
    async with async_session() as db:
        result = await db.execute(
            select(ControlCollectorMapping).where(ControlCollectorMapping.is_active == True)
        )
        mappings = result.scalars().all()

        for mapping in mappings:
            control = await db.get(FrameworkControl, mapping.framework_control_id)
            if not control:
                continue

            collector_classes = COLLECTOR_REGISTRY.get(control.control_ref, [])
            for cls in collector_classes:
                collector = cls()
                config = mapping.collector_params_template or {}
                target = CollectorTarget(
                    control_ref=str(control.id),
                    config=config,
                )
                try:
                    await engine.run_check(db, collector, target, user_id=None)
                except Exception as e:
                    print(f"Error running {collector.collector_type} on {control.control_ref}: {e}")
