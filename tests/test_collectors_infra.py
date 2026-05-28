import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from src.collectors.infra.ssh_password_policy import SSHPasswordPolicyCheck
from src.collectors.infra.patch_level_check import PatchLevelCheck
from src.collectors.infra.disk_encryption_check import DiskEncryptionCheck
from src.collectors.infra.auditd_status import AuditdStatusCheck
from src.collectors.infra.tls_version_check import TLSVersionCheck
from src.collectors.base import CollectorTarget


class AsyncContextMock:
    """Mock that supports async context manager protocol."""

    def __init__(self, stdout="", stderr=""):
        self.stdout = stdout
        self.stderr = stderr

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass

    async def run(self, command):
        result = AsyncMock()
        result.stdout = self.stdout
        result.stderr = self.stderr
        return result


class TestSSHPasswordPolicy:
    @pytest.mark.asyncio
    async def test_good_policy(self, ssh_config):
        target = CollectorTarget(control_ref="test", config=ssh_config)
        collector = SSHPasswordPolicyCheck()

        with patch("asyncssh.connect", return_value=AsyncContextMock(
            stdout="PASS_MAX_DAYS   90\nminlen = 12\n"
        )):
            result = await collector.collect(target)
            assert result.is_passing is True
            assert result.metrics["pass_max_days"] == 90
            assert result.metrics["minlen"] == 12

    @pytest.mark.asyncio
    async def test_bad_policy(self, ssh_config):
        target = CollectorTarget(control_ref="test", config=ssh_config)
        collector = SSHPasswordPolicyCheck()

        with patch("asyncssh.connect", return_value=AsyncContextMock(
            stdout="PASS_MAX_DAYS   365\n"
        )):
            result = await collector.collect(target)
            assert result.is_passing is False
            assert result.metrics["pass_max_days"] == 365

    @pytest.mark.asyncio
    async def test_can_run(self, ssh_config):
        collector = SSHPasswordPolicyCheck()
        target = CollectorTarget(control_ref="test", config=ssh_config)
        assert await collector.can_run(target) is True

        bad_target = CollectorTarget(control_ref="test", config={"host": "x"})
        assert await collector.can_run(bad_target) is False


class TestPatchLevelCheck:
    @pytest.mark.asyncio
    async def test_few_patches(self, ssh_config):
        target = CollectorTarget(control_ref="test", config=ssh_config)
        collector = PatchLevelCheck()

        with patch("asyncssh.connect", return_value=AsyncContextMock(stdout="2\n")):
            result = await collector.collect(target)
            assert result.is_passing is True

    @pytest.mark.asyncio
    async def test_many_patches(self, ssh_config):
        target = CollectorTarget(control_ref="test", config=ssh_config)
        collector = PatchLevelCheck()

        with patch("asyncssh.connect", return_value=AsyncContextMock(stdout="15\n")):
            result = await collector.collect(target)
            assert result.is_passing is False
            assert "threshold" in result.reason


class TestDiskEncryptionCheck:
    @pytest.mark.asyncio
    async def test_luks_active(self, ssh_config):
        target = CollectorTarget(control_ref="test", config=ssh_config)
        collector = DiskEncryptionCheck()

        with patch("asyncssh.connect", return_value=AsyncContextMock(stdout="---\n3\n")):
            result = await collector.collect(target)
            assert result.is_passing is True
            assert result.metrics["luks_partitions"] == 3

    @pytest.mark.asyncio
    async def test_no_luks(self, ssh_config):
        target = CollectorTarget(control_ref="test", config=ssh_config)
        collector = DiskEncryptionCheck()

        with patch("asyncssh.connect", return_value=AsyncContextMock(stdout="---\n0\n")):
            result = await collector.collect(target)
            assert result.is_passing is False


class TestAuditdStatus:
    @pytest.mark.asyncio
    async def test_auditd_active(self, ssh_config):
        target = CollectorTarget(control_ref="test", config=ssh_config)
        collector = AuditdStatusCheck()

        with patch("asyncssh.connect", return_value=AsyncContextMock(stdout="active")):
            result = await collector.collect(target)
            assert result.is_passing is True

    @pytest.mark.asyncio
    async def test_auditd_inactive(self, ssh_config):
        target = CollectorTarget(control_ref="test", config=ssh_config)
        collector = AuditdStatusCheck()

        with patch("asyncssh.connect", return_value=AsyncContextMock(stdout="inactive")):
            result = await collector.collect(target)
            assert result.is_passing is False


class TestTLSVersionCheck:
    @pytest.mark.asyncio
    async def test_modern_tls(self, tls_config):
        target = CollectorTarget(control_ref="test", config=tls_config)
        collector = TLSVersionCheck()

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                stdout='<ssl><protocol>TLSv1.2</protocol></ssl><ssl><protocol>TLSv1.3</protocol></ssl>',
                stderr="",
            )

            result = await collector.collect(target)
            assert result.is_passing is True

    @pytest.mark.asyncio
    async def test_weak_tls_detected(self, tls_config):
        target = CollectorTarget(control_ref="test", config=tls_config)
        collector = TLSVersionCheck()

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                stdout='<ssl><protocol>TLSv1.0</protocol></ssl>',
                stderr="",
            )

            result = await collector.collect(target)
            assert result.is_passing is False
            assert "Weak" in result.reason

    @pytest.mark.asyncio
    async def test_nmap_not_installed(self, tls_config):
        target = CollectorTarget(control_ref="test", config=tls_config)
        collector = TLSVersionCheck()

        with patch("subprocess.run", side_effect=FileNotFoundError):
            result = await collector.collect(target)
            assert result.is_passing is False
            assert "nmap not installed" in result.reason
