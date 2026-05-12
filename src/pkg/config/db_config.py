import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from src.pkg.models import Base, Tier

class DatabaseConfig:
    def __init__(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            
        data_dir = os.path.join(base_dir, "data")
        os.makedirs(data_dir, exist_ok=True)
        self.db_path = os.path.join(data_dir, "palestra3000.db")

        self.engine = create_engine(f"sqlite:///{self.db_path}", connect_args={"check_same_thread": False})
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

        Base.metadata.create_all(bind=self.engine)
        
        # Creazione indici aggiuntivi per SQLite per ottimizzare le query di ricerca e ordinamento
        self._create_performance_indexes()
    
    def _create_performance_indexes(self):
        """Crea indici specifici per migliorare le performance delle query sui soci."""
        with self.engine.connect() as conn:
            # Indici composti per le ricerche frequenti
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_members_badge ON members(badge_number)",
                "CREATE INDEX IF NOT EXISTS idx_members_last_name_first_name ON members(last_name, first_name)",
                "CREATE INDEX IF NOT EXISTS idx_members_tier_id ON members(tier_id)",
                "CREATE INDEX IF NOT EXISTS idx_members_membership_expiration ON members(membership_expiration)",
                "CREATE INDEX IF NOT EXISTS idx_members_enrollment_expiration ON members(enrollment_expiration)",
                "CREATE INDEX IF NOT EXISTS idx_members_phone ON members(phone)",
                "CREATE INDEX IF NOT EXISTS idx_members_city ON members(city)",
                "CREATE INDEX IF NOT EXISTS idx_members_birth_place ON members(birth_place)",
                "CREATE INDEX IF NOT EXISTS idx_members_first_name ON members(first_name)",
                "CREATE INDEX IF NOT EXISTS idx_tiers_name ON tiers(name)"
            ]
            
            for index_sql in indexes:
                try:
                    conn.execute(text(index_sql))
                    conn.commit()
                except Exception as e:
                    # Silenziosamente ignora errori su indici già esistenti o non supportati
                    pass

    def get_session(self):
        return self.SessionLocal()


def seed_data(session_factory):
    db = session_factory()
    try:
        if db.query(Tier).count() == 0:
            db.add_all([
                Tier(name="F1", cost=50.0, start_time="16:30", end_time="21:59", max_entries=25, duration_months=1),
                Tier(name="F3", cost=130.0, start_time="16:30", end_time="21:59", max_entries=70, duration_months=3),
                Tier(name="F6", cost=40.0, start_time="16:30", end_time="21:59", max_entries=150, duration_months=6)
            ])
            db.commit()
    finally:
        db.close()
