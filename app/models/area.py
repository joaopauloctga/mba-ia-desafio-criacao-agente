from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.database import Base


class Area(Base):
    __tablename__ = "areas"

    id: Mapped[str] = mapped_column(primary_key=True)
    nome: Mapped[str]
    taxa: Mapped[float]

    reservas: Mapped[list["Reserva"]] = relationship(back_populates="area")
