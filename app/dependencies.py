from collections.abc import Generator

from google.adk.apps import App as AdkApp
from google.adk.runners import Runner
from google.adk.sessions import BaseSessionService
from google.adk.sessions.sqlite_session_service import SqliteSessionService
from sqlalchemy.orm import Session

from app.agents.manager.agent import root_agent
from app.models.database import DB_PATH, SessionLocal


async def get_session_service() -> BaseSessionService:
    session_service = SqliteSessionService(
        db_path=str(DB_PATH)
    )
    return session_service

async def get_agent_runner() -> Runner:
    agent_app = AdkApp(root_agent=root_agent, name="operador_conta")
    service = await get_session_service()
    runner = Runner(
        app=agent_app,
        session_service=service,
    )

    return runner

def get_db() -> Generator[Session]:
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()
