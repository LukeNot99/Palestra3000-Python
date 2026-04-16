from contextlib import contextmanager
from sqlalchemy import func
from src.pkg.models.models import Booking, Member, Lesson

class BookingRepository:
    def __init__(self, session_factory):
        self.session_factory = session_factory
    
    @contextmanager
    def _get_session(self):
        """Context manager per gestire automaticamente aperture/chiusura sessioni DB."""
        db = self.session_factory()
        try:
            yield db
        finally:
            db.close()

    def get_bookings_for_lesson(self, lesson_id):
        with self._get_session() as db:
            prenotazioni = db.query(Booking).filter_by(lesson_id=lesson_id).join(Member).order_by(Member.first_name).all()
            return [{"id": p.id, "nome_comp": f"{p.member.first_name} {p.member.last_name}"} for p in prenotazioni]

    def search_for_booking(self, lesson_id, activity_id, term=""):
        with self._get_session() as db:
            if term:
                soci = db.query(Member).filter(
                    (Member.first_name.ilike(f"%{term}%")) |
                    (Member.last_name.ilike(f"%{term}%")) |
                    (Member.badge_number.ilike(f"%{term}%"))
                ).order_by(Member.first_name).limit(30).all()
                return [{"id": s.id, "first_name": s.first_name, "last_name": s.last_name, "badge_number": s.badge_number, "is_abituale": False} for s in soci]
            
            # Suggeriti
            soci_suggeriti = db.query(Member).join(Booking).join(Lesson).filter(Lesson.activity_id == activity_id).group_by(Member.id).order_by(func.count(Booking.id).desc()).limit(15).all()
            result = [{"id": s.id, "first_name": s.first_name, "last_name": s.last_name, "badge_number": s.badge_number, "is_abituale": True} for s in soci_suggeriti]
            
            if len(result) < 30:
                suggeriti_ids = [s["id"] for s in result]
                query_altri = db.query(Member)
                if suggeriti_ids: query_altri = query_altri.filter(~Member.id.in_(suggeriti_ids))
                altri = query_altri.order_by(Member.first_name).limit(30 - len(result)).all()
                result.extend([{"id": s.id, "first_name": s.first_name, "last_name": s.last_name, "badge_number": s.badge_number, "is_abituale": False} for s in altri])
            return result

    def make_booking(self, member_id, lesson_id, force_overbooking=False):
        with self._get_session() as db:
            esistente = db.query(Booking).filter_by(member_id=member_id, lesson_id=lesson_id).first()
            if esistente: return False, "Il socio è già prenotato per questo corso!"
            
            lezione = db.query(Lesson).get(lesson_id)
            occupati = db.query(Booking).filter_by(lesson_id=lesson_id).count()
            
            if occupati >= lezione.total_seats and not force_overbooking:
                return False, "OVERBOOKING_PROMPT"
                
            db.add(Booking(member_id=member_id, lesson_id=lesson_id))
            db.commit()
            return True, "Prenotazione effettuata."

    def remove(self, booking_id):
        with self._get_session() as db:
            b = db.query(Booking).get(booking_id)
            if b:
                db.delete(b)
                db.commit()
