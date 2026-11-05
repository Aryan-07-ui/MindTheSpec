# MindTheSpec
## Product Requirements Document (PRD)
**Product:** MindTheSpec — Requirement Interpretation & Divergence Detection Platform  
**Document version:** 2.0 (expanded scope) | **Date:** 29 October 2026  
**Delivery model:** Solo academic project | **Build approach:** Full implementation pass, iteratively verified | **Budget:** Zero paid APIs, services, or templates  
**Target checkpoints:** Security demonstration — 3 November 2026; final submission — 6 November 2026  
**Status:** Implementation specification. Functionality must be verified against the actual repository; this document does not claim features are already implemented.

> **Product promise:** Make different interpretations of a software requirement visible before they become expensive development mistakes.

## 1. Executive summary
Software requirements often appear clear until developers, testers, analysts, and clients implement different interpretations. MindTheSpec turns a written requirement into a structured, traceable decision. A project owner records the requirement; members submit interpretations independently while answers are hidden; a session is locked; the app reveals differences; the team records a resolution and preserves an audit trail. The product is not a generic task manager or AI chatbot. Its distinguishing feature is **blind interpretation followed by evidence-based divergence review**.

Build one complete, reliable user journey first, then continue through all in-scope product, security, design and publishing requirements instead of stopping after a short demo. Use deterministic comparisons for structured inputs. Never claim that free-text similarity proves a semantic contradiction, and never display invented confidence or accuracy scores.

### 1.1 Decision summary
| Decision | Specification |
|---|---|
| Name | MindTheSpec (exact styling, no spaces) |
| Core workflow | Project → Requirement → Blind interpretations → Lock → Divergence report → Resolution → Audit history |
| Main stack | Python 3.11, FastAPI, MySQL 8.4, server-rendered HTML/Jinja2 plus lightweight CSS/vanilla JavaScript |
| Existing environment | FastAPI `/docs` and MySQL app-user connection were previously confirmed; actual code and schema must be inspected before changing anything |
| Cost | Free/local tooling only; no paid LLM API, premium component libraries, or paid hosted database |
| Primary users | Project owner, developer, tester, analyst; solo demo via seeded accounts |
| Quality priority | Correct workflow and access control > stable persistence > complete, accessible UX > reliable deployment > verifiable polish |
| Work window | An extended focused build session is available: no 50-minute limitation; do not take unnecessary shortcuts or omit meaningful features solely for speed |

## 2. Problem, goals and boundaries
### 2.1 Problem
A requirement such as “The system must support fast delivery” is ambiguous: one stakeholder may expect 24 hours and another 48 hours. Normal review meetings can anchor later answers to the first person who speaks. A blind first pass captures independent expectations and makes disagreement easier to discuss.

### 2.2 Product goals
- **G1:** Allow a project owner to create and organize requirements in a persistent database.
- **G2:** Collect at least two independent stakeholder interpretations without premature disclosure.
- **G3:** On session lock, present specific differences, supporting inputs, and clear human-review status.
- **G4:** Record an accepted resolution and link it to the originating requirement and interpretation session.
- **G5:** Maintain an auditable sequence of meaningful changes and enforce project membership permissions.
- **G6:** Give an evaluator a reproducible local demo and an understandable ER diagram, API, tests, and setup instructions.

### 2.3 Scope exclusions and factual constraints
Extended time means the app should be complete and polished, not that every internet checklist item must be implemented misleadingly. The following are outside the truthful product requirements:
- Paid language-model APIs, fabricated semantic confidence, dependency on any subscription or payment card, pretend AI analysis, or unverifiable accuracy claims.
- Fabricated social proof, customer reviews, usage metrics, client logos, or claims of enterprise certification.
- Local-business structured data: MindTheSpec is software, not a physical retail location. If structured data is added, use only accurate `SoftwareApplication`/`WebSite` markup for real public pages.
- Billing, organization-scale SSO, native mobile apps and production enterprise scale that the academic product does not support.
- Buying a custom domain: wire a domain correctly if the user **already owns one**; otherwise a genuine free HTTPS hostname meets the deployment need.

### 2.4 Full-build priorities, not a time-boxed shortcut
**P0 — Essential application:** project/requirement CRUD; authenticated users/members; independent hidden submissions; atomic lock; deterministic divergence report; resolution; persistent traceability and audit; MySQL-backed schema; replayable seed; executable tests.

**P1 — Complete project experience:** requirement version history; useful owner/member roles; real dashboard metrics and filters; responsive polished UI across required routes; accessible forms, meaningful empty states, errors, loading states and breadcrumbs; setup and deployment documentation.

**P2 — Security and publishing:** negative authorization tests, session/CSRF validation, STRIDE evidence, migration safety, security headers, privacy/terms pages, accurate public metadata, canonical links, robots/sitemap, favicon, share preview asset, `SoftwareApplication` structured data if accurate, custom 404, bundle/performance checks, console-clean production build.

**P3 — Optional depth after P0–P2 are verified:** self-comparison perspectives; structured comparison expansions; CSV report export; advanced filtering; optional `llms.txt`; nicer audit and version diff views; existing custom-domain linkage if user supplies a domain. Never sacrifice correct core behavior to finish P3.

**Execution rule:** use multiple verified passes; keep building after the first working MVP. Do not mark unfinished features as complete. Ask only for necessary secrets, destructive actions or external account access.

## 3. Users, roles and permissions
### 3.1 Personas
- **Owner:** creates a project, adds requirements, creates/locks sessions, reviews conflicts and records resolutions.
- **Analyst:** structures requirement expectations and contributes an interpretation.
- **Developer:** records expected behavior and constraints from an implementation perspective.
- **Tester:** records observable acceptance criteria and edge-case expectations.
- **Observer:** optional read-only role after a session is locked; never reads unsubmitted or hidden content.

A **single-stakeholder mode** may let one user submit separately as two named perspectives for demonstration. It must be labeled as a self-comparison and not misrepresented as independent stakeholder consensus.

