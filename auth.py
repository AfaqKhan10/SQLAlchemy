# auth.py
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from models import User
from database import get_db
from exceptions import AuthException

# ────────────────────── SETTINGS ──────────────────────
SECRET_KEY = "ye_bohot_strong_secret_key_hai_123456789_@#$%^&*()_change_in_production"
ALGORITHM = "HS256"
TOKEN_EXPIRE_MINUTES = 60          # token 1 hour tak chalega

# Password ko hash karne ka tool
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Ye batata hai FastAPI ko ke token header mein "Bearer <token>" ke format mein aayega
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# ────────────────────── HELPER FUNCTIONS ──────────────────────
def hash_password(password: str) -> str:
    # Plain password → safe hash (database mein yehi save hoga)
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    # Login pe check karega ke password match karta hai ya nahi
    return pwd_context.verify(plain_password, hashed_password)

# ← NAYA CHANGE: ab user object pass karte hain taake is_admin check kar sakein
def create_access_token(user: User):
    # Roman Urdu comment: normal user ko "user" scope, admin ko "admin" bhi
    scopes = ["user"]
    if user.is_admin:
        scopes.append("admin")
    
    data = {"sub": str(user.id), "scopes": scopes}
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# ← NAYA CHANGE: token se scopes nikal kar user object mein add kar dete hain
def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = int(payload.get("sub"))
        scopes: list = payload.get("scopes", [])   # ← scopes nikal liye
    except JWTError:
        raise AuthException()                     # token galat ya expire
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise AuthException()
    
    # ← YE LINE ADD KI: scopes ko user object mein daal dete hain taake routes mein check kar sakein
    user.scopes = scopes
    
    return user

