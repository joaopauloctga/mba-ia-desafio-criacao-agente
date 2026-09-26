from fastapi import FastAPI
from google.adk import Runner
from google.adk.apps import App as AdkApp
from google.adk.sessions.sqlite_session_service import SqliteSessionService
from pydantic import BaseModel

from app.agents.manager.agent import root_agent
from app.models.database import DB_PATH

session_service = SqliteSessionService(db_path=str(DB_PATH))

app = FastAPI()

agent_app = AdkApp(root_agent=root_agent, name="operador_conta")

runner = Runner(
    app=agent_app,
    session_service=session_service,
)

class SessionRequest(BaseModel):
    apartamento: str


@app.post("/session")
async def create_session(payload: SessionRequest):
    ap = payload.apartamento
    session = await session_service.create_session(
        app_name=agent_app.name, user_id=ap, state={}
    )
    return {"session_id": session.id}


@app.get("/health")
async def health():
    return "ok"
