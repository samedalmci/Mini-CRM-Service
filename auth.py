from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session, select
from typing import Optional
from db import get_session
from models import User


SECRET_KEY = "a3f1c5b7e9d4f6a2c9b1d8e7f0a3c5b7e9d4f6a2c9b1d8e7f0a3c5b7e9d4f6a2"
ALGORITHM = "HS256"



pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth_2_scheme = OAuth2PasswordBearer(tokenUrl="token")



def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)

    
def get_user(session: Session, username: str):
    statement = select(User).where(User.username == username)
    user = session.exec(statement).first()
    return user    
    

def authenticate_user(session: Session, username: str, password: str):
    user = get_user(session, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
      
    return user



#"Fonksiyon önce data bilgisini alıp kopyalar. Eğer expires_delta verilmişse bu süreyi, verilmemişse varsayılan olarak 15 dakikayı ekleyerek token’in bitiş zamanını hesaplar. Bu süre exp alanı olarak data içine eklenir ve sonrasında jwt.encode ile şifrelenerek access token üretilir."
def create_access_token(data: dict, expires_delta: Optional[timedelta]= None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=10)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt



#Fonksiyon önce request’ten gelen token’ı alır. Token’ı çözümleyip içinden "sub" alanından kullanıcı adını alır. Eğer kullanıcı adı yoksa veya token geçersizse 401 Unauthorized hatası verir. Kullanıcı adı varsa db içinde arama yapar; kullanıcı bulunmazsa yine hata döner. Eğer kullanıcı bulunursa, bu kullanıcı nesnesini geri döndürür.
async def get_current_user(token: str = Depends(oauth_2_scheme), session: Session = Depends(get_session)):
    credential_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,      detail="Could not validate credentials", headers={"WWW-Authenticate": "Bearer"})

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credential_exception        
        # token_data = TokenData(username =  username)
    except JWTError:
        print("Token iS done")
        raise credential_exception
    
    user = get_user(session, username)  
    if user is None:
        raise credential_exception
    return user    

#Fonksiyon, get_current_user’dan dönen kullanıcı nesnesini alır. Eğer kullanıcı disabled=True ise, yani hesabı pasifse, 400 Bad Request hatası döner. Eğer kullanıcı aktifse, kullanıcı nesnesini olduğu gibi geri döndürür.
async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    return current_user
