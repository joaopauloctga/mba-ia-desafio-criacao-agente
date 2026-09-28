from fastapi import FastAPI, HTTPException
from google.adk import Runner
from google.adk.apps import App as AdkApp
from google.adk.sessions.sqlite_session_service import SqliteSessionService
from google.genai import types
from pydantic import BaseModel

from app.agents.manager.agent import root_agent
from app.controllers.apartamentos import aps_ctrl
from app.models.database import DB_PATH

session_service = SqliteSessionService(db_path=str(DB_PATH))

app = FastAPI()

app.include_router(aps_ctrl)

agent_app = AdkApp(root_agent=root_agent, name="operador_conta")

runner = Runner(
    app=agent_app,
    session_service=session_service,
)

class SessionRequest(BaseModel):
    apartamento: str

class MessageRequest(BaseModel):
    content: str


@app.post("/sessoes")
async def create_session(payload: SessionRequest):
    ap = payload.apartamento
    session = await session_service.create_session(
        app_name=agent_app.name, user_id=ap, state={
            "user_id": ap,
            "apartamento": ap,
        }
    )
    return {"session_id": session.id, "user_id": ap}

@app.post("/sessoes/{session_id}/mensagens")
async def send_message(payload: MessageRequest, session_id: str):
    session = await session_service.get_session(
        session_id=session_id,
        app_name=agent_app.name,
        user_id="101"
    )
    if not session:
        raise HTTPException(409)

    conteudo = types.Content(
        role="user",
        parts=[
            types.Part.from_text(text=payload.content)
        ]
    )

    async for event in runner.run_async(
        session_id=session.id,
        user_id=session.user_id,
        new_message=conteudo
    ):
        if event.is_final_response() and event.content and event.content.parts:
            print("Resposta final: ", event.content.parts[0].text)
            return {
                "data": event.content.parts[0].text,
                "error": False
            }

@app.get("/health")
async def health():
    return "ok"
