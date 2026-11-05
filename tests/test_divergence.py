def test_lock_and_divergence_detection_mismatch(client, seeded_users):
    owner_headers = seeded_users["owner"]["headers"]
    dev_headers = seeded_users["dev"]["headers"]
    test_headers = seeded_users["test"]["headers"]

    # 1. Setup project, requirement, session
    res = client.post("/api/projects", headers=owner_headers, json={"title": "Delivery App"})
    proj_id = res.json()["id"]
    client.post(f"/api/projects/{proj_id}/members", headers=owner_headers, json={"email": "dev@example.com", "role": "developer"})
    client.post(f"/api/projects/{proj_id}/members", headers=owner_headers, json={"email": "test@example.com", "role": "tester"})

    res = client.post(f"/api/projects/{proj_id}/requirements", headers=owner_headers, json={
        "req_code": "REQ-001",
        "title": "Fast Delivery",
        "description": "The system must support fast delivery.",
    })
    req_id = res.json()["id"]

    res = client.post(f"/api/requirements/{req_id}/sessions", headers=owner_headers, json={"mode": "standard"})
    session_id = res.json()["id"]

    # 2. Submissions: Dev states 24h, Tester states 48h (T-05)
    client.post(f"/api/sessions/{session_id}/interpretations", headers=dev_headers, json={
        "perspective": "Developer",
        "actor": "Order Worker",
        "expected_behavior": "Dispatch order in 24 hours.",
        "delivery_hours": 24,
        "acceptance_criteria": "Delivery within one day.",
    })
    client.post(f"/api/sessions/{session_id}/interpretations", headers=test_headers, json={
        "perspective": "Tester",
        "actor": "Ground Logistics",
        "expected_behavior": "Package delivered to door within 48 hours.",
        "delivery_hours": 48,
        "acceptance_criteria": "Delivery within two days.",
    })

    # 3. Non-owner attempts to lock -> 403 Forbidden (SEC-06)
    res = client.post(f"/api/sessions/{session_id}/lock", headers=dev_headers)
    assert res.status_code == 403

    # 4. Owner locks session (T-04)
    res = client.post(f"/api/sessions/{session_id}/lock", headers=owner_headers)
    assert res.status_code == 200
    assert res.json()["status"] == "analyzed"
    assert res.json()["locked_at"] is not None

    # 5. Subsequent submission is rejected with 409 Conflict (T-04, SEC-05)
    res = client.post(f"/api/sessions/{session_id}/interpretations", headers=owner_headers, json={
        "perspective": "Owner",
        "expected_behavior": "Late submission after lock",
        "delivery_hours": 24,
    })
    assert res.status_code == 409

    # 6. Post-lock: all interpretations are visible to members
    res = client.get(f"/api/sessions/{session_id}/interpretations", headers=dev_headers)
    assert res.status_code == 200
    assert len(res.json()) == 2

    # 7. Check Divergence Report (T-05)
    res = client.get(f"/api/sessions/{session_id}/divergences", headers=dev_headers)
    assert res.status_code == 200
    divergences = res.json()
    assert len(divergences) >= 1

    # Find delivery_hours divergence
    timeline_div = next((d for d in divergences if d["field_name"] == "delivery_hours"), None)
    assert timeline_div is not None
    assert timeline_div["kind"] == "structured_mismatch"
    assert timeline_div["review_status"] == "open"

    # Verify evidence details
    evidence = timeline_div["evidence_json"]
    discrepancies = evidence["discrepancies"]
    values = [d["value"] for d in discrepancies]
    assert 24 in values
    assert 48 in values
    assert "24h" in evidence["summary"] or "24" in evidence["summary"]

    # 8. Idempotency test (T-10): Re-fetching or re-locking yields stable findings, zero duplicates
    res2 = client.get(f"/api/sessions/{session_id}/divergences", headers=dev_headers)
    assert len(res2.json()) == len(divergences)

def test_divergence_detection_agreement(client, seeded_users):
    """T-06: Compare 24h and 24h -> No delivery timeline mismatch."""
    owner_headers = seeded_users["owner"]["headers"]
    dev_headers = seeded_users["dev"]["headers"]
    test_headers = seeded_users["test"]["headers"]

    # Setup project and session
    res = client.post("/api/projects", headers=owner_headers, json={"title": "Agreement App"})
    proj_id = res.json()["id"]
    client.post(f"/api/projects/{proj_id}/members", headers=owner_headers, json={"email": "dev@example.com", "role": "developer"})
    client.post(f"/api/projects/{proj_id}/members", headers=owner_headers, json={"email": "test@example.com", "role": "tester"})

    res = client.post(f"/api/projects/{proj_id}/requirements", headers=owner_headers, json={
        "req_code": "REQ-002",
        "title": "Consistent Requirement",
        "description": "Standard fast delivery expectation.",
    })
    req_id = res.json()["id"]

    res = client.post(f"/api/requirements/{req_id}/sessions", headers=owner_headers, json={"mode": "standard"})
    session_id = res.json()["id"]

    # Both Developer and Tester agree on 24 hours
    client.post(f"/api/sessions/{session_id}/interpretations", headers=dev_headers, json={
        "perspective": "Developer",
        "expected_behavior": "Complete within 24 hours.",
        "delivery_hours": 24,
    })
    client.post(f"/api/sessions/{session_id}/interpretations", headers=test_headers, json={
        "perspective": "Tester",
        "expected_behavior": "Complete within 24 hours.",
        "delivery_hours": 24,
    })

    # Owner locks session
    client.post(f"/api/sessions/{session_id}/lock", headers=owner_headers)

    # Check divergences -> delivery_hours must NOT be flagged!
    res = client.get(f"/api/sessions/{session_id}/divergences", headers=owner_headers)
    assert res.status_code == 200
    timeline_div = next((d for d in res.json() if d["field_name"] == "delivery_hours"), None)
    assert timeline_div is None
