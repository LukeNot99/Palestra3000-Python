from sqlalchemy import func
from datetime import datetime, date, timedelta
from core.database import SessionLocal, Tier, Activity, Lesson, Booking, Member
from core.utils import parse_date

class TierRepository:
    @staticmethod
    def get_all():
        db = SessionLocal()
        try:
            tiers = db.query(Tier).all()
            return [{
                "id": t.id, "name": t.name, "cost": t.cost, 
                "start_time": t.start_time, "end_time": t.end_time,
                "min_age": t.min_age, "max_age": t.max_age,
                "max_entries": t.max_entries, "duration_months": t.duration_months
            } for t in tiers]
        finally:
            db.close()

    @staticmethod
    def get_by_id(tier_id):
        db = SessionLocal()
        try:
            t = db.query(Tier).filter(Tier.id == tier_id).first()
            if not t: return None
            return {
                "id": t.id, "name": t.name, "cost": t.cost, 
                "start_time": t.start_time, "end_time": t.end_time,
                "min_age": t.min_age, "max_age": t.max_age,
                "max_entries": t.max_entries, "duration_months": t.duration_months
            }
        finally:
            db.close()

    @staticmethod
    def save(data, tier_id=None):
        db = SessionLocal()
        try:
            if tier_id:
                t = db.query(Tier).filter(Tier.id == tier_id).first()
                if t:
                    for key, value in data.items(): setattr(t, key, value)
            else:
                t = Tier(**data)
                db.add(t)
            db.commit()
        finally:
            db.close()

    @staticmethod
    def delete(tier_id):
        db = SessionLocal()
        try:
            t = db.query(Tier).filter(Tier.id == tier_id).first()
            if t:
                db.delete(t)
                db.commit()
        finally:
            db.close()

    @staticmethod
    def count_linked_members(tier_id):
        db = SessionLocal()
        try:
            return db.query(Member).filter(Member.tier_id == tier_id).count()
        finally:
            db.close()

class ActivityRepository:
    @staticmethod
    def get_all():
        db = SessionLocal()
        try:
            activities = db.query(Activity).order_by(Activity.name).all()
            return [{"id": a.id, "name": a.name} for a in activities]
        finally:
            db.close()

    @staticmethod
    def get_by_name(name):
        db = SessionLocal()
        try:
            a = db.query(Activity).filter(Activity.name == name).first()
            return {"id": a.id, "name": a.name} if a else None
        finally:
            db.close()

    @staticmethod
    def check_exists(name):
        db = SessionLocal()
        try:
            return db.query(Activity).filter(Activity.name.ilike(name)).first() is not None
        finally:
            db.close()

    @staticmethod
    def save(name):
        db = SessionLocal()
        try:
            db.add(Activity(name=name))
            db.commit()
        finally:
            db.close()

    @staticmethod
    def get_linked_lessons_count(activity_id):
        db = SessionLocal()
        try:
            return db.query(Lesson).filter(Lesson.activity_id == activity_id).count()
        finally:
            db.close()

    @staticmethod
    def delete(activity_id, force_cascade=False):
        db = SessionLocal()
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

