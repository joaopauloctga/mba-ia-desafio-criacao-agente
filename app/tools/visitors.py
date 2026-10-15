import asyncio
from datetime import date

from google.adk.tools import ToolContext

from app.models.database import SessionLocal
from app.models.visitante import Visitante
from app.tools.apartments import list_apartments


def identifica_morador_atual(context: ToolContext) -> str:
    """"
        Identifica o apartamento do morador em atendimento.

        Returns:
            str: Nome do apartamento que o morador em atendimento mora.
    """
    ap = context.state.get("apartamento")
    if not ap:
        raise ValueError("Erro ao identificar o morador atual.")

    apartamentos = list_apartments()
    if apartamentos.get(ap) is None:
        raise ValueError("Apartamento nao existe no condominio.")
    
    return ap

async def autorizar_entrada_visitante(
    nome: str,
    data: str,
    context: ToolContext
) -> dict:
    """"
        Libera a entrada de um visitante no apartamento do morador em atendimento. O sistema pede a confirmacao ao morador.

        Args:
            nome: nome do visitante
            data: data da visita, formato AAAA-MM-DD
        Returns:
            {
                error: bool,
                message: str
            }
    """

    try:
        data_visita = date.fromisoformat(data)
    except ValueError:
        return {
            "error": True,
            "message": "Formato de data invalido, use AAAA-MM-DD",
        }

    apartamento = context.state.get("apartamento")
    if not apartamento:
        raise ValueError("Apartamento nao informado!")

    apartamentos = list_apartments()
    if not apartamentos.get(apartamento):
        raise ValueError("Apartamento informado nao encontrado!")

    # Liberar acesso sempre depende da confirmacao do morador pela rota de confirmacoes.
    if context.tool_confirmation is None:
        context.request_confirmation(
            hint=f"Você confirma a entrada de {nome} no dia {data}?",
            payload={
                "nome": nome,
                "data": data,
                "apartamento": apartamento
            }
        )
        # Evita uma nova chamada ao LLM enquanto aguarda a confirmacao do morador.
        context.actions.skip_summarization = True
        return {
            "error": False,
            "status": "aguardando_confirmacao",
            "message": "Confirmacao solicitada ao morador. Aguarde a resposta antes de responder."
        }

    if not context.tool_confirmation.confirmed:
        return {
            "error": True,
            "message": f"O morador respondeu NAO na confirmacao, entao a entrada de {nome} no dia {data} nao foi liberada."
        }

    # Grava fora do event loop para nao disputar o lock do SQLite com o SessionService do ADK.
    await asyncio.to_thread(_grava_visitante, apartamento, nome, data_visita)

    return {
        "error": False,
        "message": f"O morador aprovou a confirmacao. A entrada de {nome} no dia {data} esta liberada."
    }


def _grava_visitante(apartamento: str, nome: str, data_visita: date) -> None:
    with SessionLocal() as session:
        session.add(Visitante(
            apartamento_numero=apartamento,
            nome=nome,
            data=data_visita
        ))
        session.commit()


async def lista_meus_visitantes(context: ToolContext) -> dict:
    """
        Lista os visitantes autorizados do apartamento do morador em atendimento.

        Returns:
            {
                error: bool,
                visitantes: [{nome, data}]
            }
    """
    apartamento = context.state.get("apartamento")
    if not apartamento:
        raise ValueError("Apartamento nao informado!")

    with SessionLocal() as session:
        visitantes = (
            session.query(Visitante)
            .filter(Visitante.apartamento_numero == apartamento)
            .order_by(Visitante.data)
            .all()
        )
        return {
            "error": False,
            "visitantes": [{"nome": v.nome, "data": v.data.isoformat()} for v in visitantes],
        }
