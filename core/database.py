from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
import os
import sys

if getattr(sys, 'frozen', False):
    base_dir = os.path.dirname(sys.executable)
else:
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

db_path = os.path.join(base_dir, "palestra3000.db")

engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def init_db():
    """Inizializza il database creando le tabelle e applicando le migrazioni."""
    # Importa i modelli per registrarli in Base
    from core.models import Member, Tier, Activity, Lesson, Booking, DashboardConfig
    
    # Crea le tabelle
    Base.metadata.create_all(bind=engine)
    
    # Applica migrazioni automatiche per vecchi database
    _run_migrations()
    
    # Seed dati iniziali se necessario
    _seed_data()


def _run_migrations():
    """Esegue le migrazioni del database per aggiungere colonne mancanti."""
    migrations = [
        "ALTER TABLE members ADD COLUMN enrollment_expiration VARCHAR",
        "ALTER TABLE members ADD COLUMN other_contact VARCHAR",
        "ALTER TABLE members ADD COLUMN membership_start VARCHAR",
        "ALTER TABLE tiers ADD COLUMN duration_months INTEGER DEFAULT 1",
        "ALTER TABLE members ADD COLUMN codice_fiscale VARCHAR",
    ]
    
    for migration in migrations:
        try:
            with engine.connect() as conn:
                conn.execute(text(migration))
                conn.commit()
        except Exception:
            pass  # La colonna esiste già o altro errore ignorabile


def _seed_data():
    """Inserisce dati iniziali se il database è vuoto."""
    db = SessionLocal()
    try:
        from core.models import Tier
        if db.query(Tier).count() == 0:
            db.add_all([
                Tier(name="Mensile Open", cost=50.0, start_time="06:00", end_time="23:59", max_entries=0, duration_months=1),
                Tier(name="Trimestrale", cost=130.0, start_time="06:00", end_time="23:59", max_entries=0, duration_months=3),
                Tier(name="10 Ingressi (Valido 2 Mesi)", cost=40.0, start_time="06:00", end_time="23:59", max_entries=10, duration_months=2)
            ])
            db.commit()
    finally:
        db.close()


def get_db_session():
    """Context manager per la gestione delle sessioni database."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()