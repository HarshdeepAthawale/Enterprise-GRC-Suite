import boto3
from src.collectors.base import EvidenceCollector, EvidenceResult, CollectorTarget


class CloudTrailEnabledCheck(EvidenceCollector):
    collector_type = "aws_cloudtrail_enabled"
    collector_version = "1.0.0"

    async def collect(self, target: CollectorTarget) -> EvidenceResult:
        ct = boto3.client(
            "cloudtrail",
            aws_access_key_id=target.config.get("access_key_id"),
            aws_secret_access_key=target.config.get("secret_access_key"),
            region_name=target.config.get("region", "us-east-1"),
        )

        trails = ct.describe_trails()["trailList"]
        active_trails = [t for t in trails if t.get("IsLogging", False)]
        multi_region_trails = [t for t in active_trails if t.get("IsMultiRegionTrail", False)]
        log_validated = [t for t in active_trails if t.get("LogFileValidationEnabled", False)]

        return EvidenceResult(
            collector_type=self.collector_type,
            collector_version=self.collector_version,
            raw_data={"trails": trails, "active_count": len(active_trails)},
            structured_result={
                "active_trails": len(active_trails),
                "multi_region_trails": len(multi_region_trails),
                "log_validation_enabled": len(log_validated),
            },
            is_passing=len(active_trails) > 0,
            reason=f"{len(active_trails)} active trails ({len(multi_region_trails)} multi-region, {len(log_validated)} with log validation)" if active_trails else "No active CloudTrail trails found",
            metrics={
                "active_trails": len(active_trails),
                "multi_region_trails": len(multi_region_trails),
                "log_validation_enabled": len(log_validated),
            },
        )

    async def can_run(self, target: CollectorTarget) -> bool:
        return all(k in target.config for k in ("access_key_id", "secret_access_key"))
