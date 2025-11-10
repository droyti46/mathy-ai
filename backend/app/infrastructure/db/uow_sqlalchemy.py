from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
from app.infrastructure.db.repositories_sqlalchemy import SqlAttemptRepo, SqlUserRepo

class SqlUoW:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession], tasks_repo, theory_repo):
        self.session: AsyncSession = session_factory()
        self.attempts = SqlAttemptRepo(self.session)
        self.users = SqlUserRepo(self.session)
        self.tasks = tasks_repo
        self.theory = theory_repo

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.session.close()
        return False

    async def commit(self):
        await self.session.commit()
