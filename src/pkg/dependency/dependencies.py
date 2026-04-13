from src.pkg.config.db_config import DatabaseConfig
from src.pkg.repository.tier_repository import TierRepository
from src.pkg.repository.activity_repository import ActivityRepository
from src.pkg.repository.member_repository import MemberRepository
from src.pkg.repository.lesson_repository import LessonRepository
from src.pkg.repository.booking_repository import BookingRepository
from src.pkg.repository.dashboard_repository import DashboardRepository

class DependencyContainer:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DependencyContainer, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        self.db_config = DatabaseConfig()
        self.session_factory = self.db_config.get_session

        self.tier_repo = TierRepository(self.session_factory)
        self.activity_repo = ActivityRepository(self.session_factory)
        self.member_repo = MemberRepository(self.session_factory)
        self.lesson_repo = LessonRepository(self.session_factory)
        self.booking_repo = BookingRepository(self.session_factory)
        self.dashboard_repo = DashboardRepository(self.session_factory, self.lesson_repo)

    def get_session_factory(self):
        return self.session_factory

    def get_tier_repository(self) -> TierRepository:
        return self.tier_repo
    
    def get_activity_repository(self) -> ActivityRepository:
        return self.activity_repo
    
    def get_member_repository(self) -> MemberRepository:
        return self.member_repo

    def get_lesson_repository(self) -> LessonRepository:
        return self.lesson_repo

    def get_booking_repository(self) -> BookingRepository:
        return self.booking_repo

    def get_dashboard_repository(self) -> DashboardRepository:
        return self.dashboard_repo
