from datetime import datetime, timedelta
from src.pkg.models import Lesson, Booking
from src.pkg.repository.base_repository import BaseRepository

class LessonRepository(BaseRepository):

    def get_by_month_and_activity(self, activity_id, year, month):
        with self._get_session() as db:
            filtro_data = f"{year}-{month:02d}-"
            lezioni = db.query(Lesson).filter(
                Lesson.activity_id == activity_id,
                Lesson.date.like(f"{filtro_data}%")
            ).order_by(Lesson.date, Lesson.start_time).all()
            return [{
                "id": l.id, "data": datetime.strptime(l.date, "%Y-%m-%d").strftime("%d/%m/%Y") if l.date else "-",
                "giorno": l.day_of_week, "orario": f"{l.start_time} - {l.end_time}",
                "posti": str(l.total_seats)
            } for l in lezioni]

    def get_daily_lessons_with_bookings(self, date_obj):
        with self._get_session() as db:
            data_str = date_obj.strftime("%Y-%m-%d")
            lezioni = db.query(Lesson).filter(Lesson.date == data_str).order_by(Lesson.start_time).all()
            result = []
            for l in lezioni:
                occupati = db.query(Booking).filter_by(lesson_id=l.id).count()
                result.append({
                    "id": l.id, "start_time": l.start_time[:5], "end_time": l.end_time[:5],
                    "activity_name": l.activity.name if l.activity else "Attività",
                    "total_seats": l.total_seats, "occupati": occupati,
                    "lesson_name": f"{l.activity.name if l.activity else 'Corso'} - {l.start_time[:5]}"
                })
            return result

    def get_lesson_details(self, lesson_id):
        with self._get_session() as db:
            l = db.query(Lesson).get(lesson_id)
            if not l: return None
            return {
                "id": l.id, "activity_name": l.activity.name,
                "start_time": l.start_time[:5], "end_time": l.end_time[:5],
                "total_seats": l.total_seats, "activity_id": l.activity_id
            }

    def generate_batch(self, activity_id, start_date, end_date, start_time, end_time, seats, days_selected):
        g_nomi = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]
        count = 0
        with self._get_session() as db:
            current_date = start_date
            while current_date <= end_date:
                if current_date.weekday() in days_selected:
                    ds = current_date.strftime("%Y-%m-%d")
                    esiste = db.query(Lesson).filter(Lesson.date == ds, Lesson.start_time == start_time, Lesson.activity_id == activity_id).first()
                    if not esiste:
                        db.add(Lesson(date=ds, day_of_week=g_nomi[current_date.weekday()], start_time=start_time, end_time=end_time, total_seats=seats, activity_id=activity_id))
                        count += 1
                current_date += timedelta(days=1)
            db.commit()
            return count

    def delete_multiple(self, lesson_ids):
        with self._get_session() as db:
            for l_id in lesson_ids:
                l = db.query(Lesson).filter(Lesson.id == l_id).first()
                if l: db.delete(l)
            db.commit()
