from typing import Dict, Any


class HardwareConfig:
    """Gestione della configurazione dell'hardware."""
    
    # Porte seriali predefinite
    DEFAULT_TURNSTILE_PORT = "COM3"
    DEFAULT_AUDIO_PORT = "COM4"
    DEFAULT_BADGE_READER_PORT = "COM5"
    
    @staticmethod
    def get_turnstile_port() -> str:
        """Restituisce la porta seriale del tornello."""
        from core.config.settings import Settings
        settings = Settings()
        return settings.get("turnstile_port", HardwareConfig.DEFAULT_TURNSTILE_PORT)
    
    @staticmethod
    def set_turnstile_port(port: str):
        """Imposta la porta seriale del tornello."""
        from core.config.settings import Settings
        settings = Settings()
        settings.set("turnstile_port", port)
    
    @staticmethod
    def get_audio_port() -> str:
        """Restituisce la porta seriale dell'audio player."""
        from core.config.settings import Settings
        settings = Settings()
        return settings.get("audio_port", HardwareConfig.DEFAULT_AUDIO_PORT)
    
    @staticmethod
    def set_audio_port(port: str):
        """Imposta la porta seriale dell'audio player."""
        from core.config.settings import Settings
        settings = Settings()
        settings.set("audio_port", port)
    
    @staticmethod
    def get_badge_reader_port() -> str:
        """Restituisce la porta seriale del badge reader."""
        from core.config.settings import Settings
        settings = Settings()
        return settings.get("badge_reader_port", HardwareConfig.DEFAULT_BADGE_READER_PORT)
    
    @staticmethod
    def set_badge_reader_port(port: str):
        """Imposta la porta seriale del badge reader."""
        from core.config.settings import Settings
        settings = Settings()
        settings.set("badge_reader_port", port)
    
    @staticmethod
    def get_all_ports() -> Dict[str, str]:
        """Restituisce tutte le porte seriali configurate."""
        return {
            "turnstile": HardwareConfig.get_turnstile_port(),
            "audio": HardwareConfig.get_audio_port(),
            "badge_reader": HardwareConfig.get_badge_reader_port(),
        }
