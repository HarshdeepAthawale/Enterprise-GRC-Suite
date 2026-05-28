# Phase 1: Core Engine — Single Framework, Working Controls

**Duration**: ~5 weeks  
**Goal**: A working GRC tool for ONE framework (NIST CSF 2.0) with 10 automated controls, a dashboard, and risk matrix.  
**Output**: `docker compose up` → login → see controls → run checks → see pass/fail → download report.

---

## Sub-Phase 1A: Foundation Scaffold (Week 1)

### 1A.1 — Project Structure & Docker Compose

Create the skeleton that every subsequent phase builds on.

```
Enterprise-GRC-Suite/
├── docker/
│   ├── docker-compose.yml
│   ├── Dockerfile.api
│   ├── Dockerfile.worker
│   └── Dockerfile.frontend
├── src/
│   ├── api/               # FastAPI app
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── controls.py
│   │   │   ├── evidence.py
│   │   │   ├── frameworks.py
│   │   │   ├── dashboard.py
│   │   │   └── risk.py
│   │   ├── middleware/
│   │   │   └── auth.py
│   │   └── deps.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── database.py       # SQLAlchemy engine + session
│   │   ├── security.py       # JWT hashing, tokens
│   │   └── config.py         # Pydantic settings
│   ├── models/
│   │   ├── __init__.py
│   │   ├── base.py           # Declarative base
│   │   ├── user.py
│   │   ├── framework.py
│   │   ├── control.py
│   │   ├── evidence.py
│   │   └── risk.py
│   ├── collectors/
│   │   ├── __init__.py
│   │   ├── base.py           # Abstract base class
│   │   ├── aws/
│   │   └── infra/
│   ├── engine/
│   │   ├── __init__.py
│   │   ├── evaluator.py
│   │   └── risk.py
│   ├── seed/
│   │   └── import_nist_csf.py
│   ├── scheduler/
│   │   └── __init__.py
│   └── shared/
│       ├── __init__.py
│       └── schemas.py       # Pydantic models
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── lib/
│   │   └── App.tsx
│   └── package.json
├── migrations/               # Alembic
├── tests/
└── plan/
```

### 1A.2 — Docker Compose Configuration

**File**: `docker/docker-compose.yml`

```yaml
version: "3.9"

services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: grc_suite
      POSTGRES_USER: grc_user
      POSTGRES_PASSWORD: ${DB_PASSWORD:-grc_dev_pass}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U grc_user -d grc_suite"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5

  api:
    build:
      context: ..
      dockerfile: docker/Dockerfile.api
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql+asyncpg://grc_user:${DB_PASSWORD:-grc_dev_pass}@postgres:5432/grc_suite
      REDIS_URL: redis://redis:6379/0
      SECRET_KEY: ${SECRET_KEY:-dev-secret-key-change-in-prod}
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - ../src:/app/src
    command: uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload

  worker:
    build:
      context: ..
      dockerfile: docker/Dockerfile.worker
    environment:
      DATABASE_URL: postgresql+asyncpg://grc_user:${DB_PASSWORD:-grc_dev_pass}@postgres:5432/grc_suite
      REDIS_URL: redis://redis:6379/0
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - ../src:/app/src
    command: celery -A src.scheduler.worker worker --loglevel=info --concurrency=4

  beat:
    build:
      context: ..
      dockerfile: docker/Dockerfile.worker
    environment:
      REDIS_URL: redis://redis:6379/0
    depends_on:
      redis:
        condition: service_healthy
    volumes:
      - ../src:/app/src
    command: celery -A src.scheduler.worker beat --loglevel=info

  frontend:
    build:
      context: ../frontend
      dockerfile: ../docker/Dockerfile.frontend
    ports:
      - "3000:3000"
    depends_on:
      - api
    volumes:
      - ../frontend/src:/app/src
      - ../frontend/public:/app/public

volumes:
  postgres_data:
```

**Dockerfile.api** — multi-stage Python build:

```dockerfile
FROM python:3.12-slim AS builder
WORKDIR /app
RUN pip install uv
COPY requirements.txt .
RUN uv pip install --system -r requirements.txt

FROM python:3.12-slim
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY src/ src/
EXPOSE 8000
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Dockerfile.worker**:

```dockerfile
FROM python:3.12-slim
WORKDIR /app
RUN pip install uv
COPY requirements.txt .
RUN uv pip install --system -r requirements.txt
COPY src/ src/
CMD ["celery", "-A", "src.scheduler.worker", "worker", "--loglevel=info"]
```

### 1A.3 — Database Models (SQLAlchemy)

**`src/models/base.py`**:
```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass
```

**`src/models/user.py`**:
```python
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from src.models.base import Base

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    display_name = Column(String(100))
    is_active = Column(Boolean, default=True)
    role = Column(String(20), default="admin")  # admin, auditor, viewer
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

