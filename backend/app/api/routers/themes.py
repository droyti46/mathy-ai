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


@router.get("/{theme_id}/{lesson_id}", response_model=LessonOut)
async def get_lesson(theme_id: str, lesson_id: str, uow = Depends(get_uow)):
    lesson = await uow.tasks.get_lesson(theme_id, lesson_id)
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return LessonOut(**lesson)

@router.get("/{theme_id}/{lesson_id}/theory")
async def get_theory(theme_id: str, lesson_id: str, uow = Depends(get_uow)):
    return {
        "theme_id": theme_id,
        "lesson_id": lesson_id,
        "content_md": (
            f"# Теория по теме {theme_id}, урок {lesson_id}"
            "\nЗдесь будет Markdown с теорией."
        ),
    }
