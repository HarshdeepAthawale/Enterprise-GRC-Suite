import boto3
from src.collectors.base import EvidenceCollector, EvidenceResult, CollectorTarget


class SecurityGroupOpenPortsCheck(EvidenceCollector):
    collector_type = "aws_security_group_open_ports"
    collector_version = "1.0.0"
    SENSITIVE_PORTS = [22, 3389, 1433, 3306, 5432, 6379, 27017]

    async def collect(self, target: CollectorTarget) -> EvidenceResult:
        ec2 = boto3.client(
            "ec2",
            aws_access_key_id=target.config.get("access_key_id"),
            aws_secret_access_key=target.config.get("secret_access_key"),
            region_name=target.config.get("region", "us-east-1"),
        )

        sgs = ec2.describe_security_groups()["SecurityGroups"]
        open_rules = []
        for sg in sgs:
            for perm in sg.get("IpPermissions", []):
                for ip_range in perm.get("IpRanges", []):
                    if ip_range.get("CidrIp") == "0.0.0.0/0":
                        port = perm.get("FromPort")
                        if port in self.SENSITIVE_PORTS:
                            open_rules.append({
                                "group_id": sg["GroupId"],
                                "group_name": sg.get("GroupName", ""),
                                "port": port,
                                "protocol": perm.get("IpProtocol", ""),
                            })

        return EvidenceResult(
            collector_type=self.collector_type,
            collector_version=self.collector_version,
            raw_data={"security_groups": len(sgs), "open_rules": open_rules},
            structured_result={"open_sensitive_ports_count": len(open_rules)},
            is_passing=len(open_rules) == 0,
            reason=f"{len(open_rules)} security groups expose sensitive ports to 0.0.0.0/0" if open_rules else "No security groups expose sensitive ports to 0.0.0.0/0",
            metrics={"total_sgs": len(sgs), "open_rules_count": len(open_rules)},
        )

    async def can_run(self, target: CollectorTarget) -> bool:
        return all(k in target.config for k in ("access_key_id", "secret_access_key"))
