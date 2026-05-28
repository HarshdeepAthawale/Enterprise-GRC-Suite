import boto3
from src.collectors.base import EvidenceCollector, EvidenceResult, CollectorTarget


class EC2EncryptionCheck(EvidenceCollector):
    collector_type = "aws_ec2_encryption"
    collector_version = "1.0.0"

    async def collect(self, target: CollectorTarget) -> EvidenceResult:
        ec2 = boto3.client(
            "ec2",
            aws_access_key_id=target.config.get("access_key_id"),
            aws_secret_access_key=target.config.get("secret_access_key"),
            region_name=target.config.get("region", "us-east-1"),
        )

        volumes = ec2.describe_volumes()["Volumes"]
        unencrypted = [v for v in volumes if not v.get("Encrypted", False)]

        return EvidenceResult(
            collector_type=self.collector_type,
            collector_version=self.collector_version,
            raw_data={"total_volumes": len(volumes), "unencrypted": unencrypted},
            structured_result={
                "total_volumes": len(volumes),
                "unencrypted_count": len(unencrypted),
                "encrypted_count": len(volumes) - len(unencrypted),
            },
            is_passing=len(unencrypted) == 0,
            reason=f"{len(unencrypted)} EBS volumes are NOT encrypted" if unencrypted else f"All {len(volumes)} EBS volumes are encrypted",
            metrics={"total_volumes": len(volumes), "unencrypted_count": len(unencrypted)},
        )

    async def can_run(self, target: CollectorTarget) -> bool:
        return all(k in target.config for k in ("access_key_id", "secret_access_key"))
