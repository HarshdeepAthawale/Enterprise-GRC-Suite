from datetime import datetime, timezone
import boto3
from src.collectors.base import EvidenceCollector, EvidenceResult, CollectorTarget


class IAMKeyAgeCheck(EvidenceCollector):
    collector_type = "aws_iam_key_age"
    collector_version = "1.0.0"
    MAX_KEY_AGE_DAYS = 90

    async def collect(self, target: CollectorTarget) -> EvidenceResult:
        iam = boto3.client(
            "iam",
            aws_access_key_id=target.config.get("access_key_id"),
            aws_secret_access_key=target.config.get("secret_access_key"),
            region_name=target.config.get("region", "us-east-1"),
        )

        users = iam.list_users()["Users"]
        old_keys = []
        for user in users:
            keys = iam.list_access_keys(UserName=user["UserName"])["AccessKeyMetadata"]
            for key in keys:
                age = (datetime.now(timezone.utc) - key["CreateDate"].replace(tzinfo=timezone.utc)).days
                if age > self.MAX_KEY_AGE_DAYS:
                    old_keys.append({
                        "user": user["UserName"],
                        "key": key["AccessKeyId"],
                        "age_days": age,
                    })

        return EvidenceResult(
            collector_type=self.collector_type,
            collector_version=self.collector_version,
            raw_data={"users": [u["UserName"] for u in users], "old_keys": old_keys},
            structured_result={"old_key_count": len(old_keys), "max_key_age_days": self.MAX_KEY_AGE_DAYS},
            is_passing=len(old_keys) == 0,
            reason=f"{len(old_keys)} IAM keys older than {self.MAX_KEY_AGE_DAYS} days" if old_keys else "All IAM keys within rotation policy",
            metrics={"total_users": len(users), "old_keys_count": len(old_keys)},
        )

    async def can_run(self, target: CollectorTarget) -> bool:
        return all(k in target.config for k in ("access_key_id", "secret_access_key"))
