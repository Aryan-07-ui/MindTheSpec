def test_sec_01_anonymous_access_denied(client):
    res = client.get("/api/projects")
    assert res.status_code == 401

def test_sec_02_non_member_idor_denied(client, seeded_users):
    owner_headers = seeded_users["owner"]["headers"]
    stranger_headers = seeded_users["stranger"]["headers"]

    # Owner creates project
    res = client.post("/api/projects", headers=owner_headers, json={"title": "Private Project"})
    proj_id = res.json()["id"]

    # Stranger accesses project -> 403
    res = client.get(f"/api/projects/{proj_id}", headers=stranger_headers)
    assert res.status_code == 403

def test_sec_07_invalid_session_token_rejected(client):
    res = client.get("/api/projects", headers={"Authorization": "Bearer invalid.fake.token"})
    assert res.status_code == 401

def test_sec_08_sql_injection_safety(client, seeded_users):
    owner_headers = seeded_users["owner"]["headers"]
    sql_payload = "Project'; DROP TABLE users; --"

    # Should be safely parameterized and stored as literal string
    res = client.post("/api/projects", headers=owner_headers, json={"title": sql_payload})
    assert res.status_code == 201
    assert res.json()["title"] == sql_payload

    # Users table still exists and functions normally
    res = client.get("/api/auth/me", headers=owner_headers)
    assert res.status_code == 200

def test_sec_09_xss_safety_in_template_rendering(client, seeded_users):
    owner_headers = seeded_users["owner"]["headers"]
    xss_payload = "<script>alert('XSS')</script>"

    # Create project with script tags
    res = client.post("/api/projects", headers=owner_headers, json={"title": xss_payload})
    proj_id = res.json()["id"]

    # Request HTML view with session cookie
    client.cookies.set("mindthespec_session", seeded_users["owner"]["token"])
    res = client.get(f"/app/projects/{proj_id}")
    assert res.status_code == 200
    # Must be escaped in HTML output
    assert "<script>alert('XSS')</script>" not in res.text or "&lt;script&gt;" in res.text

def test_sec_13_security_headers_and_clean_health(client):
    # Check security headers
    res = client.get("/health")
    assert res.status_code == 200
    assert res.headers["x-content-type-options"] == "nosniff"
    assert res.headers["x-frame-options"] == "DENY"
    assert res.headers["x-xss-protection"] == "1; mode=block"

    # Verify no database host, password, or trace in health output
    health_data = res.json()
    assert "password" not in health_data
    assert "host" not in health_data
    assert "user" not in health_data
    assert health_data["status"] == "healthy"
