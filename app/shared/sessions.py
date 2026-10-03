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

async def _get_session_or_404(
        session_id: str, 
        session_service: BaseSessionService,
        app_name: str
):
    session = await session_service.get_session(
        session_id=session_id,
        app_name=app_name,
        user_id="101"
    )
    if not session:
        raise HTTPException(409)
    return session