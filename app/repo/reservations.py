from datetime import date, datetime

from sqlalchemy.orm import Session

from app.models import Area, Reserva
from app.models.database import get_db_session


class InvalidArea(ValueError):
    pass

class AreaNotAvailable(ValueError):
    pass

async def repo_reserva_disponivel(
    area: str,
    data: str,
    db: Session | None = None,
) -> bool:
    with get_db_session(db) as session:
        if session.get(Area, area) is None:
            areas = session.query(Area).all()
            areas = ", ".join([a.nome for a in areas])
            raise InvalidArea()

        data_reserva = date.fromisoformat(data)
        exists = (
            session.query(Reserva)
            .filter(Reserva.area_id == area, Reserva.data == data_reserva)
            .count()
        )
        return exists == 0


async def repo_faz_reserva(
    area: str,
    data: str,
    morador: str,
    db: Session | None = None,
) -> Reserva | None:
    with get_db_session(db) as session:
        codigo = f"RSV-{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
        available = await repo_reserva_disponivel(area, data)
        if not available:
            raise AreaNotAvailable()
        
        new_reservation = Reserva(
            codigo=codigo,
            area_id=area,
            data=date.fromisoformat(data),
            apartamento_numero=morador,
        )
        session.add(new_reservation)
        session.commit()
        return new_reservation
        