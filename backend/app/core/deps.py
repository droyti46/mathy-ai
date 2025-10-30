from fastapi import Request, Depends
from app.core.security import get_current_user_opt

def get_container(request: Request):
    return request.app.state.container

def get_settings(request: Request):
    return request.app.state.container["settings"]

def get_uow(request: Request):
    return request.app.state.container["uow"]

def get_llm(request: Request):
    return request.app.state.container["llm"]

def get_ocr(request: Request):
    return request.app.state.container["ocr"]

def get_storage(request: Request):
    return request.app.state.container["storage"]

async def get_user_opt(user=Depends(get_current_user_opt)):
    return user
