def test_create_and_list_projects(client, seeded_users):
    owner_headers = seeded_users["owner"]["headers"]
    stranger_headers = seeded_users["stranger"]["headers"]

    # Owner creates project
    res = client.post("/api/projects", headers=owner_headers, json={
        "title": "Online Shopping System",
        "description": "E-commerce platform with fast shipping expectations",
    })
    assert res.status_code == 201
    proj_id = res.json()["id"]

    # Owner lists projects -> should see it
    res = client.get("/api/projects", headers=owner_headers)
    assert res.status_code == 200
    ids = [p["id"] for p in res.json()]
    assert proj_id in ids

    # Stranger lists projects -> should NOT see it
    res = client.get("/api/projects", headers=stranger_headers)
    assert res.status_code == 200
    ids = [p["id"] for p in res.json()]
    assert proj_id not in ids

    # Stranger direct access to project -> 403 Forbidden (SEC-02, T-08)
    res = client.get(f"/api/projects/{proj_id}", headers=stranger_headers)
    assert res.status_code == 403

def test_member_management(client, seeded_users):
    owner_headers = seeded_users["owner"]["headers"]
    dev_headers = seeded_users["dev"]["headers"]
    stranger_headers = seeded_users["stranger"]["headers"]

    # Create project
    res = client.post("/api/projects", headers=owner_headers, json={
        "title": "Membership Test Project",
    })
    proj_id = res.json()["id"]

    # Add Developer as member
    res = client.post(f"/api/projects/{proj_id}/members", headers=owner_headers, json={
        "email": "dev@example.com",
        "role": "developer",
    })
    assert res.status_code == 201
    assert res.json()["role"] == "developer"

    # Developer can now access project detail
    res = client.get(f"/api/projects/{proj_id}", headers=dev_headers)
    assert res.status_code == 200

    # Developer cannot add members (Owner-only operation, SEC-06)
    res = client.post(f"/api/projects/{proj_id}/members", headers=dev_headers, json={
        "email": "stranger@example.com",
        "role": "observer",
    })
    assert res.status_code == 403

def test_requirement_creation(client, seeded_users):
    owner_headers = seeded_users["owner"]["headers"]
    dev_headers = seeded_users["dev"]["headers"]

    # Create project
    res = client.post("/api/projects", headers=owner_headers, json={"title": "Req Test Project"})
    proj_id = res.json()["id"]

    # Owner creates requirement REQ-001 (T-01)
    res = client.post(f"/api/projects/{proj_id}/requirements", headers=owner_headers, json={
        "req_code": "REQ-001",
        "title": "Fast Delivery Support",
        "description": "The system must support fast delivery for qualifying customer orders.",
        "acceptance_notes": "Delivery within 24h or 48h SLA to be determined.",
    })
    assert res.status_code == 201
    req_data = res.json()
    assert req_data["req_code"] == "REQ-001"
    assert req_data["version"] == 1
    assert req_data["current_version_id"] is not None

    # Duplicate req_code in same project rejected
    res = client.post(f"/api/projects/{proj_id}/requirements", headers=owner_headers, json={
        "req_code": "REQ-001",
        "title": "Duplicate",
        "description": "Should fail",
    })
    assert res.status_code == 400
