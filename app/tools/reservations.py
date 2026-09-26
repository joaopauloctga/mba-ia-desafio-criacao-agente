from datetime import date

from app.models import Area, Reserva
from app.models.database import SessionLocal


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
                mensagem: str
            }
    """
    with SessionLocal() as session:
        if session.get(Area, area) is None:
            areas = session.query(Area).all()
            areas = ", ".join([a.nome for a in areas])
            return {
                "error": True,
                "message": f"Area {area} nao foi encontrada, nossas areas sao: {areas}"
            }

        data_reserva = date.fromisoformat(data)
        reserva_existente = (
            session.query(Reserva)
            .filter(Reserva.area_id == area, Reserva.data == data_reserva)
            .first()
        )
        status = "indisponivel" if reserva_existente else "disponivel"
        return {
            "error": False,
            "message": f"Area {area} {status} para a data {data_reserva}"
        }

async def faz_reserva(
    area: str,
    data: str
) -> str | None:

    

    
    return None