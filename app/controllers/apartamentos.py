from fastapi import APIRouter
from sqlalchemy import select

from app.models.apartamento import Apartamento
from app.models.database import SessionLocal
from app.models.reserva import Reserva
from app.models.visitante import Visitante

aps_ctrl = APIRouter(
    prefix="/apartamentos"
)

@aps_ctrl.get("/{apartamento}/reservas")
def list_apartment_reservations(apartamento: str):
    filter_reservas = select(Reserva).join(Apartamento, Apartamento.numero == Reserva.apartamento_numero).where(Apartamento.numero == apartamento)
    with SessionLocal() as session:
        reservas = session.execute(filter_reservas).scalars().all()
        return [{"codigo": r.codigo, "area": r.area, "data": r.data} for r in reservas]

@aps_ctrl.get("/{apartamento}/visitantes")
def list_apartment_visitantes(apartamento: str):
    filter_reservas = select(Visitante).join(Apartamento, Apartamento.numero == Visitante.apartamento_numero).where(Apartamento.numero == apartamento)
    with SessionLocal() as session:
        visitas = session.execute(filter_reservas).scalars().all()
        return [{"nome": r.nome, "data": r.data} for r in visitas]


