import os
import shutil
from typing import Optional
from core.database import db_path, engine
from sqlalchemy import text


class DatabaseConfig:
    """Gestione della configurazione e manutenzione del database."""
    
    @staticmethod
    def get_db_path() -> str:
        """Restituisce il percorso completo del file database."""
        return db_path
    
    @staticmethod
    def get_db_filename() -> str:
        """Restituisce solo il nome del file database."""
        return os.path.basename(db_path)
    
    @staticmethod
    def backup_database(backup_dir: str) -> Optional[str]:
        """
        Esegue un backup del database.
        
        Args:
            backup_dir: Directory dove salvare il backup.
            
        Returns:
            Il percorso del file di backup creato, o None se fallisce.
        """
        try:
            os.makedirs(backup_dir, exist_ok=True)
            
            filename = os.path.basename(db_path)
            name, ext = os.path.splitext(filename)
            backup_filename = f"{name}_backup{ext}"
            backup_path = os.path.join(backup_dir, backup_filename)
            
            # Copia fisica del file
            shutil.copy2(db_path, backup_path)
            
            return backup_path
        except Exception as e:
            print(f"Errore durante il backup del database: {e}")
            return None
    
    @staticmethod
    def restore_database(backup_path: str) -> bool:
        """
        Ripristina il database da un backup.
        
        Args:
            backup_path: Percorso del file di backup da ripristinare.
            
        Returns:
            True se il ripristino è riuscito, False altrimenti.
        """
        try:
            if not os.path.exists(backup_path):
                print(f"File di backup non trovato: {backup_path}")
                return False
            
            # Copia il backup sopra il database corrente
            shutil.copy2(backup_path, db_path)
            
            return True
        except Exception as e:
            print(f"Errore durante il ripristino del database: {e}")
            return False
    
    @staticmethod
    def get_backup_directory() -> str:
        """Restituisce la directory predefinita per i backup."""
        if getattr(os.sys, 'frozen', False):
            base_dir = os.path.dirname(os.sys.executable)
        else:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        return os.path.join(base_dir, "core", "backups")
