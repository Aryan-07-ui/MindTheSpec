def test_record_resolution_and_traceability(client, seeded_users):
    owner_headers = seeded_users["owner"]["headers"]
    dev_headers = seeded_users["dev"]["headers"]
    test_headers = seeded_users["test"]["headers"]

    # 1. Setup session with 24h vs 48h discrepancy
    res = client.post("/api/projects", headers=owner_headers, json={"title": "Resolution Test App"})
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

    client.post(f"/api/sessions/{session_id}/interpretations", headers=dev_headers, json={
        "perspective": "Developer",
        "expected_behavior": "Deliver in 24 hours.",
        "delivery_hours": 24,
    })
    client.post(f"/api/sessions/{session_id}/interpretations", headers=test_headers, json={
        "perspective": "Tester",
        "expected_behavior": "Deliver in 48 hours.",
        "delivery_hours": 48,
    })

    # Cannot resolve while collecting
    res = client.post(f"/api/sessions/{session_id}/resolution", headers=owner_headers, json={
        "statement": "Premature resolution",
        "rationale": "Session not locked yet",
    })
    assert res.status_code == 409

    # Owner locks session
    client.post(f"/api/sessions/{session_id}/lock", headers=owner_headers)

    # Developer attempts to record resolution -> 403 Forbidden (SEC-06)
    res = client.post(f"/api/sessions/{session_id}/resolution", headers=dev_headers, json={
        "statement": "Developer decision",
        "rationale": "I want 24 hours",
    })
    assert res.status_code == 403

    # Owner records official resolution (T-07)
    res = client.post(f"/api/sessions/{session_id}/resolution", headers=owner_headers, json={
        "statement": "Delivery within 48 hours for eligible orders.",
        "rationale": "Logistics carrier SLAs guarantee 48 hours; next-day 24h service is not universally viable.",
    })
    assert res.status_code == 201
    res_data = res.json()
    assert res_data["session_id"] == session_id
    assert res_data["statement"] == "Delivery within 48 hours for eligible orders."
    assert "48 hours" in res_data["rationale"]

    # Session status is now resolved
    sess_res = client.get(f"/api/sessions/{session_id}", headers=owner_headers)
    assert sess_res.json()["status"] == "resolved"

    # Divergences review status is now resolved
    div_res = client.get(f"/api/sessions/{session_id}/divergences", headers=dev_headers)
    for d in div_res.json():
        assert d["review_status"] == "resolved"

    # Audit trail contains resolution event
    audit_res = client.get(f"/api/projects/{proj_id}/audit", headers=dev_headers)
    actions = [a["action"] for a in audit_res.json()]
    assert "RESOLUTION_RECORDED" in actions
    assert "SESSION_LOCKED" in actions
    assert "REQUIREMENT_CREATED" in actions
    assert "PROJECT_CREATED" in actions

    # FR-15: CSV Export verification
    csv_res = client.get(f"/api/sessions/{session_id}/export/csv", headers=dev_headers)
    assert csv_res.status_code == 200
    assert "text/csv" in csv_res.headers["content-type"]
    assert "attachment;" in csv_res.headers["content-disposition"]
    csv_text = csv_res.text
    assert "Delivery Timeline Mismatch" in csv_text or "delivery_hours" in csv_text
    assert "Delivery within 48 hours for eligible orders." in csv_text
    assert "Dave Developer" in csv_text
    assert "Tina Tester" in csv_text
