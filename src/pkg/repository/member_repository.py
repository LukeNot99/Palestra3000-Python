from sqlalchemy import func
from src.pkg.models import Member, Tier
from src.pkg.utility.utils import parse_date
from src.pkg.repository.base_repository import BaseRepository

class MemberRepository(BaseRepository):

    def get_unique_cities_and_birthplaces(self):
        with self._get_session() as db:
            cities = sorted(list(set([m.city for m in db.query(Member.city).filter(Member.city != None).all()])))
            places = sorted(list(set([m.birth_place for m in db.query(Member.birth_place).filter(Member.birth_place != None).all()])))
            return cities, places

    def get_by_id(self, member_id):
        with self._get_session() as db:
            m = db.query(Member).filter(Member.id == member_id).first()
            if not m: return None
            return {
                "id": m.id, "badge_number": m.badge_number, "first_name": m.first_name,
                "last_name": m.last_name, "codice_fiscale": m.codice_fiscale,
                "birth_date": m.birth_date, "birth_place": m.birth_place, "city": m.city,
                "address": m.address, "phone": m.phone, "email": m.email, "other_contact": m.other_contact,
                "gender": m.gender, "enrollment_expiration": m.enrollment_expiration,
                "membership_start": m.membership_start, "membership_expiration": m.membership_expiration,
                "has_medical_certificate": m.has_medical_certificate, "certificate_expiration": m.certificate_expiration,
                "tier_name": m.tier.name if m.tier else None, "tier_cost": m.tier.cost if m.tier else 0.0,
                "entries_used": m.entries_used
            }

    def search(self, badge="", tier="Tutte", name="", surname="", phone="", limit=50, offset=0):
        with self._get_session() as db:
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

    def check_badge_exists(self, badge, exclude_id=None):
        with self._get_session() as db:
            q = db.query(Member).filter(Member.badge_number == badge)
            if exclude_id: q = q.filter(Member.id != exclude_id)
            return q.first() is not None

    def save(self, data, member_id=None):
        with self._get_session() as db:
            if member_id:
                m = db.query(Member).filter(Member.id == member_id).first()
                if m:
                    for key, value in data.items(): setattr(m, key, value)
            else:
                m = Member(**data)
                db.add(m)
            db.commit()
            return m.id

    def delete(self, member_id):
        with self._get_session() as db:
            m = db.query(Member).filter(Member.id == member_id).first()
            if m:
                db.delete(m)
                db.commit()

    def get_member_for_access(self, badge_number):
        """
        Cerca un socio per il controllo accessi.
        Il badge_number passato sono le ultime 4 cifre estratte dal badge completo.
        Nel database, i badge possono essere memorizzati solo con le ultime 4 cifre.
        """
        with self._get_session() as db:
            # Cerco il socio usando solo le ultime 4 cifre (come memorizzato nel DB)
            m = db.query(Member).filter(Member.badge_number == badge_number).first()
            if not m: return None
            return {
                "id": m.id,
                "first_name": m.first_name,
                "last_name": m.last_name,
                "email": m.email,
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
        with self._get_session() as db:
            m = db.query(Member).filter(Member.id == member_id).first()
            if m:
                m.entries_used = (m.entries_used or 0) + 1
                db.commit()
                return m.entries_used
            return 0

    def get_member_by_name(self, first_name, last_name):
        with self._get_session() as db:
            m = db.query(Member).filter(
                func.lower(Member.first_name) == func.lower(first_name),
                func.lower(Member.last_name) == func.lower(last_name)
            ).first()
            return m
