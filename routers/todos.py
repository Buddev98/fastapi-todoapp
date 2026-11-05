from fastapi import APIRouter, Depends, Path, HTTPException, status
import fastapi
from sqlalchemy.orm import Session
from typing import Annotated
from models import Base, Users, Todos
from database import engine, SessionLocal
from pydantic import BaseModel, Field
from .auth import get_current_user
from starlette.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(
    prefix="/todos",
    tags=["todos"]
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

class TodoRequest(BaseModel):
    title: str = Field(min_length=3)
    description: str = Field(min_length=3, max_length=100)
    priority: int = Field(gt=0, lt=6)
    completed: bool = False

def redirect_to_login():
    response = RedirectResponse(url="/auth/login-page", status_code=status.HTTP_302_FOUND)
    response.delete_cookie("access_token")
    return response

def get_user_from_cookie(request: fastapi.Request, db: Session):
    # Browser page loads send the JWT in a cookie, not an Authorization header
    token = request.cookies.get("access_token")
    if not token:
        return None
    try:
        return get_current_user(token, db)
    except HTTPException:
        return None

# Templates
templates = Jinja2Templates(directory="templates")

@router.get("/todo-page", status_code=status.HTTP_200_OK)
async def todo_page(request: fastapi.Request, db: db_dependency):
    user = get_user_from_cookie(request, db)
    if not user:
        return redirect_to_login()

    todos = db.query(Todos).filter(Todos.owner_id == user.id).all()
    return templates.TemplateResponse(request, "todos.html", {"user": user, "todos": todos})

@router.get("/add-todo-page", status_code=status.HTTP_200_OK)
async def add_todo_page(request: fastapi.Request, db: db_dependency):
    if not get_user_from_cookie(request, db):
        return redirect_to_login()
    return templates.TemplateResponse(request, "add-todo.html")

@router.get("/edit-todo-page/{todo_id}", status_code=status.HTTP_200_OK)
async def edit_todo_page(request: fastapi.Request, db: db_dependency, todo_id: int = Path(gt=0)):
    user = get_user_from_cookie(request, db)
    if not user:
        return redirect_to_login()
    todo = db.query(Todos).filter(Todos.id == todo_id, Todos.owner_id == user.id).first()
    if todo is None:
        return RedirectResponse(url="/todos/todo-page", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse(request, "edit-todo.html", {"todo": todo})



#requests

@router.get("/", status_code=status.HTTP_200_OK)
async def read_all(db: db_dependency, user: user_dependency):
    return db.query(Todos).filter(Todos.owner_id == user.id).all()

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_todo(todo: TodoRequest, db: db_dependency, user: user_dependency):
    if not user:
        raise HTTPException(status_code=401, detail={"error": "Unauthorized"})
    todo_model = Todos(**todo.model_dump(), owner_id=user.id)
    db.add(todo_model)
    db.commit()
    db.refresh(todo_model)
    return todo_model

@router.get("/{todo_id}", status_code=status.HTTP_200_OK)
async def read_todo(db: db_dependency, user: user_dependency, todo_id: int = Path(gt=0)):
    if not user:
        raise HTTPException(status_code=401, detail={"error": "Unauthorized"})
    todo_model = db.query(Todos).filter(Todos.id == todo_id, Todos.owner_id == user.id).first()
    if todo_model is None:
        raise HTTPException(status_code=404, detail={"error": "Todo not found"})
    return todo_model


@router.put("/{todo_id}", status_code=status.HTTP_200_OK)
async def update_todo(db: db_dependency, user: user_dependency, todo: TodoRequest, todo_id: int = Path(gt=0)):
    if not user:
        raise HTTPException(status_code=401, detail={"error": "Unauthorized"})
    todo_model = db.query(Todos).filter(Todos.id == todo_id, Todos.owner_id == user.id).first()
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
    todo_model = db.query(Todos).filter(Todos.id == todo_id, Todos.owner_id == user.id).first()
    if todo_model is None:
        raise HTTPException(status_code=404, detail={"error": "Todo not found"})
    db.delete(todo_model)
    db.commit()
    return {"message": "Todo deleted successfully"}