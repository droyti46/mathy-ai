from fastapi import APIRouter, Depends, HTTPException
from app.core.deps import get_uow
from app.api.schemas.theme import ThemeOut, LessonOut

router = APIRouter(prefix="/themes", tags=["themes"])

@router.get("", response_model=list[ThemeOut])
async def list_themes(uow = Depends(get_uow)):
    themes = await uow.tasks.list_themes()
    return [ThemeOut(**th) for th in themes]

@router.get("/{theme_id}", response_model=ThemeOut)
async def get_theme(theme_id: str, uow = Depends(get_uow)):
    th = await uow.tasks.get_theme(theme_id)
    if not th:
        raise HTTPException(status_code=404, detail="Theme not found")
    return ThemeOut(**th)