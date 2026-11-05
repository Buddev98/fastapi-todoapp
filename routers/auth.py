from fastapi import APIRouter, HTTPException, status, Request
from pydantic import BaseModel
from fastapi import Depends
from models import Users
from sqlalchemy.orm import Session
from typing import Annotated
from passlib.context import CryptContext
from database import SessionLocal
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import jwt, JWTError
from datetime import timedelta, datetime, timezone
from fastapi.templating import Jinja2Templates
from starlette.responses import RedirectResponse

templates = Jinja2Templates(directory="templates")

SECRET_KEY = "shans_todo_app_with_auth"  # Replace with your actual secret key
ALGORITHM = "HS256"

router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)
bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

class UserRequest(BaseModel):
    username: str
    email: str
    first_name: str
    last_name: str
    password: str
    role: str
    is_active: bool = True
    phone_number: str | None = None

class TokenResponse(BaseModel):
    access_token: str
    token_type: str

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]


def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db: db_dependency):
    return _decode_user(token, db)


def _decode_user(token: str, db: Session):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user_id: int = payload.get("user_id")
        role: str = payload.get("role")
        if username is None or user_id is None or role is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    user = db.query(Users).filter(Users.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


def get_user_from_cookie(request: Request, db: Session):
    # Browser page loads send the JWT in a cookie, not an Authorization header
    token = request.cookies.get("access_token")
    if not token:
        return None
    try:
        return _decode_user(token, db)
    except HTTPException:
        return None


#pages for rendering templates
@router.get("/login-page", status_code=status.HTTP_200_OK)
async def login_page(request: Request, db: db_dependency):
    if get_user_from_cookie(request, db):
        return RedirectResponse(url="/todos/todo-page", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse(request, "login.html")

@router.get("/register", status_code=status.HTTP_200_OK)
async def register_page(request: Request, db: db_dependency):
    if get_user_from_cookie(request, db):
        return RedirectResponse(url="/todos/todo-page", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse(request, "register.html")



#endpoints for authentication and user management

def authenticate_user(username: str, password: str, db: db_dependency):
    user = db.query(Users).filter(Users.username == username).first()
    if not user or not bcrypt_context.verify(password, user.hashed_password):
        return False
    return user

def create_access_token(username: str, user_id: int, role: str, expires_delta: timedelta = timedelta(seconds=3600)):
    token_data = {"sub": username, "user_id": user_id, "role": role}
    if expires_delta:
        expire = timedelta(seconds=expires_delta.total_seconds())
        token_data.update({"exp": (datetime.now(timezone.utc) + expire).timestamp()})
    token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)
    return token


@router.post("/user", status_code=status.HTTP_201_CREATED)
async def create_user(user: UserRequest, db: db_dependency):
    existing = db.query(Users).filter((Users.username == user.username) | (Users.email == user.email)).first()
    if existing:
        field = "Username" if existing.username == user.username else "Email"
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"{field} already registered")
    new_user = Users(
        username=user.username,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        hashed_password=bcrypt_context.hash(user.password),
        role=user.role,
        is_active=True,
        phone_number=user.phone_number
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "User created successfully", "user": {"id": new_user.id, "username": new_user.username, "email": new_user.email, "role": new_user.role}}


@router.get("/user", status_code=status.HTTP_200_OK)
async def get_users(db: db_dependency):
    users = db.query(Users).all()
    users_response = [{"id": user.id, "username": user.username, "email": user.email, "role": user.role, "phone_number": user.phone_number} for user in users]
    return {"users": users_response}

@router.get("/user/{user_id}", status_code=status.HTTP_200_OK)
async def get_user(user_id: int, db: db_dependency):
    user = db.query(Users).filter(Users.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return {"user": {"id": user.id, "username": user.username, "email": user.email, "role": user.role, "phone_number": user.phone_number}}


@router.delete("/user/{user_id}", status_code=status.HTTP_200_OK)
async def delete_user(user_id: int, db: db_dependency):
    user = db.query(Users).filter(Users.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    db.delete(user)
    db.commit()
    return {"message": "User deleted successfully"}

@router.post("/token", status_code=status.HTTP_200_OK, response_model=TokenResponse)
async def generate_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: db_dependency):
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_access_token(username=user.username, user_id=user.id, role=user.role)
    return TokenResponse(access_token=token, token_type="bearer")