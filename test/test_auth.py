import pytest
from fastapi import status
from jose import jwt
from models import Users
from main import app
from routers import auth
from routers.auth import SECRET_KEY, ALGORITHM, bcrypt_context
from test.utils import client, override_get_db, TestingSessionLocal, engine, clean_db  # noqa: F401

app.dependency_overrides[auth.get_db] = override_get_db

NEW_USER = {
    "username": "newuser", "email": "newuser@example.com", "first_name": "New",
    "last_name": "User", "password": "password123", "role": "user", "phone_number": "1234567890",
}


@pytest.fixture(autouse=True)
def clean_users():
    with engine.begin() as connection:
        connection.execute(Users.__table__.delete())
    yield
    with engine.begin() as connection:
        connection.execute(Users.__table__.delete())


@pytest.fixture
def test_user():
    db = TestingSessionLocal()
    user = Users(
        username="testuser", email="testuser@example.com", first_name="Test", last_name="User",
        hashed_password=bcrypt_context.hash("testpassword"), role="admin", phone_number="0987654321",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    db.close()
    return user


def test_create_user():
    response = client.post("/auth/user", json=NEW_USER)
    assert response.status_code == status.HTTP_201_CREATED
    body = response.json()
    assert body["message"] == "User created successfully"
    assert body["user"]["username"] == "newuser"

    db = TestingSessionLocal()
    model = db.query(Users).filter(Users.username == "newuser").first()
    assert model is not None
    assert model.hashed_password != "password123"
    assert bcrypt_context.verify("password123", model.hashed_password)
    assert model.phone_number == "1234567890"
    db.close()


def test_create_user_missing_field():
    payload = {k: v for k, v in NEW_USER.items() if k != "password"}
    response = client.post("/auth/user", json=payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_get_users(test_user):
    response = client.get("/auth/user")
    assert response.status_code == status.HTTP_200_OK
    users = response.json()["users"]
    assert len(users) == 1
    assert users[0]["username"] == "testuser"
    assert "hashed_password" not in users[0]


def test_get_user(test_user):
    response = client.get(f"/auth/user/{test_user.id}")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["user"]["email"] == "testuser@example.com"


def test_get_user_not_found():
    response = client.get("/auth/user/999")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "User not found"}


def test_delete_user(test_user):
    response = client.delete(f"/auth/user/{test_user.id}")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"message": "User deleted successfully"}

    db = TestingSessionLocal()
    assert db.query(Users).filter(Users.id == test_user.id).first() is None
    db.close()


def test_delete_user_not_found():
    response = client.delete("/auth/user/999")
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_generate_token(test_user):
    response = client.post("/auth/token", data={"username": "testuser", "password": "testpassword"})
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["token_type"] == "bearer"
    payload = jwt.decode(body["access_token"], SECRET_KEY, algorithms=[ALGORITHM])
    assert payload["sub"] == "testuser"
    assert payload["user_id"] == test_user.id
    assert payload["role"] == "admin"


def test_generate_token_wrong_password(test_user):
    response = client.post("/auth/token", data={"username": "testuser", "password": "wrong"})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {"detail": "Invalid credentials"}


def test_generate_token_unknown_user():
    response = client.post("/auth/token", data={"username": "nobody", "password": "x"})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

def test_generate_token_missing_field():
    response = client.post("/auth/token", data={"username": "testuser"})
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

def test_generate_token_missing_all_fields():
    response = client.post("/auth/token", data={})
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    errors = response.json()["detail"]
    assert [(e["loc"], e["type"]) for e in errors] == [
        (["body", "username"], "missing"),
        (["body", "password"], "missing"),
    ]


def test_generate_token_extra_field(test_user):
    response = client.post("/auth/token", data={"username": "testuser", "password": "testpassword", "extra": "field"})
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["token_type"] == "bearer"
    payload = jwt.decode(body["access_token"], SECRET_KEY, algorithms=[ALGORITHM])
    assert payload["sub"] == "testuser"
    assert payload["user_id"] == test_user.id
    assert payload["role"] == "admin"

def test_generate_token_numeric_username(test_user):
    # form data is always text, so 123 is just the string "123" and matches no user
    response = client.post("/auth/token", data={"username": 123, "password": "testpassword"})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

def test_generate_token_numeric_password(test_user):
    response = client.post("/auth/token", data={"username": "testuser", "password": 123})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_generate_token_empty_username(test_user):
    response = client.post("/auth/token", data={"username": "", "password": "testpassword"})
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    errors = response.json()["detail"]
    assert [(e["loc"], e["type"]) for e in errors] == [(["body", "username"], "missing")]
