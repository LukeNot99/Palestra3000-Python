import shutil
import os
import sys
from datetime import datetime
from core.database import db_path

class DatabaseService:
    """Servizio per la gestione del database (backup, restore, info)."""
    
    @staticmethod
    def get_db_path() -> str:
        """Restituisce il percorso assoluto del database."""
        return db_path
    
    @staticmethod
    def get_backup_dir() -> str:
        """Restituisce il percorso della cartella backup."""
        if getattr(sys, 'frozen', False):
            base_dir = os.path.dirname(sys.executable)
        else:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        backup_dir = os.path.join(base_dir, "backups")
        os.makedirs(backup_dir, exist_ok=True)
        return backup_dir
    
    @staticmethod
    def create_backup() -> dict:
        """
        Crea un backup del database.
        Restituisce un dict con esito e messaggio.
        """
        try:
            db_file = DatabaseService.get_db_path()
            backup_dir = DatabaseService.get_backup_dir()
            
            if not os.path.exists(db_file):
                return {"success": False, "message": "Database non trovato."}
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"palestra_backup_{timestamp}.db"
            backup_path = os.path.join(backup_dir, backup_filename)
            
            shutil.copy2(db_file, backup_path)
            
            return {
                "success": True, 
                "message": f"Backup creato con successo: {backup_filename}",
                "path": backup_path
            }
        except Exception as e:
            return {"success": False, "message": f"Errore durante il backup: {str(e)}"}
    
    @staticmethod
    def restore_backup(backup_file_path: str) -> dict:
        """
        Ripristina il database da un file di backup.
        Restituisce un dict con esito e messaggio.
        """
        try:
            db_file = DatabaseService.get_db_path()
            
            if not os.path.exists(backup_file_path):
                return {"success": False, "message": "File di backup non trovato."}
            
            # Crea un backup di sicurezza prima del restore
            DatabaseService.create_backup()
            
            shutil.copy2(backup_file_path, db_file)
            
            return {"success": True, "message": "Database ripristinato con successo."}
        except Exception as e:
            return {"success": False, "message": f"Errore durante il restore: {str(e)}"}
    
    @staticmethod
    def list_backups() -> list:
        """
        Restituisce una lista dei backup disponibili.
        """
        try:
            backup_dir = DatabaseService.get_backup_dir()
            backups = []
            
            for filename in os.listdir(backup_dir):
                if filename.startswith("palestra_backup_") and filename.endswith(".db"):
                    filepath = os.path.join(backup_dir, filename)
                    stat = os.stat(filepath)
                    backups.append({
                        "filename": filename,
                        "path": filepath,
                        "size": stat.st_size,
                        "date": datetime.fromtimestamp(stat.st_mtime).strftime("%d/%m/%Y %H:%M")
                    })
            
            # Ordina per data decrescente
            backups.sort(key=lambda x: x["date"], reverse=True)
            return backups
        except Exception:
            return []
    
    @staticmethod
    def delete_backup(backup_file_path: str) -> dict:
        """
        Elimina un file di backup.
        """
        try:
            if not os.path.exists(backup_file_path):
                return {"success": False, "message": "File non trovato."}
            
            os.remove(backup_file_path)
            return {"success": True, "message": "Backup eliminato."}
        except Exception as e:
            return {"success": False, "message": f"Errore durante l'eliminazione: {str(e)}"}
    
    @staticmethod
    def get_db_info() -> dict:
        """
        Restituisce informazioni sul database.
        """
        try:
            db_file = DatabaseService.get_db_path()
            
            if not os.path.exists(db_file):
                return {"exists": False, "message": "Database non trovato."}
            
            stat = os.stat(db_file)
            return {
                "exists": True,
                "path": db_file,
                "size": stat.st_size,
                "created": datetime.fromtimestamp(stat.st_ctime).strftime("%d/%m/%Y %H:%M"),
                "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%d/%m/%Y %H:%M")
            }
        except Exception as e:
            return {"exists": False, "message": str(e)}
