import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from src.pkg.models.models import Base, Tier

class DatabaseConfig:
    def __init__(self):
        if getattr(sys, 'frozen', False):
            base_dir = os.path.dirname(sys.executable)
        else:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            
        data_dir = os.path.join(base_dir, "data")
        os.makedirs(data_dir, exist_ok=True)
        self.db_path = os.path.join(data_dir, "palestra3000.db")

        self.engine = create_engine(f"sqlite:///{self.db_path}", connect_args={"check_same_thread": False})
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

        Base.metadata.create_all(bind=self.engine)
        self._run_migrations()

    def get_session(self):
        return self.SessionLocal()

    def close_all_sessions(self):
        """Chiude tutte le connessioni al database."""
        self.engine.dispose()

    def _run_migrations(self):
        # --- MIGRAZIONI AUTOMATICHE (AGGIORNA I VECCHI DATABASE) ---
        migrations = [
            "ALTER TABLE members ADD COLUMN enrollment_expiration VARCHAR",
            "ALTER TABLE members ADD COLUMN other_contact VARCHAR",
            "ALTER TABLE members ADD COLUMN membership_start VARCHAR",
            "ALTER TABLE tiers ADD COLUMN duration_months INTEGER DEFAULT 1",
            "ALTER TABLE members ADD COLUMN codice_fiscale VARCHAR"
        ]
        
        for migration in migrations:
            try:
                with self.engine.connect() as conn:
                    conn.execute(text(migration))
                    conn.commit()
            except Exception:
                pass


def seed_data(session_factory):
    db = session_factory()
    try:
        if db.query(Tier).count() == 0:
            db.add_all([
                Tier(name="Mensile Open", cost=50.0, start_time="06:00", end_time="23:59", max_entries=0, duration_months=1),
                Tier(name="Trimestrale", cost=130.0, start_time="06:00", end_time="23:59", max_entries=0, duration_months=3),
                Tier(name="10 Ingressi (Valido 2 Mesi)", cost=40.0, start_time="06:00", end_time="23:59", max_entries=10, duration_months=2)
            ])
            db.commit()
    finally:
        db.close()
