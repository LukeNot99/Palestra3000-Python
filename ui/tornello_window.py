import customtkinter as ctk
import re
from core.database import SessionLocal, Member
from ui.soci_window import SocioFormWindow

class TornelloView(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app

        top_frame = ctk.CTkFrame(self, fg_color=("#FFFFFF", "#2C2C2E"), corner_radius=12, border_width=1, border_color=("#E5E5EA", "#3A3A3C"))
        top_frame.pack(fill="x", pady=(0, 20))
        ctk.CTkLabel(top_frame, text="Inserimento Manuale", font=ctk.CTkFont(family="Montserrat", size=18, weight="bold")).pack(pady=(15, 5))
        
        input_row = ctk.CTkFrame(top_frame, fg_color="transparent"); input_row.pack(pady=(0, 20))
        self.ent_id = ctk.CTkEntry(input_row, width=200, font=ctk.CTkFont(family="Montserrat", size=18, weight="bold"), justify="center", placeholder_text="Num. Scheda")
        self.ent_id.pack(side="left", padx=10)
        self.ent_id.bind("<Return>", lambda e: self.simula_strisciata())
        ctk.CTkButton(input_row, text="Verifica", width=120, height=38, font=ctk.CTkFont(family="Montserrat", weight="bold"), fg_color="#007AFF", command=self.simula_strisciata).pack(side="left", padx=5)
        ctk.CTkButton(input_row, text="Apri (Forzato)", width=140, height=38, font=ctk.CTkFont(family="Montserrat", weight="bold"), fg_color="#FF3B30", command=self.app.apertura_manuale_globale).pack(side="left", padx=(15, 10))

        log_frame = ctk.CTkFrame(self, fg_color=("#FFFFFF", "#2C2C2E"), corner_radius=12, border_width=1, border_color=("#E5E5EA", "#3A3A3C"))
        log_frame.pack(fill="both", expand=True)
        ctk.CTkLabel(log_frame, text="Cronologia (Doppio clic sul log per aprire l'anagrafica)", font=ctk.CTkFont(family="Montserrat", size=14, weight="bold"), anchor="w").pack(fill="x", padx=15, pady=(10, 5))
        self.txt_log = ctk.CTkTextbox(log_frame, state="disabled", fg_color=("#F8F8F9", "#1C1C1E"), font=ctk.CTkFont(family="Consolas", size=13))
        self.txt_log.pack(padx=15, pady=(0, 15), fill="both", expand=True)
        self.txt_log.bind("<Double-Button-1>", self.apri_scheda)

        # Ricarica lo storico pre-esistente in memoria
        for log in self.app.cronologia_accessi: self.inserisci_testo(log)

    def apri_scheda(self, event):
        try:
            i = self.txt_log._textbox.index(f"@{event.x},{event.y}"); riga = self.txt_log.get(f"{i.split('.')[0]}.0", f"{i.split('.')[0]}.end")
            match = re.search(r'\(\s*(.*?)\s*\)', riga)
            if match:
                s_str = match.group(1).strip()
                if s_str.lower() in ["operatore f12", "operatore"]: return
                db = SessionLocal()
                s = db.query(Member).filter(Member.badge_number == s_str).first()
                db.close()
                if s: SocioFormWindow(self.winfo_toplevel(), refresh_callback=lambda: None, socio_id=s.id)
        except Exception: pass

    def inserisci_testo(self, t):
        self.txt_log.configure(state="normal"); self.txt_log.insert("end", t + "\n"); self.txt_log.configure(state="disabled"); self.txt_log.see("end")

    def aggiungi_log(self, t): self.inserisci_testo(t)

    def simula_strisciata(self):
        s = self.ent_id.get().strip()
        if s: self.app.gestisci_accesso_globale(s); self.ent_id.delete(0, 'end')