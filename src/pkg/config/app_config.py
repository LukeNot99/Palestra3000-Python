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
