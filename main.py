from fastapi import FastAPI, Request, status, Depends
from sqlalchemy.orm import Session
from models import Base
from database import engine
from routers import auth, todos, admin, users
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

Base.metadata.create_all(bind=engine)

@app.get("/healthy")
def healthy():
    return {"status": "healthy"}

app.include_router(auth.router)
app.include_router(todos.router)
app.include_router(admin.router)
app.include_router(users.router)

@app.get("/", include_in_schema=False)
def home(request: Request, db: Session = Depends(auth.get_db)):
    if auth.get_user_from_cookie(request, db):
        return RedirectResponse(url="/todos/todo-page", status_code=status.HTTP_302_FOUND)
    return RedirectResponse(url="/auth/login-page", status_code=status.HTTP_302_FOUND)