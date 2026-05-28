"""
Seed control→collector mappings for Phase 1 collectors.
Maps NIST CSF 2.0 subcategories to their automated collectors.
"""
import asyncio
from src.core.database import async_session
from src.models.framework import ControlCollectorMapping, FrameworkControl
from sqlalchemy import select

MAPPINGS = {
    "PR.AA-3": ["aws_s3_bucket_policy", "aws_security_group_open_ports"],
    "PR.AA-1": ["aws_iam_key_age", "ssh_password_policy"],
    "DE.CM-1": ["aws_cloudtrail_enabled", "auditd_status"],
    "PR.DS-2": ["aws_ec2_encryption", "disk_encryption_check"],
    "PR.DS-1": ["tls_version_check"],
    "ID.RA-1": ["patch_level_check"],
}


async def seed_mappings():
    async with async_session() as db:
        count = 0
        for control_ref, collector_types in MAPPINGS.items():
            result = await db.execute(
                select(FrameworkControl).where(FrameworkControl.control_ref == control_ref).limit(1)
            )
            control = result.scalar_one_or_none()
            if not control:
                print(f"  WARNING: Control {control_ref} not found in DB. Skipping.")
                continue

            for collector_type in collector_types:
                existing = await db.execute(
                    select(ControlCollectorMapping).where(
                        ControlCollectorMapping.framework_control_id == control.id,
                        ControlCollectorMapping.collector_type == collector_type,
                    ).limit(1)
                )
                if existing.scalar_one_or_none():
                    print(f"  Mapping {control_ref} → {collector_type} already exists")
                    continue

                mapping = ControlCollectorMapping(
                    framework_control_id=control.id,
                    collector_type=collector_type,
                    is_active=True,
                )
                db.add(mapping)
                count += 1
                print(f"  Created: {control_ref} → {collector_type}")

        await db.commit()
        print(f"\nDone. Created {count} new mapping(s).")


if __name__ == "__main__":
    asyncio.run(seed_mappings())
