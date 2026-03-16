import os
import sys
import json

class ConfigManager:
    @staticmethod
    def get_persistent_path(filename):
        if getattr(sys, 'frozen', False):
            base_dir = os.path.dirname(sys.executable)
        else:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(base_dir, filename)

    @staticmethod
    def get_setting(key, default=None):
        config_path = ConfigManager.get_persistent_path("config.json")
        if os.path.exists(config_path):
            try:
                with open(config_path, "r") as f:
                    return json.load(f).get(key, default)
            except Exception: pass
        return default

    @staticmethod
    def load_all():
        config_path = ConfigManager.get_persistent_path("config.json")
        if os.path.exists(config_path):
            try:
                with open(config_path, "r") as f: return json.load(f)
            except Exception: pass
        return {}

    @staticmethod
    def save_all(config_dict):
        config_path = ConfigManager.get_persistent_path("config.json")
        with open(config_path, "w") as f:
            json.dump(config_dict, f, indent=4)