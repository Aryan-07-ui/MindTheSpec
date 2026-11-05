import pytest

def test_phase2_requirement_management_and_rbac(client, seeded_users):
    owner_headers = seeded_users["owner"]["headers"]
    dev_headers = seeded_users["dev"]["headers"]
    test_headers = seeded_users["test"]["headers"]

    # 1. Owner creates project
    res = client.post("/api/projects", headers=owner_headers, json={"title": "FinTech Core"})
    assert res.status_code == 201
    proj_id = res.json()["id"]

    # 2. Add members: Analyst (dev user temporarily), Developer, Tester
    client.post(f"/api/projects/{proj_id}/members", headers=owner_headers, json={"email": "dev@example.com", "role": "analyst"})
    client.post(f"/api/projects/{proj_id}/members", headers=owner_headers, json={"email": "test@example.com", "role": "tester"})

    # 3. Analyst creates requirement REQ-101
    res = client.post(f"/api/projects/{proj_id}/requirements", headers=dev_headers, json={
        "req_code": "REQ-101",
        "title": "Instant Wire Transfers",
        "description": "System must process domestic wire transfers in real time.",
        "priority": "critical",
        "acceptance_criteria": "Settlement confirmation within 3 seconds; 99.99% uptime.",
    })
    assert res.status_code == 201
    req_data = res.json()
    req_id = req_data["id"]
    assert req_data["req_code"] == "REQ-101"
    assert req_data["priority"] == "critical"
    assert "Settlement confirmation" in req_data["acceptance_criteria"]

    # 4. Tester (read-only requirement permissions) attempts to update -> 403 Forbidden
    res = client.put(f"/api/requirements/{req_id}", headers=test_headers, json={
        "title": "Malicious Modification",
    })
    assert res.status_code == 403

    # 5. Analyst updates requirement details
    res = client.put(f"/api/requirements/{req_id}", headers=dev_headers, json={
        "title": "Instant Wire Transfers (Domestic & SEPA)",
        "priority": "high",
        "acceptance_criteria": "Settlement within 5 seconds with dual authorization.",
    })
    assert res.status_code == 200
    assert res.json()["title"] == "Instant Wire Transfers (Domestic & SEPA)"
    assert res.json()["priority"] == "high"

    # 6. Requirement detail fetch includes all Phase 2 metadata
    res = client.get(f"/api/requirements/{req_id}", headers=test_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == req_id
    assert data["priority"] == "high"
    assert "dual authorization" in data["acceptance_criteria"]


def test_phase2_team_management(client, seeded_users):
    owner_headers = seeded_users["owner"]["headers"]
    dev_headers = seeded_users["dev"]["headers"]
    stranger_headers = seeded_users["stranger"]["headers"]

    # 1. Create project
    res = client.post("/api/projects", headers=owner_headers, json={"title": "Team Test App"})
    proj_id = res.json()["id"]

    # 2. Add Developer
    res = client.post(f"/api/projects/{proj_id}/members", headers=owner_headers, json={"email": "dev@example.com", "role": "developer"})
    assert res.status_code == 201
    assert res.json()["role"] == "developer"

    # 3. Update existing member to Analyst (idempotent / no duplicate rows)
    res = client.post(f"/api/projects/{proj_id}/members", headers=owner_headers, json={"email": "dev@example.com", "role": "analyst"})
    assert res.status_code == 201
    assert res.json()["role"] == "analyst"

    # Verify member count remains 2 (owner + analyst)
    res = client.get(f"/api/projects/{proj_id}/members", headers=owner_headers)
    assert len(res.json()) == 2

    # 4. Non-owner cannot add members
    res = client.post(f"/api/projects/{proj_id}/members", headers=dev_headers, json={"email": "test@example.com", "role": "tester"})
    assert res.status_code == 403

    # 5. Remove member
    dev_id = seeded_users["dev"]["id"]
    res = client.delete(f"/api/projects/{proj_id}/members/{dev_id}", headers=owner_headers)
    assert res.status_code == 200

    # Removed member can no longer access project
    res = client.get(f"/api/projects/{proj_id}", headers=dev_headers)
    assert res.status_code == 403


def test_phase2_blind_interpretation_and_divergence_engine(client, seeded_users):
    owner_headers = seeded_users["owner"]["headers"]
    dev_headers = seeded_users["dev"]["headers"]
    test_headers = seeded_users["test"]["headers"]

    # Setup project, members, and requirement
    res = client.post("/api/projects", headers=owner_headers, json={"title": "Order Processing Service"})
    proj_id = res.json()["id"]
    client.post(f"/api/projects/{proj_id}/members", headers=owner_headers, json={"email": "dev@example.com", "role": "developer"})
    client.post(f"/api/projects/{proj_id}/members", headers=owner_headers, json={"email": "test@example.com", "role": "tester"})

    res = client.post(f"/api/projects/{proj_id}/requirements", headers=owner_headers, json={
        "req_code": "REQ-042",
        "title": "Automated Refund Engine",
        "description": "The system must process qualifying refund requests automatically.",
        "priority": "high",
        "acceptance_criteria": "Refund issued and balance restored.",
    })
    req_id = res.json()["id"]

    # Start session
    res = client.post(f"/api/requirements/{req_id}/sessions", headers=owner_headers, json={"mode": "standard"})
    assert res.status_code == 201
    session_id = res.json()["id"]

    # Developer submits interpretation:
    # - Instant SLA: 2 hours
    # - Behavior: automatic settlement
    # - Assumption: Registered customer with verified email
    # - Edge case: Network timeout during bank gateway API call
    dev_res = client.post(f"/api/sessions/{session_id}/interpretations", headers=dev_headers, json={
        "perspective": "Developer",
        "actor": "Payment Microservice",
        "delivery_hours": 2,
        "expected_behavior": "The service triggers automatic instant refund via Stripe API without human intervention.",
        "assumptions": "Customer is authenticated and refund request is within 30 days.",
        "acceptance_criteria": "Stripe webhook confirms refund with status succeeded.",
        "edge_cases": "Network timeout or rate limit on Stripe API triggers queued retry.",
        "notes": "Idempotency key required on payment intent.",
    })
    assert dev_res.status_code == 201
    dev_interp_id = dev_res.json()["id"]

    # Tester submits conflicting interpretation:
    # - SLA: 48 hours
    # - Behavior: manual review queue by support agent
    # - Assumption: Guest checkout allowed without prior login
    # - Edge case: Out of funds in merchant account
    test_res = client.post(f"/api/sessions/{session_id}/interpretations", headers=test_headers, json={
        "perspective": "Tester",
        "actor": "Customer Support Agent",
        "delivery_hours": 48,
        "expected_behavior": "Refund requests are placed into a manual queue for human approval and batch processing.",
        "assumptions": "Guest checkout users without account can request refund via order token.",
        "acceptance_criteria": "Agent clicks approve in admin dashboard; confirmation email dispatched.",
        "edge_cases": "Merchant bank account has insufficient balance to cover refund.",
        "notes": "Audit log must record approving agent ID.",
    })
    assert test_res.status_code == 201
    test_interp_id = test_res.json()["id"]

    # -----------------------------------------------------------------
    # Secrecy Check: Dev can only see Dev; Tester can only see Tester
    # -----------------------------------------------------------------
    res = client.get(f"/api/sessions/{session_id}/interpretations", headers=dev_headers)
    assert len(res.json()) == 1
    assert res.json()[0]["id"] == dev_interp_id

    res = client.get(f"/api/sessions/{session_id}/interpretations", headers=test_headers)
    assert len(res.json()) == 1
    assert res.json()[0]["id"] == test_interp_id

    # Direct IDOR protection
    res = client.get(f"/api/interpretations/{dev_interp_id}", headers=test_headers)
    assert res.status_code == 403

    # -----------------------------------------------------------------
    # Lock session -> Triggers deterministic divergence detection
    # -----------------------------------------------------------------
    res = client.post(f"/api/sessions/{session_id}/lock", headers=owner_headers)
    assert res.status_code == 200

    # Reveal session to team
    res = client.post(f"/api/sessions/{session_id}/reveal", headers=owner_headers)
    assert res.status_code == 200
    assert res.json()["status"] == "revealed"

    # Post-reveal: all interpretations visible
    res = client.get(f"/api/sessions/{session_id}/interpretations", headers=test_headers)
    assert len(res.json()) == 2

    # Check Divergence findings:
    res = client.get(f"/api/sessions/{session_id}/divergences", headers=dev_headers)
    assert res.status_code == 200
    divergences = res.json()
    assert len(divergences) >= 3

    categories = [d.get("category") or d.get("kind") for d in divergences]
    # 1. Timeline Mismatch (2h vs 48h)
    assert "timeline_mismatch" in categories
    # 2. Conflicting Operational Behavior ("automatic" vs "manual")
    assert "behavior_conflict" in categories
    # 3. Differing Assumptions (registered vs guest)
    assert "conflicting_assumptions" in categories

    # Resolve an individual divergence item
    timeline_div = next(d for d in divergences if d["field_name"] == "delivery_hours")
    res = client.post(f"/api/divergences/{timeline_div['id']}/resolve", headers=owner_headers)
    assert res.status_code == 200
    assert res.json()["review_status"] == "resolved"

    # -----------------------------------------------------------------
    # Record Official Resolution
    # -----------------------------------------------------------------
    res = client.post(f"/api/sessions/{session_id}/resolution", headers=owner_headers, json={
        "statement": "Tiered refund model: Automated refunds under $50 issued in 2 hours; refunds above $50 require agent approval within 24 hours.",
        "rationale": "Prevents fraud on high-value orders while providing instant resolution for low-risk transactions.",
    })
    assert res.status_code == 201
    assert res.json()["session_id"] == session_id

    # Session status is now resolved
    sess_res = client.get(f"/api/sessions/{session_id}", headers=dev_headers)
    assert sess_res.json()["status"] == "resolved"

    # Divergences all marked resolved
    div_res = client.get(f"/api/sessions/{session_id}/divergences", headers=dev_headers)
    for d in div_res.json():
        assert d["review_status"] == "resolved"
