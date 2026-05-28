import asyncssh
from src.collectors.base import EvidenceCollector, EvidenceResult, CollectorTarget


class PatchLevelCheck(EvidenceCollector):
    collector_type = "patch_level_check"
    collector_version = "1.0.0"
    MAX_CRITICAL_PATCHES = 5

    async def collect(self, target: CollectorTarget) -> EvidenceResult:
        async with asyncssh.connect(
            target.config["host"],
            username=target.config.get("username", "root"),
            client_keys=[target.config["key_path"]],
            known_hosts=None,
        ) as conn:
            result = await conn.run(
                "apt list --upgradable 2>/dev/null | grep -c '\\[upgradable\\]' || "
                "yum check-update -q 2>/dev/null | wc -l || "
                "echo '0'"
            )
            try:
                patch_count = int(result.stdout.strip())
            except ValueError:
                patch_count = 0

            return EvidenceResult(
                collector_type=self.collector_type,
                collector_version=self.collector_version,
                raw_data={"stdout": result.stdout, "stderr": result.stderr},
                structured_result={"pending_patches": patch_count, "max_critical": self.MAX_CRITICAL_PATCHES},
                is_passing=patch_count < self.MAX_CRITICAL_PATCHES,
                reason=f"{patch_count} pending patches (threshold: {self.MAX_CRITICAL_PATCHES})" if patch_count >= self.MAX_CRITICAL_PATCHES
                else f"{patch_count} pending patches — within threshold",
                metrics={"pending_patches": patch_count},
            )

    async def can_run(self, target: CollectorTarget) -> bool:
        return all(k in target.config for k in ("host", "key_path"))
