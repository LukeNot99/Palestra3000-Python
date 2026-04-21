import os
import sys
import json
from typing import Any, Optional, Dict


class Settings:
    """Gestione centralizzata delle impostazioni dell'applicazione."""
    
    _instance: Optional['Settings'] = None
    _config_path: str = ""
    _cache: Dict[str, Any] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        if getattr(sys, 'frozen', False):
            base_dir = os.path.dirname(sys.executable)
        else:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        self._config_path = os.path.join(base_dir, "config.json")
        self._load_config()
        self._initialized = True
    
    def _load_config(self):
        """Carica la configurazione dal file JSON."""
        if os.path.exists(self._config_path):
            try:
                with open(self._config_path, "r") as f:
                    self._cache = json.load(f)
            except Exception:
                self._cache = {}
        else:
            self._cache = {}
    
    def _save_config(self):
        """Salva la configurazione nel file JSON."""
        with open(self._config_path, "w") as f:
            json.dump(self._cache, f, indent=4)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Ottiene un'impostazione specifica."""
        return self._cache.get(key, default)
    
    def set(self, key: str, value: Any):
        """Imposta un'impostazione e salva immediatamente."""
        self._cache[key] = value
        self._save_config()
    
    def load_all(self) -> Dict[str, Any]:
        """Restituisce tutte le impostazioni."""
        return self._cache.copy()
    
    def save_all(self, config_dict: Dict[str, Any]):
        """Sostituisce tutte le impostazioni con un nuovo dizionario."""
        self._cache = config_dict.copy()
        self._save_config()
    
    @property
    def config_path(self) -> str:
        """Restituisce il percorso del file di configurazione."""
        return self._config_path
