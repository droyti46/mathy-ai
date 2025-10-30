from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.settings import Settings, get_settings

# локальный провайдер, чтобы не тянуть deps и не создавать цикл
def _get_settings() -> Settings:
    return get_settings()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
auth_scheme = HTTPBearer(auto_error=False)

def hash_password(p: str) -> str:
    return pwd_context.hash(p)

def verify_password(p: str, h: str) -> bool:
    return pwd_context.verify(p, h)

def create_token(data: dict, secret: str, alg: str, expires_delta: timedelta) -> str:
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    to_encode.update({
        "iat": int(now.timestamp()),
        "exp": int((now + expires_delta).timestamp()),
    })
    return jwt.encode(to_encode, secret, algorithm=alg)

def decode_token(token: str, secret: str, alg: str) -> Dict[str, Any]:
    return jwt.decode(token, secret, algorithms=[alg])

async def get_current_user_opt(
    creds: Optional[HTTPAuthorizationCredentials] = Depends(auth_scheme),
    settings: Settings = Depends(_get_settings),
):
    if not creds:
        return None
    try:
        payload = decode_token(creds.credentials, settings.JWT_SECRET, settings.JWT_ALG)
        return {"user_id": payload.get("sub"), "login": payload.get("login")}
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

def teacher_mode_guard(settings: Settings = Depends(_get_settings)):
    if not settings.TEACHER_MODE:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Teacher mode disabled")
    return True
