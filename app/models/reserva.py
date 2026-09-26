from datetime import date

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.database import Base


class Reserva(Base):
    __tablename__ = "reservas"

    codigo: Mapped[str] = mapped_column(primary_key=True)
    apartamento_numero: Mapped[str] = mapped_column(ForeignKey("apartamentos.numero"))
    area_id: Mapped[str] = mapped_column(ForeignKey("areas.id"))
    data: Mapped[date]

    apartamento: Mapped["Apartamento"] = relationship(back_populates="reservas")
    area: Mapped["Area"] = relationship(back_populates="reservas")
