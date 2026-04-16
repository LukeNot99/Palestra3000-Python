import customtkinter as ctk
from src.pkg.dependency.dependencies import DependencyContainer
from src.pkg.config.app_config import ConfigManager
from src.pkg.view.main_window import App
from src.pkg.config.db_config import seed_data

def bootstrap():
    # Carica la configurazione
    ConfigManager.load_all()
    tema = ConfigManager.get_setting("tema", "Light")
    ctk.set_appearance_mode(tema)

    # Inizializza il container delle dipendenze
    di = DependencyContainer()
    
    # Inizializza il database ed effettua il seed iniziale se necessario
    seed_data(di.db_config.get_session)

    # Avvia l'applicazione
    app = App(di)
    app.mainloop()

if __name__ == "__main__":
    bootstrap()