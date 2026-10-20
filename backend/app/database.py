from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from backend.app.config import settings

connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def auto_migrate():
    from sqlalchemy import text
    with engine.connect() as conn:
        for col, col_type in [
            ("year_of_study", "INTEGER DEFAULT 3"),
            ("sleep_target", "FLOAT DEFAULT 7.5"),
            ("weekly_budget_target", "FLOAT DEFAULT 3000.0"),
            ("vocal_persona", "VARCHAR(50) DEFAULT 'EMPATHETIC_MENTOR'"),
            ("morning_briefing_time", "VARCHAR(10) DEFAULT '08:00'"),
            ("morning_briefing_enabled", "BOOLEAN DEFAULT 1"),
            ("nightly_wind_down_time", "VARCHAR(10) DEFAULT '22:30'"),
            ("nightly_wind_down_enabled", "BOOLEAN DEFAULT 1"),
        ]:
            try:
                conn.execute(text(f"ALTER TABLE profiles ADD COLUMN {col} {col_type}"))
                conn.commit()
            except Exception:
                pass

try:
    auto_migrate()
except Exception:
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
