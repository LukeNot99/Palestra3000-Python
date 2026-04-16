import os
import sys

from src.pkg.config.app_config import ConfigManager
from src.pkg.config.db_config import DatabaseConfig

# Repositories
from src.pkg.repository.tier_repository import TierRepository
from src.pkg.repository.activity_repository import ActivityRepository
from src.pkg.repository.member_repository import MemberRepository
from src.pkg.repository.lesson_repository import LessonRepository
from src.pkg.repository.booking_repository import BookingRepository
from src.pkg.repository.dashboard_repository import DashboardRepository

# Services
from src.pkg.service.hardware_service import USBRelayTurnstile, SerialBadgeReader
from src.pkg.service.audio_service import SystemAudioPlayer
from src.pkg.service.access_service import (
    AccessManager, 
    MedicalCertificateRule, 
    EnrollmentRule, 
    SubscriptionRule, 
    TimeRule, 
    EntriesRule
)

class DependencyContainer:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DependencyContainer, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        # Database & Repositories
        self.db_config = DatabaseConfig()
        self.session_factory = self.db_config.get_session

        self.tier_repo = TierRepository(self.session_factory)
        self.activity_repo = ActivityRepository(self.session_factory)
        self.member_repo = MemberRepository(self.session_factory)
        self.lesson_repo = LessonRepository(self.session_factory)
        self.booking_repo = BookingRepository(self.session_factory)
        self.dashboard_repo = DashboardRepository(self.session_factory, self.lesson_repo)

    # --- Repository Getters ---
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

    # --- Service Getters ---
    def get_reader_hardware(self):
        porta_lettore = ConfigManager.get_setting("porta_lettore", "Nessun hardware")
        return SerialBadgeReader(porta_lettore)

    def get_access_manager(self, ui_callbacks) -> AccessManager:
        # Hardware Setup
        porta_rele = ConfigManager.get_setting("porta_rele", "Nessun hardware")
        turnstile = USBRelayTurnstile(porta_rele)
        
        # Determine Base Path for Audio 
        if getattr(sys, 'frozen', False):
            base_dir = os.path.dirname(sys.executable)
        else:
            # Navigate back from src/pkg/dependency/dependencies.py to the root folder
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
            
        audio_player = SystemAudioPlayer(base_dir)
        
        # Access Manager Setup
        access_manager = AccessManager(
            turnstile=turnstile,
            audio=audio_player,
            member_repository=self.member_repo,
            ui_callbacks=ui_callbacks
        )
        
        # Register validation rules
        access_manager.register_rule(MedicalCertificateRule())
        access_manager.register_rule(EnrollmentRule())
        access_manager.register_rule(SubscriptionRule())
        access_manager.register_rule(TimeRule())
        access_manager.register_rule(EntriesRule())
        
        return access_manager