import asyncssh
from src.collectors.base import EvidenceCollector, EvidenceResult, CollectorTarget


class SSHPasswordPolicyCheck(EvidenceCollector):
    collector_type = "ssh_password_policy"
    collector_version = "1.0.0"

    async def collect(self, target: CollectorTarget) -> EvidenceResult:
        async with asyncssh.connect(
            target.config["host"],
            username=target.config.get("username", "root"),
            client_keys=[target.config["key_path"]],
            known_hosts=None,
        ) as conn:
            result = await conn.run(
                "grep -E '^PASS_MAX_DAYS|^PASS_MIN_LEN|minlen|dcredit|ucredit' "
                "/etc/login.defs /etc/security/pwquality.conf 2>/dev/null"
            )
            stdout = result.stdout.strip()
            parsed = self._parse_policy(stdout)

            return EvidenceResult(
                collector_type=self.collector_type,
                collector_version=self.collector_version,
                raw_data={"stdout": stdout, "stderr": result.stderr},
                structured_result=parsed,
                is_passing=parsed.get("pass_max_days", 99999) <= 90 and parsed.get("minlen", 0) >= 8,
                reason=f"Password max days: {parsed.get('pass_max_days')}, min length: {parsed.get('minlen')}",
                metrics=parsed,
            )

    def _parse_policy(self, text: str) -> dict:
        result = {"pass_max_days": 99999, "minlen": 0}
        for line in text.split("\n"):
            parts = line.split()
            if len(parts) >= 2:
                key = parts[0].split(":")[-1] if ":" in parts[0] else parts[0]
                val = parts[-1]
                if key.upper() == "PASS_MAX_DAYS":
                    try:
                        result["pass_max_days"] = int(val)
                    except ValueError:
                        pass
                elif key == "minlen":
                    try:
                        result["minlen"] = int(val)
                    except ValueError:
                        pass
        return result

    async def can_run(self, target: CollectorTarget) -> bool:
        return all(k in target.config for k in ("host", "key_path"))
