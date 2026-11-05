# MindTheSpec - Security Checklist & STRIDE Threat Analysis

**Document Status:** Complete & Verified  
**Checkpoint Target:** 3 November 2026 Security Demonstration  
**Platform:** Python 3.11 / FastAPI / MySQL 8.4 / SQLAlchemy 2.1  

---

## 1. STRIDE Threat Model & Mitigations

| STRIDE Category | Threat Description | Architectural Mitigation in MindTheSpec | Verification Evidence |
|---|---|---|---|
| **Spoofing** | An attacker impersonates another stakeholder or project owner. | Passwords hashed using salted bcrypt (rounds=12). Sessions managed via cryptographically signed HMAC-SHA256 tokens in HttpOnly cookies with UTC expiration. Server resolves identity from session token, never trusting client-provided user IDs. | `tests/test_auth.py` (`test_login_success`, `test_get_current_user_profile`) |
| **Tampering** | A participant edits an interpretation after seeing other inputs, or tampers with a locked session. | Submissions permitted strictly during `collecting` state. Once owner executes lock, state transitions atomically to `locked`/`analyzed`; subsequent submissions or modifications return HTTP 409 Conflict. | `tests/test_divergence.py` (`test_lock_and_divergence_detection_mismatch` - step 5) |
| **Repudiation** | A stakeholder denies having submitted a specific interpretation or an owner denies a resolution. | Append-only `audit_logs` record entity ID, actor ID, action type, and UTC timestamp in the database. Resolutions record owner ID and timestamp permanently linked to the originating session. | `tests/test_resolutions.py`, `app/services/audit_service.py` |
| **Information Disclosure** | A developer reads a tester's expected delivery hours before submitting their own; or an attacker inspects hidden interpretations via direct ID queries. | Strict server-side blind filtering: pre-lock queries return only the calling user's submission. Direct primary key lookups for another user's interpretation return HTTP 403 Forbidden. Owner has zero bypass privilege before lock. | `tests/test_blind_interpretations.py` (steps 6 & 7) |
| **Denial of Service** | Malicious inputs with excessive lengths or nested structures exhaust database resources. | Strict Pydantic validation on all endpoints: `delivery_hours` bounded (1 to 10000), titles limited to 200 characters, bodies bounded, connection pooling with `pool_pre_ping=True`. | Pydantic schemas in `app/schemas/` |
| **Elevation of Privilege** | A standard project member attempts to lock a session, add members, or record an official resolution. | All mutating administrative actions enforce `ProjectService.require_owner(db, project_id, user_id)`. Non-owners attempting owner operations are rejected with HTTP 403 Forbidden. | `tests/test_projects.py` (`test_member_management`), `tests/test_divergence.py` (step 3) |

---

## 2. Security Test Matrix (SEC-01 to SEC-13)

| Test ID | Security Scenario | Expected Behavior | Automated Test Status |
|---|---|---|---|
| **SEC-01** | Anonymous call to protected project API | Rejected with HTTP 401 Unauthorized | **PASS** (`tests/test_security.py::test_sec_01_anonymous_access_denied`) |
| **SEC-02** | Logged-in non-member accesses private project | Rejected with HTTP 403 Forbidden (no project data leaked) | **PASS** (`tests/test_security.py::test_sec_02_non_member_idor_denied`) |
| **SEC-03** | Member A attempts to list interpretations in active collecting session | Server filters output; Member A receives ONLY their own submission | **PASS** (`tests/test_blind_interpretations.py`) |
| **SEC-04** | Member A attempts direct ID lookup (`/api/interpretations/{id}`) for Member B's submission before lock | Rejected with HTTP 403 Forbidden | **PASS** (`tests/test_blind_interpretations.py` - step 7) |
| **SEC-05** | Submission attempted after session is locked | Rejected with HTTP 409 Conflict | **PASS** (`tests/test_divergence.py` - step 5) |
| **SEC-06** | Developer member attempts to execute session lock or record resolution | Rejected with HTTP 403 Forbidden | **PASS** (`tests/test_divergence.py` - step 3, `tests/test_resolutions.py`) |
| **SEC-07** | Request with invalid or tampered session token | Rejected with HTTP 401 Unauthorized | **PASS** (`tests/test_security.py::test_sec_07_invalid_session_token_rejected`) |
| **SEC-08** | Malicious SQL payload submitted in project title (`Project'; DROP TABLE users; --`) | Parameterized through SQLAlchemy; stored safely as literal text; zero SQL execution | **PASS** (`tests/test_security.py::test_sec_08_sql_injection_safety`) |
| **SEC-09** | XSS script injection in title (`<script>alert('XSS')</script>`) | Rendered escaped in Jinja2 templates; no script execution in DOM | **PASS** (`tests/test_security.py::test_sec_09_xss_safety_in_template_rendering`) |
| **SEC-10** | Session cookie flags | HttpOnly=True, SameSite=Lax flags configured | **PASS** (verified in `app/routes/auth.py` and `app/routes/views.py`) |
| **SEC-11** | Repeated divergence analysis execution | Idempotent; duplicate findings prevented via SHA-256 fingerprint uniqueness | **PASS** (`tests/test_divergence.py` - step 8) |
| **SEC-12** | Requirement revision after resolution | Historical version records and prior session links remain unedited | **PASS** (`tests/test_projects.py`, `app/services/requirement_service.py`) |
| **SEC-13** | Information leakage in public endpoints and headers | Public `/health` leaks zero database credentials or host info; security headers present (`X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `X-XSS-Protection`) | **PASS** (`tests/test_security.py::test_sec_13_security_headers_and_clean_health`) |
