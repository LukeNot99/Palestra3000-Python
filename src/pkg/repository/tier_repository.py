from src.pkg.models.models import Tier, Member

class TierRepository:
    def __init__(self, session_factory):
        self.session_factory = session_factory

    def get_all(self):
        db = self.session_factory()
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

    def get_by_id(self, tier_id):
        db = self.session_factory()
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

    def save(self, data, tier_id=None):
        db = self.session_factory()
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

    def delete(self, tier_id):
        db = self.session_factory()
        try:
            t = db.query(Tier).filter(Tier.id == tier_id).first()
            if t:
                db.delete(t)
                db.commit()
        finally:
            db.close()

    def count_linked_members(self, tier_id):
        db = self.session_factory()
        try:
            return db.query(Member).filter(Member.tier_id == tier_id).count()
        finally:
            db.close()
