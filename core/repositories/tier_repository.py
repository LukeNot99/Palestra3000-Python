"""Tier repository for managing tier data."""

from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from core.database import Tier, Member
from core.repositories.base import BaseRepository


class TierRepository(BaseRepository[Tier]):
    """Repository per la gestione dei Tier."""
    
    def __init__(self, db: Session):
        super().__init__(db, Tier)
    
    def get_all(self) -> List[Dict[str, Any]]:
        """Ottiene tutti i tier formattati come dizionari."""
        tiers = self.db.query(Tier).all()
        return [{
            "id": t.id, "name": t.name, "cost": t.cost, 
            "start_time": t.start_time, "end_time": t.end_time,
            "min_age": t.min_age, "max_age": t.max_age,
            "max_entries": t.max_entries, "duration_months": t.duration_months
        } for t in tiers]
    
    def get_by_id(self, tier_id: int) -> Optional[Dict[str, Any]]:
        """Ottiene un tier per ID formattato come dizionario."""
        t = self.db.get(Tier, tier_id)
        if not t:
            return None
        return {
            "id": t.id, "name": t.name, "cost": t.cost, 
            "start_time": t.start_time, "end_time": t.end_time,
            "min_age": t.min_age, "max_age": t.max_age,
            "max_entries": t.max_entries, "duration_months": t.duration_months
        }
    
    def save(self, data: Dict[str, Any], tier_id: Optional[int] = None) -> None:
        """Salva un tier (insert o update)."""
        if tier_id:
            t = self.db.get(Tier, tier_id)
            if t:
                for key, value in data.items(): 
                    setattr(t, key, value)
        else:
            t = Tier(**data)
            self.db.add(t)
        self.db.commit()
    
    def count_linked_members(self, tier_id: int) -> int:
        """Conta il numero di membri collegati a un tier."""
        return self.db.query(Member).filter(Member.tier_id == tier_id).count()
