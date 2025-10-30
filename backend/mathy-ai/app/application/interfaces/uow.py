from typing import Protocol
from app.domain.tasks.repository import ITaskRepo
from app.domain.attempts.repository import IAttemptRepo

class UnitOfWork(Protocol):
    tasks: ITaskRepo
    attempts: IAttemptRepo
    users: "IUserRepo"
    async def __aenter__(self): ...
    async def __aexit__(self, exc_type, exc, tb): ...
    async def commit(self): ...