class MemberRepository:
    @staticmethod
    def get_unique_cities_and_birthplaces():
        db = SessionLocal()
        try:
            cities = sorted(list(set([m.city for m in db.query(Member.city).filter(Member.city != None).all()])))
            places = sorted(list(set([m.birth_place for m in db.query(Member.birth_place).filter(Member.birth_place != None).all()])))
            return cities, places
        finally:
            db.close()

    @staticmethod
    def get_by_id(member_id):
        db = SessionLocal()
        try:
            m = db.query(Member).filter(Member.id == member_id).first()
            if not m: return None
            return {
                "id": m.id, "badge_number": m.badge_number, "first_name": m.first_name,
                "last_name": m.last_name, "codice_fiscale": m.codice_fiscale,
                "birth_date": m.birth_date, "birth_place": m.birth_place, "city": m.city,
                "address": m.address, "phone": m.phone, "other_contact": m.other_contact,
                "gender": m.gender, "enrollment_expiration": m.enrollment_expiration,
                "membership_start": m.membership_start, "membership_expiration": m.membership_expiration,
                "has_medical_certificate": m.has_medical_certificate, "certificate_expiration": m.certificate_expiration,
                "tier_name": m.tier.name if m.tier else None, "tier_cost": m.tier.cost if m.tier else 0.0,
                "entries_used": m.entries_used
            }
        finally:
            db.close()

    @staticmethod
    def search(badge="", tier="Tutte", name="", surname="", phone="", limit=50, offset=0):
        db = SessionLocal()
        try:
            query = db.query(Member)
            if badge: query = query.filter(Member.badge_number.ilike(f"%{badge}%"))
            if tier != "Tutte": query = query.join(Tier).filter(Tier.name == tier)
            if name: query = query.filter(Member.first_name.ilike(f"%{name}%"))
            if surname: query = query.filter(Member.last_name.ilike(f"%{surname}%"))
            if phone: query = query.filter(Member.phone.ilike(f"%{phone}%"))

            total_count = query.count()
            members_db = query.order_by(Member.first_name, Member.last_name).offset(offset).limit(limit).all()
            
            data = []
            for m in members_db:
                data.append({
                    "id": m.id, "scheda": m.badge_number if m.badge_number else "-",
                    "nome": m.first_name, "cognome": m.last_name,
                    "fascia": m.tier.name if m.tier else "Nessuna",
                    "scad_abb": m.membership_expiration if m.membership_expiration else "N/D",
                    "scad_iscr": m.enrollment_expiration if m.enrollment_expiration else "N/D"
                })
            return data, total_count
        finally:
            db.close()

    @staticmethod
    def check_badge_exists(badge, exclude_id=None):
        db = SessionLocal()
        try:
            q = db.query(Member).filter(Member.badge_number == badge)
            if exclude_id: q = q.filter(Member.id != exclude_id)
            return q.first() is not None
        finally:
            db.close()

    @staticmethod
    def save(data, member_id=None):
        db = SessionLocal()
        try:
            if member_id:
                m = db.query(Member).filter(Member.id == member_id).first()
                if m:
                    for key, value in data.items(): setattr(m, key, value)
            else:
                m = Member(**data)
                db.add(m)
            db.commit()
            return m.id
        finally:
            db.close()

    @staticmethod
    def delete(member_id):
        db = SessionLocal()
        try:
            m = db.query(Member).filter(Member.id == member_id).first()
            if m:
                db.delete(m)
                db.commit()
        finally:
            db.close()

    # --- METODI NUOVI PER IL TORNELLO ---
    @staticmethod
    def get_member_for_access(badge_number):
        db = SessionLocal()
        try:
            m = db.query(Member).filter(Member.badge_number == badge_number).first()
            if not m: return None
            return {
                "id": m.id,
                "first_name": m.first_name,
                "last_name": m.last_name,
                "gender": m.gender,
                "has_medical_certificate": m.has_medical_certificate,
                "certificate_expiration": m.certificate_expiration,
                "enrollment_expiration": m.enrollment_expiration,
                "membership_expiration": m.membership_expiration,
                "entries_used": m.entries_used,
                "tier_name": m.tier.name if m.tier else None,
                "tier_max_entries": m.tier.max_entries if m.tier else 0,
                "tier_start_time": m.tier.start_time if m.tier else "00:00",
                "tier_end_time": m.tier.end_time if m.tier else "23:59"
            }
        finally:
            db.close()

    @staticmethod
    def increment_entries(member_id):
        db = SessionLocal()
        try:
            m = db.query(Member).filter(Member.id == member_id).first()
            if m:
                m.entries_used = (m.entries_used or 0) + 1
                db.commit()
                return m.entries_used
            return 0
        finally:
            db.close()

