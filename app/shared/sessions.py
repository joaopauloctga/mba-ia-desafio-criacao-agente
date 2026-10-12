from fastapi import HTTPException
from google.adk.sessions import BaseSessionService
from google.genai import types


async def _run_and_respond(session, new_message: types.Content, runner):
    resposta = None

    async for event in runner.run_async(
        session_id=session.id,
        user_id=session.user_id,
        new_message=new_message
    ):
        if not (event.is_final_response() and event.content and event.content.parts):
            continue

        # Quando a execucao para esperando confirmacao, a resposta vem vazia.
        if any(c.name == "adk_request_confirmation" for c in event.get_function_calls()):
            resposta = ""
            continue

        text = "".join(
            p.text for p in event.content.parts if p.text and not p.thought
        )
        if text:
            resposta = text

    session = await runner.session_service.get_session(
        app_name=session.app_name,
        user_id=session.user_id,
        session_id=session.id,
    )
    pendentes = _get_pending_confirmations(session)

    if resposta is None and not pendentes:
        resposta = "Nao foi possivel obter uma resposta do agente."
    return _build_response(resposta or "", pendentes)


def _build_response(resposta: str, pendentes: list[dict]) -> dict:
    return {
        "resposta": resposta,
        "confirmacoes_pendentes": pendentes,
    }

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

def _get_pending_confirmations(session) -> list[dict]:
    """Lista as confirmacoes pendentes da sessao no formato do contrato da API."""
    pending_ids = _get_pending_confirmation_ids(session)
    pendentes = []
    for event in session.events:
        for call in event.get_function_calls():
            if call.name != "adk_request_confirmation" or call.id not in pending_ids:
                continue
            args = call.args or {}
            original = args.get("originalFunctionCall") or {}
            confirmation = args.get("toolConfirmation") or {}
            pendentes.append({
                "id": call.id,
                "acao": original.get("name"),
                "detalhes": confirmation.get("payload") or original.get("args") or {},
            })
    return pendentes
