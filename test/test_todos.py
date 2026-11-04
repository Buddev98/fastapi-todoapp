from fastapi import status
from models import Todos
from main import app
from routers.auth import get_current_user
from routers.todos import get_db
from test.utils import override_get_db, override_get_user, client, TestingSessionLocal, test_todo, clean_db  # noqa: F401

app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_user] = override_get_user


def test_read_todos(test_todo):
    response = client.get("/todos/")
    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.json(), list)
    assert response.json() == [{"title": test_todo.title, "description": test_todo.description, "completed": test_todo.completed, "owner_id": test_todo.owner_id, "id": test_todo.id, "priority": test_todo.priority}]

def test_read_todo_by_id(test_todo):
    response = client.get(f"/todos/{test_todo.id}")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"title": test_todo.title, "description": test_todo.description, "completed": test_todo.completed, "owner_id": test_todo.owner_id, "id": test_todo.id, "priority": test_todo.priority}

def test_read_todo_not_found():
    response = client.get("/todos/999")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": {"error": "Todo not found"}}

def test_create_todo():
    response = client.post("/todos/", json={"title": "New Todo", "description": "New Description", "completed": False, "owner_id": 1, "priority": 1})
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["title"] == "New Todo"
    assert response.json()["description"] == "New Description"
    assert response.json()["completed"] is False
    assert response.json()["owner_id"] == 1
    assert response.json()["priority"] == 1

    db = TestingSessionLocal()
    model = db.query(Todos).filter(Todos.title == "New Todo").first()
    assert model is not None
    assert model.description == "New Description"
    assert model.completed is False
    assert model.owner_id == 1
    assert model.priority == 1
    db.close()


def test_update_todo(test_todo):
    response = client.put(f"/todos/{test_todo.id}", json={"title": "Updated Todo", "description": "Updated Description", "completed": True, "owner_id": 1, "priority": 2})
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["title"] == "Updated Todo"
    assert response.json()["description"] == "Updated Description"
    assert response.json()["completed"] is True
    assert response.json()["owner_id"] == 1
    assert response.json()["priority"] == 2

    db = TestingSessionLocal()
    model = db.query(Todos).filter(Todos.id == test_todo.id).first()
    assert model is not None
    assert model.title == "Updated Todo"
    assert model.description == "Updated Description"
    assert model.completed is True
    assert model.owner_id == 1
    assert model.priority == 2
    db.close()

def test_update_todo_not_found():
    response = client.put("/todos/999", json={"title": "Updated Todo", "description": "Updated Description", "completed": True, "owner_id": 1, "priority": 2})
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": {"error": "Todo not found"}}

def test_delete_todo(test_todo):
    response = client.delete(f"/todos/{test_todo.id}")
    assert response.status_code == status.HTTP_204_NO_CONTENT

    db = TestingSessionLocal()
    model = db.query(Todos).filter(Todos.id == test_todo.id).first()
    assert model is None
    db.close()

def test_delete_todo_not_found():
    response = client.delete("/todos/999")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": {"error": "Todo not found"}}