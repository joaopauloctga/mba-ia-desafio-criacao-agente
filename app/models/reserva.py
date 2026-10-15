from datetime import date

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.database import Base


class Reserva(Base):
    __tablename__ = "reservas"
    # Exclusividade garantida pelo banco no momento da gravacao: uma reserva por area e data.
    __table_args__ = (UniqueConstraint("area_id", "data", name="uq_reserva_area_data"),)

    codigo: Mapped[str] = mapped_column(primary_key=True)
    apartamento_numero: Mapped[str] = mapped_column(ForeignKey("apartamentos.numero"))
    area_id: Mapped[str] = mapped_column(ForeignKey("areas.id"))
    data: Mapped[date]

    apartamento: Mapped["Apartamento"] = relationship(back_populates="reservas")
    area: Mapped["Area"] = relationship(back_populates="reservas")
