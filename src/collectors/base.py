from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class CollectorTarget:
    control_ref: str
    config: dict
    credentials_ref: str | None = None


@dataclass
class EvidenceResult:
    collector_type: str
    collector_version: str
    raw_data: dict
    structured_result: dict
    is_passing: bool
    reason: str
    metrics: dict = field(default_factory=dict)


class EvidenceCollector(ABC):
    collector_type: str = ""
    collector_version: str = "1.0.0"

    @abstractmethod
    async def collect(self, target: CollectorTarget) -> EvidenceResult:
        ...

    @abstractmethod
    async def can_run(self, target: CollectorTarget) -> bool:
        ...
