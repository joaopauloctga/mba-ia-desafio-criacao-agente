from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from google.adk import Runner
from google.adk.sessions import BaseSessionService
from google.genai import types
from pydantic import BaseModel

from app.dependencies import get_agent_runner, get_session_service
from app.shared.sessions import _get_session_or_404, _run_and_respond

sessions_controller = APIRouter(
    prefix="/sessoes"
)

class SessionRequest(BaseModel):
    apartamento: str

class MessageRequest(BaseModel):
    content: str

class ConfirmationRequest(BaseModel):
    id: str
    confirmado: bool


@sessions_controller.post("/")
async def create_session(
    payload: SessionRequest, 
    session_service: Annotated[BaseSessionService, Depends(get_session_service)],
    runner: Annotated[Runner, Depends(get_agent_runner)]
):
    ap = payload.apartamento
    session = await session_service.create_session(
        app_name=runner.app_name, 
        user_id=ap, 
        state={
            "user_id": ap,
            "apartamento": ap,
        }
    )
    return {"session_id": session.id, "user_id": ap}


@sessions_controller.post("/{session_id}/mensagens")
async def send_message(
    payload: MessageRequest, 
    session_id: str, 
    session_service: Annotated[BaseSessionService, Depends(get_session_service)],
    runner: Annotated[Runner, Depends(get_agent_runner)]
):
    session = await _get_session_or_404(session_id, session_service, runner.app_name)

    new_message = types.Content(
        role="user",
        parts=[
            types.Part.from_text(text=payload.content)
        ]
    )

    return await _run_and_respond(session, new_message, runner)

@sessions_controller.post("/{session_id}/confirmacoes")
async def confirmations(
    session_id: str, 
    data: ConfirmationRequest,
    session_service: Annotated[BaseSessionService, Depends(get_session_service)],
    runner: Annotated[Runner, Depends(get_agent_runner)]
):
    session = await _get_session_or_404(session_id, session_service, runner.app_name)

    conteudo = types.Content(
        role="user",
        parts=[
            types.Part(
                function_response=types.FunctionResponse(
                    id=data.id,
                    name="adk_request_confirmation",
                    response={"confirmed": data.confirmado}
                )
            )
        ]
    )

    return await _run_and_respond(session, conteudo, runner)


@sessions_controller.get("/{session_id}/eventos")
async def list_events(
    session_id: str,
    session_service: Annotated[BaseSessionService, Depends(get_session_service)],
    runner: Annotated[Runner, Depends(get_agent_runner)]
):
    session = await session_service.get_session(
        session_id=session_id,
        app_name=runner.app_name,
        user_id="101"
    )

    if not session:
        raise HTTPException(404, "Invalid Session")

    return session.events
    