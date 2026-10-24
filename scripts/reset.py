from sqlalchemy import inspect, text

from app.models.database import SessionLocal, engine

APP_TABLES = [
    "app_states",
    "events",
    "sessions",
    "user_states",
    "reservas",
    "visitantes",
]

def main():
    existing_tables = set(inspect(engine).get_table_names())

    with SessionLocal() as session:
        for table in APP_TABLES:
            if table not in existing_tables:
                print(f"Tabela '{table}' não existe, ignorando.")
                continue

            truncate_table = text(f'DELETE FROM "{table}";')
            session.execute(truncate_table)
            session.commit()


if __name__ == "__main__":
    main()