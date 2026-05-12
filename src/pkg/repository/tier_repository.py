from src.pkg.models import Tier, Member
from src.pkg.repository.base_repository import BaseRepository

class TierRepository(BaseRepository):

    def get_all(self):
        with self._get_session() as db:
            tiers = db.query(Tier).all()
            return [{
                "id": t.id, "name": t.name, "cost": t.cost, 
                "start_time": t.start_time, "end_time": t.end_time,
                "min_age": t.min_age, "max_age": t.max_age,
                "max_entries": t.max_entries, "duration_months": t.duration_months
            } for t in tiers]

    def get_by_id(self, tier_id):
        with self._get_session() as db:
            t = db.get(Tier, tier_id)
            if not t: return None
            return {
                "id": t.id, "name": t.name, "cost": t.cost, 
                "start_time": t.start_time, "end_time": t.end_time,
                "min_age": t.min_age, "max_age": t.max_age,
                "max_entries": t.max_entries, "duration_months": t.duration_months
            }

    def save(self, data, tier_id=None):
        with self._get_session() as db:
            if tier_id:
                t = db.get(Tier, tier_id)
                if t:
                    for key, value in data.items(): setattr(t, key, value)
            else:
                t = Tier(**data)
                db.add(t)
            db.commit()

    def delete(self, tier_id):
        with self._get_session() as db:
            t = db.get(Tier, tier_id)
            if t:
                db.delete(t)
                db.commit()

    def count_linked_members(self, tier_id):
        with self._get_session() as db:
            return db.query(Member).filter(Member.tier_id == tier_id).count()
