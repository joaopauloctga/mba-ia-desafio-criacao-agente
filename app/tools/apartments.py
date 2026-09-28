from app.models.apartamento import Apartamento
from app.models.database import SessionLocal


def list_apartments():
    with SessionLocal() as session:
        data = session.query(Apartamento).all()
        return {a.numero: a.morador for a in data}

