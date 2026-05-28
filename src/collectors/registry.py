from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.models.framework import ControlCollectorMapping

COLLECTOR_METADATA: list[dict] = []
COLLECTOR_REGISTRY: dict[str, list] = {}


def register_collector(collector_class, description: str, controls: list[str]):
    COLLECTOR_METADATA.append({
        "type": collector_class.collector_type,
        "description": description,
        "version": collector_class.collector_version,
        "controls": controls,
    })
    for control_ref in controls:
        if control_ref not in COLLECTOR_REGISTRY:
            COLLECTOR_REGISTRY[control_ref] = []
        if collector_class not in COLLECTOR_REGISTRY[control_ref]:
            COLLECTOR_REGISTRY[control_ref].append(collector_class)


from src.collectors.aws.s3_public_access import S3PublicAccessCheck
from src.collectors.aws.iam_key_age import IAMKeyAgeCheck
from src.collectors.aws.security_group_open_ports import SecurityGroupOpenPortsCheck
from src.collectors.aws.cloudtrail_enabled import CloudTrailEnabledCheck
from src.collectors.aws.ec2_encryption import EC2EncryptionCheck
from src.collectors.infra.ssh_password_policy import SSHPasswordPolicyCheck
from src.collectors.infra.tls_version_check import TLSVersionCheck
from src.collectors.infra.patch_level_check import PatchLevelCheck
from src.collectors.infra.disk_encryption_check import DiskEncryptionCheck
from src.collectors.infra.auditd_status import AuditdStatusCheck

register_collector(S3PublicAccessCheck, "Check S3 bucket for public access via bucket policy", ["PR.AC-3"])
register_collector(IAMKeyAgeCheck, "Check IAM access keys are rotated within 90 days", ["PR.AC-1"])
register_collector(SecurityGroupOpenPortsCheck, "Check security groups for 0.0.0.0/0 on sensitive ports", ["PR.AC-3"])
register_collector(CloudTrailEnabledCheck, "Check CloudTrail is active in all regions", ["DE.CM-1"])
register_collector(EC2EncryptionCheck, "Check all EBS volumes have encryption at rest enabled", ["PR.DS-2"])
register_collector(SSHPasswordPolicyCheck, "Check SSH password policy (max days, min length)", ["PR.AC-1"])
register_collector(TLSVersionCheck, "Check TLS version (reject 1.0, 1.1, SSLv3)", ["PR.DS-1"])
register_collector(PatchLevelCheck, "Check pending security patch count", ["ID.RA-1"])
register_collector(DiskEncryptionCheck, "Check LUKS disk encryption status", ["PR.DS-2"])
register_collector(AuditdStatusCheck, "Check auditd service is active and has rules", ["DE.CM-1"])


async def get_collector_config(db: AsyncSession, collector_type: str) -> dict:
    result = await db.execute(
        select(ControlCollectorMapping)
        .where(
            ControlCollectorMapping.collector_type == collector_type,
            ControlCollectorMapping.is_active == True,
        )
        .limit(1)
    )
    mapping = result.scalar_one_or_none()
    if mapping and mapping.collector_params_template:
        return mapping.collector_params_template
    return {}
