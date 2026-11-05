# MindTheSpec - Golden Path Demonstration Walkthrough

This document provides a 3 to 5 minute step-by-step walkthrough for evaluating **MindTheSpec** (Requirement Interpretation & Divergence Detection Platform).

---

## 1. Prerequisites & Launching the App

Open **Windows PowerShell** in the project directory:

```powershell
Set-Location -Path "C:\Users\Kaila\OneDrive\Documents\MindThe Spec"

# 1. Activate Virtual Environment
.\.venv\Scripts\Activate.ps1

# 2. Seed Demo Data (Populates sample project & accounts without overwriting data)
python scripts/seed_demo.py

# 3. Start the FastAPI Server
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Open your browser to: **`http://127.0.0.1:8000`**

---

## 2. Seeded Stakeholder Accounts

| Stakeholder Role | Email Address | Password | Purpose in Demonstration |
|---|---|---|---|
| **Project Owner** | `owner@example.com` | `Owner123!` | Creates requirements, locks sessions, records resolutions. |
| **Developer** | `dev@example.com` | `Dev123!` | Contributes technical perspective (`delivery_hours = 24`). |
| **Tester** | `test@example.com` | `Test123!` | Contributes QA/acceptance perspective (`delivery_hours = 48`). |

*(Note: These accounts are safely seeded for local evaluation only).*

---

## 3. Step-by-Step Demonstration Sequence

### Step 1: Owner Workspace Inspection
1. Navigate to `http://127.0.0.1:8000/login` and log in as `owner@example.com` / `Owner123!`.
2. Inspect the **Workspace Dashboard** (`/app`):
   - Notice the genuine database counts (Accessible Projects, Requirements, Active Sessions).
   - Click on the **Online Shopping System** project card.
3. On the Project page (`/app/projects/1`), see the stakeholder roster with assigned roles (Owner, Developer, Tester).
4. Click on requirement **`REQ-001: Fast Delivery Support`**.

---

### Step 2: The Blind Interpretation Session
1. On the Requirement page (`/app/requirements/1`), open **Session #1**.
2. Notice the session state banner: **`COLLECTING (BLIND)`**.
3. Notice the participation alert: *"Total submissions received: 2. Stakeholder answers remain strictly confidential on the server until the project owner locks this session."*
4. Notice that even as the project owner, **you cannot see Developer or Tester answers before lock**. Server-enforced blind isolation prevents premature disclosure.

---

### Step 3: Demonstrating Pre-Lock Secrecy & IDOR Protection
1. Open an incognito browser window or log in as **Dave Developer** (`dev@example.com` / `Dev123!`).
2. Navigate to `http://127.0.0.1:8000/app/sessions/1`:
   - Developer sees **only their own** 24-hour submission.
3. Open a separate browser or log in as **Tina Tester** (`test@example.com` / `Test123!`):
   - Tester sees **only their own** 48-hour submission.
4. **Direct API IDOR Check:**
   - Attempt to fetch Developer's interpretation via API: `GET /api/interpretations/1` while signed in as Tester.
   - The server immediately returns **HTTP 403 Forbidden**:
     ```json
     {"detail": "Access denied. Interpretation answers are strictly confidential until session lock."}
     ```

---

### Step 4: Atomic Owner Lock & Deterministic Divergence Analysis
1. Return to the browser session signed in as **Alex Owner**.
2. On Session #1 (`/app/sessions/1`), click the red **`🔒 Lock Session & Analyze`** button and confirm the dialog.
3. Submissions are now permanently frozen (any future submit attempts return HTTP 409 Conflict).
4. The system automatically redirects to the **Divergence Detection Report** (`/app/sessions/1/compare`).

---

### Step 5: Reviewing the Divergence Report
1. Observe the **Delivery Timeline Mismatch** finding:
   - **Discrepancy:** Developer stated `24 hours` vs Tester stated `48 hours`.
   - **Review Status:** `Decision Required`.
   - **Deterministic Guarantee:** Explicitly marked as rule-based analysis with zero fabricated AI confidence scores.
2. Below the findings, inspect the **Side-by-Side Submissions Table**, which is now unlocked for all project members to review transparently.

---

### Step 6: Recording Official Resolution & Traceability
1. Click **`Record Official Resolution`** (or go to `/app/sessions/1/resolution`).
2. Fill in the decision:
   - **Binding Decision Statement:** `Delivery within 48 hours for eligible orders.`
   - **Decision Rationale:** `Operations confirmed that 24h ground delivery is not universally reliable across all shipping zones; 48h committed carrier SLA adopted.`
3. Click **`Save Official Resolution`**.
4. The report page now permanently displays the resolution banner linked to Alex Owner and the UTC decision timestamp.
5. All original interpretations remain preserved in their historical form for audit traceability.

---

### Step 7: Exporting CSV & Inspecting the Audit Trail
1. Click the **Export CSV** link or navigate to `/api/sessions/1/export/csv` to download `mindthespec_session_1_report.csv`.
   - Notice that spreadsheet formula injection characters (`=`, `+`, `-`, `@`) are safely escaped.
2. Navigate to the project's **Audit Trail** (`/app/projects/1/history`):
   - See the complete chronological sequence: `PROJECT_CREATED` &rarr; `REQUIREMENT_CREATED` &rarr; `SESSION_OPENED` &rarr; `INTERPRETATION_SUBMITTED` &rarr; `SESSION_LOCKED` &rarr; `RESOLUTION_RECORDED`.
   - Notice that confidential interpretation bodies were never written to general log messages.

---

### Step 8: Persistence Verification
1. Stop the FastAPI server in PowerShell (`Ctrl+C`).
2. Restart the server (`python -m uvicorn main:app --reload`).
3. Refresh the browser at `http://127.0.0.1:8000/app/sessions/1/compare`.
4. All project data, versions, locked states, divergence findings, and resolutions persist without data loss.
