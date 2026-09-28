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

def autorizar_entrada_visitante(
    visitantes: list[str] | str,
    context: ToolContext
) -> dict:
    """"
        Libera a entrada dos visitantes pro morador em atendimento.

        Args:
            visitantes: lista de nomes ou nome do visiteante
        Returns:
            {
                error: bool,
                message: str
            }
    """

    if isinstance(visitantes, str):
        visitantes = [visitantes]

    apartamento = context.state.get("apartamento")

    if not apartamento:
        raise ValueError("Apartamento nao informado!")

    apartamentos = list_apartments()
    if not apartamentos.get(apartamento):
        raise ValueError("Apartamento informado nao encontrado!")

    if context.tool_confirmation is None:
        context.request_confirmation(
            hint="Pode por gentileza liberar a entrada do visitante?",
            payload={
                "visitantes": visitantes,
                "apartamento": apartamento
            }
        )
        return {
            "error": True,
            "message": "Necessario tool confirmation para liberar a entrada!"
        }

    if context.tool_confirmation.confirmed:
        with SessionLocal() as session:
            for v in visitantes:
                session.add(Visitante(
                    apartamento_numero=apartamento,
                    nome=v,
                    data=date.today()
                ))
            session.commit()
            return {
                "error": False,
                "message": "Visita liberada!"
            }
    else:
        return {
            "error": True,
            "message": "Necessaria a confirmacao do morador para liberar a entrada!"
        }