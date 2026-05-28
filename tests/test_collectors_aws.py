import pytest
from unittest.mock import patch, MagicMock
from src.collectors.aws.s3_public_access import S3PublicAccessCheck
from src.collectors.aws.iam_key_age import IAMKeyAgeCheck
from src.collectors.aws.security_group_open_ports import SecurityGroupOpenPortsCheck
from src.collectors.aws.cloudtrail_enabled import CloudTrailEnabledCheck
from src.collectors.aws.ec2_encryption import EC2EncryptionCheck
from src.collectors.base import CollectorTarget


class TestS3PublicAccessCheck:
    @pytest.mark.asyncio
    async def test_pass_no_bucket_policy(self, aws_config):
        target = CollectorTarget(control_ref="test", config=aws_config)
        collector = S3PublicAccessCheck()

        assert await collector.can_run(target) is True

        with patch("boto3.client") as mock_boto:
            s3_mock = MagicMock()
            s3_mock.get_bucket_policy.side_effect = type(
                "err", (Exception,), {"response": {"Error": {"Code": "NoSuchBucketPolicy"}}}
            )()
            s3_mock.exceptions.ClientError = Exception
            mock_boto.return_value = s3_mock

            result = await collector.collect(target)
            assert result.is_passing is True
            assert "no bucket policy" in result.reason

    @pytest.mark.asyncio
    async def test_fail_public_bucket(self, aws_config):
        target = CollectorTarget(control_ref="test", config=aws_config)
        collector = S3PublicAccessCheck()

        with patch("boto3.client") as mock_boto:
            s3_mock = MagicMock()
            s3_mock.get_bucket_policy.return_value = {
                "Policy": '{"Statement": [{"Effect": "Allow", "Principal": "*", "Action": "s3:GetObject"}]}'
            }
            mock_boto.return_value = s3_mock

            result = await collector.collect(target)
            assert result.is_passing is False
            assert "publicly accessible" in result.reason

    @pytest.mark.asyncio
    async def test_pass_private_bucket(self, aws_config):
        target = CollectorTarget(control_ref="test", config=aws_config)
        collector = S3PublicAccessCheck()

        with patch("boto3.client") as mock_boto:
            s3_mock = MagicMock()
            s3_mock.get_bucket_policy.return_value = {
                "Policy": '{"Statement": [{"Effect": "Deny", "Principal": "*", "Action": "s3:GetObject"}]}'
            }
            mock_boto.return_value = s3_mock

            result = await collector.collect(target)
            assert result.is_passing is True
            assert "NOT public" in result.reason


class TestIAMKeyAgeCheck:
    @pytest.mark.asyncio
    async def test_pass_all_keys_rotated(self, aws_config):
        target = CollectorTarget(control_ref="test", config=aws_config)
        collector = IAMKeyAgeCheck()

        with patch("boto3.client") as mock_boto:
            iam_mock = MagicMock()
            from datetime import datetime, timezone, timedelta
            recent = datetime.now(timezone.utc) - timedelta(days=30)
            iam_mock.list_users.return_value = {
                "Users": [{"UserName": "alice"}]
            }
            iam_mock.list_access_keys.return_value = {
                "AccessKeyMetadata": [{"AccessKeyId": "AKIA123", "UserName": "alice", "CreateDate": recent}]
            }
            mock_boto.return_value = iam_mock

            result = await collector.collect(target)
            assert result.is_passing is True
            assert "rotation policy" in result.reason

    @pytest.mark.asyncio
    async def test_fail_old_keys(self, aws_config):
        target = CollectorTarget(control_ref="test", config=aws_config)
        collector = IAMKeyAgeCheck()

        with patch("boto3.client") as mock_boto:
            iam_mock = MagicMock()
            from datetime import datetime, timezone, timedelta
            old = datetime.now(timezone.utc) - timedelta(days=200)
            iam_mock.list_users.return_value = {
                "Users": [{"UserName": "alice"}]
            }
            iam_mock.list_access_keys.return_value = {
                "AccessKeyMetadata": [{"AccessKeyId": "AKIA123", "UserName": "alice", "CreateDate": old}]
            }
            mock_boto.return_value = iam_mock

            result = await collector.collect(target)
            assert result.is_passing is False
            assert "older than 90" in result.reason


