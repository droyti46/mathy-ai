from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

class DomainError(Exception):
    def __init__(self, message: str):
        self.message = message

def register_handlers(app: FastAPI):
    @app.exception_handler(DomainError)
    async def _domain_error_handler(request: Request, exc: DomainError):
        return JSONResponse(status_code=400, content={"error": exc.message})