### 3.2 Permission matrix
| Action | Owner | Member (analyst/developer/tester) | Observer / other user |
|---|---|---|---|
| View project requirements | Yes | Yes, if a project member | Observer: yes if member; unrelated user: no |
| Create/edit requirement | Yes | No by default | No |
| Submit own interpretation | Yes | Yes, once per session (unless perspective mode) | No |
| Read others before lock | **No** | **No** | **No** |
| Lock and analyze session | Yes | No | No |
| View all after lock | Yes | Yes, if a project member | Observer: yes if member |
| Record / revise resolution | Yes | No by default | No |
| View audit trail | Yes | Read-only project-level events | Observer: limited read-only if allowed |

**Non-negotiable:** hiding interpretations only in the frontend is insufficient. Backend API queries must enforce the restriction; a direct URL or API request must not reveal hidden submissions.

## 4. Key user journeys and state model
### 4.1 Golden-path demo
1. Sign in as the seeded project owner. Open **Online Shopping System**.
2. Add requirement **REQ-001**: “The system must support fast delivery.”
3. Start a blind interpretation session and assign Developer and Tester test accounts.
4. As Developer, submit `delivery_hours = 24`, with acceptance criteria “delivery within one day.”
5. As Tester, submit `delivery_hours = 48`, with acceptance criteria “delivery within two days.”
6. Before lock, verify neither account can access the other's content by UI **or API**.
7. As Owner, lock the session; submissions become read-only.
8. Show a difference: **Delivery timeline — 24 h versus 48 h**. Do not assert which interpretation is correct.
9. Save a resolution, e.g., “Delivery within 48 hours for eligible orders,” with decision rationale.
10. Show the locked state, the resolved difference and immutable audit entries after a refresh.

### 4.2 Session states
`DRAFT → COLLECTING → LOCKED → ANALYZED → RESOLVED`

- **DRAFT:** session configured; no interpretations accepted yet.
- **COLLECTING:** eligible users submit or edit their own draft until submitting; other answers stay hidden.
- **LOCKED:** owner closes collection; atomic server action prevents further edits or new submissions.
- **ANALYZED:** comparison rows are generated and viewable by project members.
- **RESOLVED:** owner records a final decision; linked disagreements retain their historical evidence.

Allowed shortcut: locking may calculate the report in the same transaction or one immediate, idempotent follow-on operation. Invalid transitions return a controlled 409 error. The owner must not unlock merely to rewrite previous submissions. Create a new session/version for a new comparison cycle.

### 4.3 Requirement lifecycle
`DRAFT → ACTIVE → RESOLVED / ARCHIVED`. Requirement versions preserve historic text when revised after a resolution. Each session refers to the exact requirement version it evaluated. Never silently rewrite an interpretation's original requirement text.

## 5. Detailed functional requirements
Each requirement below has an ID, priority, behavior and acceptance criteria. The implementation log must mark each as **verified**, **partial**, or **not built**, backed by a test or a reproducible demo.

### FR-01 — Authentication and membership (P0/P1)
- Users can register or use seeded development accounts; passwords are stored only as modern password hashes.
- Users log in/out. Protected pages and API routes reject unauthenticated access.
- Owners manage project membership; authorization uses server-side member checks.
- **Accept:** user A cannot read or modify an unrelated project by guessing an ID; passwords never appear in API output or logs.

### FR-02 — Project management (P0)
- Owner creates a project with unique ID, title, description, status and timestamps.
- Dashboard lists only projects accessible to the logged-in user.
- **Accept:** create, list, refresh and retrieve one project persistently; empty state is informative.

### FR-03 — Requirements and versions (P0 base / P1 history)
- Owner adds requirement code, title, description, priority and structured acceptance notes.
- Each requirement belongs to one project and has one current version; edits create another version after a session is locked.
- **Accept:** submit and reload a requirement; invalid required fields return useful validation errors; historic versions remain accessible in read-only form, with the session linked to the exact version reviewed.

### FR-04 — Blind interpretation session (P0)
- Owner creates a session for a specific requirement version and opens collection.
- A participant submits a structured interpretation: actor/role, expected behavior, trigger/conditions, optional `delivery_hours`, constraints and acceptance criteria.
- Participants can view their **own** submission. Others' submissions are inaccessible until lock, including from API requests.
- One authenticated user has one submitted interpretation per normal session. Self-comparison mode explicitly creates separate perspectives and remains labeled.
- **Accept:** two test accounts submit differing answers; API request for another user's answer returns 403/404 before lock.

### FR-05 — Lock and divergence report (P0)
- Only owner locks. Lock prevents edits and reveals submissions to authorized project members.
- Compare fields using deterministic logic; store an explicit evidence record for each flagged difference.
- Show field, participant/perspective values, classification, and whether human review is needed.
- **Accept:** `24` vs `48` hours yields a timeline mismatch; matching normalized hours yields no timing mismatch; a re-run does not duplicate report rows.

### FR-06 — Resolution and traceability (P0)
- Owner records a resolution statement, rationale, decision timestamp and associated session.
- Original interpretations remain unmodified. Resolution is clearly presented as a human decision, not AI truth.
- **Accept:** save, refresh and read the resolution; mark report resolved; link from requirement to session and audit event.

### FR-07 — Audit log (P0 basic / P1 security)
- Server creates records for project creation, requirement changes, session open/lock, submissions (metadata only while hidden), comparison runs, and resolution.
- Include actor ID, event type, target type/ID, timestamp and safe minimal details.
- **Accept:** chronological history shows correct actors and transitions; no passwords, tokens or secret hidden interpretation bodies leak into general log messages.

### FR-08 — Dashboard and genuine counts (P1)
- Show counts derived from database queries: active projects, requirements, open sessions, unresolved divergences.
- Do not insert hard-coded “12,400 happy customers,” fake metrics or fake reviews.
- **Accept:** counts update after real actions; zero values and empty states are honest.

### FR-09 — Demo setup and documentation (P0/P1)
- One command or a documented small sequence launches the app locally; use `.env.example` and dependency pinning.
- Seed command populates a clearly labeled **demo** project, users, requirement and sample interpretations without overwriting existing data.
- **Accept:** another person can follow README from a fresh environment and run the golden path.

