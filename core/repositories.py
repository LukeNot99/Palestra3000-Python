from sqlalchemy import func, select
from datetime import datetime, date, timedelta
from core.database import SessionLocal, Tier, Activity, Lesson, Booking, Member
from core.utils import parse_date


def get_db():
    """Factory function per ottenere una nuova sessione database."""
    return SessionLocal()


class TierRepository:
    def __init__(self, db):
        """Inizializza il repository con una sessione database."""
        self.db = db

    def get_all(self):
        tiers = self.db.execute(select(Tier)).scalars().all()
        return [{
            "id": t.id, "name": t.name, "cost": t.cost, 
            "start_time": t.start_time, "end_time": t.end_time,
            "min_age": t.min_age, "max_age": t.max_age,
            "max_entries": t.max_entries, "duration_months": t.duration_months
        } for t in tiers]

    def get_by_id(self, tier_id):
        t = self.db.get(Tier, tier_id)
        if not t: return None
        return {
            "id": t.id, "name": t.name, "cost": t.cost, 
            "start_time": t.start_time, "end_time": t.end_time,
            "min_age": t.min_age, "max_age": t.max_age,
            "max_entries": t.max_entries, "duration_months": t.duration_months
        }

    def save(self, data, tier_id=None):
        if tier_id:
            t = self.db.get(Tier, tier_id)
            if t:
                for key, value in data.items(): 
                    setattr(t, key, value)
        else:
            t = Tier(**data)
            self.db.add(t)
        self.db.commit()

    def delete(self, tier_id):
        t = self.db.get(Tier, tier_id)
        if t:
            self.db.delete(t)
            self.db.commit()

    def count_linked_members(self, tier_id):
        return self.db.query(Member).filter(Member.tier_id == tier_id).count()


class ActivityRepository:
    def __init__(self, db):
        """Inizializza il repository con una sessione database."""
        self.db = db

    def get_all(self):
        activities = self.db.query(Activity).order_by(Activity.name).all()
        return [{"id": a.id, "name": a.name} for a in activities]

    def get_by_name(self, name):
        a = self.db.query(Activity).filter(Activity.name == name).first()
        return {"id": a.id, "name": a.name} if a else None

    def check_exists(self, name):
        return self.db.query(Activity).filter(Activity.name.ilike(name)).first() is not None

    def save(self, name):
        self.db.add(Activity(name=name))
        self.db.commit()

    def get_linked_lessons_count(self, activity_id):
        return self.db.query(Lesson).filter(Lesson.activity_id == activity_id).count()

    def delete(self, activity_id, force_cascade=False):
        a = self.db.query(Activity).filter(Activity.id == activity_id).first()
        if not a: return False
        if force_cascade:
            lezioni = self.db.query(Lesson).filter(Lesson.activity_id == activity_id).all()
            for lez in lezioni:
                self.db.query(Booking).filter(Booking.lesson_id == lez.id).delete()
            self.db.query(Lesson).filter(Lesson.activity_id == activity_id).delete()
        self.db.delete(a)
        self.db.commit()
        return True


class MemberRepository:
    def __init__(self, db):
        """Inizializza il repository con una sessione database."""
        self.db = db

    def get_unique_cities_and_birthplaces(self):
        cities = sorted(list(set([m.city for m in self.db.query(Member.city).filter(Member.city != None).all()])))
        places = sorted(list(set([m.birth_place for m in self.db.query(Member.birth_place).filter(Member.birth_place != None).all()])))
        return cities, places

    def get_by_id(self, member_id):
        m = self.db.query(Member).filter(Member.id == member_id).first()
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

    def search(self, badge="", tier="Tutte", name="", surname="", phone="", limit=50, offset=0):
        query = self.db.query(Member)
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

    def check_badge_exists(self, badge, exclude_id=None):
        q = self.db.query(Member).filter(Member.badge_number == badge)
        if exclude_id: q = q.filter(Member.id != exclude_id)
        return q.first() is not None

    def save(self, data, member_id=None):
        if member_id:
            m = self.db.query(Member).filter(Member.id == member_id).first()
            if m:
                for key, value in data.items(): setattr(m, key, value)
        else:
            m = Member(**data)
            self.db.add(m)
        self.db.commit()
        return m.id

    def delete(self, member_id):
        m = self.db.query(Member).filter(Member.id == member_id).first()
        if m:
            self.db.delete(m)
            self.db.commit()

    # --- METODI NUOVI PER IL TORNELLO ---
    def get_member_for_access(self, badge_number):
        m = self.db.query(Member).filter(Member.badge_number == badge_number).first()
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

    def increment_entries(self, member_id):
        m = self.db.query(Member).filter(Member.id == member_id).first()
        if m:
            m.entries_used = (m.entries_used or 0) + 1
            self.db.commit()
            return m.entries_used
        return 0


