from fastapi import APIRouter, Depends, Path, HTTPException, status
from sqlalchemy.orm import Session
from typing import Annotated
import models
from database import engine, SessionLocal
from pydantic import BaseModel, Field
from .auth import get_current_user

router = APIRouter(
    prefix="/todos",
    tags=["todos"]
)

models.Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[models.Users, Depends(get_current_user)]

class TodoRequest(BaseModel):
    title: str = Field(min_length=3)
    description: str = Field(min_length=3, max_length=100)
    priority: int = Field(gt=0, lt=6)
    completed: bool = False

@router.get("/", status_code=status.HTTP_200_OK)
async def read_all(db: db_dependency, user: user_dependency):
    return db.query(models.Todos).filter(models.Todos.owner_id == user.id).all()

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_todo(todo: TodoRequest, db: db_dependency, user: user_dependency):
    if not user:
        raise HTTPException(status_code=401, detail={"error": "Unauthorized"})
    todo_model = models.Todos(**todo.model_dump(), owner_id=user.id)
    db.add(todo_model)
    db.commit()
    db.refresh(todo_model)
    return todo_model

@router.get("/{todo_id}", status_code=status.HTTP_200_OK)
async def read_todo(db: db_dependency, user: user_dependency, todo_id: int = Path(gt=0)):
    if not user:
        raise HTTPException(status_code=401, detail={"error": "Unauthorized"})
    todo_model = db.query(models.Todos).filter(models.Todos.id == todo_id, models.Todos.owner_id == user.id).first()
    if todo_model is None:
        raise HTTPException(status_code=404, detail={"error": "Todo not found"})
    return todo_model


@router.put("/{todo_id}", status_code=status.HTTP_200_OK)
async def update_todo(db: db_dependency, user: user_dependency, todo: TodoRequest, todo_id: int = Path(gt=0)):
    if not user:
        raise HTTPException(status_code=401, detail={"error": "Unauthorized"})
    todo_model = db.query(models.Todos).filter(models.Todos.id == todo_id, models.Todos.owner_id == user.id).first()
    if todo_model is None:
        raise HTTPException(status_code=404, detail={"error": "Todo not found"})
    for key, value in todo.model_dump().items():
        setattr(todo_model, key, value)
    db.commit()
    db.refresh(todo_model)
    return todo_model


@router.delete("/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo(db: db_dependency, user: user_dependency, todo_id: int = Path(gt=0)):
    if not user:
        raise HTTPException(status_code=401, detail={"error": "Unauthorized"})
    todo_model = db.query(models.Todos).filter(models.Todos.id == todo_id, models.Todos.owner_id == user.id).first()
    if todo_model is None:
        raise HTTPException(status_code=404, detail={"error": "Todo not found"})
    db.delete(todo_model)
    db.commit()