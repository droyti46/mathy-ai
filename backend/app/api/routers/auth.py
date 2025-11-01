from datetime import timedelta
import uuid

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.schemas.auth import (
    RegisterIn,
    LoginIn,
    TokenPair,
    UserOut,
    StatsOut,
    TaskSolvedOut,
    SolvedCountOut,
)
from app.core.deps import get_uow, get_settings
from app.core.security import hash_password, verify_password, create_token, decode_token, get_current_user_opt
from app.core.user_stats import default_user_stats

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


@router.get("/me", response_model=UserOut)
async def me(user=Depends(get_current_user_opt), uow=Depends(get_uow)):
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    db = await uow.users.get(user["user_id"])
    return UserOut(id=db["id"], login=db["login"], name=db.get("name") or db["login"])


@router.get("/me/stats", response_model=StatsOut)
async def my_stats(user=Depends(get_current_user_opt), uow=Depends(get_uow)):
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    stats = await uow.users.get_stats(user["user_id"])
    if stats is None:
        raise HTTPException(status_code=404, detail="User not found")
    attempts = await uow.attempts.list_by_user(user["user_id"])
    solved = len(stats.get("solved_task_ids", []))
    return StatsOut(
        solved=solved,
        attempts=len(attempts),
        streak_days=stats.get("streak_days", 0),
        coins=stats.get("coins", 0),
        solved_task_ids=stats.get("solved_task_ids", []),
    )


@router.get("/me/solved/{task_id}", response_model=TaskSolvedOut)
async def task_solved_status(
    task_id: str, user=Depends(get_current_user_opt), uow=Depends(get_uow)
):
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    solved = await uow.users.has_solved_task(user["user_id"], task_id)
    return TaskSolvedOut(task_id=str(task_id), solved=bool(solved))


@router.get("/me/solved-count", response_model=SolvedCountOut)
async def solved_tasks_count(user=Depends(get_current_user_opt), uow=Depends(get_uow)):
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    solved = await uow.users.count_solved_tasks(user["user_id"])
    return SolvedCountOut(solved=solved)
