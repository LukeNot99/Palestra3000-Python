from src.pkg.models.models import Activity, Lesson, Booking

class ActivityRepository:
    def __init__(self, session_factory):
        self.session_factory = session_factory

    def get_all(self):
        db = self.session_factory()
        try:
            activities = db.query(Activity).order_by(Activity.name).all()
            return [{"id": a.id, "name": a.name} for a in activities]
        finally:
            db.close()

    def get_by_name(self, name):
        db = self.session_factory()
        try:
            a = db.query(Activity).filter(Activity.name == name).first()
            return {"id": a.id, "name": a.name} if a else None
        finally:
            db.close()

    def check_exists(self, name):
        db = self.session_factory()
        try:
            return db.query(Activity).filter(Activity.name.ilike(name)).first() is not None
        finally:
            db.close()

    def save(self, name):
        db = self.session_factory()
        try:
            db.add(Activity(name=name))
            db.commit()
        finally:
            db.close()

    def get_linked_lessons_count(self, activity_id):
        db = self.session_factory()
        try:
            return db.query(Lesson).filter(Lesson.activity_id == activity_id).count()
        finally:
            db.close()

    def delete(self, activity_id, force_cascade=False):
        db = self.session_factory()
        try:
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
        finally:
            db.close()
