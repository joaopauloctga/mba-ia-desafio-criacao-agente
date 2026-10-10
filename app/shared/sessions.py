from fastapi import HTTPException
from google.adk.sessions import BaseSessionService
from google.genai import types


async def _run_and_respond(session, new_message: types.Content, runner):
    result = None
    confirmation_call = None

    async for event in runner.run_async(
        session_id=session.id,
        user_id=session.user_id,
        new_message=new_message
    ):
        if not (event.is_final_response() and event.content and event.content.parts):
            continue

        parts = event.content.parts[0]

        tool_call = parts.function_call
        if tool_call is not None:
            if tool_call.name == "adk_request_confirmation":
                confirmation_call = tool_call
            continue

        result = {
            "data": parts.text,
            "error": False
        }

    return confirmation_call if confirmation_call is not None else result

async def _get_session(
    session_id: str,
    session_service: BaseSessionService,
    app_name: str,
):
    # As rotas só recebem session_id; o ADK exige user_id, então descobrimos o dono da sessão.
    listed = await session_service.list_sessions(app_name=app_name)
    owner = next((s.user_id for s in listed.sessions if s.id == session_id), None)
    if owner is None:
        raise HTTPException(404, "Invalid Session")

    session = await session_service.get_session(
        session_id=session_id,
        app_name=app_name,
        user_id=owner,
    )
    if not session:
        raise HTTPException(404, "Invalid Session")
    return session

def _get_pending_confirmation_ids(session) -> set[str]:
    """Retorna os ids de adk_request_confirmation que ainda não receberam resposta."""
    requested: set[str] = set()
    answered: set[str] = set()

    for event in session.events:
        if not (event.content and event.content.parts):
            continue
        for part in event.content.parts:
            call = part.function_call
            if call is not None and call.name == "adk_request_confirmation" and call.id:
                requested.add(call.id)
            response = part.function_response
            if response is not None and response.name == "adk_request_confirmation" and response.id:
                answered.add(response.id)

    return requested - answered
