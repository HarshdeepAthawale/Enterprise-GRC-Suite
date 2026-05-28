from src.collectors.registry import COLLECTOR_REGISTRY, COLLECTOR_METADATA


class TestCollectorRegistry:
    def test_all_collectors_registered(self):
        assert len(COLLECTOR_METADATA) == 10

        types = {m["type"] for m in COLLECTOR_METADATA}
        expected = {
            "aws_s3_bucket_policy",
            "aws_iam_key_age",
            "aws_security_group_open_ports",
            "aws_cloudtrail_enabled",
            "aws_ec2_encryption",
            "ssh_password_policy",
            "tls_version_check",
            "patch_level_check",
            "disk_encryption_check",
            "auditd_status",
        }
        assert types == expected, f"Missing: {expected - types}"

    def test_registry_has_controls_mapped(self):
        mapped_refs = set(COLLECTOR_REGISTRY.keys())
        expected = {"PR.AC-3", "PR.AC-1", "DE.CM-1", "PR.DS-2", "PR.DS-1", "ID.RA-1"}
        assert mapped_refs == expected

    def test_each_collector_has_description(self):
        for meta in COLLECTOR_METADATA:
            assert meta["description"], f"Missing description for {meta['type']}"
            assert meta["controls"], f"Missing control mapping for {meta['type']}"
