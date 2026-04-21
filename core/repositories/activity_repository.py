"""Activity repository for managing activity data."""

from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from core.database import Activity, Lesson, Booking
from core.repositories.base import BaseRepository


class ActivityRepository(BaseRepository[Activity]):
    """Repository per la gestione delle Activity."""
    
    def __init__(self, db: Session):
        super().__init__(db, Activity)
    
    def get_all(self) -> List[Dict[str, Any]]:
        """Ottiene tutte le attività ordinate per nome."""
        activities = self.db.query(Activity).order_by(Activity.name).all()
        return [{"id": a.id, "name": a.name} for a in activities]
    
    def get_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Ottiene un'attività per nome."""
        a = self.db.query(Activity).filter(Activity.name == name).first()
        return {"id": a.id, "name": a.name} if a else None
    
    def check_exists(self, name: str) -> bool:
        """Verifica se esiste un'attività con il nome specificato."""
        return self.db.query(Activity).filter(Activity.name.ilike(name)).first() is not None
    
    def save(self, name: str) -> None:
        """Salva una nuova attività."""
        self.db.add(Activity(name=name))
        self.db.commit()
    
    def get_linked_lessons_count(self, activity_id: int) -> int:
        """Conta il numero di lezioni collegate a un'attività."""
        return self.db.query(Lesson).filter(Lesson.activity_id == activity_id).count()
    
    def delete(self, activity_id: int, force_cascade: bool = False) -> bool:
        """Elimina un'attività, opzionalmente con cascade sulle lezioni."""
        a = self.db.query(Activity).filter(Activity.id == activity_id).first()
        if not a:
            return False
        if force_cascade:
            lezioni = self.db.query(Lesson).filter(Lesson.activity_id == activity_id).all()
            for lez in lezioni:
                self.db.query(Booking).filter(Booking.lesson_id == lez.id).delete()
            self.db.query(Lesson).filter(Lesson.activity_id == activity_id).delete()
        self.db.delete(a)
        self.db.commit()
        return True
