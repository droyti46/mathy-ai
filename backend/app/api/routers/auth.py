from datetime import timedelta
import uuid

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.schemas.auth import (
    RegisterIn,
    LoginIn,
    TokenPair,
    UserOut,
    StatsOut,
)
from app.core.deps import get_uow, get_settings
from app.core.security import hash_password, verify_password, create_token, decode_token, get_current_user_opt
from app.core.user_stats import default_user_stats, ensure_user_stats

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut)
async def register(payload: RegisterIn, uow=Depends(get_uow)):
    existing = await uow.users.get_by_login(payload.login)
    if existing:
        raise HTTPException(status_code=400, detail="Login already registered")
    user_id = str(uuid.uuid4())
    name = payload.name or payload.login
    user = {
        "id": user_id,
        "name": name,
        "login": payload.login,
        "password_hash": hash_password(payload.password),
        "stats": default_user_stats(),
    }
    await uow.users.add(user)
    return UserOut(id=user_id, login=payload.login, name=name)


@router.post("/login", response_model=TokenPair)
async def login(payload: LoginIn, uow=Depends(get_uow), settings=Depends(get_settings)):
    user = await uow.users.get_by_login(payload.login)
    if not user or not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    access = create_token({"sub": user["id"], "login": user["login"]}, settings.JWT_SECRET, settings.JWT_ALG, timedelta(minutes=settings.ACCESS_EXPIRES_MIN))
    refresh = create_token({"sub": user["id"], "login": user["login"], "type": "refresh"}, settings.JWT_SECRET, settings.JWT_ALG, timedelta(days=settings.REFRESH_EXPIRES_DAYS))
    return TokenPair(access_token=access, refresh_token=refresh)


@router.post("/refresh", response_model=TokenPair)
async def refresh_token(refresh_token: str, settings=Depends(get_settings)):
    try:
        payload = decode_token(refresh_token, settings.JWT_SECRET, settings.JWT_ALG)
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Not a refresh token")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    access = create_token({"sub": payload["sub"], "login": payload["login"]}, settings.JWT_SECRET, settings.JWT_ALG, timedelta(minutes=settings.ACCESS_EXPIRES_MIN))
    new_refresh = create_token({"sub": payload["sub"], "login": payload["login"], "type": "refresh"}, settings.JWT_SECRET, settings.JWT_ALG, timedelta(days=settings.REFRESH_EXPIRES_DAYS))
    return TokenPair(access_token=access, refresh_token=new_refresh)


async def _resolve_user(uow, user, login: str | None, name: str | None):
    if login:
        db = await uow.users.get_by_login(login)
    elif name:
        db = await uow.users.get_by_name(name)
    elif user:
        db = await uow.users.get(user["user_id"])
    else:
        raise HTTPException(status_code=401, detail="Unauthorized")

    if not db:
        raise HTTPException(status_code=404, detail="User not found")

    return db


@router.get("/me", response_model=UserOut)
async def me(
    login: str | None = None,
    name: str | None = None,
    user=Depends(get_current_user_opt),
    uow=Depends(get_uow),
):
    db = await _resolve_user(uow, user, login, name)
    return UserOut(id=db["id"], login=db["login"], name=db.get("name") or db["login"])


@router.get("/me/stats", response_model=StatsOut)
async def my_stats(
    login: str | None = None,
    name: str | None = None,
    user=Depends(get_current_user_opt),
    uow=Depends(get_uow),
):
    db = await _resolve_user(uow, user, login, name)
    attempts = await uow.attempts.list_by_user(db["id"])
    solved = sum(1 for a in attempts if (a.get("score") or 0) >= 0.99)
    stats = ensure_user_stats(db.get("stats"))
    return StatsOut(
        solved=stats.get("solved_tasks", solved),
        attempts=len(attempts),
        streak_days=stats.get("streak_days", 0),
        coins=stats.get("coins", 0),
        solved_task_ids=stats.get("solved_task_ids", []),
    )
