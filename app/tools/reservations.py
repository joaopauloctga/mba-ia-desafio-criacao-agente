from datetime import date, datetime

from google.adk.tools import ToolContext

from app.models import Area, Reserva
from app.models.database import SessionLocal


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
    data: str,
    context: ToolContext
) -> dict:

    if not validate_format_date(data):
        return {
            "error": True,
            "message": "Formato de data invalido, use Y-m-d",
        }

    morador = context.state.get("apartamento")
    if not morador:
        raise ValueError("Morador nao identificado!")

    with SessionLocal() as session:
        codigo = f"RSV-{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
        new_reservation = Reserva(
            codigo=codigo,
            area_id=area,
            data=date.fromisoformat(data),
            apartamento_numero=morador,
        )
        session.add(new_reservation)
        session.commit()

        return {
            "error": False,
            "message": f"Reserva na area {area} feita com sucesso para {data} (codigo {codigo})"
        }