class TestSecurityGroupOpenPorts:
    @pytest.mark.asyncio
    async def test_pass_no_open_ports(self, aws_config):
        target = CollectorTarget(control_ref="test", config=aws_config)
        collector = SecurityGroupOpenPortsCheck()

        with patch("boto3.client") as mock_boto:
            ec2_mock = MagicMock()
            ec2_mock.describe_security_groups.return_value = {
                "SecurityGroups": [{
                    "GroupId": "sg-123",
                    "GroupName": "default",
                    "IpPermissions": [
                        {"FromPort": 80, "ToPort": 80, "IpProtocol": "tcp", "IpRanges": [{"CidrIp": "10.0.0.0/8"}]}
                    ],
                }]
            }
            mock_boto.return_value = ec2_mock

            result = await collector.collect(target)
            assert result.is_passing is True

    @pytest.mark.asyncio
    async def test_fail_ssh_open_to_world(self, aws_config):
        target = CollectorTarget(control_ref="test", config=aws_config)
        collector = SecurityGroupOpenPortsCheck()

        with patch("boto3.client") as mock_boto:
            ec2_mock = MagicMock()
            ec2_mock.describe_security_groups.return_value = {
                "SecurityGroups": [{
                    "GroupId": "sg-456",
                    "GroupName": "open-ssh",
                    "IpPermissions": [
                        {"FromPort": 22, "ToPort": 22, "IpProtocol": "tcp", "IpRanges": [{"CidrIp": "0.0.0.0/0"}]}
                    ],
                }]
            }
            mock_boto.return_value = ec2_mock

            result = await collector.collect(target)
            assert result.is_passing is False
            assert "sensitive ports" in result.reason


class TestCloudTrailEnabled:
    @pytest.mark.asyncio
    async def test_pass_trails_active(self, aws_config):
        target = CollectorTarget(control_ref="test", config=aws_config)
        collector = CloudTrailEnabledCheck()

        with patch("boto3.client") as mock_boto:
            ct_mock = MagicMock()
            ct_mock.describe_trails.return_value = {
                "trailList": [{
                    "Name": "default",
                    "IsLogging": True,
                    "IsMultiRegionTrail": True,
                    "LogFileValidationEnabled": True,
                }]
            }
            mock_boto.return_value = ct_mock

            result = await collector.collect(target)
            assert result.is_passing is True

    @pytest.mark.asyncio
    async def test_fail_no_trails(self, aws_config):
        target = CollectorTarget(control_ref="test", config=aws_config)
        collector = CloudTrailEnabledCheck()

        with patch("boto3.client") as mock_boto:
            ct_mock = MagicMock()
            ct_mock.describe_trails.return_value = {"trailList": []}
            mock_boto.return_value = ct_mock

            result = await collector.collect(target)
            assert result.is_passing is False


class TestEC2Encryption:
    @pytest.mark.asyncio
    async def test_pass_all_encrypted(self, aws_config):
        target = CollectorTarget(control_ref="test", config=aws_config)
        collector = EC2EncryptionCheck()

        with patch("boto3.client") as mock_boto:
            ec2_mock = MagicMock()
            ec2_mock.describe_volumes.return_value = {
                "Volumes": [
                    {"VolumeId": "vol-001", "Encrypted": True},
                    {"VolumeId": "vol-002", "Encrypted": True},
                ]
            }
            mock_boto.return_value = ec2_mock

            result = await collector.collect(target)
            assert result.is_passing is True
            assert "All" in result.reason

    @pytest.mark.asyncio
    async def test_fail_unencrypted_volumes(self, aws_config):
        target = CollectorTarget(control_ref="test", config=aws_config)
        collector = EC2EncryptionCheck()

        with patch("boto3.client") as mock_boto:
            ec2_mock = MagicMock()
            ec2_mock.describe_volumes.return_value = {
                "Volumes": [
                    {"VolumeId": "vol-001", "Encrypted": True},
                    {"VolumeId": "vol-002", "Encrypted": False},
                ]
            }
            mock_boto.return_value = ec2_mock

            result = await collector.collect(target)
            assert result.is_passing is False
            assert "NOT encrypted" in result.reason
