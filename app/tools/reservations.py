from datetime import datetime

from google.adk.tools import ToolContext

from app.repo.areas import repo_get_area
from app.repo.reservations import (
    ReservationNotAvailable,
    ReservationNotFound,
    pesquisa_reservas,
    repo_cancela_reserva,
    repo_faz_reserva,
    repo_reserva_disponivel,
)


def validate_format_date(data: str) -> bool:
    try:
        datetime.strptime(data, "%Y-%m-%d")
        return True
    except ValueError:
        return False


async def reserva_disponivel(
    area: str,
    data: str
) -> dict:
    """"
        Verifica se a reserva na area e data especificada esta disponivel.

        Args:
            area: código da area (ex: quadra), obtido em lista_areas_condominio
            data: data para a reserva, formato AAAA-MM-DD
        Returns:
            {
                error: bool,
                message: str
            }
    """

    if not validate_format_date(data):
        return {
            "error": True,
            "message": "Formato de data invalido, use Y-m-d",
        }

    area_data = await repo_get_area(area=area)
    if not area_data:
        return {
            "error": True,
            "message": f"Area {area} invalida, use o código retornado por lista_areas_condominio"
        }

    available = await repo_reserva_disponivel(area, data)
    status = "disponivel" if available else "indisponivel"
    return {
        "error": False,
        "message": f"Area {area} {status} para a data {data}"
    }


async def cancela_reserva(
    area: str,
    data: str,
    context: ToolContext
):
    """
        Cancela a reserva do morador na area e data informadas.

        Args:
            area: código da area da reserva a ser cancelada (ex: quadra), obtido em lista_areas_condominio
            data: data da reserva a ser cancelada, formato AAAA-MM-DD
        Returns:
            {
                error: bool,
                message: resultado da operacao
            }
    """

    if not validate_format_date(data):
        return {
            "error": True,
            "message": "Formato de data invalido, use AAAA-MM-DD",
        }

    area_data = await repo_get_area(area=area)
    if not area_data:
        return {
            "error": True,
            "message": f"Area {area} invalida, use o código retornado por lista_areas_condominio"
        }

    apartamento = context.state.get("apartamento")
    if not apartamento:
        raise ValueError("Missing apartamento in the context")

    reservas = await pesquisa_reservas(area=area, data=data, apartamento=apartamento)
    if not reservas:
        return {
            "error": True,
            "message": f"O morador nao tem reserva da area {area_data.nome} no dia {data}."
        }

    codigos = [r.codigo for r in reservas]
    try:
        for codigo in codigos:
            await repo_cancela_reserva(codigo, apartamento)
    except ReservationNotFound:
        return {
            "error": True,
            "message": "Reserva nao encontrada."
        }

    return {
        "error": False,
        "message": f"Reserva da area {area_data.nome} no dia {data} cancelada com sucesso (codigo {', '.join(codigos)})."
    }


async def faz_reserva(
    area: str,
    data: str,
    context: ToolContext
) -> dict:
    """"
        Faz a reserva da area no condominio. Se a area tiver taxa, o sistema pede a confirmacao ao morador.

        Args:
            area: código da area ser reservada.
            data: data pra realizar a reserva -> Y-m-d
        Returns:
            {
                error: bool,
                message: resultado da operacao
            }
    """

    if not validate_format_date(data):
        return {
            "error": True,
            "message": "Formato de data invalido, use Y-m-d",
        }

    morador = context.state.get("apartamento")
    if not morador:
        raise ValueError("Morador nao identificado!")

    area_data = await repo_get_area(area=area)
    if not area_data:
        return {
            "error": True,
            "message": f"Area {area} invalida"
        }

    # Somente reserva com cobranca (taxa > 0) precisa da confirmacao do morador.
    if area_data.taxa > 0 and context.tool_confirmation is None:
        context.request_confirmation(
            hint=f"Você confirma a reserva da area {area_data.nome} para o dia {data}? Taxa de R$ {area_data.taxa:.2f}.",
            payload={
                "area": area,
                "data": data,
                "taxa": area_data.taxa,
                "apartamento": morador
            }
        )
        # Evita uma nova chamada ao LLM enquanto aguarda a confirmacao do morador.
        context.actions.skip_summarization = True
        return {
            "error": False,
            "status": "aguardando_confirmacao",
            "message": "Confirmacao solicitada ao morador. Aguarde a resposta antes de responder."
        }

    if area_data.taxa > 0 and not context.tool_confirmation.confirmed:
        return {
            "error": True,
            "message": f"O morador respondeu NAO na confirmacao, entao a reserva da area {area_data.nome} no dia {data} nao foi feita."
        }

    try:
        reservation = await repo_faz_reserva(area, data, morador)
        if reservation is not None:
            return {
                "error": False,
                "message": f"Reserva na area {reservation.area_id} feita com sucesso para {reservation.data} (codigo {reservation.codigo})"
            }
    except ReservationNotAvailable:
        return {
            "error": True,
            "message": "Infelizmente a area ja foi reservada por outro morador!"
        }
    return {
        "error": True,
        "message": "Não possivel fazer a reserva."
    }


async def lista_minhas_reservas(context: ToolContext) -> dict:
    """
        Lista as reservas do apartamento do morador em atendimento.

        Returns:
            {
                error: bool,
                reservas: [{codigo, area, data}]
            }
    """
    apartamento = context.state.get("apartamento")
    if not apartamento:
        raise ValueError("Missing apartamento in the context")

    reservas = await pesquisa_reservas(apartamento=apartamento)
    return {
        "error": False,
        "reservas": [
            {"codigo": r.codigo, "area": r.area_id, "data": r.data.isoformat()}
            for r in reservas
        ],
    }
