from sqlalchemy import text

from app.models.database import SessionLocal

APP_TABLES = [
    "app_states",
    "events",
    "sessions",
    "user_states",
    "reservas",
    "visitantes",
]

def main():
    with SessionLocal() as session:
        for table in APP_TABLES:
            truncate_table = text(f"DELETE FROM '{table}';")
            session.execute(truncate_table)
            session.commit()
        

if __name__ == "__main__":
    main()