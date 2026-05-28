import asyncssh
from src.collectors.base import EvidenceCollector, EvidenceResult, CollectorTarget


class DiskEncryptionCheck(EvidenceCollector):
    collector_type = "disk_encryption_check"
    collector_version = "1.0.0"

    async def collect(self, target: CollectorTarget) -> EvidenceResult:
        async with asyncssh.connect(
            target.config["host"],
            username=target.config.get("username", "root"),
            client_keys=[target.config["key_path"]],
            known_hosts=None,
        ) as conn:
            result = await conn.run(
                "cryptsetup status 2>/dev/null; "
                "lsblk -o NAME,TYPE,FSTYPE,MOUNTPOINT 2>/dev/null | head -30; "
                "echo '---'; "
                "blkid 2>/dev/null | grep -i 'crypto_LUKS' | wc -l"
            )
            stdout = result.stdout.strip()
            try:
                luks_count = int(stdout.split("---")[-1].strip())
            except (ValueError, IndexError):
                luks_count = 0

            return EvidenceResult(
                collector_type=self.collector_type,
                collector_version=self.collector_version,
                raw_data={"stdout": stdout, "stderr": result.stderr},
                structured_result={"luks_partitions": luks_count, "encryption_active": luks_count > 0},
                is_passing=luks_count > 0,
                reason=f"{luks_count} LUKS encrypted partitions found" if luks_count > 0
                else "No LUKS encrypted partitions detected",
                metrics={"luks_partitions": luks_count},
            )

    async def can_run(self, target: CollectorTarget) -> bool:
        return all(k in target.config for k in ("host", "key_path"))
