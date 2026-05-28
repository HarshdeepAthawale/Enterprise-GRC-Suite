"""
API Integration Tests — run against the running Docker services.
"""
import pytest
import httpx

API_BASE = "http://localhost:8000"


class TestAuth:
    def setup_method(self):
        self.client = httpx.Client(base_url=API_BASE, timeout=10)

    def test_health(self):
        r = self.client.get("/api/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"

    def test_login_success(self):
        r = self.client.post("/api/auth/login", json={
            "email": "admin@grcsuite.com",
            "password": "admin123",
        })
        assert r.status_code == 200
        data = r.json()
        assert "access_token" in data
        assert data["email"] == "admin@grcsuite.com"
        assert data["role"] == "admin"

    def test_login_bad_password(self):
        r = self.client.post("/api/auth/login", json={
            "email": "admin@grcsuite.com",
            "password": "wrong",
        })
        assert r.status_code == 401

    def test_register_and_login(self):
        import uuid
        suffix = uuid.uuid4().hex[:6]
        email = f"testuser{suffix}@test.com"

        r = self.client.post("/api/auth/register", json={
            "email": email,
            "password": "testpass123",
            "display_name": "Test User",
        })
        assert r.status_code == 201
        data = r.json()
        assert data["email"] == email
        assert "access_token" in data

    def test_me_authenticated(self):
        login_r = self.client.post("/api/auth/login", json={
            "email": "admin@grcsuite.com",
            "password": "admin123",
        })
        token = login_r.json()["access_token"]

        r = self.client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200
        assert r.json()["email"] == "admin@grcsuite.com"

    def test_me_unauthenticated(self):
        r = self.client.get("/api/auth/me")
        assert r.status_code == 403


class TestFrameworks:
    def setup_method(self):
        self.client = httpx.Client(base_url=API_BASE, timeout=10)
        login_r = self.client.post("/api/auth/login", json={
            "email": "admin@grcsuite.com",
            "password": "admin123",
        })
        self.token = login_r.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}

    def test_list_frameworks(self):
        r = self.client.get("/api/frameworks", headers=self.headers)
        assert r.status_code == 200
        data = r.json()
        assert len(data) >= 1
        assert data[0]["name"] == "NIST Cybersecurity Framework"
        assert data[0]["control_count"] == 106

    def test_get_framework(self):
        r = self.client.get("/api/frameworks", headers=self.headers)
        fw_id = r.json()[0]["id"]

        r = self.client.get(f"/api/frameworks/{fw_id}", headers=self.headers)
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == "NIST Cybersecurity Framework"
        assert len(data["functions"]) == 6


class TestControls:
    def setup_method(self):
        self.client = httpx.Client(base_url=API_BASE, timeout=10)
        login_r = self.client.post("/api/auth/login", json={
            "email": "admin@grcsuite.com",
            "password": "admin123",
        })
        self.token = login_r.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}

    def test_list_controls(self):
        r = self.client.get("/api/controls", headers=self.headers)
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 106
        refs = {c["control_ref"] for c in data}
        assert "PR.AA-3" in refs
        assert "DE.CM-1" in refs

    def test_control_detail(self):
        r = self.client.get("/api/controls", headers=self.headers)
        control_id = r.json()[0]["id"]

        r = self.client.get(f"/api/controls/{control_id}", headers=self.headers)
        assert r.status_code == 200
        data = r.json()
        assert "control_ref" in data
        assert "evidence" in data


class TestDashboard:
    def setup_method(self):
        self.client = httpx.Client(base_url=API_BASE, timeout=10)
        login_r = self.client.post("/api/auth/login", json={
            "email": "admin@grcsuite.com",
            "password": "admin123",
        })
        self.token = login_r.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}

    def test_dashboard_summary(self):
        r = self.client.get("/api/dashboard/summary", headers=self.headers)
        assert r.status_code == 200
        data = r.json()
        assert "total_controls" in data
        assert "pass_rate" in data

    def test_dashboard_heatmap(self):
        r = self.client.get("/api/dashboard/heatmap", headers=self.headers)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)


class TestCollectors:
    def setup_method(self):
        self.client = httpx.Client(base_url=API_BASE, timeout=10)
        login_r = self.client.post("/api/auth/login", json={
            "email": "admin@grcsuite.com",
            "password": "admin123",
        })
        self.token = login_r.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}

    def test_list_collectors(self):
        r = self.client.get("/api/collectors", headers=self.headers)
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 10
        types = {c["type"] for c in data}
        assert "aws_s3_bucket_policy" in types
        assert "auditd_status" in types


class TestRisk:
    def setup_method(self):
        self.client = httpx.Client(base_url=API_BASE, timeout=10)
        login_r = self.client.post("/api/auth/login", json={
            "email": "admin@grcsuite.com",
            "password": "admin123",
        })
        self.token = login_r.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}

    def test_get_risk_matrix(self):
        r = self.client.get("/api/risk/matrix", headers=self.headers)
        assert r.status_code == 200
        data = r.json()
        assert "likelihood_labels" in data
        assert "impact_labels" in data
        assert "matrix" in data
