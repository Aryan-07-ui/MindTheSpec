# MindTheSpec

**Requirement Interpretation & Divergence Detection Platform**  
*Different minds. One understanding.*

---

## 1. Product Overview

When software engineering teams discuss written requirements, different stakeholders form conflicting mental models. For example, when a requirement says *"The system must support fast delivery"*, a developer may plan for automated next-day dispatch (24h) while a quality assurance tester expects 48-hour delivery with manual verification.

**MindTheSpec** prevents costly development rework through **server-enforced blind interpretation sessions followed by deterministic, rule-based divergence detection and binding consensus resolutions**:

1. **Requirement Management:** Create, version, and manage requirements with priority tiers (`critical`, `high`, `medium`, `low`), detailed specifications, and observable acceptance criteria.
2. **Project Team Management:** Invite stakeholders with role-based access (`owner`, `analyst`, `developer`, `tester`) to participate in requirement evaluations.
3. **Mutual Secrecy (Blind Interpretations):** Stakeholders independently submit interpretations covering expected behavior, prerequisite assumptions, acceptance criteria, edge cases, and delivery timeline hours. Submissions remain strictly confidential at the database query level until the session is locked.
4. **Deterministic Divergence Engine:** Analyzes locked sessions using deterministic rules (zero fabricated AI confidence) to flag timeline mismatches, operational behavior conflicts, divergent assumptions, and missing edge cases.
5. **Traceable Consensus Resolution:** The project owner records an official binding decision and rationale, locking the session into permanent audit history and enabling authenticated CSV report export.

---

## 2. Architecture & Tech Stack

- **Presentation Layer:** Accessible, responsive server-rendered HTML5 templates using Jinja2 with Sketchbook Studio aesthetic (light and dark mode support, mobile navigation drawer, and WCAG 2.2 AA compliant contrast).
- **Application Layer:** FastAPI (Python 3.11+) with RESTful JSON endpoints, Pydantic data validation schemas, bcrypt password hashing, and cryptographically signed HttpOnly session cookies.
- **Data Persistence Layer:** MySQL 8.4 Server (InnoDB engine, `utf8mb4_unicode_ci`, foreign keys with cascading/restrict rules, composite primary keys, and unique constraints). Supports SQLite as an isolated zero-dependency automated testing harness.

---

## 3. Getting Started & Local Setup

### Prerequisites
- Python 3.11+
- MySQL 8.4+ (or SQLite for automated testing)
- Git

### 3.1 Clone the Repository
```bash
git clone https://github.com/Aryan-07-ui/MindTheSpec.git
cd MindTheSpec
```

### 3.2 Set Up Virtual Environment & Dependencies
```bash
# Create and activate virtual environment
python -m venv .venv

# Windows PowerShell:
.\.venv\Scripts\Activate.ps1

# Linux / macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3.3 Configure Environment Variables
Copy the example environment file and update with your local database credentials:
```bash
cp .env.example .env
```

Edit `.env`:
```ini
DB_HOST=localhost
DB_PORT=3306
DB_NAME=mind_the_spec
DB_USER=mindthespec_app
DB_PASSWORD=your_least_privilege_password_here
APP_ENV=development
SECRET_KEY=generate-a-secure-random-secret-key
SESSION_COOKIE_NAME=mindthespec_session
```

### 3.4 Initialize MySQL Database & Migrations
Execute the migration scripts against your MySQL server:
```bash
# Using Python:
python migrations/002_phase2_schema_update.py

# Or via MySQL CLI:
mysql -u root -p mind_the_spec < migrations/001_v2_schema_update.sql
mysql -u root -p mind_the_spec < migrations/002_phase2_schema_update.sql
```

### 3.5 Run Automated Tests
MindTheSpec includes an automated Pytest test suite covering authentication, RBAC permissions, blind secrecy enforcement, divergence detection, and security headers:
```bash
python -m pytest -v
```

Expected output:
```text
======================= 23 passed in 14.47s =======================
```

### 3.6 Start the Application Server
```bash
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

- Web Application: **`http://127.0.0.1:8000`**
- Interactive OpenAPI Docs: **`http://127.0.0.1:8000/docs`**

---

## 4. Evaluation Accounts

If seeded with `scripts/seed_demo.py`, you can test using the following pre-configured credentials:

| Role | Email Address | Password | Primary Workflow |
|---|---|---|---|
| **Project Owner** | `owner@example.com` | `Owner123!` | Create projects/requirements, lock sessions, record binding resolutions |
| **Developer** | `dev@example.com` | `Dev123!` | Submit technical blind interpretations (e.g. 24h automated SLA) |
| **Tester** | `test@example.com` | `Test123!` | Submit validation blind interpretations (e.g. 48h manual queue) |

---

## 5. Security & Confidentiality Principles

- **Server-Side Secrecy:** Unrevealed stakeholder interpretations are filtered directly by database queries. No hidden answers exist in HTML source, JavaScript payloads, or API responses.
- **Access Control (RBAC):** Strict project membership checks prevent IDOR attacks across projects.
- **Append-Only Audit Trail:** Project creation, member changes, requirement revisions, session locks, and resolutions are recorded in `audit_logs`.
- **Formula Injection Defense:** CSV exports escape potentially malicious spreadsheet command characters (`=`, `+`, `-`, `@`).

---

## 6. License & Course Attribution

MindTheSpec is an academic software engineering and relational DBMS capstone project (Course: 25CSH-210). Developed by Aryan Kushwaha.
