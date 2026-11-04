from fastapi import APIRouter, Depends, Path, HTTPException, status
from sqlalchemy.orm import Session
from typing import Annotated
from database import engine, SessionLocal
from pydantic import BaseModel, Field
from .auth import get_current_user
from models import Base, Users, Todos

router = APIRouter(
    prefix="/admin",
    tags=["admin"]
)

Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[Users, Depends(get_current_user)]


@router.get("/todos", status_code=status.HTTP_200_OK)
async def get_all_todos(db: db_dependency, user: user_dependency):
    if not user or user.role != "admin":
        raise HTTPException(status_code=401, detail={"error": "Unauthorized"})
    todos = db.query(Todos).all()
    todos_response = [{"id": todo.id, "title": todo.title, "description": todo.description, "owner_id": todo.owner_id} for todo in todos]
    return {"todos": todos_response}

@router.get("/users", status_code=status.HTTP_200_OK)
async def get_all_users(db: db_dependency, user: user_dependency):
    if not user or user.role != "admin":
        raise HTTPException(status_code=401, detail={"error": "Unauthorized"})
    users = db.query(Users).all()
    users_response = [{"id": u.id, "username": u.username, "email": u.email, "role": u.role} for u in users]
    return {"users": users_response}

@router.delete("/user/{user_id}", status_code=status.HTTP_200_OK)
async def delete_user(user_id: int, db: db_dependency, user: user_dependency):
    if not user or user.role != "admin":
        raise HTTPException(status_code=401, detail={"error": "Unauthorized"})
    user_to_delete = db.query(Users).filter(Users.id == user_id).first()
    if not user_to_delete:
        raise HTTPException(status_code=404, detail={"error": "User not found"})
    db.delete(user_to_delete)
    db.commit()
    return {"message": "User deleted successfully"}

@router.delete("/todo/{todo_id}", status_code=status.HTTP_200_OK)
async def delete_todo(todo_id: int, db: db_dependency, user: user_dependency):
    if not user or user.role != "admin":
        raise HTTPException(status_code=401, detail={"error": "Unauthorized"})
    todo_to_delete = db.query(Todos).filter(Todos.id == todo_id).first()
    if not todo_to_delete:
        raise HTTPException(status_code=404, detail={"error": "Todo not found"})
    db.delete(todo_to_delete)
    db.commit()
    return {"message": "Todo deleted successfully"}