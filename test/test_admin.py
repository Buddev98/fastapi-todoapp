from test.utils import override_get_db, override_get_user, client, TestingSessionLocal, test_todo, clean_db  # noqa: F401
from models import Users
from types import SimpleNamespace
from fastapi import status
from routers.auth import get_current_user
from routers.admin import get_db
from main import app

app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_user] = override_get_user

def test_admin_access(test_todo):
    response = client.get("/admin/todos")
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()["todos"]) == 1

def test_admin_access_denied():
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id=2, username="testuser2", email="testuser2@example.com", role="user")
    try:
        response = client.get("/admin/todos")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    finally:
        app.dependency_overrides[get_current_user] = override_get_user

def test_admin_delete_todo(test_todo):
    response = client.delete(f"/admin/todo/{test_todo.id}")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"message": "Todo deleted successfully"}

def test_admin_delete_todo_not_found():
    response = client.delete("/admin/todo/999")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": {"error": "Todo not found"}}

def test_admin_delete_todo_access_denied():
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id=2, username="testuser2", email="testuser2@example.com", role="user")
    try:
        response = client.delete("/admin/todo/1")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    finally:
        app.dependency_overrides[get_current_user] = override_get_user

def test_admin_delete_user():
    db = TestingSessionLocal()
    user = Users(username="victim", email="victim@example.com", first_name="V", last_name="U", hashed_password="x", role="user")
    db.add(user)
    db.commit()
    user_id = user.id
    db.close()

    response = client.delete(f"/admin/user/{user_id}")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"message": "User deleted successfully"}

    db = TestingSessionLocal()
    assert db.query(Users).filter(Users.id == user_id).first() is None
    db.close()

def test_admin_delete_user_not_found():
    response = client.delete("/admin/user/999")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": {"error": "User not found"}}

def test_admin_delete_user_access_denied():
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id=2, username="testuser2", email="testuser2@example.com", role="user")
    try:
        response = client.delete("/admin/user/1")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    finally:
        app.dependency_overrides[get_current_user] = override_get_user

