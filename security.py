from datetime import datetime, timedelta
import bcrypt as _bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from database import get_db
import models

# 🔴 SECURITY NOTE: In a real production app, move SECRET_KEY into the .env file!
SECRET_KEY = "SAKINAH_SUPER_SECRET_KEY_FOR_JWT_TOKENS"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 43200  # 30 days

# Using bcrypt directly (bypasses passlib Python 3.14 incompatibility)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return _bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))

def get_password_hash(password: str) -> str:
    salt = _bcrypt.gensalt()
    return _bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials - token invalid or expired",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Decode the token to get the user ID
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
        
    # Fetch the user from the database to ensure they still exist and aren't banned
    user = db.query(models.User).filter(models.User.id == int(user_id)).first()
    if user is None or user.is_banned:
        raise credentials_exception
    return user
