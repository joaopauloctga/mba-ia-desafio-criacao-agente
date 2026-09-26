from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.database import Base


class Apartamento(Base):
    __tablename__ = "apartamentos"

    numero: Mapped[str] = mapped_column(primary_key=True)
    morador: Mapped[str]

    reservas: Mapped[list["Reserva"]] = relationship(back_populates="apartamento")
    visitantes: Mapped[list["Visitante"]] = relationship(back_populates="apartamento")