### FR-10 — Versioning and change review (P1)
- Revision of a requirement creates `requirement_versions(version_no + 1)` with author and timestamp; lock-cycle sessions remain anchored to the prior version.
- Show current version, history list and a readable comparison of earlier text against the current text.
- **Accept:** historical sessions continue displaying the text originally submitted for comparison after a new requirement revision.

### FR-11 — Member management and perspective clarity (P1)
- Owner can add existing users by verified identifier/email; choose analyst, developer, tester or observer membership, change permitted roles and revoke access.
- Display role, project owner and member list; all permissions are rechecked on backend on every request.
- **Accept:** revoked members are denied on the next request; a self-comparison by one person is explicitly labeled on every affected page and report.

### FR-12 — Findings triage and search (P1)
- Filter requirement and findings lists by session state, requirement status and resolution status; provide practical text search scoped to accessible projects.
- Finding cards show compared field, actual conflicting values, source actors, state and traceability to original submissions.
- **Accept:** filters update from database records, not fabricated frontend counts; no blind content leaks in results.

### FR-13 — Accessible, responsive production frontend (P1/P2)
- Build complete navigation, forms, loading/empty/error/confirmation states, toast or inline feedback, accessible labels and keyboard support.
- Provide desktop, tablet and mobile layouts without clipping. Avoid animation that obscures critical form content.
- **Accept:** keyboard-only golden path works; form errors identify fields; browser console has no uncaught errors in the primary demo.

### FR-14 — Public information pages and metadata (P2)
- Create a restrained, accurate landing page, About, Privacy, Terms, custom 404, favicon, social preview and truthful description of the project.
- Add public-page titles, descriptions, canonical links, accessible metadata, internal links, sitemap/robots and valid schema only where truthful.
- **Accept:** public pages have unique headings/titles; sensitive app routes never enter the sitemap; robots and metadata do not substitute for authentication.

### FR-15 — Export, operational support and diagnostics (P2/P3)
- Provide authenticated CSV export for divergence findings and resolutions if the core release is already verified. Escape spreadsheet formulas and never export hidden submissions.
- Provide health readiness response without secrets; configuration diagnostics must not leak credentials.
- **Accept:** exported data matches authorized, currently visible records; public health endpoint has no stack/config secrets.

### FR-16 — Privacy and data handling (P2)
- Disclose what demo/project data is retained, how users request removal and what the academic prototype does **not** guarantee. Restrict data visibility by membership and state.
- Do not place private requirements or tokens into public URL parameters, logs, social metadata, analytics or error messages.
- **Accept:** privacy page matches real collection and retention behavior; logout removes session access; no false compliance claims.

### FR-17 — Production verification and evaluator readiness (P2)
- Run application/tests and browser checks; record screenshots and honest implementation status. If an actual free persistent deployment is possible, verify its HTTPS URL from a separate session.
- **Accept:** reviewer can follow a deterministic setup/demo script, reproduce 24 h vs 48 h mismatch and inspect PASS/FAIL evidence for security-critical checks.

## 6. Divergence detection specification
### 6.1 Input design
Structured fields are preferred over pretending an arbitrary paragraph has machine-understandable meaning. Represent the interpretation as typed columns plus safe text fields: `perspective`, `actor`, `expected_behavior`, `trigger_conditions`, `delivery_hours` (nullable positive integer), `constraints`, `acceptance_criteria` (text or JSON list), `created_at`, `submitted_at`.

### 6.2 Algorithm (deterministic v1)
1. Load interpretations for a **locked** session only and confirm the user has project membership.
2. Trim/case-normalize comparable short categorical values; never erase original text.
3. For each field with at least two non-empty values, group distinct normalized values.
4. Create mismatch records for materially different typed values (e.g., `delivery_hours: 24 vs 48`, required vs optional if modeled as enum).
5. For descriptive text, use an optional **“potential wording difference — human review required”** flag; lexical inequality alone is not proof of a contradiction.
6. Store each finding with `field_name`, `kind`, `evidence_json`, `review_status`, session ID and creation time. Use uniqueness / idempotent upsert to prevent duplicates.
7. If only one submission is present, show **insufficient comparisons** instead of inventing a disagreement.

**Output language:** “Different stated delivery times” is valid. “AI detected a 92% conflict probability” is prohibited unless a real, documented model supports it.

### 6.3 Edge cases
- Duplicate submission → controlled error, not a hidden overwrite.
- Missing optional timeline → “not comparable”; do not equate null with zero.
- All fields agree → “No structured differences found”; do not claim the requirement is universally unambiguous.
- Session locked while submit in progress → transactional lock wins or submit wins consistently, never half-writes.
- Two perspectives by one user → label **self-comparison** in UI and reports.
- Updated requirement → create new version/session; historic comparison remains linked to previous version.

## 7. Data model and DBMS requirements
This schema is a target, not a claim that the tables currently exist. Preserve existing names and migrate non-destructively when possible. Use InnoDB, utf8mb4, UTC timestamps and foreign keys.

| Entity | Main columns and constraints |
|---|---|
| `users` | `id` PK; `email` UNIQUE NOT NULL; `name`; `password_hash`; timestamps |
| `projects` | `id` PK; `owner_id` FK → users; `title`; `description`; `status`; timestamps |
| `project_members` | Composite PK (`project_id`, `user_id`); each FK; `role`; `joined_at` |
| `requirements` | `id` PK; `project_id` FK; `req_code`; `title`; `status`; `current_version_id` nullable; UNIQUE(project_id, req_code) |
| `requirement_versions` | `id` PK; `requirement_id` FK; `version_no`; `body`; `acceptance_notes`; `created_by` FK; UNIQUE(requirement_id, version_no) |
| `interpretation_sessions` | `id` PK; `requirement_version_id` FK; `created_by` FK; `status`; `mode`; `locked_at`; timestamps |
| `interpretations` | `id` PK; `session_id` FK; `user_id` FK; `perspective`; structured content; `submitted_at`; UNIQUE(session_id, user_id) for normal mode |
| `divergences` | `id` PK; `session_id` FK; `field_name`; `kind`; `evidence_json`; `review_status`; unique stable fingerprint |
| `divergence_interpretations` | Composite PK (`divergence_id`, `interpretation_id`) with two FKs; evidence relation |
| `resolutions` | `id` PK; `session_id` FK UNIQUE for one accepted resolution per cycle; `statement`; `rationale`; `decided_by` FK; `decided_at` |
| `audit_logs` | `id` PK; `project_id` FK; `actor_id` FK; `action`; `entity_type`; `entity_id`; `metadata_json`; `created_at` |

