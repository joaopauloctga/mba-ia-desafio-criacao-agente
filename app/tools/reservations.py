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


async def cancela_reserva(
    area: str | None,
    data: str | None,
    context: ToolContext
):
    """
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


    if data is not None and not validate_format_date(data):
        return {
            "error": True,
            "message": "Formato de data invalido, use Y-m-d",
        }

    if area is not None:
        area_data = await repo_get_area(area=area)
        if not area_data:
            return {
                "error": True,
                "message": f"Area {area} invalida"
            }

    apartamento = context.state.get("apartamento")
    if not apartamento:
        raise ValueError("Missing apartamento in the context")

    has_reservations = await pesquisa_reservas(
        area=area,
        data=data,
        apartamento=context.state.get("apartamento")
    )

    if not has_reservations:
        return {
            "error": True,
            "message" : "Voce nao tem reservas para serem canceladas!"
        }

    if context.tool_confirmation is None:
        context.request_confirmation(
            hint="Voce realmente deseja cancelar sua reserva?",
            payload={
                "codigos": [r.codigo for r in has_reservations]
            }
        )
        return {
            "error": True,
            "message": "Necessario tool confirmation para cancelar reserva!"
        }  

    if not context.tool_confirmation.confirmed:
        return {
            "error": True,
            "message": "Cancelamento nao confirmado."
        }

    payload = context.tool_confirmation.payload or {}
    codigos: list[str] = payload.get("codigos", [])

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
        "message": f"Reservas canceladas com sucesso: {', '.join(codigos)}."
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

    area_data = await repo_get_area(area=area)
    if not area_data:
        return {
            "error": True,
            "message": f"Area {area} invalida"
        }

    if area_data.taxa:
        if context.tool_confirmation is None:
            context.request_confirmation(
                hint=f"Você confirma a reserva da area {area} para o dia {data}",
                payload={
                    "area": area,
                    "data": data,
                    "apartamento": morador
                }
            )
            return {
                "error": True,
                "message": "Necessario tool confirmation para reservar area!"
            }    

        if not context.tool_confirmation.confirmed:
            return {
                        "error": True,
                        "message": "Necessario confirmar a reserva."
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
        
    