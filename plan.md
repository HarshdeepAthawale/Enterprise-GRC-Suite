# CT-CS-05: Automated Information Security Auditing Tool (GRC Tool) — Build Plan

## Problem

Organizations spend 11 weeks/year on manual compliance tasks. 59% list automating security/compliance as a top strategic priority. Existing solutions are either expensive enterprise suites ($50-100K+/yr) or spreadsheets.

Build a production-grade automated GRC (Governance, Risk, Compliance) tool that:
- Automates evidence collection from corporate systems (cloud APIs, LDAP, endpoints, network)
- Maps evidence to multiple compliance frameworks simultaneously (NIST CSF, ISO 27001, SOC 2, GDPR, HIPAA)
- Detects compliance drift in real time
- Produces auditor-ready evidence packages (OSCAL format, PDF reports)
- Scales from single-team to multi-tenant enterprise

---

## Architecture Principles

1. **Plugin-based collectors** — every integration is a standalone Python class
2. **API-first** — all functionality accessible via REST
3. **Evidence chain-of-custody** — Merkle-style hash chain per control, tamper-evident
4. **Multi-framework by design** — Common Control Library (CCL) as canonical layer
5. **Gemara-aligned** — 7-layer GRC engineering model (OpenSSF standard, Mar 2026)
6. **Continuous, not point-in-time** — scheduled re-checks + drift detection + alerts

---

## Tech Stack

| Component | Choice |
|-----------|--------|
| Backend | Python 3.12+ / FastAPI |
| Async workers | Celery + Redis |
| Database | PostgreSQL 16 (JSONB for evidence blobs) |
| ORM | SQLAlchemy 2.0 + Alembic migrations |
| Frontend | React 19 + Chart.js |
| Deployment | Docker Compose (dev), Kubernetes (prod) |
| Auth | JWT (early), OIDC/SAML (Phase 6) |
| Validation | Pydantic v2 |
| Schemas | CUE (Gemara-compatible) |

---

## Project Structure

```
ct-cs-05-grc-tool/
├── docker/
│   ├── docker-compose.yml
│   ├── Dockerfile.api
│   └── Dockerfile.worker
├── src/
│   ├── api/                    # FastAPI routes
│   │   ├── routes/
│   │   ├── middleware/
│   │   └── deps.py
│   ├── core/                   # Config, DB session, auth
│   ├── models/                 # SQLAlchemy ORM models
│   │   ├── framework.py
│   │   ├── control.py
│   │   ├── evidence.py
│   │   ├── schedule.py
│   │   └── policy.py
│   ├── collectors/             # Plugin-based evidence collectors
│   │   ├── base.py             # Abstract base class
│   │   ├── aws/
│   │   ├── ssh/
│   │   ├── ldap/
│   │   └── manual/
│   ├── engine/                 # Evaluation, mapping, risk
│   │   ├── evaluator.py
│   │   ├── mapper.py
│   │   └── risk.py
│   ├── scheduler/              # Celery tasks, scheduler logic
│   ├── seed/                   # Framework import scripts
│   ├── export/                 # OSCAL, PDF, Excel exporters
│   └── shared/                 # Pydantic schemas, enums
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   └── lib/
│   └── package.json
├── migrations/                 # Alembic migrations
├── tests/
├── plan.md
└── README.md
```

---

## Phased Implementation Plan

### MONTH 1: Foundation

#### Phase 0: Scaffolding (Weeks 1-2)

**Goal**: Skeleton that compiles, runs, and can ingest one framework.

| Deliverable | Details |
|-------------|---------|
| PostgreSQL schema | `framework_standards`, `framework_controls`, `evidence` tables |
| Framework importer | Script to parse NIST CSF 2.0 machine-readable JSON into DB |
| API scaffold | CRUD for controls, evidence, findings |
| Frontend scaffold | React + Chart.js with login page placeholder |
| Docker Compose | FastAPI + Celery + Postgres + Redis running in 1 command |
| Auth system | JWT-based user registration/login |

**Verify**: `docker compose up` → login → import NIST CSF → see 106 controls in DB.

#### Phase 1: Core Engine (Weeks 3-5)

**Goal**: Working tool for ONE framework (NIST CSF) with 10 automated controls.

| Deliverable | Details |
|-------------|---------|
| 5 cloud collectors | AWS S3 public access, AWS security groups, IAM key age, CloudTrail status, EC2 encryption |
| 5 infra collectors | SSH password policy check, TLS version (nmap), patch level, disk encryption, auditd status |
| Evaluation engine | `raw_data → structured_result → pass/fail` pipeline |
| Dashboard | Control heat map, overall score |
| Control detail page | Raw evidence, history chart, pass/fail trend |
| Manual re-check | Trigger single collector on demand |
| Risk matrix | 5×5 qualitative, configurable |

---

### MONTH 2: Multi-Framework & Continuous Monitoring

#### Phase 2: Multi-Framework Engine (Weeks 6-8)

**Goal**: One evidence set maps to N frameworks — the core differentiator.

| Deliverable | Details |
|-------------|---------|
| Common Control Library | 50-80 canonical controls, `control_mappings` bridge table |
| Framework importers | ISO 27001, SOC 2, GDPR, HIPAA |
| Mapping UI | "Drag to link" — framework control → CCL control |
| Cross-framework dashboard | "87% pass across 3 frameworks" |
| Gap analysis | "100% NIST CSF but only 62% ISO 27001 — missing controls" |
| Statement of Applicability | Auto-generated for ISO 27001 |

