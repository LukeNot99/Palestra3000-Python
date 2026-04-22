import os
import sys
import json
from functools import lru_cache
from threading import Lock

class ConfigManager:
    _config_cache = None
    _cache_lock = Lock()
    _path_cache = None
    
    @staticmethod
    def get_persistent_path(filename):
        if ConfigManager._path_cache is None:
            if getattr(sys, 'frozen', False):
                base_dir = os.path.dirname(sys.executable)
            else:
                base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            ConfigManager._path_cache = os.path.join(base_dir, "data", filename)
        return ConfigManager._path_cache
    
    @staticmethod
    def _load_config():
        """Carica la configurazione dal file con caching thread-safe."""
        config_path = ConfigManager.get_persistent_path("config.json")
        if os.path.exists(config_path):
            try:
                with open(config_path, "r") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}
    
    @staticmethod
    def get_setting(key, default=None):
        with ConfigManager._cache_lock:
            if ConfigManager._config_cache is None:
                ConfigManager._config_cache = ConfigManager._load_config()
            return ConfigManager._config_cache.get(key, default)
    
    @staticmethod
    def load_all():
        with ConfigManager._cache_lock:
            ConfigManager._config_cache = ConfigManager._load_config()
            return ConfigManager._config_cache
    
    @staticmethod
    def save_all(config_dict):
        config_path = ConfigManager.get_persistent_path("config.json")
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        with open(config_path, "w") as f:
            json.dump(config_dict, f, indent=4)
        # Invalida cache dopo save
        with ConfigManager._cache_lock:
            ConfigManager._config_cache = config_dict.copy()

    # Metodi specifici per Badge Prefix
    @staticmethod
    def get_badge_prefix():
        return ConfigManager.get_setting("badge_prefix", "57340000000")

    @staticmethod
    def set_badge_prefix(prefix):
        config = ConfigManager.load_all()
        config["badge_prefix"] = prefix
        ConfigManager.save_all(config)

    # Metodi specifici per Alert Scadenza (giorni)
    @staticmethod
    def get_scadenza_alert_giorni():
        return ConfigManager.get_setting("scadenza_alert_giorni", 2)

    @staticmethod
    def set_scadenza_alert_giorni(giorni):
        config = ConfigManager.load_all()
        config["scadenza_alert_giorni"] = int(giorni)
        ConfigManager.save_all(config)

    # Metodi specifici per Colori (Temi)
    @staticmethod
    def get_colors():
        default_colors = {
            "primary": "#007AFF",
            "bg_color": "#F2F2F7",
            "text_color": "#1D1D1F",
            "button_color": "#007AFF",
            "button_text": "#FFFFFF"
        }
        colors = ConfigManager.get_setting("colors", {})
        # Merge con defaults se mancano chiavi
        return {**default_colors, **colors} #type: ignore

    @staticmethod
    def set_colors(colors_dict):
        config = ConfigManager.load_all()
        config["colors"] = colors_dict
        ConfigManager.save_all(config)