**Model note:** the original concept has a `RESOLUTION` entity; use plural or singular naming consistently with the existing code. Avoid multiple conflicting sources of truth for “current version.” Set the pointer transactionally or derive it from the highest valid version, and document which method you use.

**Key indexes:** session by requirement version/status; interpretations by session/user; requirement by project/code; divergences by session/review status; audit by project/created_at. FK referential behavior must be explicit: generally restrict deletion of history-bearing records, use archive/soft-delete, and do not cascade-delete audit history without a documented retention rule.

**DBMS learning evidence:** ER diagram; PK/FK/composite keys; normalization reasoning (at least 3NF for relational entities); SQL joins for requirement/session reports; aggregate `GROUP BY` for genuine dashboard stats; transactions for lock+resolution; safe migrations; parameterized queries.

## 8. API contract (proposed v1)
Use REST-style routes under `/api`. Keep OpenAPI `/docs` enabled for local testing and protect its exposure as appropriate for public deployment. Shapes are illustrative; do not blindly replace compatible existing routes.

| Method / route | Behavior | Access |
|---|---|---|
| `POST /api/auth/login`, `POST /api/auth/logout` | Start/end secure session | Public / authenticated |
| `GET /api/projects`, `POST /api/projects` | List accessible projects / create | Authenticated |
| `GET /api/projects/{id}` | Project detail | Project member |
| `POST /api/projects/{id}/members` | Add member | Owner |
| `GET /api/projects/{id}/requirements`, `POST ...` | List/create requirements | Member / owner |
| `POST /api/requirements/{id}/sessions` | New session tied to current version | Owner |
| `POST /api/sessions/{id}/interpretations` | Create own interpretation | Eligible member, collecting |
| `GET /api/sessions/{id}/interpretations` | Own only before lock, all after lock | Member, filtered server-side |
| `POST /api/sessions/{id}/lock` | Atomic lock | Owner |
| `GET /api/sessions/{id}/divergences` | Report after lock | Member |
| `POST /api/sessions/{id}/resolution` | Record owner decision | Owner |
| `GET /api/projects/{id}/audit` | Safe activity history | Authorized member |
| `GET /health` | Minimal readiness/liveness | Public with no secrets |

**API behavior:** validate with Pydantic; use 400/422 for bad input, 401 for unauthenticated, 403 for forbidden, 404 for missing/out-of-scope resources, 409 for state conflicts. Never return raw database traces, authentication secrets, or another user's blind content. Never infer authorization from a client-supplied role string alone.

## 9. Information architecture and user interface
### 9.1 Public pages (in scope for a complete public deployment)
- `/` — clear product explanation; short, accurate headline: **“Catch conflicting requirement interpretations before development begins.”**
- `/about` — process and limitations, no fictitious usage claims.
- `/privacy` and `/terms` — simple truthful documents that reflect actual data collection and behavior; do not claim certifications not obtained.
- `/login` — authentication. When publishing the complete site, these public pages are included and must contain only truthful product information.

### 9.2 Private application pages (core)
- `/app` — honest overview dashboard and project list.
- `/app/projects/{id}` — requirements list, members and recent activity.
- `/app/requirements/{id}` — full requirement, current version and sessions.
- `/app/sessions/{id}` — interpretation form, state indicator and submission progress (counts only while collecting).
- `/app/sessions/{id}/compare` — side-by-side evidence and specific divergences; locked sessions only.
- `/app/sessions/{id}/resolution` — decision with rationale and linked evidence.
- `/app/projects/{id}/history` — timestamped audit entries.
- `/404` — useful custom not-found state, with navigation back.

### 9.3 Visual design rules based on the supplied screenshots
**Intent:** restrained, trustworthy, accessible developer-tool UI; not an over-styled AI landing-page clone.

**Avoid:** purple gradients; vague hero text; fictitious counters/reviews/metrics; excessive scroll or cursor animation; pill-shaped buttons everywhere; emojis as UI icons; generic AI-generated hero images; “made with AI” badges; robotic promotional copy; em dashes used as decorative filler; lorem ipsum or placeholder text in the finished experience.

**Use:** charcoal/navy/neutral slate + one restrained blue/teal accent; simple 6–10px corner radius (not capsules); clear page hierarchy; accessible typography; consistent SVG icon set if needed; concise outcome-led copy; visible focus states; helpful empty/error/loading states; meaningful validation messages. No unnecessary images are required for this product.

**Component rules:** semantic header/nav/main/section/footer; one clear H1 per page; ordinary buttons that say “Add requirement,” “Submit interpretation,” “Lock session,” “Record resolution”; confirmation before lock; breadcrumbs on nested project screens; tables with headings and mobile overflow handling; real data only. Support prefers-reduced-motion and keyboard navigation.

### 9.4 Content and microcopy
- Good hero: “Spot conflicting interpretations before the team builds the wrong thing.”
- Bad hero: “Revolutionizing next-generation AI-powered collaboration.”
- Good discrepancy: “Developer: 24 hours · Tester: 48 hours. Requires a decision.”
- Bad discrepancy: “AI is 98% confident your team is wrong.”
- Good empty state: “No requirements yet. Add one to start an interpretation session.”
- Good security message: “Interpretations stay hidden until the owner locks this session.”

## 10. Complete design, technical SEO and production checklist
Both supplied screenshots are explicit design and release-quality inputs. Implement **every relevant, truthful improvement** during the complete build, rather than dismissing useful items as not worth the time. Public-site SEO applies to public pages; private requirement data must remain authenticated and non-indexable. Security does not come from `robots.txt`.

