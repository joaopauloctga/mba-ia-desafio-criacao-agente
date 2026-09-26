from datetime import date

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.database import Base


class Visitante(Base):
    __tablename__ = "visitantes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    apartamento_numero: Mapped[str] = mapped_column(ForeignKey("apartamentos.numero"))
    nome: Mapped[str]
    data: Mapped[date]

    apartamento: Mapped["Apartamento"] = relationship(back_populates="visitantes")