**`src/models/framework.py`**:
```python
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from src.models.base import Base

class FrameworkStandard(Base):
    """Layer 1 in Gemara model — the raw standard itself."""
    __tablename__ = "framework_standards"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)        # "NIST Cybersecurity Framework"
    version = Column(String(20), nullable=False)       # "2.0"
    source_url = Column(Text)
    raw_import = Column(JSONB)                         # Original JSON imported
    imported_at = Column(DateTime, default=datetime.utcnow)

    catalogs = relationship("ControlCatalog", back_populates="standard")

class ControlCatalog(Base):
    """Layer 2 — the organized hierarchy within a standard."""
    __tablename__ = "control_catalogs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    standard_id = Column(UUID(as_uuid=True), ForeignKey("framework_standards.id"), nullable=False)
    catalog_ref = Column(String(50))                   # "CSF 2.0 Core"
    title = Column(String(255))
    description = Column(Text)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("control_catalogs.id"))
    sort_order = Column(Integer, default=0)

    standard = relationship("FrameworkStandard", back_populates="catalogs")
    children = relationship("ControlCatalog", backref="parent", remote_side=[id])
    controls = relationship("FrameworkControl", back_populates="catalog")

class FrameworkControl(Base):
    """Leaf-level control in a framework taxonomy."""
    __tablename__ = "framework_controls"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    catalog_id = Column(UUID(as_uuid=True), ForeignKey("control_catalogs.id"), nullable=False)
    control_ref = Column(String(50), nullable=False)   # "PR.AC-3", "GV.OC-1"
    name = Column(String(255), nullable=False)
    description = Column(Text)
    implementation_examples = Column(JSONB)             # NIST CSF has these built in

    catalog = relationship("ControlCatalog", back_populates="controls")
```

**`src/models/evidence.py`** (simplified for Phase 1):
```python
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from src.models.base import Base

class CollectedEvidence(Base):
    """A single evidence collection event. Chain-of-custody added in Phase 4."""
    __tablename__ = "evidence"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    framework_control_id = Column(UUID(as_uuid=True), ForeignKey("framework_controls.id"), nullable=False)

    collector_type = Column(String(50), nullable=False)   # "aws_s3_get_bucket_policy"
    collector_version = Column(String(20))

    raw_data = Column(JSONB, nullable=False)
    structured_result = Column(JSONB)

    collected_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    requested_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))

    is_passing = Column(Boolean, nullable=False)
    pass_fail_reason = Column(Text)
```

**`src/models/risk.py`**:
```python
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from src.models.base import Base

class RiskMatrix(Base):
    """Configurable 5x5 risk matrix template."""
    __tablename__ = "risk_matrices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), default="Default 5x5")
    likelihood_labels = Column(JSONB)    # ["Rare", "Unlikely", "Possible", "Likely", "Almost Certain"]
    impact_labels = Column(JSONB)        # ["Insignificant", "Minor", "Moderate", "Major", "Critical"]
    matrix = Column(JSONB)               # 5x5 grid of severity values

class RiskAssessment(Base):
    """A risk assessment linked to a control failure."""
    __tablename__ = "risk_assessments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    control_id = Column(UUID(as_uuid=True), ForeignKey("framework_controls.id"))
    evidence_id = Column(UUID(as_uuid=True), ForeignKey("evidence.id"))

    likelihood = Column(Integer)          # 1-5
    impact = Column(Integer)             # 1-5
    risk_score = Column(Integer)         # likelihood × impact
    risk_level = Column(String(20))      # low / medium / high / critical

    notes = Column(Text)
    assessed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    assessed_at = Column(DateTime, default=datetime.utcnow)
```

### 1A.4 — Auth System (JWT)

**`src/core/security.py`**:
```python
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from passlib.context import CryptContext
from src.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = "HS256"

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def create_access_token(user_id: str, expires_delta: timedelta = timedelta(hours=24)) -> str:
    payload = {
        "sub": user_id,
        "exp": datetime.now(timezone.utc) + expires_delta,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None
```