| Item from screenshots | Decision for MindTheSpec |
|---|---|
| Remove Vite/React from browser | **Interpret correctly:** do not expose dev server, dev overlays or test scaffolding in production. React is not banned; prefer vanilla JS/Jinja2 for faster MVP. |
| Internal links, breadcrumbs, unique page headings and titles | **Required** for clear navigation; use per-page titles and one H1. |
| Meta descriptions, canonical tags, social share image | **Required for deployed public pages**; accurate page-specific values; private screens must not expose content. |
| Favicon, accessible image alt text, custom 404 | **Required** basic polish; alt text only where images convey information. |
| Robots.txt and sitemap.xml | **Required when the public landing site is deployed.** Never list private app routes in a public sitemap. |
| Structured data | **Required if applicable and truthful:** `SoftwareApplication` / `WebSite`, without invented ratings. |
| Local business schema | **Not applicable**: MindTheSpec is not a physical local business. |
| llms.txt | **P3 optional**: create accurate `llms.txt` only after core, accessibility and search basics; it is not a search ranking guarantee. |
| Custom domain | **Supported when user already owns a domain**; otherwise a free HTTPS subdomain is appropriate and no purchase is mandated. |
| Remove production source maps | **Required deployment review:** disable public source-map serving if unnecessary, never embed secrets; retain private debugging facilities. |
| Fix console errors and remove placeholders | **Required**: no uncaught errors or lorem ipsum on demo path. |
| Reduce huge JS bundles | **Required in spirit**: keep frontend lightweight, avoid unnecessary dependencies. |
| Privacy / Terms pages | **Required if public users are invited**; accurately describe actual app behavior, otherwise label prototype as limited-access demo. |
| Fake counts, reviews, AI artwork, emoji icons, aggressive animation | **Prohibited by product design rule**. |

**Search/privacy principle:** public pages may be indexable by design; login, dashboards, requirement text, interpretation content, audit logs, and APIs must never be publicly indexable or exposed to unauthenticated users. Restrict access on the server, not solely using meta tags or robots rules.

## 11. Security and privacy requirements (STRIDE-aligned)
### 11.1 Assets and trust boundaries
Most sensitive asset: **unsubmitted or not-yet-revealed interpretations**. Also protect requirement versions, audit history, project membership, credentials and session tokens. Boundaries: browser → FastAPI routes → data access layer → MySQL. Attackers include anonymous visitors, logged-in non-members and malicious project members.

### 11.2 Controls
- **Spoofing:** hashed passwords, secure sessions, no client-trusted user IDs or roles, logout invalidates session.
- **Tampering:** ownership checks on writes, Pydantic input validation, transaction-safe session locking, historical immutability for submitted data and audit events.
- **Repudiation:** append-only application audit events, timestamps and actor IDs; restrict edits/deletion of log entries.
- **Information disclosure:** enforce hidden-until-lock in all APIs; prevent insecure direct object reference (IDOR); no token or secret logging; redact errors; set security headers.
- **Denial of service:** sane length limits, basic request limits where feasible, paginated lists, query indexes and bounded comparison inputs.
- **Elevation of privilege:** server-side role checks on every protected operation; do not accept `owner` from submitted form data.

**Web configuration:** HTTPS on public deployments; HttpOnly/Secure/SameSite cookie flags as appropriate; CSRF protection on cookie-authenticated mutating requests; trusted CORS origins if needed; escaped output to prevent XSS; environment variables for secrets; `.env` ignored by Git; restrictive database account grants. Avoid putting JWTs in browser localStorage just for convenience.

### 11.3 Security checkpoint acceptance
- Unauthenticated and unrelated-user API requests are denied.
- Before lock, members cannot retrieve others' interpretations by direct request.
- Duplicate submit and lock state conflicts fail safely.
- SQL inputs cannot alter query structure; template output is safely escaped.
- Secret scan finds no committed DB passwords, keys, tokens or `.env`.
- Access-control and blind-visibility tests are runnable from README.
- Live URL, if available, uses HTTPS and returns no debug traceback; otherwise document deployment blocker honestly.

## 12. Architecture, infrastructure and deployment
### 12.1 Recommended implementation
**Monolith for speed:** FastAPI application + Jinja2 views / static CSS/vanilla JS + Pydantic validation + SQLAlchemy or existing parameterized MySQL access + Alembic migrations if already present. Continue with current MySQL 8.4 database `mind_the_spec` and least-privilege app user. If the repository already uses a viable UI framework, prefer retaining it over a rewrite.

Suggested layout: `app/main.py`, `app/routes/`, `app/models/`, `app/schemas/`, `app/services/divergence.py`, `app/templates/`, `app/static/`, `migrations/`, `tests/`, `scripts/seed_demo.py`, `README.md`, `.env.example`.

**Fallback rule:** If MySQL setup blocks a *temporary local demo*, use a documented temporary SQLite option, not a secret permanent replacement. Final integrated-DBMS evidence should use MySQL. Never delete a working database to change stacks.

### 12.2 Deployment
Deploy only on a free tier that actually supports the chosen stack and persistence, or use a local demonstration plus honest documentation of the missing live URL. Confirm current provider limitations before choosing. Separate demo credentials from production; never publish an open admin account with a weak default password. Configure production environment variables, HTTPS, migrations and a durable database. Provide a health endpoint and a clear deployment README. A custom domain is optional.