class LessonRepository:
    @staticmethod
    def get_by_month_and_activity(activity_id, year, month):
        db = SessionLocal()
        try:
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
        finally:
            db.close()

    @staticmethod
    def get_daily_lessons_with_bookings(date_obj):
        db = SessionLocal()
        try:
            data_str = date_obj.strftime("%Y-%m-%d")
            lezioni = db.query(Lesson).filter(Lesson.date == data_str).order_by(Lesson.start_time).all()
            result = []
            for l in lezioni:
                occupati = db.query(Booking).filter_by(lesson_id=l.id).count()
                result.append({
                    "id": l.id, "start_time": l.start_time[:5], "end_time": l.end_time[:5],
                    "activity_name": l.activity.name if l.activity else "Attività",
                    "total_seats": l.total_seats, "occupati": occupati
                })
            return result
        finally:
            db.close()

    @staticmethod
    def get_lesson_details(lesson_id):
        db = SessionLocal()
        try:
            l = db.query(Lesson).get(lesson_id)
            if not l: return None
            return {
                "id": l.id, "activity_name": l.activity.name,
                "start_time": l.start_time[:5], "end_time": l.end_time[:5],
                "total_seats": l.total_seats, "activity_id": l.activity_id
            }
        finally:
            db.close()

    @staticmethod
    def generate_batch(activity_id, start_date, end_date, start_time, end_time, seats, days_selected):
        g_nomi = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]
        count = 0
        db = SessionLocal()
        try:
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
        finally:
            db.close()

    @staticmethod
    def delete_multiple(lesson_ids):
        db = SessionLocal()
        try:
            for l_id in lesson_ids:
                l = db.query(Lesson).filter(Lesson.id == l_id).first()
                if l: db.delete(l)
            db.commit()
        finally:
            db.close()

class BookingRepository:
    @staticmethod
    def get_bookings_for_lesson(lesson_id):
        db = SessionLocal()
        try:
            prenotazioni = db.query(Booking).filter_by(lesson_id=lesson_id).join(Member).order_by(Member.first_name).all()
            return [{"id": p.id, "nome_comp": f"{p.member.first_name} {p.member.last_name}"} for p in prenotazioni]
        finally:
            db.close()

    @staticmethod
    def search_for_booking(lesson_id, activity_id, term=""):
        db = SessionLocal()
        try:
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
        finally:
            db.close()

    @staticmethod
    def make_booking(member_id, lesson_id, force_overbooking=False):
        db = SessionLocal()
        try:
            esistente = db.query(Booking).filter_by(member_id=member_id, lesson_id=lesson_id).first()
            if esistente: return False, "Il socio è già prenotato per questo corso!"
            
            lezione = db.query(Lesson).get(lesson_id)
            occupati = db.query(Booking).filter_by(lesson_id=lesson_id).count()
            
            if occupati >= lezione.total_seats and not force_overbooking:
                return False, "OVERBOOKING_PROMPT"
                
            db.add(Booking(member_id=member_id, lesson_id=lesson_id))
            db.commit()
            return True, "Prenotazione effettuata."
        finally:
            db.close()

    @staticmethod
    def remove(booking_id):
        db = SessionLocal()
        try:
            b = db.query(Booking).get(booking_id)
            if b:
                db.delete(b)
                db.commit()
        finally:
            db.close()

class DashboardRepository:
    @staticmethod
    def get_dashboard_stats():
        db = SessionLocal()
        try:
            now_dt = datetime.now()
            now_str = now_dt.strftime("%Y-%m-%d")
            
            date_today = now_dt.date()
            date_tomorrow = date_today + timedelta(days=1)
            date_after = date_today + timedelta(days=2)
            target_dates = [date_today, date_tomorrow, date_after]
            
            all_members = db.query(Member).all()
            active_members_count = 0
            expiring_list = []
            
            for m in all_members:
                exp_sub = parse_date(m.membership_expiration)
                if exp_sub:
                    if exp_sub.date() in target_dates:
                        expiring_list.append({"id": m.id, "full_name": f"{m.first_name} {m.last_name}", "badge": m.badge_number, "exp_date": exp_sub.date()})
                        
                if not m.tier: continue
                if not exp_sub or now_dt > exp_sub: continue
                
                exp_enr = parse_date(m.enrollment_expiration)
                if not exp_enr or now_dt > exp_enr: continue
                active_members_count += 1

            expiring_list.sort(key=lambda x: x["exp_date"])
            
            lessons_count = db.query(Lesson).filter(Lesson.date == now_str).count()
            lessons_today = LessonRepository.get_daily_lessons_with_bookings(date_today)
            
            return {
                "active_members": active_members_count,
                "lessons_count": lessons_count,
                "expiring_count": len(expiring_list),
                "lessons_today": lessons_today,
                "expiring_list": expiring_list,
                "date_today": date_today,
                "date_tomorrow": date_tomorrow
            }
        finally:
            db.close()