from fastapi import FastAPI, Request
from models import Base
from database import engine
from routers import auth, todos, admin, users
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

Base.metadata.create_all(bind=engine)

@app.get("/healthy")
def healthy():
    return {"status": "healthy"}

app.include_router(auth.router)
app.include_router(todos.router)
app.include_router(admin.router)
app.include_router(users.router)

@app.get("/")
def home(request: Request):
    return templates.TemplateResponse(request, "home.html")

@app.get("/auth/login-page")
def login(request: Request):
    return templates.TemplateResponse(request, "login.html")

@app.get("/auth/register")
def register(request: Request):
    return templates.TemplateResponse(request, "register.html")