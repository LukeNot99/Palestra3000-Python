"""Dashboard repository for managing dashboard statistics."""

from typing import Dict, Any, List
from datetime import datetime, timedelta, date
from sqlalchemy.orm import Session
from core.database import Member, Lesson
from core.repositories.base import BaseRepository
from core.repositories.lesson_repository import LessonRepository
from core.utils import parse_date


class DashboardRepository(BaseRepository[Member]):
    """Repository per la gestione delle statistiche dashboard."""
    
    def __init__(self, db: Session, lesson_repository: LessonRepository):
        super().__init__(db, Member)
        self.lesson_repository = lesson_repository
    
    def get_dashboard_stats(self) -> Dict[str, Any]:
        """Ottiene le statistiche per la dashboard."""
        now_dt = datetime.now()
        now_str = now_dt.strftime("%Y-%m-%d")
        
        date_today = now_dt.date()
        date_tomorrow = date_today + timedelta(days=1)
        date_after = date_today + timedelta(days=2)
        target_dates = [date_today, date_tomorrow, date_after]
        
        all_members = self.db.query(Member).all()
        active_members_count = 0
        expiring_list: List[Dict[str, Any]] = []
        
        for m in all_members:
            exp_sub = parse_date(m.membership_expiration)
            if exp_sub:
                if exp_sub.date() in target_dates:
                    expiring_list.append({
                        "id": m.id, 
                        "full_name": f"{m.first_name} {m.last_name}", 
                        "badge": m.badge_number, 
                        "exp_date": exp_sub.date()
                    })
                    
            if not m.tier:
                continue
            if not exp_sub or now_dt > exp_sub:
                continue
            
            exp_enr = parse_date(m.enrollment_expiration)
            if not exp_enr or now_dt > exp_enr:
                continue
            active_members_count += 1
        
        expiring_list.sort(key=lambda x: x["exp_date"])
        
        lessons_count = self.db.query(Lesson).filter(Lesson.date == now_str).count()
        lessons_today = self.lesson_repository.get_daily_lessons_with_bookings(date_today)
        
        return {
            "active_members": active_members_count,
            "lessons_count": lessons_count,
            "expiring_count": len(expiring_list),
            "lessons_today": lessons_today,
            "expiring_list": expiring_list,
            "date_today": date_today,
            "date_tomorrow": date_tomorrow
        }
