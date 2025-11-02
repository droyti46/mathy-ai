from app.settings import get_settings
from app.infrastructure.llm.router import LLMRouter
from app.infrastructure.pandas_repo.tasks_repo_pandas import PandasTaskRepo
from app.infrastructure.db.base import create_engine_and_session, init_models
from app.infrastructure.db.uow_sqlalchemy import SqlUoW
from app.infrastructure.ocr.vision_openrouter import VisionOCROpenRouter
from app.infrastructure.storage.local import LocalStorage
from app.infrastructure.prompts.text_store import PromptTextStore

def build_container():
    s = get_settings()
    engine, session_factory = create_engine_and_session(s.DATABASE_URL)
    tasks_repo = PandasTaskRepo(s.DATA_PATH)
    uow = SqlUoW(session_factory=session_factory, tasks_repo=tasks_repo)
    llm = LLMRouter.from_settings(s)
    ocr_model = s.OCR_MODEL.strip().strip('"')
    ocr = VisionOCROpenRouter(
        model=ocr_model,
        api_key=s.OPENROUTER_API_KEY,
        base_url=s.OPENROUTER_BASE_URL,   # ← тот же base_url, что у LLM
        trust_env=True,                           # или False, если хочешь игнорировать системные proxy
    )
    storage = LocalStorage(base_dir=s.STORAGE_DIR)
    prompts = PromptTextStore('app/infrastructure/prompts')
    return dict(settings=s, uow=uow, llm=llm, ocr=ocr, storage=storage, engine=engine, prompts=prompts)
 
async def init_db(engine):
    await init_models(engine)
