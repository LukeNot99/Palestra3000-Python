from core.database import Tier, Member, Activity, Lesson, Booking
from datetime import datetime

def test_creazione_fascia(db_session):
    """Testa se riusciamo a creare una Fascia (Tier) correttamente"""
    nuova_fascia = Tier(
        name="Mensile Gold", 
        cost=50.0, 
        duration_months=1,
        max_entries=10
    )
    db_session.add(nuova_fascia)
    db_session.commit()
    
    fascia_salvata = db_session.query(Tier).filter_by(name="Mensile Gold").first()
    
    # Le ASSERZIONI: verifichiamo che i dati corrispondano
    assert fascia_salvata is not None
    assert fascia_salvata.cost == 50.0
    assert fascia_salvata.duration_months == 1

def test_creazione_socio_e_relazione_fascia(db_session):
    """Testa se riusciamo a collegare un Socio a una Fascia (Foreign Key)"""
    fascia = Tier(name="Open", cost=100.0)
    db_session.add(fascia)
    db_session.commit()
    
    socio = Member(
        first_name="Mario", 
        last_name="Rossi", 
        badge_number="0001",
        tier_id=fascia.id
    )
    db_session.add(socio)
    db_session.commit()
    
    socio_salvato = db_session.query(Member).filter_by(badge_number="0001").first()
    
    assert socio_salvato is not None
    assert socio_salvato.first_name == "Mario"
    # Verifichiamo che la relazione ("relationship" di SQLAlchemy) funzioni
    assert socio_salvato.tier.name == "Open"

def test_prenotazione_lezione(db_session):
    """Test avanzato: creazione Attività -> Lezione -> Socio -> Prenotazione"""
    # 1. Creo Attività
    att = Activity(name="Pilates")
    db_session.add(att)
    db_session.commit()
    
    # 2. Creo Lezione
    lez = Lesson(
        date="2026-10-15", 
        day_of_week="Giovedì", 
        start_time="18:00", 
        end_time="19:00", 
        total_seats=20,
        activity_id=att.id
    )
    db_session.add(lez)
    
    # 3. Creo Socio
    socio = Member(first_name="Luca", last_name="Bianchi")
    db_session.add(socio)
    db_session.commit()
    
    # 4. Creo Prenotazione
    prenotazione = Booking(member_id=socio.id, lesson_id=lez.id)
    db_session.add(prenotazione)
    db_session.commit()
    
    # Asserzioni
    prenotazione_salvata = db_session.query(Booking).first()
    assert prenotazione_salvata is not None
    assert prenotazione_salvata.member.first_name == "Luca"
    assert prenotazione_salvata.lesson.activity.name == "Pilates"