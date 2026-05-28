import asyncssh
from src.collectors.base import EvidenceCollector, EvidenceResult, CollectorTarget


class AuditdStatusCheck(EvidenceCollector):
    collector_type = "auditd_status"
    collector_version = "1.0.0"

    async def collect(self, target: CollectorTarget) -> EvidenceResult:
        async with asyncssh.connect(
            target.config["host"],
            username=target.config.get("username", "root"),
            client_keys=[target.config["key_path"]],
            known_hosts=None,
        ) as conn:
            status_result = await conn.run("systemctl is-active auditd 2>/dev/null || echo 'inactive'")
            rules_result = await conn.run("auditctl -l 2>/dev/null | head -20 || echo 'no rules'")

            is_active = status_result.stdout.strip() == "active"
            rules = rules_result.stdout.strip()

            return EvidenceResult(
                collector_type=self.collector_type,
                collector_version=self.collector_version,
                raw_data={"service_status": status_result.stdout.strip(), "rules": rules},
                structured_result={
                    "auditd_active": is_active,
                    "rule_count": len(rules.split("\n")) if rules and rules != "no rules" else 0,
                },
                is_passing=is_active,
                reason="auditd is active and running" if is_active else "auditd is NOT running",
                metrics={"auditd_active": is_active, "rule_count": len(rules.split("\n")) if rules and rules != "no rules" else 0},
            )

    async def can_run(self, target: CollectorTarget) -> bool:
        return all(k in target.config for k in ("host", "key_path"))
