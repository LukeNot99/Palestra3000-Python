"""
Package di configurazione dell'applicazione.
Centralizza la gestione delle impostazioni, del database e dell'hardware.
"""

from core.config.settings import Settings
from core.config.database_config import DatabaseConfig
from core.config.hardware_config import HardwareConfig

__all__ = [
    "Settings",
    "DatabaseConfig",
    "HardwareConfig",
]
