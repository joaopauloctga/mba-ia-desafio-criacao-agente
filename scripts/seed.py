import json
from datetime import date
from pathlib import Path

from app.models import Apartamento, Area, Base, Reserva, SessionLocal, Visitante, engine

DADOS_DIR = Path(__file__).resolve().parent.parent / "dados"


def load_json(nome: str) -> list[dict]:
    with open(DADOS_DIR / nome, encoding="utf-8") as f:
        return json.load(f)


def seed() -> None:
    Base.metadata.create_all(engine)

    with SessionLocal() as session:
        session.query(Visitante).delete()
        session.query(Reserva).delete()
        session.query(Apartamento).delete()
        session.query(Area).delete()

        for item in load_json("apartamentos.json"):
            session.add(Apartamento(numero=item["numero"], morador=item["morador"]))

        for item in load_json("areas.json"):
            session.add(Area(id=item["id"], nome=item["nome"], taxa=item["taxa"]))

        for item in load_json("reservas.json"):
            session.add(
                Reserva(
                    codigo=item["codigo"],
                    apartamento_numero=item["apartamento"],
                    area_id=item["area"],
                    data=date.fromisoformat(item["data"]),
                )
            )

        for item in load_json("visitantes.json"):
            session.add(
                Visitante(
                    apartamento_numero=item["apartamento"],
                    nome=item["nome"],
                    data=date.fromisoformat(item["data"]),
                )
            )

        session.commit()

    print(f"Banco de dados populado em: {engine.url}")


if __name__ == "__main__":
    seed()
