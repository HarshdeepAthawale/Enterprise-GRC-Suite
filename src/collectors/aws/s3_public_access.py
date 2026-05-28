import boto3
from src.collectors.base import EvidenceCollector, EvidenceResult, CollectorTarget


class S3PublicAccessCheck(EvidenceCollector):
    collector_type = "aws_s3_bucket_policy"
    collector_version = "1.0.0"

    async def collect(self, target: CollectorTarget) -> EvidenceResult:
        s3 = boto3.client(
            "s3",
            aws_access_key_id=target.config.get("access_key_id"),
            aws_secret_access_key=target.config.get("secret_access_key"),
            region_name=target.config.get("region", "us-east-1"),
        )

        bucket = target.config.get("bucket_name", "")
        try:
            policy_resp = s3.get_bucket_policy(Bucket=bucket)
            import json
            policy = json.loads(policy_resp["Policy"]) if isinstance(policy_resp["Policy"], str) else policy_resp["Policy"]
            is_public = any(
                stmt.get("Effect") == "Allow" and stmt.get("Principal") in ("*", {"AWS": "*"})
                for stmt in policy.get("Statement", [])
            )
            return EvidenceResult(
                collector_type=self.collector_type,
                collector_version=self.collector_version,
                raw_data=policy,
                structured_result={"is_public": is_public, "bucket": bucket},
                is_passing=not is_public,
                reason=f"Bucket {bucket} IS publicly accessible" if is_public else f"Bucket {bucket} is NOT public",
            )
        except s3.exceptions.ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "NoSuchBucketPolicy":
                return EvidenceResult(
                    collector_type=self.collector_type,
                    collector_version=self.collector_version,
                    raw_data={},
                    structured_result={"is_public": False, "bucket": bucket, "note": "No bucket policy"},
                    is_passing=True,
                    reason=f"Bucket {bucket} has no bucket policy",
                )
            raise

    async def can_run(self, target: CollectorTarget) -> bool:
        return all(k in target.config for k in ("access_key_id", "secret_access_key", "bucket_name"))
