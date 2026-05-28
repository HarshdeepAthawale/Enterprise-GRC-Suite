import pytest


@pytest.fixture
def aws_config():
    return {
        "access_key_id": "AKIA_TEST",
        "secret_access_key": "test-secret-key",
        "region": "us-east-1",
        "bucket_name": "test-bucket",
    }


@pytest.fixture
def ssh_config():
    return {
        "host": "192.168.1.100",
        "username": "root",
        "key_path": "/tmp/test-key",
    }


@pytest.fixture
def tls_config():
    return {
        "host": "example.com",
        "port": "443",
    }
