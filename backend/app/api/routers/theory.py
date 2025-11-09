from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from app.core.deps import get_uow
from app.api.schemas.theory import TheoryContentOut, TheoryIdPair, ThemeOut, LessonOut

router = APIRouter(prefix="/theory", tags=["theory"])


@router.get("/{theme_id}/{lesson_id}", response_model=TheoryContentOut)
async def get_theory(theme_id: str, lesson_id: str, uow = Depends(get_uow)):
    repo = getattr(uow, "theory", None)
    if repo is None:
        raise HTTPException(status_code=500, detail="Theory repository is not configured")

    item = repo.get_lesson(theme_id=theme_id, lesson_id=lesson_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Theory not found")

    md_lines = [
        f"# {item.title}",
        f"_Раздел:_ **{item.section_title}**",
        f"_Урок ID:_ `{item.lesson_id}`",
        "",
        item.answer_md or "Материал временно отсутствует.",
    ]
    content_md = "\n".join(md_lines)

    return TheoryContentOut(
        theme_id=item.theme_id,
        theme_title=item.section_title,   # ← НОВОЕ
        lesson_id=item.lesson_id,
        title=item.title,
        content_md=content_md,
    )


@router.get("/ids/all", response_model=list[TheoryIdPair])
async def get_all_theory_ids(uow = Depends(get_uow)):
    repo = getattr(uow, "theory", None)
    if repo is None:
        raise HTTPException(status_code=500, detail="Theory repository is not configured")

    pairs = repo.list_all_ids()
    return [
        TheoryIdPair(
            theme_id=p.theme_id,
            lesson_id=p.lesson_id,
            theme_title=p.theme_title,   # ← НОВОЕ
        )
        for p in pairs
    ]


@router.get("/tree", response_model=list[ThemeOut])
async def get_theory_tree(uow = Depends(get_uow)):
    repo = getattr(uow, "theory", None)
    if repo is None:
        raise HTTPException(status_code=500, detail="Theory repository is not configured")

    tree = repo.list_tree()
    out: list[ThemeOut] = []
    for t in tree:
        lessons = [
            LessonOut(id=l["id"], title=l["title"], theme_id=t["id"])
            for l in t["lessons"]
        ]
        out.append(ThemeOut(id=t["id"], title=t["title"], lessons=lessons))
    return out