#### Phase 3: Continuous Monitoring Engine (Weeks 9-11)

**Goal**: Checks run automatically. Drift is detected and alerted.

| Deliverable | Details |
|-------------|---------|
| Celery Beat scheduler | Priority queues (critical/hourly, standard/daily, low/weekly) |
| Check execution tracking | Every run: status, attempt, worker, timing |
| Retry logic | 2 retries + exponential backoff → alert on final failure |
| SLA tracking | `max_interval_hours` per control, stale detection |
| Drift detection | "Control was passing, now failing" — the core signal |
| Alert routing | Slack webhook, email SMTP, generic webhook |
| Scheduler dashboard | "97.2% SLA, 3 stale, 2 active drifts" |

---

### MONTH 3: Audit Readiness

#### Phase 4: Evidence Chain & OSCAL Export (Weeks 12-14)

**Goal**: Output an auditor can use directly. Separates a demo from a product.

| Deliverable | Details |
|-------------|---------|
| Evidence chain hash | Merkle-style chain per control — tamper-evident |
| Evidence TTL | Stale flagging + re-collection scheduling |
| OSCAL export v1 | `assessment-results` JSON output |
| OSCAL export v2 | `system-security-plan` (SSP) output |
| OSCAL import | Ingest component definitions |
| PDF report | Scope, methodology, findings table, evidence index |
| Excel export | For teams that live in spreadsheets |
| Evidence replay | Re-run with same params, compare results |

**Auditor workflow**: Auditor gets link → raw evidence with chain-of-custody hashes → downloads OSCAL JSON → done.

---

### MONTH 4-5: Ecosystem & Integration

#### Phase 5: Plugin Ecosystem & Collectors (Weeks 15-18)

**Goal**: 15+ collectors covering common corporate systems.

| Category | Collectors |
|----------|------------|
| Cloud | AWS, GCP, Azure (3-5 checks each) |
| Identity | AD/LDAP, Okta, Azure AD, Google Workspace |
| Network | Firewall rule review (API), TLS config (nmap), DNS |
| Endpoint | EDR status, patch level (WSUS/Intune), disk encryption |
| Compliance scanners | OpenSCAP (config), Trivy (containers), OWASP ZAP (web apps) |
| Manual | Evidence upload UI with chain-of-custody |

**Plugin architecture**: Each collector is pip-installable. Third parties can write collectors without forking core.

#### Phase 6: Enterprise Features (Weeks 19-22)

**Goal**: Production-ready — multi-org, multi-user, scalable.

| Deliverable | Details |
|-------------|---------|
| Multi-tenancy | Row-level security in Postgres |
| RBAC | Admin, Compliance Manager, Auditor, Read-only |
| API keys | Programmatic CI/CD integration |
| Rate limiting | Per-tenant |
| Audit log | Every user action logged |
| SAML/SSO | OIDC integration (Okta, Azure AD, Google) |
| Backup/restore | Automated evidence + DB backups |
| Health + metrics | `/health`, `/metrics` (Prometheus) |
| Horizontal scaling | Celery auto-scale, read replicas |

---

### MONTH 6+: Advanced

#### Phase 7: AI & DevSecOps (Weeks 23+)

| Feature | Details |
|---------|---------|
| AI risk prediction | "Controls A, B, C 70% likely to fail next month" |
| Remediation workflows | Failed control → Jira ticket → track → re-verify |
| Policy-as-code | YAML policies → auto-derived controls → auto-check |
| Natural language query | "Show all encryption controls that failed this week" |
| Vendor risk management | Questionnaires, scoring, tracking |
| CI/CD integration | "Block deploy if critical controls fail" |
| Compliance score trending | Predict next audit score from drift rate |

---

## Go/No-Go Decision Gates

| Phase | Question |
|-------|----------|
| After P0 | Does `docker compose up` work in <2 min on a fresh machine? |
| After P1 | Can a non-technical person run a check and understand the result? |
| After P2 | Does the cross-framework report show correct, useful data? |
| After P3 | If I break a config, does the tool detect it within 1 hour? |
| After P4 | Can an auditor verify the evidence chain hasn't been tampered with? |
| After P5 | Do the 6 most common corporate systems have working collectors? |
| After P6 | Can 3 different orgs use the same instance with isolated data? |

---

## Key Risks

| Risk | Mitigation |
|------|------------|
| Framework imports are brittle | Use machine-readable formats (NIST JSON, OSCAL XML). Don't scrape PDFs. |
| Collector API changes break checks | Version-pin collectors. Integration tests per collector. |
| Evidence storage grows fast | JSONB + gzip compression. TTL-based archiving to cold storage. |
| Auditor rejects evidence format | Ship OSCAL support early. It's becoming mandatory (FedRAMP Sept 2026). |
| Too many frameworks = maintenance burden | CCL limits blast radius. 50-80 controls, not 500. |
| Schedule coordination complexity | Celery Beat + priority queues. Don't build your own cron. |

---

## References

- OpenSSF Gemara Model (Mar 2026) — 7-layer GRC engineering standard
- NIST OSCAL — Machine-readable compliance format (mandatory Sept 2026)
- CISO Assistant (GitHub 3.6K★) — Open-source GRC, 100+ frameworks
- NIST CSF 2.0 — Machine-readable JSON available from NIST
- RegScale 2026 CCM Report — Industry survey on continuous monitoring adoption
