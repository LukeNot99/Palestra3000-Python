from sqlalchemy import func
from src.pkg.models.models import Member, Tier
from src.pkg.utility.utils import parse_date

class MemberRepository:
    def __init__(self, session_factory):
        self.session_factory = session_factory

    def get_unique_cities_and_birthplaces(self):
        db = self.session_factory()
        try:
            cities = sorted(list(set([m.city for m in db.query(Member.city).filter(Member.city != None).all()])))
            places = sorted(list(set([m.birth_place for m in db.query(Member.birth_place).filter(Member.birth_place != None).all()])))
            return cities, places
        finally:
            db.close()

    def get_by_id(self, member_id):
        db = self.session_factory()
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

    def search(self, badge="", tier="Tutte", name="", surname="", phone="", limit=50, offset=0):
        db = self.session_factory()
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

    def check_badge_exists(self, badge, exclude_id=None):
        db = self.session_factory()
        try:
            q = db.query(Member).filter(Member.badge_number == badge)
            if exclude_id: q = q.filter(Member.id != exclude_id)
            return q.first() is not None
        finally:
            db.close()

    def save(self, data, member_id=None):
        db = self.session_factory()
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

    def delete(self, member_id):
        db = self.session_factory()
        try:
            m = db.query(Member).filter(Member.id == member_id).first()
            if m:
                db.delete(m)
                db.commit()
        finally:
            db.close()

    def get_member_for_access(self, badge_number):
        db = self.session_factory()
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

    def increment_entries(self, member_id):
        db = self.session_factory()
        try:
            m = db.query(Member).filter(Member.id == member_id).first()
            if m:
                m.entries_used = (m.entries_used or 0) + 1
                db.commit()
                return m.entries_used
            return 0
        finally:
            db.close()
