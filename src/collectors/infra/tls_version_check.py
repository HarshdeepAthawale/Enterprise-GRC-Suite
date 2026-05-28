import subprocess
import json
from src.collectors.base import EvidenceCollector, EvidenceResult, CollectorTarget


class TLSVersionCheck(EvidenceCollector):
    collector_type = "tls_version_check"
    collector_version = "1.0.0"

    async def collect(self, target: CollectorTarget) -> EvidenceResult:
        host = target.config["host"]
        port = target.config.get("port", "443")

        try:
            result = subprocess.run(
                [
                    "nmap", "--script", "ssl-enum-ciphers",
                    "-p", port, host,
                    "-oX", "-",
                ],
                capture_output=True, text=True, timeout=60,
            )
            stdout = result.stdout

            tls_versions = self._parse_nmap_output(stdout)
            has_weak_tls = any(v in tls_versions for v in ["TLSv1.0", "TLSv1.1", "SSLv3", "SSLv2"])

            return EvidenceResult(
                collector_type=self.collector_type,
                collector_version=self.collector_version,
                raw_data={"nmap_output": stdout[:5000]},
                structured_result={"tls_versions": list(tls_versions), "has_weak_tls": has_weak_tls},
                is_passing=not has_weak_tls,
                reason=f"Weak TLS versions detected: {', '.join(tls_versions & {'TLSv1.0', 'TLSv1.1', 'SSLv3', 'SSLv2'})}" if has_weak_tls
                else f"TLS {', '.join(sorted(tls_versions))} — no weak versions detected",
                metrics={"tls_versions": list(tls_versions)},
            )
        except FileNotFoundError:
            return EvidenceResult(
                collector_type=self.collector_type,
                collector_version=self.collector_version,
                raw_data={"error": "nmap not installed"},
                structured_result={"tls_versions": [], "has_weak_tls": True, "error": "nmap not installed"},
                is_passing=False,
                reason="nmap not installed on collector host",
            )
        except subprocess.TimeoutExpired:
            return EvidenceResult(
                collector_type=self.collector_type,
                collector_version=self.collector_version,
                raw_data={"error": "nmap timed out"},
                structured_result={"tls_versions": [], "has_weak_tls": True, "error": "timeout"},
                is_passing=False,
                reason=f"nmap scan timed out for {host}:{port}",
            )

    def _parse_nmap_output(self, xml_output: str) -> set:
        import re
        versions = set()
        for match in re.finditer(r'<ssl>[^<]*<state>[^<]*</state>[^<]*<protocol>([^<]+)</protocol>', xml_output):
            versions.add(match.group(1))
        if not versions:
            for match in re.finditer(r'TLSv1\.\d|SSLv\d', xml_output):
                versions.add(match.group(0))
        return versions

    async def can_run(self, target: CollectorTarget) -> bool:
        return "host" in target.config
