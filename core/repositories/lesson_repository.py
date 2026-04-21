"""Lesson repository for managing lesson data."""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta, date
from sqlalchemy.orm import Session
from core.models import Lesson, Booking, Activity
from core.repositories.base import BaseRepository


class LessonRepository(BaseRepository[Lesson]):
    """Repository per la gestione delle Lesson."""
    
    def __init__(self, db: Session):
        super().__init__(db, Lesson)
    
    def get_by_month_and_activity(self, activity_id: int, year: int, month: int) -> List[Dict[str, Any]]:
        """Ottiene le lezioni di un'attività per mese."""
        filtro_data = f"{year}-{month:02d}-"
        lezioni = self.db.query(Lesson).filter(
            Lesson.activity_id == activity_id,
            Lesson.date.like(f"{filtro_data}%")
        ).order_by(Lesson.date, Lesson.start_time).all()
        return [{
            "id": l.id, "data": datetime.strptime(l.date, "%Y-%m-%d").strftime("%d/%m/%Y") if l.date else "-",
            "giorno": l.day_of_week, "orario": f"{l.start_time} - {l.end_time}",
            "posti": str(l.total_seats)
        } for l in lezioni]
    
    def get_daily_lessons_with_bookings(self, date_obj: date) -> List[Dict[str, Any]]:
        """Ottiene le lezioni di un giorno con i booking associati."""
        data_str = date_obj.strftime("%Y-%m-%d")
        lezioni = self.db.query(Lesson).filter(Lesson.date == data_str).order_by(Lesson.start_time).all()
        result = []
        for l in lezioni:
            occupati = self.db.query(Booking).filter_by(lesson_id=l.id).count()
            result.append({
                "id": l.id, "start_time": l.start_time[:5], "end_time": l.end_time[:5],
                "activity_name": l.activity.name if l.activity else "Attività",
                "total_seats": l.total_seats, "occupati": occupati
            })
        return result
    
    def get_lesson_details(self, lesson_id: int) -> Optional[Dict[str, Any]]:
        """Ottiene i dettagli di una lezione."""
        l = self.db.get(Lesson, lesson_id)
        if not l:
            return None
        return {
            "id": l.id, "activity_name": l.activity.name,
            "start_time": l.start_time[:5], "end_time": l.end_time[:5],
            "total_seats": l.total_seats, "activity_id": l.activity_id
        }
    
    def generate_batch(self, activity_id: int, start_date: date, end_date: date, 
                       start_time: str, end_time: str, seats: int, days_selected: List[int]) -> int:
        """Genera un batch di lezioni per un periodo."""
        g_nomi = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]
        count = 0
        current_date = start_date
        while current_date <= end_date:
            if current_date.weekday() in days_selected:
                ds = current_date.strftime("%Y-%m-%d")
                esiste = self.db.query(Lesson).filter(
                    Lesson.date == ds, 
                    Lesson.start_time == start_time, 
                    Lesson.activity_id == activity_id
                ).first()
                if not esiste:
                    self.db.add(Lesson(
                        date=ds, 
                        day_of_week=g_nomi[current_date.weekday()], 
                        start_time=start_time, 
                        end_time=end_time, 
                        total_seats=seats, 
                        activity_id=activity_id
                    ))
                    count += 1
            current_date += timedelta(days=1)
        self.db.commit()
        return count
    
    def delete_multiple(self, lesson_ids: List[int]) -> None:
        """Elimina multiple lezioni per ID."""
        for l_id in lesson_ids:
            l = self.db.query(Lesson).filter(Lesson.id == l_id).first()
            if l:
                self.db.delete(l)
        self.db.commit()
