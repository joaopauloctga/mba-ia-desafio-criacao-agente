from app.models.area import Area
from app.models.database import SessionLocal


async def lista_areas_condominio() -> list[dict]:
    """"
        Lista as areas comumns do condominio.

        Returns:
            list[dict]: {"id": int, "nome": str, "taxa": float}
    """
    with SessionLocal() as session:
        areas = session.query(Area).all()
        return [{"id": a.id, "nome": a.nome, "taxa": a.taxa} for a in areas]