## 13. Testing and acceptance matrix
| Test ID | Scenario | Expected result |
|---|---|---|
| T-01 | Owner creates project and requirement | Persisted, retrievable after restart |
| T-02 | Developer submits interpretation in collecting session | Only their own submission visible pre-lock |
| T-03 | Tester attempts to fetch Developer answer via API pre-lock | Denied or excluded on server side |
| T-04 | Owner locks session | Future edits/submissions rejected; state persists |
| T-05 | Compare 24 h and 48 h | One explicit delivery-time mismatch with both values |
| T-06 | Compare 24 h and 24 h | No timeline mismatch |
| T-07 | Owner records resolution | Decision + rationale persisted and linked |
| T-08 | Non-member guesses project/session ID | 403/404; no data exposure |
| T-09 | Anonymous user calls protected API | 401 or authentication redirect |
| T-10 | Re-run comparison or reload page | No duplicate findings or data loss |
| T-11 | Invalid field lengths / missing values | Clear 422 or validation message, no server crash |
| T-12 | Access on mobile viewport, keyboard only | Critical flow usable; no inaccessible controls |
| T-13 | Logs and repository inspected | No credentials in source, logs or responses |
| T-14 | Fresh install follows README | Reproducible demo with stated prerequisites |

Automate the highest-risk routes with pytest/TestClient and integration tests using a clean test database. A manual browser walkthrough with screenshots supplements, but does not replace, backend permission tests.

## 14. Execution plan and checkpoints
### Phase A — Minimal verifiable app (first priority)
1. Inspect repository, current migrations, `.env.example` and API routes without modifying existing data.
2. Make the shortest local launch path pass.
3. Complete core project/requirement CRUD; seed one project and two users.
4. Implement blind collection and server-side visibility filtering.
5. Implement atomic lock, rule-based comparison, resolution and audit trail.
6. Run full golden-path demo; fix blocking errors. Save a truthful progress report.

### Phase B — 3 November 2026 security check
1. Verify access controls and lock rules with negative tests.
2. Check secrets, session handling, validation, SQL injection protections and safe errors.
3. Attempt a deploy on a genuinely free provider if feasible; provide live URL only when verified.
4. Produce STRIDE mapping and security evidence (tests, screenshots, checklist).

### Phase C — 6 November 2026 final submission
1. Complete and verify responsive interface, audit display and version history; record any remaining blocked item explicitly.
2. Complete ER diagram, SQL schema/migrations, README, API explanation and demo seed.
3. Capture screenshots of actual working flows and final test results.
4. Report what is complete, partial and missing. Never fabricate work or percentages.

### Definition of done for the core release
A fresh setup can authenticate, create a project/requirement, collect two mutually hidden submissions, lock a session, show a genuine data-backed difference, record a resolution, reload persistent history, and pass access-control tests. A teacher can follow these actions without editing code. A screenshot or static HTML mock alone is **not** considered complete.

## 15. Risks, tradeoffs and default decisions
| Risk | Mitigation |
|---|---|
| Solo developer and deadline pressure | Establish a verified vertical slice first, then work through the full release checklist systematically |
| Existing code may differ from this PRD | Audit and adapt; preserve working migrations/routes; record deviations |
| Blind interpretations accidentally exposed | Test direct API access under different authenticated users |
| AI-generated code appears correct but is broken | Require actual command output, tests and browser confirmation |
| Database or cloud setup fails | Keep local reliable; document fallback and deployment blockers honestly |
| Rule-based detection overstates certainty | Report typed differences and human-review labels only |
| Public SEO work competes with core features | Build it into the release pass once the core flow works; implement all relevant, truthful public-page items |

**Defaults pending repository inspection:** MySQL 8.4 remains authoritative; session creator is project owner; a lock is irreversible; 2+ submissions required for a normal comparison; one accepted resolution per session; demo accounts are local-only and seeded safely; public registration is optional; version history is in P1 and should be implemented after secure core workflows.

## 16. Demonstration script (3 to 5 minutes)
1. “MindTheSpec helps teams find differing interpretations of a requirement before building it.”
2. Show project/requirement page and mention PK/FK-backed data persistence.
3. Use two demo users to submit 24-hour and 48-hour expectations; show that answers are hidden.
4. Lock as owner; compare the two inputs; point out the exact timeline difference.
5. Enter the accepted decision and inspect the audit history.
6. Refresh. Show data persists. If asked, open `/docs`, ER diagram and the access-control test.

**Truthful presentation rule:** say “implemented and tested” only where evidence exists; distinguish a seeded demo from live production usage and a deterministic rule from an AI model.

## 17. Full product design, screen-by-screen acceptance
The finished application is an operational product, not a static dashboard. Implement the screen sequence below with linked data, permissions, normal/empty/error states, and responsive behavior.

| Route / screen | Required interface elements | Acceptance demonstration |
|---|---|---|
| `/` public home | Clear title; explicit problem and flow; functional CTA to sign in; honest feature summary; footer legal links | No vague hero text or fabricated outcomes; metadata and custom logo/favicon visible |
| `/about` | What the project does, interpretation vs resolution distinctions, limitations | Describes deterministic detection truthfully |
| `/login` (and `/register` if enabled) | Labeled inputs, password handling, form errors, session feedback | Redirects to intended authorized page, never reveals account existence needlessly |
| `/app` dashboard | Accessible project cards/table, real status counts, activity snippets | Counts reflect rows and change with actual actions |
| `/app/projects/{id}` | Title, member list, role badges, requirements, project actions | Non-members cannot view even by guessed URL |
| `/app/requirements/{id}` | Requirement details, priority/status, versions, sessions, start action | Sessions correctly link to their requirement version |
| `/app/sessions/{id}` | State banner, own blind interpretation form, safe participation count, submit action | No other person's answers are returned pre-lock |
| `/app/sessions/{id}/compare` | Side-by-side data and findings with source names, human-review notes | 24 h vs 48 h flagged; agreeing fields not falsely flagged |
| `/app/sessions/{id}/resolution` | Owner decision editor, rationale, decision time, read-only final result | Non-owner cannot write resolution |
| `/app/projects/{id}/history` | Time-ordered audit events with actor, date, action and target | Logs persist and contain no hidden answer bodies |
| `/privacy`, `/terms`, custom 404 | Accurate policy text, navigation, proper HTTP status | Real 404 status, helpful next action and no broken links |

