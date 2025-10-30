from fastapi import APIRouter, Depends
from app.core.deps import get_uow
from app.api.schemas.theme import ThemeOut

router = APIRouter(prefix="/themes", tags=["themes"])

@router.get("", response_model=list[ThemeOut])
async def list_themes(uow = Depends(get_uow)):
    items = []
    for th in await uow.tasks.list_themes():
        items.append(ThemeOut(id=th["id"], title=th["title"], description=th.get("description"), tasks_count=th["count"]))
    return items

@router.get("/{theme_id}", response_model=ThemeOut)
async def get_theme(theme_id: str, uow = Depends(get_uow)):
    th = await uow.tasks.get_theme(theme_id)
    return ThemeOut(id=th["id"], title=th["title"], description=th.get("description"), tasks_count=th["count"])

@router.get("/{theme_id}/theory")
async def get_theory(theme_id: str, uow = Depends(get_uow)):
    return {"theme_id": theme_id, "content_md": f"# Теория по теме {theme_id}\nЗдесь будет Markdown с теорией."}
