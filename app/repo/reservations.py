import asyncio
from datetime import date, datetime

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Reserva
from app.models.database import get_db_session


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
    # A gravacao roda fora do event loop: o SessionService do ADK grava eventos no mesmo
    # arquivo SQLite e precisa do loop livre para concluir a transacao dele. Bloquear o
    # loop esperando o lock do SQLite trava as duas escritas ate "database is locked".
    return await asyncio.to_thread(_grava_reserva, area, data, morador, db)


def _grava_reserva(
    area: str,
    data: str,
    morador: str,
    db: Session | None = None,
) -> Reserva:
    with get_db_session(db) as session:
        codigo = f"RSV-{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
        data_reserva = date.fromisoformat(data)
        exists = (
            session.query(Reserva)
            .filter(Reserva.area_id == area, Reserva.data == data_reserva)
            .count()
        )
        if exists:
            raise ReservationNotAvailable()

        new_reservation = Reserva(
            codigo=codigo,
            area_id=area,
            data=data_reserva,
            apartamento_numero=morador,
        )
        session.add(new_reservation)
        # A conferencia acima nao basta: outra reserva pode entrar antes do commit.
        # A UniqueConstraint (area_id, data) recusa a segunda gravacao.
        try:
            session.commit()
        except IntegrityError as e:
            session.rollback()
            raise ReservationNotAvailable() from e
        return new_reservation


async def repo_cancela_reserva(
    codigo: str,
    apartamento: str,
    db: Session | None = None,
) -> None:
    await asyncio.to_thread(_remove_reserva, codigo, apartamento, db)


def _remove_reserva(
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