**Routes**: `POST /api/auth/register`, `POST /api/auth/login`, `GET /api/auth/me`

### 1A.5 — NIST CSF 2.0 Importer

NIST publishes the CSF 2.0 Core as machine-readable JSON via their [CSF 2.0 Reference Tool](https://csrc.nist.gov/Projects/Cybersecurity-Framework/Filters#/csf/filters). 

**`src/seed/import_nist_csf.py`**:
```python
"""
Import NIST CSF 2.0 Core into the database.
Downloads from NIST's official machine-readable JSON.

CSF 2.0 structure:
  6 Functions (Govern, Identify, Protect, Detect, Respond, Recover)
  22 Categories
  106 Subcategories (these are our controls)
"""

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

NIST_CSF_URL = "https://csrc.nist.gov/csaf/csf/2.0/csf.json"

async def import_nist_csf(db: AsyncSession):
    # 1. Download the JSON
    async with httpx.AsyncClient() as client:
        resp = await client.get(NIST_CSF_URL)
        data = resp.json()

    # 2. Create FrameworkStandard row
    standard = FrameworkStandard(
        name="NIST Cybersecurity Framework",
        version="2.0",
        raw_import=data,
    )
    db.add(standard)
    await db.flush()

    # 3. Parse Functions → Categories → Subcategories
    #    Functions and Categories are ControlCatalog entries (hierarchical)
    #    Subcategories are FrameworkControl entries

    for func in data["functions"]:
        func_cat = ControlCatalog(
            standard_id=standard.id,
            catalog_ref=func["id"],        # "GV", "ID", "PR", etc.
            title=func["name"],
            description=func.get("description", ""),
        )
        db.add(func_cat)
        await db.flush()

        for cat in func.get("categories", []):
            cat_cat = ControlCatalog(
                standard_id=standard.id,
                catalog_ref=cat["id"],
                title=cat["name"],
                parent_id=func_cat.id,
                description=cat.get("description", ""),
            )
            db.add(cat_cat)
            await db.flush()

            for subcat in cat.get("subcategories", []):
                control = FrameworkControl(
                    catalog_id=cat_cat.id,
                    control_ref=subcat["id"],     # "GV.OC-1", "PR.AC-3"
                    name=subcat["name"],
                    description=subcat.get("description", ""),
                    implementation_examples=subcat.get("implementation_examples", []),
                )
                db.add(control)

    await db.commit()
```

### 1A.6 — Verification Gate

```
[ ] docker compose up starts all 5 services without errors
[ ] POST /api/auth/register creates a user
[ ] POST /api/auth/login returns a JWT token
[ ] Import NIST CSF → 1 standard, 6 functions, 22 categories, 106 controls in DB
[ ] GET /api/frameworks returns NIST CSF with control count
[ ] Frontend loads at localhost:3000 and shows login page
```

---

## Sub-Phase 1B: Collectors (Weeks 2-3)

### 1B.1 — Collector Base Class

**`src/collectors/base.py`**:
```python
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

@dataclass
class CollectorTarget:
    """What to check."""
    control_ref: str
    config: dict                                  # Bucket name, host, region, etc.
    credentials_ref: str | None = None            # Reference to stored credentials

@dataclass
class EvidenceResult:
    """What was found."""
    collector_type: str
    collector_version: str
    raw_data: dict                                # The full API response / command output
    structured_result: dict                       # Parsed key values for evaluation
    is_passing: bool
    reason: str
    metrics: dict = field(default_factory=dict)   # Extra data for dashboard

class EvidenceCollector(ABC):
    """Every collector implements this. Add new collectors without changing core."""

    collector_type: str = ""
    collector_version: str = "1.0.0"

    @abstractmethod
    async def collect(self, target: CollectorTarget) -> EvidenceResult:
        """Execute the check. Must be safe to call (no side effects on target)."""
        ...

    @abstractmethod
    async def can_run(self, target: CollectorTarget) -> bool:
        """Verify credentials are valid and target is reachable."""
        ...
```

### 1B.2 — AWS Collectors (5 checks)

**Setup**: Uses boto3. Credentials stored securely in DB, passed to collector via `CollectorTarget.config`.

**`src/collectors/aws/s3_public_access.py`**:
```python
import boto3
from src.collectors.base import EvidenceCollector, EvidenceResult, CollectorTarget

class S3PublicAccessCheck(EvidenceCollector):
    collector_type = "aws_s3_bucket_policy"
    collector_version = "1.0.0"

    async def collect(self, target: CollectorTarget) -> EvidenceResult:
        s3 = boto3.client(
            "s3",
            aws_access_key_id=target.config["access_key_id"],
            aws_secret_access_key=target.config["secret_access_key"],
            region_name=target.config.get("region", "us-east-1"),
        )

        bucket = target.config["bucket_name"]
        try:
            policy_resp = s3.get_bucket_policy(Bucket=bucket)
            policy = policy_resp["Policy"]
            # Check for public access grants
            is_public = any(
                stmt["Effect"] == "Allow" and stmt["Principal"] == "*"
                for stmt in policy.get("Statement", [])
            )
            return EvidenceResult(
                collector_type=self.collector_type,
                collector_version=self.collector_version,
                raw_data=policy,
                structured_result={"is_public": is_public, "bucket": bucket},
                is_passing=not is_public,
                reason=f"Bucket {bucket} IS publicly accessible" if is_public else f"Bucket {bucket} is NOT public",
            )
        except s3.exceptions.from_code("NoSuchBucketPolicy"):
            # No policy = no bucket-level public access (not the only vector)
            return EvidenceResult(
                collector_type=self.collector_type,
                collector_version=self.collector_version,
                raw_data={},
                structured_result={"is_public": False, "bucket": bucket, "note": "No bucket policy"},
                is_passing=True,
                reason=f"Bucket {bucket} has no bucket policy",
            )

    async def can_run(self, target: CollectorTarget) -> bool:
        return all(k in target.config for k in ("access_key_id", "secret_access_key", "bucket_name"))
```

**`src/collectors/aws/iam_key_age.py`**:
```python
class IAMKeyAgeCheck(EvidenceCollector):
    collector_type = "aws_iam_key_age"
    collector_version = "1.0.0"
    MAX_KEY_AGE_DAYS = 90

    async def collect(self, target: CollectorTarget) -> EvidenceResult:
        iam = boto3.client("iam", ...)
        users = iam.list_users()["Users"]
        old_keys = []
        for user in users:
            keys = iam.list_access_keys(UserName=user["UserName"])["AccessKeyMetadata"]
            for key in keys:
                age = (datetime.now(timezone.utc) - key["CreateDate"]).days
                if age > self.MAX_KEY_AGE_DAYS:
                    old_keys.append({"user": user["UserName"], "key": key["AccessKeyId"], "age_days": age})
        return EvidenceResult(
            raw_data={"users_with_old_keys": old_keys},
            is_passing=len(old_keys) == 0,
            reason=f"{len(old_keys)} IAM keys older than {self.MAX_KEY_AGE_DAYS} days" if old_keys else "All IAM keys within rotation policy",
            ...
        )
```

**`src/collectors/aws/security_group_open_ports.py`**: Checks for 0.0.0.0/0 on SSH (22), RDP (3389), or admin ports.

**`src/collectors/aws/cloudtrail_enabled.py`**: Checks that CloudTrail is enabled in all regions, with log file validation enabled.

**`src/collectors/aws/ec2_encryption.py`**: Checks that all EBS volumes have encryption-at-rest enabled.

### 1B.3 — Infrastructure Collectors (5 checks)

**`src/collectors/infra/ssh_password_policy.py`**:
```python
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
        ) as conn:
            # Check /etc/security/pwquality.conf and /etc/login.defs
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
                is_passing=parsed["pass_max_days"] <= 90 and parsed.get("minlen", 0) >= 8,
                reason=f"Password max days: {parsed.get('pass_max_days')}, min length: {parsed.get('minlen')}",
                metrics=parsed,
            )

    def _parse_policy(self, text: str) -> dict:
        result = {"pass_max_days": 99999, "minlen": 0}
        for line in text.split("\n"):
            parts = line.split()
            if len(parts) >= 2:
                if parts[0].upper() == "PASS_MAX_DAYS":
                    result["pass_max_days"] = int(parts[-1])
                elif parts[0] == "minlen":
                    result["minlen"] = int(parts[-1])
        return result
```

**`src/collectors/infra/tls_version_check.py`**: Uses `sslscan` or `nmap --script ssl-enum-ciphers` to check TLS version on web servers. Pass = TLS 1.2+ only.

**`src/collectors/infra/patch_level_check.py`**: SSH + `apt list --upgradable` or `yum check-update`. Counts available security patches. Pass = < 5 critical patches.

**`src/collectors/infra/disk_encryption_check.py`**: SSH + check LUKS (`cryptsetup status`) or BitLocker status. Pass = system encryption active.

**`src/collectors/infra/auditd_status.py`**: SSH + `systemctl status auditd` + check rules. Pass = auditd active and key events are logged.

### 1B.4 — Collector Registry

```python
from src.collectors.aws.s3_public_access import S3PublicAccessCheck
from src.collectors.aws.iam_key_age import IAMKeyAgeCheck
from src.collectors.aws.security_group_open_ports import SecurityGroupOpenPortsCheck
from src.collectors.aws.cloudtrail_enabled import CloudTrailEnabledCheck
from src.collectors.aws.ec2_encryption import EC2EncryptionCheck
from src.collectors.infra.ssh_password_policy import SSHPasswordPolicyCheck
from src.collectors.infra.tls_version_check import TLSVersionCheck
from src.collectors.infra.patch_level_check import PatchLevelCheck
from src.collectors.infra.disk_encryption_check import DiskEncryptionCheck
from src.collectors.infra.auditd_status import AuditdStatusCheck

# Maps NIST CSF subcategory → collector class
COLLECTOR_REGISTRY = {
    "PR.AC-3":   [S3PublicAccessCheck, SecurityGroupOpenPortsCheck],
    "PR.AC-1":   [IAMKeyAgeCheck, SSHPasswordPolicyCheck],
    "DE.CM-1":   [CloudTrailEnabledCheck, AuditdStatusCheck],
    "PR.DS-2":   [EC2EncryptionCheck, DiskEncryptionCheck],
    "PR.DS-1":   [TLSVersionCheck],
    "ID.RA-1":   [PatchLevelCheck],
}
```

### 1B.5 — Verification Gate

```
[ ] s3_public_access: returns correct pass/fail for public vs. private buckets
[ ] iam_key_age: correctly calculates key age
[ ] security_group: detects 0.0.0.0/0 rules
[ ] cloudtrail: detects disabled trails
[ ] ec2_encryption: detects unencrypted volumes
[ ] ssh_password_policy: returns correct parsed values
[ ] tls_version: detects TLS 1.0/1.1 vs 1.2/1.3
[ ] patch_level: returns integer count of pending patches
[ ] disk_encryption: detects LUKS/BitLocker status
[ ] auditd: detects auditd running vs stopped
[ ] Collector registry can list all available collectors
[ ] GET /api/collectors returns all 10 collectors with descriptions
```

---

## Sub-Phase 1C: Evaluation Engine & API (Week 4)

### 1C.1 — Evaluation Engine

**`src/engine/evaluator.py`**:
```python
"""
Takes a CollectorTarget + collector → runs check → stores evidence → updates dashboard.
This is the orchestrator that ties collectors to the database.
"""
from uuid import UUID
from datetime import datetime
from src.collectors.base import EvidenceCollector, CollectorTarget
from src.models.evidence import CollectedEvidence

class EvaluationEngine:
    async def run_check(
        self,
        db: AsyncSession,
        collector: EvidenceCollector,
        target: CollectorTarget,
        user_id: UUID | None = None,
    ) -> CollectedEvidence:
        """Run a single check and persist the evidence."""

        # 1. Validate
        if not await collector.can_run(target):
            raise ValueError(f"Collector {collector.collector_type} cannot run with provided config")

        # 2. Execute
        result = await collector.collect(target)

        # 3. Store
        evidence = CollectedEvidence(
            framework_control_id=UUID(target.control_ref),
            collector_type=result.collector_type,
            collector_version=result.collector_version,
            raw_data=result.raw_data,
            structured_result=result.structured_result,
            collected_at=datetime.utcnow(),
            requested_by=user_id,
            is_passing=result.is_passing,
            pass_fail_reason=result.reason,
        )
        db.add(evidence)
        await db.commit()
        await db.refresh(evidence)

        return evidence
```

### 1C.2 — API Routes

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/auth/register` | Create account |
| POST | `/api/auth/login` | Get JWT |
| GET | `/api/auth/me` | Current user |
| GET | `/api/frameworks` | List frameworks with control counts |
| GET | `/api/frameworks/{id}/controls` | List controls with pass/fail status |
| GET | `/api/controls/{id}` | Single control detail + last 50 evidence |
| POST | `/api/controls/{id}/check` | Trigger a manual re-check |
| GET | `/api/collectors` | List available collectors |
| POST | `/api/collectors/{type}/config` | Save credentials for a collector |
| GET | `/api/dashboard/summary` | Pass rate, control counts, risk levels |
| GET | `/api/dashboard/heatmap` | Grid of controls × pass/fail for NIST CSF |
| GET | `/api/evidence/{id}` | Single evidence detail with raw data |
| GET | `/api/evidence/{id}/raw` | Raw response body |
| GET | `/api/risk/matrix` | Current risk matrix configuration |
| PUT | `/api/risk/matrix` | Update risk matrix |
| POST | `/api/risk/assess` | Create risk assessment for a finding |

### 1C.3 — Key API Implementation Patterns

**Trigger a check**:
```python
@router.post("/controls/{control_id}/check")
async def trigger_check(
    control_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # 1. Find which collectors map to this control
    control = await db.get(FrameworkControl, control_id)
    collector_classes = COLLECTOR_REGISTRY.get(control.control_ref, [])

    if not collector_classes:
        raise HTTPException(404, f"No collectors configured for {control.control_ref}")

    # 2. Run each collector
    engine = EvaluationEngine()
    results = []
    for cls in collector_classes:
        collector = cls()
        config = await get_collector_config(db, collector.collector_type)
        target = CollectorTarget(
            control_ref=control_id,
            config=config,
        )
        evidence = await engine.run_check(db, collector, target, user.id)
        results.append(evidence)

    return {"control": control.control_ref, "checks": len(results), "results": results}
```

**Dashboard summary**:
```python
@router.get("/dashboard/summary")
async def dashboard_summary(db: AsyncSession = Depends(get_db)):
    # Latest evidence per control
    latest = await db.execute("""
        SELECT DISTINCT ON (framework_control_id)
            fc.control_ref,
            fc.name,
            e.is_passing,
            e.collected_at,
            e.id as evidence_id
        FROM evidence e
        JOIN framework_controls fc ON e.framework_control_id = fc.id
        ORDER BY framework_control_id, collected_at DESC
    """)
    rows = latest.fetchall()

    total = len(rows)
    passing = sum(1 for r in rows if r.is_passing)
    failing = total - passing

    return {
        "total_controls": total,
        "passing": passing,
        "failing": failing,
        "pass_rate": round((passing / total * 100), 1) if total > 0 else 0,
        "last_updated": max(r.collected_at for r in rows) if rows else None,
        "controls": [{"ref": r.control_ref, "name": r.name, "passing": r.is_passing} for r in rows],
    }
```

### 1C.4 — Verification Gate

```
[ ] POST /api/controls/{id}/check runs a collector and stores evidence
[ ] GET /api/dashboard/summary returns correct pass/fail counts
[ ] GET /api/dashboard/heatmap returns a grid of 106 controls × pass/fail
[ ] GET /api/evidence/{id} returns full evidence with raw_data
[ ] Collectors handle errors gracefully (timeout, bad credentials, unreachable host)
[ ] Evidence stores fail reason when check errors vs when check fails
```

---

## Sub-Phase 1D: Frontend (Week 4-5)

### 1D.1 — Tech Stack

- React 19 + TypeScript
- React Router v7 for routing
- Chart.js + react-chartjs-2 for visualizations
- Tailwind CSS v4 for styling
- Axios for API calls

### 1D.2 — Pages

```
/login                  → Login/Register
/dashboard              → Summary + heat map + trend
/dashboard/heatmap      → Full-screen control heat grid
/frameworks             → List frameworks with import option
/frameworks/{id}        → Framework detail with controls list
/controls/{id}          → Control detail + evidence history
/evidence/{id}          → Evidence raw data view
/collectors             → Manage collector configs
/risk                   → Risk matrix + assessments
```

### 1D.3 — Dashboard Wireframe

```
┌──────────────────────────────────────────────────┐
│  Enterprise GRC Suite               User ▲       │
├──────────────────────────────────────────────────┤
│                                                   │
│  ┌──────────────┐  ┌──────────────┐              │
│  │ Compliance    │  │ Controls     │              │
│  │ Score         │  │ Checked      │              │
│  │    87.3%     │  │    1,234     │              │
│  └──────────────┘  └──────────────┘              │
│  ┌──────────────┐  ┌──────────────┐              │
│  │ Passing      │  │ Failing      │              │
│  │     92       │  │     14       │              │
│  └──────────────┘  └──────────────┘              │
│                                                   │
│  Control Heat Map (NIST CSF 2.0)                  │
│  ┌───────┬───────┬───────┬───────┬───────┬──────┐ │
│  │  GV   │  ID   │  PR   │  DE   │  RS   │  RC  │ │
│  │ █████ │ ████  │ ████  │ █████ │  ██   │ ████ │ │
│  │ 92%   │ 85%   │ 78%   │ 95%   │ 100%  │ 90%  │ │
│  └───────┴───────┴───────┴───────┴───────┴──────┘ │
│                                                   │
│  Recent Failures                                   │
│  ┌──────────────────────────────────────────┐     │
│  │ PR.AC-3  S3 public access   2h ago  🔴  │     │
│  │ PR.DS-2  EC2 no encryption  6h ago  🔴  │     │
│  │ ID.RA-1  15 critical patches 1d ago 🔴  │     │
│  └──────────────────────────────────────────┘     │
│                                                   │
│  [Re-run All Failing] [Export Report]              │
└──────────────────────────────────────────────────┘
```

### 1D.4 — Key Frontend Component: HeatMap

```typescript
// src/pages/Dashboard.tsx
const Dashboard = () => {
  const { data: summary } = useQuery({ queryKey: ["dashboard"], queryFn: getDashboard });
  const { data: controls } = useQuery({ queryKey: ["controls"], queryFn: getControls });

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-2xl font-bold">Compliance Dashboard</h1>

      {/* Stat cards */}
      <div className="grid grid-cols-4 gap-4">
        <StatCard title="Compliance Score" value={`${summary?.pass_rate}%`} color="green" />
        <StatCard title="Controls Checked" value={summary?.total_controls} color="blue" />
        <StatCard title="Passing" value={summary?.passing} color="green" />
        <StatCard title="Failing" value={summary?.failing} color="red" />
      </div>

      {/* Heat map by function */}
      <div className="bg-white rounded-lg shadow p-4">
        <h2 className="text-lg font-semibold mb-4">NIST CSF 2.0 — Control Heat Map</h2>
        <div className="grid grid-cols-6 gap-2">
          {functions.map((fn) => (
            <FunctionBlock
              key={fn.id}
              name={fn.name}
              passRate={fn.passRate}
              controls={fn.controls}
            />
          ))}
        </div>
      </div>

      {/* Failing controls table */}
      <div className="bg-white rounded-lg shadow p-4">
        <h2 className="text-lg font-semibold mb-4">Failed Controls</h2>
        <table className="w-full">
          <thead>
            <tr>
              <th>Control</th>
              <th>Name</th>
              <th>Age</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {controls?.filter(c => !c.passing).map(c => (
              <tr key={c.id} className="border-t">
                <td className="font-mono text-sm">{c.ref}</td>
                <td>{c.name}</td>
                <td>{(Date.now() - c.lastChecked) / 3600000}h ago</td>
                <td><button onClick={() => recheck(c.id)}>Re-check</button></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
```

### 1D.5 — Verification Gate

```
[ ] Login page works (register → login → redirect)
[ ] Dashboard loads with real data from DB
[ ] Heat map shows 6 NIST CSF functions with pass rates
[ ] Failing controls table shows red rows
[ ] Clicking a control row navigates to control detail page
[ ] Control detail page shows evidence history chart (pass/fail over time)
[ ] "Re-check" button triggers a check and refreshes the page
[ ] Evidence detail page shows raw JSON
[ ] Risk matrix page shows a 5x5 grid (static in Phase 1)
```

---

## Sub-Phase 1E: Risk Matrix & Integrations (Week 5)

### 1E.1 — Risk Matrix Implementation

A 5×5 matrix configurable via API:

```python
# Default matrix stored in seed data
DEFAULT_MATRIX = {
    "likelihood": ["Rare", "Unlikely", "Possible", "Likely", "Almost Certain"],
    "impact": ["Insignificant", "Minor", "Moderate", "Major", "Critical"],
    "grid": [
        [1, 2, 3, 4, 5],      # Rare × impact
        [2, 4, 6, 8, 10],     # Unlikely × impact
        [3, 6, 9, 12, 15],    # Possible × impact
        [4, 8, 12, 16, 20],   # Likely × impact
        [5, 10, 15, 20, 25],  # Almost Certain × impact
    ],
}
```

Severity mapping: 1-4 = Low, 5-9 = Medium, 10-15 = High, 16-25 = Critical.

### 1E.2 — Seed Data Script

```bash
# Run once during setup
docker compose run api python -m src.seed.all
```

`src/seed/all.py`:
```python
import asyncio
from src.core.database import async_session
from src.seed.import_nist_csf import import_nist_csf
from src.models.risk import RiskMatrix
from src.core.security import hash_password
from src.models.user import User

DEFAULT_MATRIX = { ... }

async def seed_all():
    async with async_session() as db:
        # 1. Create admin user
        admin = User(
            email="admin@grcsuite.local",
            display_name="Admin",
            hashed_password=hash_password("admin123"),
            role="admin",
        )
        db.add(admin)

        # 2. Import NIST CSF 2.0
        await import_nist_csf(db)

        # 3. Create default risk matrix
        matrix = RiskMatrix(name="Default 5x5", matrix=DEFAULT_MATRIX)
        db.add(matrix)

        await db.commit()
        print("Seed complete: 1 admin user, NIST CSF 2.0, 1 risk matrix")

asyncio.run(seed_all())
```

### 1E.3 — NIST CSF → Collector Mapping Table

Create the bridge between FrameworkControl rows and collector classes:

```sql
CREATE TABLE control_collector_mappings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    framework_control_id UUID REFERENCES framework_controls(id),
    collector_type VARCHAR(100) NOT NULL,   -- "aws_s3_bucket_policy"
    collector_params_template JSONB,         -- default params for this collector
    is_active BOOLEAN DEFAULT true
);

-- Seed mappings for Phase 1
-- Control "PR.AC-3" (remote access management) → S3PublicAccessCheck + SecurityGroupCheck
-- Control "PR.AC-1" (identity and credentials) → IAMKeyAgeCheck + SSHPasswordPolicyCheck
-- etc.
```

---

## Complete Phase 1 Verification Checklist

### Infrastructure
```
[ ] docker compose up starts in < 2 min on a fresh machine
[ ] All 5 services (postgres, redis, api, worker, frontend) are healthy
[ ] `POST /api/seed` creates admin user + NIST CSF + risk matrix
[ ] Alembic migrations run cleanly (no manual SQL needed)
```

### API
```
[ ] Auth: register, login, JWT refresh, protected routes
[ ] Frameworks: list, detail with control count
[ ] Controls: list with latest pass/fail, detail with evidence history
[ ] Evidence: detail with raw data, raw download
[ ] Dashboard: summary stats, heat map data
[ ] Check trigger: POST runs collector, stores evidence, returns result
[ ] Risk: matrix GET/PUT, assessment POST
```

### Collectors
```
[ ] 5 AWS collectors all working (tested against a real or mock AWS account)
[ ] 5 infra collectors all working (tested against a real or mock Linux server)
[ ] Collector registry correctly maps control_ref → collector classes
[ ] Graceful failure: bad credentials → error evidence (not crash)
[ ] Timeout handling: collector stops after 60s, stored as timeout evidence
[ ] Empty results: no S3 buckets → evidence says "no buckets found" (pass)
```

### Frontend
```
[ ] Login → dashboard redirect
[ ] Dashboard shows real data (not mock data)
[ ] Heat map is interactive (click a block → shows control list)
[ ] Control detail shows evidence chart (pass/fail over time)
[ ] "Re-check" button works and shows loading state
[ ] Risk matrix renders as 5x5 colored grid
```

### Handover to Phase 2
```
[ ] All models have Alembic migration files
[ ] All collector results include structured_result for cross-framework mapping
[ ] API response format is consistent (pagination, error format, timestamps)
[ ] README.md has setup instructions (prerequisites, docker compose, seed, log in)
```

---

## Time Budget Summary

| Week | Sub-Phase | Deliverable |
|------|-----------|-------------|
| 1 | 1A — Scaffold | Docker Compose, all 5 services, auth, NIST CSF import, DB models |
| 2 | 1B — Collectors Part 1 | 5 AWS collectors: S3, IAM, SG, CloudTrail, EC2 encryption |
| 3 | 1B — Collectors Part 2 | 5 infra collectors: SSH password, TLS, patch, disk encrypt, auditd |
| 4 | 1C — Evaluation Engine | API routes for check trigger, evidence storage, dashboard data |
| 4-5 | 1D — Frontend | React pages: login, dashboard, heat map, control detail, evidence |
| 5 | 1E — Risk & Polish | Risk matrix, seed data, collector mapping table, README |

Total: **5 weeks** for a working single-framework GRC tool with 10 automated controls.
