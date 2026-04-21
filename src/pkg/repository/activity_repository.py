from contextlib import contextmanager
from src.pkg.models.models import Activity, Lesson, Booking

class ActivityRepository:
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

    def get_all(self):
        with self._get_session() as db:
            activities = db.query(Activity).order_by(Activity.name).all()
            return [{"id": a.id, "name": a.name} for a in activities]

    def get_by_name(self, name):
        with self._get_session() as db:
            a = db.query(Activity).filter(Activity.name == name).first()
            return {"id": a.id, "name": a.name} if a else None

    def check_exists(self, name):
        with self._get_session() as db:
            return db.query(Activity).filter(Activity.name.ilike(name)).first() is not None

    def save(self, name):
        with self._get_session() as db:
            db.add(Activity(name=name))
            db.commit()

    def get_linked_lessons_count(self, activity_id):
        with self._get_session() as db:
            return db.query(Lesson).filter(Lesson.activity_id == activity_id).count()

    def delete(self, activity_id, force_cascade=False):
        with self._get_session() as db:
            a = db.query(Activity).filter(Activity.id == activity_id).first()
            if not a: return False
            if force_cascade:
                lezioni = db.query(Lesson).filter(Lesson.activity_id == activity_id).all()
                for lez in lezioni:
                    db.query(Booking).filter(Booking.lesson_id == lez.id).delete()
                db.query(Lesson).filter(Lesson.activity_id == activity_id).delete()
            db.delete(a)
            db.commit()
            return True
