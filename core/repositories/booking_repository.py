"""Booking repository for managing booking data."""

from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func
from core.database import Booking, Member, Lesson
from core.repositories.base import BaseRepository


class BookingRepository(BaseRepository[Booking]):
    """Repository per la gestione dei Booking."""
    
    def __init__(self, db: Session):
        super().__init__(db, Booking)
    
    def get_bookings_for_lesson(self, lesson_id: int) -> List[Dict[str, Any]]:
        """Ottiene tutte le prenotazioni per una lezione."""
        prenotazioni = self.db.query(Booking).filter_by(lesson_id=lesson_id).join(Member).order_by(Member.first_name).all()
        return [{"id": p.id, "nome_comp": f"{p.member.first_name} {p.member.last_name}"} for p in prenotazioni]
    
    def search_for_booking(self, lesson_id: int, activity_id: int, term: str = "") -> List[Dict[str, Any]]:
        """Cerca membri per effettuare una prenotazione."""
        if term:
            soci = self.db.query(Member).filter(
                (Member.first_name.ilike(f"%{term}%")) |
                (Member.last_name.ilike(f"%{term}%")) |
                (Member.badge_number.ilike(f"%{term}%"))
            ).order_by(Member.first_name).limit(30).all()
            return [{
                "id": s.id, "first_name": s.first_name, "last_name": s.last_name, 
                "badge_number": s.badge_number, "is_abituale": False
            } for s in soci]
        
        # Suggeriti
        soci_suggeriti = self.db.query(Member).join(Booking).join(Lesson).filter(
            Lesson.activity_id == activity_id
        ).group_by(Member.id).order_by(func.count(Booking.id).desc()).limit(15).all()
        result = [{
            "id": s.id, "first_name": s.first_name, "last_name": s.last_name, 
            "badge_number": s.badge_number, "is_abituale": True
        } for s in soci_suggeriti]
        
        if len(result) < 30:
            suggeriti_ids = [s["id"] for s in result]
            query_altri = self.db.query(Member)
            if suggeriti_ids:
                query_altri = query_altri.filter(~Member.id.in_(suggeriti_ids))
            altri = query_altri.order_by(Member.first_name).limit(30 - len(result)).all()
            result.extend([{
                "id": s.id, "first_name": s.first_name, "last_name": s.last_name, 
                "badge_number": s.badge_number, "is_abituale": False
            } for s in altri])
        return result
    
    def make_booking(self, member_id: int, lesson_id: int, force_overbooking: bool = False) -> Tuple[bool, str]:
        """Effettua una prenotazione."""
        esistente = self.db.query(Booking).filter_by(member_id=member_id, lesson_id=lesson_id).first()
        if esistente:
            return False, "Il socio è già prenotato per questo corso!"
        
        lezione = self.db.get(Lesson, lesson_id)
        occupati = self.db.query(Booking).filter_by(lesson_id=lesson_id).count()
        
        if occupati >= lezione.total_seats and not force_overbooking:
            return False, "OVERBOOKING_PROMPT"
            
        self.db.add(Booking(member_id=member_id, lesson_id=lesson_id))
        self.db.commit()
        return True, "Prenotazione effettuata."
    
    def remove(self, booking_id: int) -> None:
        """Rimuove una prenotazione."""
        b = self.db.get(Booking, booking_id)
        if b:
            self.db.delete(b)
            self.db.commit()
