from app.models.user import User

def test_register_success(client, db):
    payload = {
        "email": "newuser@example.com",
        "name": "New User",
        "password": "Password123!",
    }
    res = client.post("/api/auth/register", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["email"] == "newuser@example.com"
    assert data["name"] == "New User"

    # Verify password is never returned and is hashed in DB
    assert "password" not in data
    assert "password_hash" not in data
    user = db.query(User).filter(User.email == "newuser@example.com").first()
    assert user is not None
    assert user.password_hash != "Password123!"
    assert user.password_hash.startswith("$2b$")

def test_register_duplicate_email(client):
    payload = {
        "email": "duplicate@example.com",
        "name": "User One",
        "password": "Password123!",
    }
    res1 = client.post("/api/auth/register", json=payload)
    assert res1.status_code == 201

    res2 = client.post("/api/auth/register", json=payload)
    assert res2.status_code == 400
    assert "already exists" in res2.json()["detail"]

def test_login_success(client):
    # Register first
    client.post("/api/auth/register", json={
        "email": "loginuser@example.com",
        "name": "Login User",
        "password": "SecretPassword123!",
    })

    # Login
    res = client.post("/api/auth/login", json={
        "email": "loginuser@example.com",
        "password": "SecretPassword123!",
    })
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert "mindthespec_session" in res.cookies

def test_login_invalid_password(client):
    res = client.post("/api/auth/login", json={
        "email": "nobody@example.com",
        "password": "WrongPassword!",
    })
    assert res.status_code == 401

def test_get_current_user_profile(client, seeded_users):
    headers = seeded_users["owner"]["headers"]
    res = client.get("/api/auth/me", headers=headers)
    assert res.status_code == 200
    assert res.json()["email"] == "owner@example.com"

def test_unauthenticated_access_rejected(client):
    res = client.get("/api/auth/me")
    assert res.status_code == 401
