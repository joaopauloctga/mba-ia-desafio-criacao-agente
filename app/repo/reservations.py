from datetime import date, datetime

from sqlalchemy.orm import Session

from app.models import Reserva
from app.models.database import get_db_session
from app.repo.areas import repo_get_area


class ReservationNotAvailable(ValueError):
    pass


class ReservationNotFound(ValueError):
    pass

async def repo_reserva_disponivel(
    area: str,
    data: str,
    db: Session | None = None,
) -> bool:
    with get_db_session(db) as session:
        await repo_get_area(area, session)

        data_reserva = date.fromisoformat(data)
        exists = (
            session.query(Reserva)
            .filter(Reserva.area_id == area, Reserva.data == data_reserva)
            .count()
        )
        return exists == 0


async def pesquisa_reservas(
    area: str | None = None,
    data: str | None = None,
    apartamento: str | None = None,
    db: Session | None = None,
) -> list[Reserva]:
    with get_db_session(db) as session:
        query = session.query(Reserva)

        if area is not None:
            query = query.filter(Reserva.area_id == area)
        if data is not None:
            query = query.filter(Reserva.data == date.fromisoformat(data))
        if apartamento is not None:
            query = query.filter(Reserva.apartamento_numero == apartamento)

        return query.order_by(Reserva.data).all()


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
            raise ReservationNotAvailable()
        
        new_reservation = Reserva(
            codigo=codigo,
            area_id=area,
            data=date.fromisoformat(data),
            apartamento_numero=morador,
        )
        session.add(new_reservation)
        session.commit()
        return new_reservation


async def repo_cancela_reserva(
    codigo: str,
    apartamento: str,
    db: Session | None = None,
) -> None:
    with get_db_session(db) as session:
        reserva = (
            session.query(Reserva)
            .filter(
                Reserva.codigo == codigo,
                Reserva.apartamento_numero == apartamento,
            )
            .first()
        )
        if reserva is None:
            raise ReservationNotFound()

        session.delete(reserva)
        session.commit()