class LessonRepository:
    def __init__(self, db):
        """Inizializza il repository con una sessione database."""
        self.db = db

    def get_by_month_and_activity(self, activity_id, year, month):
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

    def get_daily_lessons_with_bookings(self, date_obj):
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

    def get_lesson_details(self, lesson_id):
        l = self.db.get(Lesson, lesson_id)
        if not l: return None
        return {
            "id": l.id, "activity_name": l.activity.name,
            "start_time": l.start_time[:5], "end_time": l.end_time[:5],
            "total_seats": l.total_seats, "activity_id": l.activity_id
        }

    def generate_batch(self, activity_id, start_date, end_date, start_time, end_time, seats, days_selected):
        g_nomi = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]
        count = 0
        current_date = start_date
        while current_date <= end_date:
            if current_date.weekday() in days_selected:
                ds = current_date.strftime("%Y-%m-%d")
                esiste = self.db.query(Lesson).filter(Lesson.date == ds, Lesson.start_time == start_time, Lesson.activity_id == activity_id).first()
                if not esiste:
                    self.db.add(Lesson(date=ds, day_of_week=g_nomi[current_date.weekday()], start_time=start_time, end_time=end_time, total_seats=seats, activity_id=activity_id))
                    count += 1
            current_date += timedelta(days=1)
        self.db.commit()
        return count

    def delete_multiple(self, lesson_ids):
        for l_id in lesson_ids:
            l = self.db.query(Lesson).filter(Lesson.id == l_id).first()
            if l: self.db.delete(l)
        self.db.commit()


class BookingRepository:
    def __init__(self, db):
        """Inizializza il repository con una sessione database."""
        self.db = db

    def get_bookings_for_lesson(self, lesson_id):
        prenotazioni = self.db.query(Booking).filter_by(lesson_id=lesson_id).join(Member).order_by(Member.first_name).all()
        return [{"id": p.id, "nome_comp": f"{p.member.first_name} {p.member.last_name}"} for p in prenotazioni]

    def search_for_booking(self, lesson_id, activity_id, term=""):
        if term:
            soci = self.db.query(Member).filter(
                (Member.first_name.ilike(f"%{term}%")) |
                (Member.last_name.ilike(f"%{term}%")) |
                (Member.badge_number.ilike(f"%{term}%"))
            ).order_by(Member.first_name).limit(30).all()
            return [{"id": s.id, "first_name": s.first_name, "last_name": s.last_name, "badge_number": s.badge_number, "is_abituale": False} for s in soci]
        
        # Suggeriti
        soci_suggeriti = self.db.query(Member).join(Booking).join(Lesson).filter(Lesson.activity_id == activity_id).group_by(Member.id).order_by(func.count(Booking.id).desc()).limit(15).all()
        result = [{"id": s.id, "first_name": s.first_name, "last_name": s.last_name, "badge_number": s.badge_number, "is_abituale": True} for s in soci_suggeriti]
        
        if len(result) < 30:
            suggeriti_ids = [s["id"] for s in result]
            query_altri = self.db.query(Member)
            if suggeriti_ids: query_altri = query_altri.filter(~Member.id.in_(suggeriti_ids))
            altri = query_altri.order_by(Member.first_name).limit(30 - len(result)).all()
            result.extend([{"id": s.id, "first_name": s.first_name, "last_name": s.last_name, "badge_number": s.badge_number, "is_abituale": False} for s in altri])
        return result

    def make_booking(self, member_id, lesson_id, force_overbooking=False):
        esistente = self.db.query(Booking).filter_by(member_id=member_id, lesson_id=lesson_id).first()
        if esistente: return False, "Il socio è già prenotato per questo corso!"
        
        lezione = self.db.get(Lesson, lesson_id)
        occupati = self.db.query(Booking).filter_by(lesson_id=lesson_id).count()
        
        if occupati >= lezione.total_seats and not force_overbooking:
            return False, "OVERBOOKING_PROMPT"
            
        self.db.add(Booking(member_id=member_id, lesson_id=lesson_id))
        self.db.commit()
        return True, "Prenotazione effettuata."

    def remove(self, booking_id):
        b = self.db.get(Booking, booking_id)
        if b:
            self.db.delete(b)
            self.db.commit()


class DashboardRepository:
    def __init__(self, db):
        """Inizializza il repository con una sessione database."""
        self.db = db

    def get_dashboard_stats(self):
        now_dt = datetime.now()
        now_str = now_dt.strftime("%Y-%m-%d")
        
        date_today = now_dt.date()
        date_tomorrow = date_today + timedelta(days=1)
        date_after = date_today + timedelta(days=2)
        target_dates = [date_today, date_tomorrow, date_after]
        
        all_members = self.db.query(Member).all()
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
        
        lessons_count = self.db.query(Lesson).filter(Lesson.date == now_str).count()
        lesson_repo = LessonRepository(self.db)
        lessons_today = lesson_repo.get_daily_lessons_with_bookings(date_today)
        
        return {
            "active_members": active_members_count,
            "lessons_count": lessons_count,
            "expiring_count": len(expiring_list),
            "lessons_today": lessons_today,
            "expiring_list": expiring_list,
            "date_today": date_today,
            "date_tomorrow": date_tomorrow
        }
            }