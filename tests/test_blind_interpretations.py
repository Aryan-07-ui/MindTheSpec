import pytest

def test_blind_interpretation_mutual_secrecy(client, seeded_users):
    owner_headers = seeded_users["owner"]["headers"]
    dev_headers = seeded_users["dev"]["headers"]
    test_headers = seeded_users["test"]["headers"]
    stranger_headers = seeded_users["stranger"]["headers"]

    # 1. Owner creates project
    res = client.post("/api/projects", headers=owner_headers, json={"title": "E-Commerce App"})
    proj_id = res.json()["id"]

    # Add Developer and Tester
    client.post(f"/api/projects/{proj_id}/members", headers=owner_headers, json={"email": "dev@example.com", "role": "developer"})
    client.post(f"/api/projects/{proj_id}/members", headers=owner_headers, json={"email": "test@example.com", "role": "tester"})

    # 2. Owner creates requirement REQ-001
    res = client.post(f"/api/projects/{proj_id}/requirements", headers=owner_headers, json={
        "req_code": "REQ-001",
        "title": "Fast Delivery Support",
        "description": "The system must support fast delivery.",
    })
    req_id = res.json()["id"]

    # 3. Owner starts blind session
    res = client.post(f"/api/requirements/{req_id}/sessions", headers=owner_headers, json={"mode": "standard"})
    assert res.status_code == 201
    session_id = res.json()["id"]

    # 4. Developer submits: delivery_hours = 24 (T-02)
    dev_res = client.post(f"/api/sessions/{session_id}/interpretations", headers=dev_headers, json={
        "perspective": "Developer",
        "actor": "Order Processing Service",
        "expected_behavior": "Order is packaged and dispatched within 24 hours.",
        "delivery_hours": 24,
        "acceptance_criteria": "Delivery within one day (24h).",
    })
    assert dev_res.status_code == 201
    dev_interp_id = dev_res.json()["id"]

    # 5. Tester submits: delivery_hours = 48
    test_res = client.post(f"/api/sessions/{session_id}/interpretations", headers=test_headers, json={
        "perspective": "Tester",
        "actor": "Fulfillment Carrier",
        "expected_behavior": "Customer receives package within 48 hours.",
        "delivery_hours": 48,
        "acceptance_criteria": "Delivery within two days (48h).",
    })
    assert test_res.status_code == 201
    test_interp_id = test_res.json()["id"]

    # 6. MUTUAL BLINDNESS VERIFICATION (T-02, T-03, SEC-03)
    # Developer queries session interpretations -> MUST ONLY SEE THEIR OWN!
    res = client.get(f"/api/sessions/{session_id}/interpretations", headers=dev_headers)
    assert res.status_code == 200
    interps = res.json()
    assert len(interps) == 1
    assert interps[0]["id"] == dev_interp_id
    assert interps[0]["delivery_hours"] == 24

    # Tester queries session interpretations -> MUST ONLY SEE THEIR OWN!
    res = client.get(f"/api/sessions/{session_id}/interpretations", headers=test_headers)
    assert res.status_code == 200
    interps = res.json()
    assert len(interps) == 1
    assert interps[0]["id"] == test_interp_id
    assert interps[0]["delivery_hours"] == 48

    # Owner queries session interpretations -> Owner has NOT submitted, so returns 0 items!
    # Server-side blind protection guarantees owner cannot read submissions before lock!
    res = client.get(f"/api/sessions/{session_id}/interpretations", headers=owner_headers)
    assert res.status_code == 200
    assert len(res.json()) == 0

    # 7. DIRECT ID LOOKUP PROTECTION (IDOR / SEC-04)
    # Tester attempts to fetch Developer's answer by direct ID -> MUST BE FORBIDDEN (403)!
    res = client.get(f"/api/interpretations/{dev_interp_id}", headers=test_headers)
    assert res.status_code == 403
    assert "confidential until session lock" in res.json()["detail"].lower()

    # Developer attempts to fetch Tester's answer by direct ID -> MUST BE FORBIDDEN (403)!
    res = client.get(f"/api/interpretations/{test_interp_id}", headers=dev_headers)
    assert res.status_code == 403

    # Stranger attempts to fetch either -> 403/404
    res = client.get(f"/api/interpretations/{dev_interp_id}", headers=stranger_headers)
    assert res.status_code == 403

    # 8. Duplicate submission in standard mode is rejected with 409 Conflict
    res = client.post(f"/api/sessions/{session_id}/interpretations", headers=dev_headers, json={
        "perspective": "Developer",
        "expected_behavior": "Attempting second submission",
        "delivery_hours": 36,
    })
    assert res.status_code == 409
