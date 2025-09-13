# routes/users.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session,select
from db import get_session
from models import User as UserModel
from auth import (
    authenticate_user, create_access_token,
    get_current_active_user, get_password_hash
)
from pydantic import BaseModel
from datetime import timedelta
from typing import Optional
from fastapi.security import OAuth2PasswordRequestForm

ACCESS_TOKEN_EXPIRE_MINUTES = 10

router = APIRouter()

class UserRegister(BaseModel):
    username: str
    email: Optional[str] = None
    password: str  # Zorunlu alan
    full_name: Optional[str] = None




@router.post("/register/")
def register(user_in: UserRegister, session: Session = Depends(get_session)):
    existing_user = session.exec(select(UserModel).where(UserModel.username == user_in.username)).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    if not user_in.password or len(user_in.password.strip()) < 1:
        raise HTTPException(status_code=400, detail="Password is required")
    

    hashed_password = get_password_hash(user_in.password)
    new_user = UserModel(
        username=user_in.username,
        full_name=user_in.full_name,
        email=user_in.email,
        hashed_password=hashed_password,
        disabled=False
    )

    session.add(new_user)
    session.commit()
    
    return {"msg": "User registered successfully", "username": user_in.username}


# @app.get("/")
# def root():
#     return {"message": "FastAPI + PostgreSQL + Docker çalışıyor!"}


#Fonksiyon login formundan (username ve password) gelen bilgileri alır. authenticate_user ile kullanıcı adı ve şifre doğrulanır. Eğer kullanıcı yoksa veya şifre yanlışsa 401 Unauthorized hatası döner. Kullanıcı doğruysa, ACCESS_TOKEN_EXPIRE_MINUTES kadar token süresi belirlenir ve create_access_token çağrılarak access token üretilir. Son olarak token ve token tipi JSON olarak kullanıcıya döner.
@router.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(),session: Session = Depends(get_session)):
    user = authenticate_user(session, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Incorrect username or password", headers={"WWW-Authenticate": "Bearer"})
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires)
    
    print(f"DEBUG - Generated token for {user.username}: {access_token}")
    return {"access_token": access_token, "token_type": "bearer"}


# #Fonksiyon request’ten gelen token ile kullanıcıyı alır (get_current_active_user üzerinden). Eğer kullanıcı aktifse, kullanıcının bilgilerini JSON formatında geri döner.

@router.get("/users/me/", response_model=UserModel)
async def read_users_me(current_user: UserModel = Depends(get_current_active_user)):
    return current_user

#Fonksiyon da aynı şekilde token ile kullanıcıyı alır. Alınan kullanıcıya ait örnek item listesini JSON olarak geri döner; burada örnek olarak sadece item_id ve sahibi gösterilir.
@router.get("/users/me/items")
async def read_own_items(current_user: UserModel  = Depends(get_current_active_user)):
    return [{"item_id": 1, "owner": {"username": current_user.username, "id": current_user.id}}]


