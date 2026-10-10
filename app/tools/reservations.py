from datetime import datetime

from google.adk.tools import ToolContext

from app.repo.reservations import (
    AreaNotAvailable,
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
            area: nome ou código da area
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

    available = await repo_reserva_disponivel(area, data)
    status = "disponivel" if available else "indisponivel"
    return {
        "error": False,
        "message": f"Area {area} {status} para a data {data}"
    }

async def faz_reserva(
    area: str,
    data: str,
    context: ToolContext
) -> dict:
    """"
        Faz a reserva da area no condominio, se tiver taxa necessita de confirmacao.

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

    try:
        reservation = await repo_faz_reserva(area, data, morador)
        if reservation is not None:
            return {
                "error": False,
                "message": f"Reserva na area {reservation.area_id} feita com sucesso para {reservation.data} (codigo {reservation.codigo})"
            }
    except AreaNotAvailable:
        return {
            "error": True,
            "message": "Infelizmente a area ja foi reservada por outro morador!"
        }
    return {
        "error": True,
        "message": "Não possivel fazer a reserva."
    }
    