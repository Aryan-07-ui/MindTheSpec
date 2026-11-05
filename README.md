# MindTheSpec

**Requirement Interpretation & Divergence Detection Platform**  
*Different minds. One understanding.*

---

## 1. Product Overview

When software engineering teams discuss written requirements, different team members often imagine different results. For example, when a requirement says *"The system must support fast delivery"*, a software developer might plan for automated next-day dispatch (24 hours), while a quality assurance tester might plan for 48 hours to allow for manual inspection.

**MindTheSpec** prevents costly development misunderstandings through **server-enforced blind interpretation sessions followed by deterministic, rule-based divergence detection and binding consensus resolutions**:

1. **Requirement Management:** Create, version, and manage requirements with priority tiers (`critical`, `high`, `medium`, `low`), detailed descriptions, and observable acceptance criteria.
2. **Project Team Management:** Invite stakeholders with role-based access (`owner`, `analyst`, `developer`, `tester`) to participate in requirement evaluations.
3. **Mutual Secrecy (Blind Interpretations):** Stakeholders independently submit their interpretation covering expected behavior, prerequisite assumptions, acceptance criteria, edge cases, and delivery timeline hours. Submissions remain strictly confidential at the database query level until the session is locked.
4. **Deterministic Divergence Engine:** Analyzes locked sessions using clear, rule-based logic (zero fabricated AI confidence scores) to highlight timeline differences, conflicting behaviors, different assumptions, and missing edge cases.
5. **Traceable Consensus Resolution:** The project owner records an official agreed decision and rationale, saving the session to the audit history and enabling authenticated CSV report export.

---

## 2. Core Platform Workflow

MindTheSpec follows a structured, step-by-step consensus workflow:

```text
Create Project ──> Add Members ──> Create Requirement ──> Start Blind Session ──> Submit Interpretations ──> Lock ──> Reveal ──> Detect Divergences ──> Resolve
```

1. **Create Project:** The project owner sets up a new workspace with a title and description.
2. **Add Members:** Team members are assigned project roles (`analyst`, `developer`, `tester`).
3. **Create Requirement:** The team defines the requirement with priority, description, and acceptance criteria.
4. **Start Blind Session:** An interpretation session is opened for that requirement.
5. **Submit Interpretations:** Each stakeholder writes their independent interpretation in private.
6. **Lock:** The session owner closes submissions so answers cannot be changed.
7. **Reveal:** The system makes all submitted interpretations visible to team members at the same time.
8. **Detect Divergences:** The comparison engine flags conflicting delivery timelines, contrasting assumptions, and differing behavior models.
9. **Resolve:** The owner records a final agreed resolution with decision notes for a clear audit trail.

---

## 3. Architecture & Tech Stack

- **Presentation Layer:** Server-rendered HTML5 templates using Jinja2 with a modern creative-studio design, responsive layouts for desktop and mobile, and theme support for light and dark modes.
- **Application Layer:** FastAPI (Python 3.11+) with RESTful JSON endpoints, Pydantic validation schemas, bcrypt password hashing, and cryptographically signed HttpOnly session cookies.
- **Data Persistence Layer:** MySQL 8.4 Server (InnoDB storage engine, `utf8mb4_unicode_ci` encoding, foreign key constraints, composite primary keys, and unique indexes). SQLite is also supported for zero-dependency local testing.

---

## 4. Repository Structure

```text
MindTheSpec/
├── app/
│   ├── models/          # SQLAlchemy ORM models (User, Project, Requirement, etc.)
│   ├── routes/          # FastAPI routes (auth, projects, requirements, sessions, views)
│   ├── schemas/         # Pydantic schemas for data validation
│   ├── services/        # Business logic, authorization, and divergence engine
│   ├── static/          # CSS stylesheets, JavaScript, and SVG branding assets
│   ├── templates/       # Jinja2 HTML templates
│   ├── config.py        # Application configuration and environment variables
│   ├── database.py      # Database engine, connection handling, and session factory
│   └── main.py          # FastAPI application initialization and middleware
├── migrations/          # Database schema migrations
│   ├── 001_v2_schema_update.sql
│   ├── 002_phase2_schema_update.py
│   └── 002_phase2_schema_update.sql
├── scripts/             # Database seeding scripts
│   └── seed_demo.py
├── tests/               # Automated test suite (Pytest)
├── .env.example         # Template environment configuration file
├── .gitignore           # Git ignore rules for environments, caches, and secrets
├── main.py              # Root ASGI entry point
├── README.md            # Project documentation and setup guide
└── requirements.txt     # Python project dependencies
```

---

## 5. Local Setup Guide (Windows)

Follow these steps to set up and run MindTheSpec on a fresh Windows system.

### Prerequisites
- **Python 3.11+** installed and added to your system `PATH`.
- **MySQL Server 8.0 or 8.4** installed and running on port 3306.
- **Git** installed on your system.

