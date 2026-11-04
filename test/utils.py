from types import SimpleNamespace
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from models import Base, Todos
from main import app
from fastapi.testclient import TestClient
import pytest

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

def override_get_user():
    return SimpleNamespace(id=1, username="testuser", email="testuser@example.com", role="admin")


client = TestClient(app)

def clear_todos():
    with engine.begin() as connection:
        connection.execute(Todos.__table__.delete())

@pytest.fixture(autouse=True)
def clean_db():
    clear_todos()
    yield
    clear_todos()

@pytest.fixture
def test_todo():
    todo = Todos(title="Test Todo", description="Test Description", completed=False, owner_id=1, priority=1)
    db = TestingSessionLocal()
    db.add(todo)
    db.commit()
    db.refresh(todo)
    db.close()
    return todo
