from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Annotated
import models
from database import engine, SessionLocal
from pydantic import BaseModel, Field
from .auth import get_current_user
from passlib.context import CryptContext

router = APIRouter(
    prefix="/users",
    tags=["users"]
)

models.Base.metadata.create_all(bind=engine)

class UpdatePasswordRequest(BaseModel):
    new_password: str = Field(min_length=8)
    password: str

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[models.Users, Depends(get_current_user)]
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@router.get("/me", status_code=status.HTTP_200_OK)
async def get_current_user_info(user: user_dependency):
    if not user:
        raise HTTPException(status_code=401, detail={"error": "Unauthorized"})
    return {"id": user.id, "username": user.username, "email": user.email, "role": user.role}

@router.put("/update-password", status_code=status.HTTP_200_OK)
async def update_password(db: db_dependency, user: user_dependency, request: UpdatePasswordRequest):
    if not user:
        raise HTTPException(status_code=401, detail={"error": "Unauthorized"})
    user_in_db = db.query(models.Users).filter(models.Users.id == user.id).first()
    if not user_in_db:
        raise HTTPException(status_code=404, detail={"error": "User not found"})
    if not pwd_context.verify(request.password, user_in_db.hashed_password):
        raise HTTPException(status_code=400, detail={"error": "Incorrect password"})
    user_in_db.hashed_password = pwd_context.hash(request.new_password)
    db.commit()
    return {"message": "Password updated successfully"}


@router.put("/update-phone-number", status_code=status.HTTP_200_OK)
async def update_phone_number(db: db_dependency, user: user_dependency, phone_number: str = Field(..., min_length=10, max_length=15)):
    if not user:
        raise HTTPException(status_code=401, detail={"error": "Unauthorized"})
    user_in_db = db.query(models.Users).filter(models.Users.id == user.id).first()
    if not user_in_db:
        raise HTTPException(status_code=404, detail={"error": "User not found"})
    user_in_db.phone_number = phone_number
    db.commit()
    return {"message": "Phone number updated successfully"}