---

### Step 1: Clone the Repository
Open PowerShell or your preferred terminal:

```powershell
git clone https://github.com/Aryan-07-ui/MindTheSpec.git
cd MindTheSpec
```

---

### Step 2: Create and Activate a Virtual Environment

**In PowerShell:**
```powershell
python -m venv .venv
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
.\.venv\Scripts\Activate.ps1
```

*(If using Command Prompt `cmd.exe`, run: `.\.venv\Scripts\activate.bat`)*

---

### Step 3: Install Dependencies

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

---

### Step 4: Configure Environment Variables

Create your local `.env` configuration file from `.env.example`:

**In PowerShell:**
```powershell
Copy-Item .env.example .env
```

Open `.env` and fill in your local MySQL database credentials:

```ini
# Database Configuration (MySQL 8.4)
DB_HOST=localhost
DB_PORT=3306
DB_NAME=mind_the_spec
DB_USER=mindthespec_app
DB_PASSWORD=your_mysql_password_here

# Application Configuration
APP_ENV=development
SECRET_KEY=replace-with-a-secure-random-secret-key
SESSION_COOKIE_NAME=mindthespec_session
```

---

### Step 5: Initialize the MySQL Database

1. Open MySQL Command Line Client or run:
   ```sql
   CREATE DATABASE IF NOT EXISTS mind_the_spec CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   ```

2. Initialize the database tables using Python:
   ```powershell
   python -c "from app.database import engine; from app.models import Base; Base.metadata.create_all(bind=engine)"
   ```

3. Run the Phase 2 schema migration script:
   ```powershell
   python migrations/002_phase2_schema_update.py
   ```

*(Alternatively, if you prefer applying SQL scripts directly through the MySQL client:)*
```powershell
mysql -u root -p mind_the_spec < migrations/001_v2_schema_update.sql
mysql -u root -p mind_the_spec < migrations/002_phase2_schema_update.sql
```

---

### Step 6: Seed Demonstration Data (Optional)

The project includes an optional script `scripts/seed_demo.py` that populates sample demonstration data:

```powershell
python scripts/seed_demo.py
```

This creates a sample project (*Online Shopping System*), a sample requirement (*REQ-001*), and three sample local evaluation accounts:

| Role | Email Address | Password | Intended Evaluation Workflow |
|---|---|---|---|
| **Project Owner** | `owner@example.com` | `Owner123!` | Create requirements, lock sessions, record final decisions |
| **Developer** | `dev@example.com` | `Dev123!` | Submit technical interpretation (e.g. 24h automated SLA) |
| **Tester** | `test@example.com` | `Test123!` | Submit validation interpretation (e.g. 48h manual inspection) |

> **Note:** These dummy accounts and passwords are created strictly for local development and demonstration. For real usage, users can register new accounts with their own unique passwords through the `/register` page.

---

### Step 7: Start the Application

Start the local development server using Uvicorn:

```powershell
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

- **Web Application:** [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Interactive API Documentation:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## 6. Running Automated Tests

MindTheSpec includes an automated test suite using `pytest`. The tests run using an isolated in-memory or SQLite database and cover:
- User registration, login, and session cookie validation
- Server-side blind interpretation confidentiality before session lock
- Role-based project access control (RBAC)
- Deterministic divergence detection logic
- Consensus resolution recording
- HTTP security response headers (`X-Frame-Options`, `X-Content-Type-Options`, `Referrer-Policy`)

Run the test suite with:

```powershell
python -m pytest -v
```

> **Note:** Test execution time may vary depending on local system performance and hardware specifications.

---

## 7. Security & Privacy Architecture

- **Server-Side Secrecy:** Interpretations submitted during active blind sessions are hidden at the SQL query level. Hidden answers are never included in HTML responses, API JSON, or client-side scripts before a session is locked.
- **Role-Based Access Control (RBAC):** Server-side checks verify project membership and role permissions before allowing access to project details, sessions, or requirements.
- **Audit Logging:** Important actions (such as creating projects, updating requirements, locking sessions, and recording resolutions) are recorded in the `audit_logs` table for review.
- **Formula Injection Defense:** Exported CSV reports escape spreadsheet formulas (`=`, `+`, `-`, `@`) to protect users opening files in spreadsheet software.
- **Security Headers:** The web application sends standard security headers (`X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, and `Referrer-Policy`) on HTTP responses.

---

## 8. Academic Project Attribution

**MindTheSpec** was designed and built by **Aryan Kushwaha** as a **Semester 3 Integrated Project** combining concepts from:
- **System Design & Software Architecture:** Multi-tier web platform design, deterministic consensus engines, and state machine workflows.
- **Database Management Systems (DBMS):** Relational schema design, normalization, referential integrity with cascading constraints, and audit logging.
- **Cloud Security:** Role-based access control, cryptographic password hashing, server-side data isolation, and defense against common web vulnerabilities.
