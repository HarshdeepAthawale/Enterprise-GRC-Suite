# Enterprise GRC Suite

Automated Information Security Auditing Tool — maps evidence to compliance frameworks, detects drift, and produces auditor-ready reports.

## Architecture

```
                    ┌─────────────┐
                    │  Frontend   │  React 19 + TypeScript + Tailwind
                    │  :3000      │
                    └──────┬──────┘
                           │ /api/* (Vite proxy)
                    ┌──────▼──────┐
                    │  API        │  FastAPI + Uvicorn
                    │  :8000      │
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
     ┌────────▼───┐ ┌─────▼──────┐ ┌───▼────────┐
     │  Postgres  │ │  Redis     │ │  Celery    │
     │  :5432     │ │  :6379     │ │  Worker    │
     └────────────┘ └────────────┘ └────────────┘
```

### 7-Layer Gemara Model Alignment

| Layer | Component |
|-------|-----------|
| 1. Standards | `framework_standards` table (NIST CSF 2.0) |
| 2. Catalogs | `control_catalogs` table (Functions, Categories) |
| 3. Controls | `framework_controls` table (106 Subcategories) |
| 4. Collectors | 10 plugin-based evidence collectors |
| 5. Evaluation | `EvaluationEngine` → pass/fail per control |
| 6. Risk | 5×5 configurable risk matrix |
| 7. Reporting | API-driven evidence retrieval (OSCAL export planned) |

## Quick Start

```bash
# 1. Start all services
docker compose -f docker/docker-compose.yml up -d

# 2. Run seed data (admin user, NIST CSF 2.0, risk matrix, collector mappings)
docker compose -f docker/docker-compose.yml exec api python -m src.seed.all

# 3. Seed collector-to-control mappings
docker compose -f docker/docker-compose.yml exec api python -m src.seed.seed_mappings

# 4. Login at http://localhost:3000
#    Email: admin@grcsuite.com
#    Password: admin123
```

## Default Credentials

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@grcsuite.com | admin123 |

## API Endpoints

### Auth
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/auth/register` | Create account |
| POST | `/api/auth/login` | Get JWT token |
| GET | `/api/auth/me` | Current user info |

### Frameworks
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/frameworks` | List frameworks with control counts |
| GET | `/api/frameworks/{id}` | Framework detail with function tree |

### Controls
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/controls` | List all controls with latest status |
| GET | `/api/controls/{id}` | Control detail + evidence history |
| POST | `/api/controls/{id}/check` | Trigger collector check |

### Dashboard
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/dashboard/summary` | Pass rate, counts, failing controls |
| GET | `/api/dashboard/heatmap` | Control grid by function |

### Evidence
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/evidence/{id}` | Full evidence with raw data |
| GET | `/api/evidence/{id}/raw` | Raw response body |

### Collectors
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/collectors` | List 10 available collectors |
| POST | `/api/collectors/{type}/config` | Save credentials/config |

### Risk
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/risk/matrix` | Current risk matrix |
| PUT | `/api/risk/matrix` | Update risk matrix |
| POST | `/api/risk/assess` | Create risk assessment |

## Collectors

### AWS (5)
| Collector | What it Checks | Mapped To |
|-----------|---------------|-----------|
| `aws_s3_bucket_policy` | S3 bucket public access | PR.AA-3 |
| `aws_iam_key_age` | IAM key rotation (>90 days) | PR.AA-1 |
| `aws_security_group_open_ports` | 0.0.0.0/0 on SSH/RDP/DB ports | PR.AA-3 |
| `aws_cloudtrail_enabled` | CloudTrail active in all regions | DE.CM-1 |
| `aws_ec2_encryption` | EBS volume encryption at rest | PR.DS-2 |

### Infrastructure (5)
| Collector | What it Checks | Mapped To |
|-----------|---------------|-----------|
| `ssh_password_policy` | Password max days + min length | PR.AA-1 |
| `tls_version_check` | TLS 1.2+ only (nmap) | PR.DS-1 |
| `patch_level_check` | Pending security patches | ID.RA-1 |
| `disk_encryption_check` | LUKS encryption status | PR.DS-2 |
| `auditd_status` | auditd service + rules | DE.CM-1 |

## Running Tests

```bash
# All 40 tests (unit + integration)
docker compose -f docker/docker-compose.yml exec api python -m pytest tests/ -v
```

## Adding a New Collector

1. Create a class in `src/collectors/<category>/` that extends `EvidenceCollector`
2. Implement `collect()` and `can_run()` methods
3. Register it in `src/collectors/registry.py` using `register_collector()`
4. Map it to controls via `src/seed/seed_mappings.py` or the `/api/collectors/{type}/config` endpoint

## Project Structure

```
Enterprise-GRC-Suite/
├── docker/              # Docker Compose + Dockerfiles
├── src/
│   ├── api/             # FastAPI routes + middleware
│   ├── core/            # Config, DB session, JWT auth
│   ├── models/          # SQLAlchemy ORM models
│   ├── collectors/      # 10 plugin-based collectors (aws/ + infra/)
│   ├── engine/          # Evaluation engine
│   ├── scheduler/       # Celery tasks
│   ├── seed/            # Framework imports + seed data
│   └── shared/          # Pydantic schemas
├── frontend/            # React 19 + TypeScript
├── tests/               # 40 pytest tests
└── migrations/          # Alembic migrations
```
