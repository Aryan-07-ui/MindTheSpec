import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Set test environment
os.environ["TESTING"] = "1"
os.environ["DB_TYPE"] = "sqlite"
os.environ["SQLITE_PATH"] = "test_mindthespec.db"

from app.database import get_db
from app.models.base import Base
from app.main import app
from app.models.user import User
from app.services.auth_service import hash_password, create_session_token

TEST_DB_URL = "sqlite:///./test_mindthespec.db"
test_engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)
    if os.path.exists("test_mindthespec.db"):
        try:
            os.remove("test_mindthespec.db")
        except Exception:
            pass

@pytest.fixture
def db():
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture
def seeded_users(db):
    """Creates Owner, Developer, Tester, and Unrelated User."""
    users = {}
    defs = [
        ("owner@example.com", "Alex Owner", "Owner123!"),
        ("dev@example.com", "Dave Developer", "Dev123!"),
        ("test@example.com", "Tina Tester", "Test123!"),
        ("stranger@example.com", "Sam Stranger", "Stranger123!"),
    ]
    for email, name, pwd in defs:
        u = db.query(User).filter(User.email == email).first()
        if not u:
            u = User(
                email=email,
                full_name=name,
                password_hash=hash_password(pwd),
            )
            db.add(u)
            db.flush()
        users[email.split("@")[0]] = {
            "user": u,
            "id": u.user_id,
            "token": create_session_token(u.user_id),
            "headers": {"Authorization": f"Bearer {create_session_token(u.user_id)}"},
        }
    db.commit()
    return users
