import pytest
from passlib.context import CryptContext
from fastapi import status
from models import Users
from main import app
from routers.auth import get_current_user
from routers.users import get_db
from test.utils import override_get_db, override_get_user, client, TestingSessionLocal, engine, clean_db  # noqa: F401

app.dependency_overrides[get_current_user] = override_get_user
app.dependency_overrides[get_db] = override_get_db

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


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
        id=1, username="testuser", email="testuser@example.com", first_name="Test",
        last_name="User", hashed_password=pwd_context.hash("oldpassword"), role="admin",
    )
    db.add(user)
    db.commit()
    db.close()
    return user


def test_get_current_user():
    response = client.get("/users/me")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"id": 1, "username": "testuser", "email": "testuser@example.com", "role": "admin"}


def test_update_password(test_user):
    response = client.put("/users/update-password", json={"password": "oldpassword", "new_password": "newpassword1"})
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"message": "Password updated successfully"}

    db = TestingSessionLocal()
    model = db.query(Users).filter(Users.id == 1).first()
    assert pwd_context.verify("newpassword1", model.hashed_password)
    db.close()


def test_update_password_incorrect_current(test_user):
    response = client.put("/users/update-password", json={"password": "wrongpassword", "new_password": "newpassword1"})
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"detail": {"error": "Incorrect password"}}


def test_update_password_too_short(test_user):
    response = client.put("/users/update-password", json={"password": "oldpassword", "new_password": "short"})
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_update_password_user_not_found():
    response = client.put("/users/update-password", json={"password": "oldpassword", "new_password": "newpassword1"})
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": {"error": "User not found"}}


def test_update_phone_number(test_user):
    response = client.put("/users/update-phone-number", params={"phone_number": "1234567890"})
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"message": "Phone number updated successfully"}

    db = TestingSessionLocal()
    model = db.query(Users).filter(Users.id == 1).first()
    assert model.phone_number == "1234567890"
    db.close()


def test_update_phone_number_too_short(test_user):
    response = client.put("/users/update-phone-number", params={"phone_number": "123"})
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