### 17.1 Layout tokens and components
- **Brand palette:** light interface by default. Canvas `#F7F9FC`, white cards, dark ink `#152238`, muted labels `#58677D`, primary blue `#1B5FA8`, teal status highlight `#157D73`, restrained warning red `#B43F3F`. Ensure accessible contrast; do not rely on color alone.
- **Typography:** one modern system/font stack, responsive sizes, base body 15–16 px, line-height around 1.5; clear H1/H2 hierarchy. No emoji used as icons; use consistent SVG icon library or simple CSS.
- **Layout:** centered public-site content, task-oriented sidebar/topbar for authenticated workspace; practical table/card density, consistent 8 px spacing system, 6–10 px corner radius, not pill-heavy.
- **Motion:** subtle purposeful feedback only, no scroll choreography or cursor trails; honor `prefers-reduced-motion`.
- **Components:** primary/secondary/destructive actions, confirmation dialog for lock, status chips with text, accessible tabs if needed, form field error, empty-state action, skeleton/loading indicator, toast/status region, data table, responsive breadcrumbs.
- **Style:** no purple gradients, decorative AI imagery, fake counters/reviews, AI-sounding marketing phrases, AI attribution badges, pointless em dashes, fake customer logos or placeholder lorem ipsum in production screens.

### 17.2 Responsive and accessibility acceptance
- Test at roughly 360px, 768px and 1280px viewports; content wraps without horizontal page overflow. Wide comparison tables may have clearly labeled internal horizontal scrolling.
- Tab order, visible focus, correctly associated `<label>`s, accessible validation summary, readable error text, landmarks and heading order.
- State communicated in words and icons, not color alone. Alt text for meaningful images; decorative images use empty alt or CSS backgrounds.
- Do not require hover for actions. Confirmation dialog announces its purpose and returns focus after closing.

## 18. Detailed publishing checklist from both screenshots
Treat this as a release audit, not as SEO theater. An individual item passes only if it is implemented and manually or automatically verified.

| Screenshot advice | Specific MindTheSpec requirement | Validation |
|---|---|---|
| No purple gradient | Neutral white/slate surfaces with one blue/teal accent | Visually inspect public and app pages |
| No vague hero copy | State exact outcome and audience in first heading | Public H1 describes interpretation disagreements |
| No fake counters, metrics, reviews | DB-backed counts only; no marketing reviews or fictitious clients | Cross-check counts against real DB |
| No excessive scroll animation / cursor animation | Limit to small purposeful transitions; honor reduced motion | Inspect interactions and motion settings |
| Avoid all-pill controls | Standard moderate-radius buttons and inputs | Check consistency across views |
| No emoji icons or generic AI images | Crisp vector SVG icons; no filler hero artwork | Asset audit |
| No “made with AI” badge / robotic AI copy | Authored, specific copy; attribute what the project truly does | Copy review |
| No filler em dashes | Use concise natural sentences and standard punctuation | Final copy pass |
| Terms & Conditions and Privacy pages | Real `/terms` and `/privacy` links; accurate prototype disclosure | Open pages; check visible footer links |
| Favicon | Provide SVG/PNG favicon referenced by layouts | Browser tab and network check |
| Custom domain | If already owned, allow simple DNS/HTTPS configuration notes; do not purchase | Confirm configured DNS only if applicable |
| Remove Vite/React from browser | Do **not** leak development badges/overlays or ship a dev server; using React/Vite is not itself a bug | Production build inspection |
| Internal links | Every public page has valid links; app nav stays authorized | Link audit |
| Unique meta descriptions | Public routes have relevant page-specific descriptions | Inspect page source |
| Custom 404 | Friendly error view and HTTP 404 response | Request missing public and private paths |
| Alt text | Meaningful images describe their content, decorative assets hidden from assistive tech | Accessibility check |
| Breadcrumbs | Useful nested navigation for projects/requirements/sessions | Check navigability |
| Proper page sources | Avoid fabricated citations or unlicensed images; use direct accurate docs links where appropriate | Content and asset audit |
| Unique headings / titles per page | One H1 per page, page-specific `<title>` | Inspect DOM and head |
| Canonical tags | Public indexable pages only, use true origin URLs after deployment | View source on public pages |
| Structured data | Accurate `SoftwareApplication` or `WebSite` JSON-LD if deployed; no invented reviews or pricing | Schema validity check |
| Fix console errors | No uncaught JS runtime errors or failed API calls on golden path | Browser console/network log |
| Remove public production source maps | Build config disables public maps when not needed; never ship secrets | Inspect deployed assets |
| `llms.txt` | Optional accurate plain-text guide to public project pages; no claim of SEO benefit | If included, content accurate and non-sensitive |
| `robots.txt` | Permit public informational pages; disallow private paths as crawler guidance, **not security** | Request `/robots.txt`; verify private auth anyway |
| Local business schema | **Do not implement**: would misrepresent a software project with no physical business | Check JSON-LD lacks false location claims |
| Remove placeholder text | Real labels, detailed empty states and truthful seeded example data | Search source for lorem/TODO in presented pages |
| `sitemap.xml` | List real public indexable pages only, exclude login, app, session and API | Request sitemap and inspect URLs |
| Social share image | Original typographic/brand preview with OG/Twitter metadata; no photos needed | Check public page metadata |
| Reduce huge JS bundles | Prefer server-rendered pages and minimal JS; avoid unnecessary client packages | Check production assets and performance |

**Important:** no public indexing of interpretation content. `noindex` and robots policies provide crawler guidance only; auth/authorization and restricted responses protect actual data. Terms and privacy text must reflect the implemented product; do not promise a deletion workflow that does not exist.

## 19. Integration, implementation details and migration safety
### 19.1 Existing database compatibility
The known local schema/database identity is `mind_the_spec`; the known normal application user previously had CRUD privileges only. **Do not attempt DDL or Alembic migrations using a user without CREATE/ALTER privileges.** Inspect the actual grants. Use a separately configured trusted administrative migration connection for initial schema creation, or provide SQL scripts the owner can execute through MySQL CLI under a suitable privileged account. Keep normal runtime access least-privileged. Never print passwords or overwrite `.env`.

