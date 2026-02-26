from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, Boolean, text
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
import os

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
db_path = os.path.join(base_dir, "palestra3000.db")

engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class Tier(Base):
    __tablename__ = "tiers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    cost = Column(Float, default=0.0)
    # RIMOSSI I SECONDI DAI VALORI DI DEFAULT!
    start_time = Column(String, default="00:00")
    end_time = Column(String, default="23:59")
    min_age = Column(Integer, default=0)
    max_age = Column(Integer, default=999)
    max_entries = Column(Integer, default=0) 
    duration_months = Column(Integer, default=1) 

class Member(Base):
    __tablename__ = "members"
    id = Column(Integer, primary_key=True, index=True)
    badge_number = Column(String, unique=True, index=True, nullable=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    birth_date = Column(String, nullable=True)
    birth_place = Column(String, nullable=True)
    city = Column(String, nullable=True)
    address = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    other_contact = Column(String, nullable=True) 
    gender = Column(String, default="M")
    
    enrollment_expiration = Column(String, nullable=True) 
    membership_start = Column(String, nullable=True) 
    membership_expiration = Column(String, nullable=True)
    has_medical_certificate = Column(Boolean, default=False)
    certificate_expiration = Column(String, nullable=True)
    entries_used = Column(Integer, default=0)
    tier_id = Column(Integer, ForeignKey("tiers.id"), nullable=True)
    tier = relationship("Tier")

class Activity(Base):
    __tablename__ = "activities"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)

class Lesson(Base):
    __tablename__ = "lessons"
    id = Column(Integer, primary_key=True, index=True)
    date = Column(String, nullable=False)
    day_of_week = Column(String, nullable=False)
    start_time = Column(String, nullable=False)
    end_time = Column(String, nullable=False)
    total_seats = Column(Integer, default=0)
    activity_id = Column(Integer, ForeignKey("activities.id"))
    activity = relationship("Activity")

class Booking(Base):
    __tablename__ = "bookings"
    id = Column(Integer, primary_key=True, index=True)
    member_id = Column(Integer, ForeignKey("members.id"))
    lesson_id = Column(Integer, ForeignKey("lessons.id"))
    member = relationship("Member")
    lesson = relationship("Lesson")

Base.metadata.create_all(bind=engine)

try:
    with engine.connect() as conn:
        conn.execute(text("ALTER TABLE members ADD COLUMN enrollment_expiration VARCHAR"))
        conn.commit()
except Exception: pass

try:
    with engine.connect() as conn:
        conn.execute(text("ALTER TABLE members ADD COLUMN other_contact VARCHAR"))
        conn.commit()
except Exception: pass

try:
    with engine.connect() as conn:
        conn.execute(text("ALTER TABLE members ADD COLUMN membership_start VARCHAR"))
        conn.commit()
except Exception: pass

try:
    with engine.connect() as conn:
        conn.execute(text("ALTER TABLE tiers ADD COLUMN duration_months INTEGER DEFAULT 1"))
        conn.commit()
except Exception: pass


def seed_data():
    db = SessionLocal()
    if db.query(Tier).count() == 0:
        db.add_all([
            # ANCHE QUI, INIZIALIZZAZIONE SENZA I SECONDI
            Tier(name="Mensile Open", cost=50.0, start_time="06:00", end_time="23:59", max_entries=0, duration_months=1),
            Tier(name="Trimestrale", cost=130.0, start_time="06:00", end_time="23:59", max_entries=0, duration_months=3),
            Tier(name="10 Ingressi (Valido 2 Mesi)", cost=40.0, start_time="06:00", end_time="23:59", max_entries=10, duration_months=2)
        ])
        db.commit()
    db.close()