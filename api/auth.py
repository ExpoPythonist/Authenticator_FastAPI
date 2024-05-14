from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Annotated
from fastapi import Depends
from starlette import status
from config.database import SessionLocal
from models import User
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordRequestForm

from fastapi import APIRouter, HTTPException
from datetime import timedelta
from config.utils import authenticate_user, create_access_token, get_current_user

auth_router = APIRouter(
    prefix='/auth',
    tags=['auth']

)

bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')


class CreateUserRequest(BaseModel):
    username: str
    password: str
    email: str


class Token(BaseModel):
    access_token: str
    token_type: str


class UserResponse(BaseModel):
    username: str
    email: str


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]


@auth_router.post('/user/create', response_model=UserResponse)
async def create_user(db: db_dependency, create_user_request: CreateUserRequest):
    try:
        create_user_model = User(
            username=create_user_request.username,
            hashed_password=bcrypt_context.hash(create_user_request.password),
            email=create_user_request.email
        )
        db.add(create_user_model)
        db.commit()

        return UserResponse(username=create_user_model.username, email=create_user_model.email)

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Username: {create_user_request.username} Already exist")


@auth_router.post('/token', response_model=Token)
async def login_for_access_token(
        from_data: Annotated[OAuth2PasswordRequestForm, Depends()],
        db: db_dependency):
    user = authenticate_user(from_data.username, from_data.password, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Could not validate user')

    token = create_access_token(user.username, user.id, timedelta(minutes=60))
    return {"access_token": token, "token_type": "bearer"}


@auth_router.get('/user/get', status_code=status.HTTP_200_OK)
async def user(user: user_dependency):
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Could not validate user')
    return {"user": user}