### 19.2 Services and transaction boundaries
- `auth_service`: authentication, password verification, session creation/invalidation, membership enforcement.
- `project_service`: project CRUD and membership, scoped requirements.
- `interpretation_service`: submissions, identity checks, safe pre-lock views and session transitions.
- `divergence_service`: field-level comparison, evidence snapshots, stable fingerprint and idempotent writes.
- `resolution_service`: author decision and immutable historical linkage.
- `audit_service`: safe, append-only event recording in the same transaction as business state changes where practical.
- Lock transition uses a row lock or equivalent serializable logic; re-check status and permissions inside the transaction; compare only the locked committed snapshot.

### 19.3 Data correctness
- Use MySQL `utf8mb4`, FK constraints, unique keys, typed nullable values and indexed ownership paths. Use UTC internally; show human local dates clearly.
- Validate allowed roles and statuses as enums; session status cannot be arbitrarily set from client JSON.
- Maintain stable requirement codes and version uniqueness within a project. History-bearing entities should be archived rather than silently cascaded away.
- Enforce `UNIQUE(session_id,user_id)` for normal stakeholder mode; if adding self-comparison, use a separate perspective identity or distinct mode-specific uniqueness rule without breaking multi-user security.
- Decide and document whether `ANALYZED` is an actual DB status or derived presentation stage; implementation and tests must agree.

### 19.4 Example acceptance payloads (illustrative)
**New requirement:** project ID, `req_code: REQ-001`, title `Fast delivery`, body `The system must support fast delivery.`, priority `high`, optional acceptance notes.

**Interpretation A:** session ID, role/perspective `developer`, `delivery_hours: 24`, expected behavior and criteria in real text.

**Interpretation B:** same session, role/perspective `tester`, `delivery_hours: 48`, different stated acceptance criterion.

**Expected divergence record:** `field_name: delivery_hours`, kind `structured_mismatch`, evidence lists source interpretation identifiers and values 24 and 48, review status `open`.

**Expected resolution:** `Delivery within 48 hours for eligible orders`, rationale `Business and operations agreed on a measurable 48-hour expectation`, owner decision timestamp, linked session/version. These are labeled **demo sample data**, not actual business agreements.

## 20. More complete engineering verification matrix
| Code | Verification | Result required |
|---|---|---|
| SEC-01 | Anonymous GET project | Auth redirect or 401 |
| SEC-02 | Non-member GET project, requirement and session | 403/404 without data leak |
| SEC-03 | Member A fetches Member B interpretation while collecting | Forbidden or omitted from response |
| SEC-04 | Member A guesses an interpretation primary key | Forbidden even if both share project |
| SEC-05 | Owner locks while other client attempts submission | One consistent state, no partial update |
| SEC-06 | Member attempts lock, resolve or reassign roles | Forbidden |
| SEC-07 | Valid user session expired/logged out | Protected routes inaccessible |
| SEC-08 | POST with malicious SQL-like content | Stored as data / safely rejected, never executable SQL |
| SEC-09 | HTML/script-like text in requirement title | Rendered escaped, no script execution |
| SEC-10 | Cookie-authenticated mutation with invalid/missing CSRF token | Rejected when CSRF protection applies |
| SEC-11 | Re-run compare | Stable finding count; no duplicates |
| SEC-12 | Change requirement after closed session | Historical version and evidence unchanged |
| SEC-13 | API errors and public health check | No traces, credentials, DB host or tokens leaked |
| UX-01 | Login and owner dashboard on narrow mobile viewport | No unusable elements or clipped forms |
| UX-02 | Tab through create/submit/lock/resolve | All critical controls keyboard reachable |
| UX-03 | 404 and validation handling | Clear messages, correct status and navigation |
| WEB-01 | Unique page title, H1, meta on public pages | Correct source markup |
| WEB-02 | Sitemap, robots, canonical and schema | Truthful and public only |
| WEB-03 | Favicon, OG preview, links, no placeholders | Complete asset and crawl audit |
| OPS-01 | Fresh Windows setup, migrations, seed and run | Reproducible using README |
| OPS-02 | Server restart and DB queries | Durable state |
| OPS-03 | Git/secrets/build check | No committed `.env`, credentials or debug bundle |
| OPS-04 | Public HTTPS deployment where feasible | Verified healthy real URL, or explicit blocker |

## 21. Agent deliverables and reporting format
Every milestone produces code plus evidence, rather than a narrative of intended changes. The agent should maintain:
1. `README.md` with copy-paste PowerShell setup, MySQL initialization, app startup and tests.
2. `.env.example`, restrictive `.gitignore`, migration scripts, schema diagram, non-destructive demo seed.
3. `IMPLEMENTATION_STATUS.md` mapping FR-01 through FR-17 to VERIFIED / PARTIAL / NOT IMPLEMENTED and the exact supporting test or URL.
4. `SECURITY_CHECKLIST.md` mapped to STRIDE and SEC-01 through SEC-13.
5. `DEMO_WALKTHROUGH.md` describing owner/developer/tester flows, sample login *setup* without publishing weak credentials, and expected findings.
6. `RELEASE_CHECKLIST.md` covering every relevant line from the two screenshots, evidence and conditional/not-applicable reasons.
7. Actual test outputs and, where possible, screenshots of functioning UI and browser console without sensitive information.

**Finish standard:** a reviewer can reproduce the core workflow, inspect real database records and see a professional, accessible application and an honest security/release report. If a checklist item requires something outside this project (such as a physical business location), record why it would be incorrect to implement instead of adding a false feature.

## 22. References and implementation guidance
- [Google Antigravity Agent documentation](https://antigravity.google/docs/agent?hl=en) — existing-code inspection, agent execution and verification workflow.
- [Google Search Central SEO starter guide](https://developers.google.com/search/docs/fundamentals/seo-starter-guide) — public-page titles, content and indexing foundations.
- [OWASP Application Security Verification Standard](https://owasp.org/www-project-application-security-verification-standard/) — security verification guidance.
- [FastAPI documentation](https://fastapi.tiangolo.com/) — Pydantic validation, route and test practices.

**Input design influences:** both supplied screenshots' visual anti-pattern checklist and production/SEO checklist, adapted into explicit verification requirements. Do not create misinformation or irrelevant schema merely to tick a checkbox.
