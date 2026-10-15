from sqlalchemy.orm import Session

from app.models import Area
from app.models.database import get_db_session


async def repo_lista_areas(db: Session | None = None) -> list[Area]:
    with get_db_session(db) as session:
        return session.query(Area).all()


async def repo_get_area(area: str, db: Session | None = None) -> Area | None:
    with get_db_session(db) as session:
        return session.get(Area, area)
