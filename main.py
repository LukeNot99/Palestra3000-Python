import customtkinter as ctk
import os
import json
from datetime import datetime, timedelta
import threading
import serial
import platform
import subprocess
from PIL import Image

from core.database import SessionLocal, Member, Lesson, Booking, seed_data

from ui.soci_window import SociView, SocioFormWindow
from ui.tariffe_window import TariffeView
from ui.attivita_window import AttivitaView
from ui.lezioni_window import LezioniView
from ui.calendario_window import CalendarioView
from ui.tornello_window import TornelloView
from ui.settings_window import SettingsView

def carica_impostazione_iniziale(chiave, default):
    if os.path.exists("config.json"):
        try:
            with open("config.json", "r") as f: return json.load(f).get(chiave, default)
        except: pass
    return default

ctk.set_appearance_mode(carica_impostazione_iniziale("tema", "Light"))  

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Palestra 3000 - Gestione")
        self.geometry("1350x850") 
        self.configure(fg_color=("#F2F2F7", "#1C1C1E")) 
        self.icons_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icons")
        
        seed_data()

        self.serial_conn = None
        self.stop_serial_thread = threading.Event()
        self.cronologia_accessi = [] 
        
        self.giorno_tracker = datetime.now().date()
        self.soci_in_sede = set() 
        
        self.avvia_ascolto_hardware(carica_impostazione_iniziale("porta_tornello", ""))
        self.bind_all("<F12>", self.apertura_manuale_globale)

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # ==================== SIDEBAR ====================
        self.sidebar = ctk.CTkFrame(self, width=280, corner_radius=0, fg_color=("#FFFFFF", "#2C2C2E"), border_width=1, border_color=("#E5E5EA", "#3A3A3C"))
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False) 
        self.sidebar.grid_columnconfigure(0, weight=1)
        self.sidebar.grid_rowconfigure(10, weight=1) 

        self.logo_container = None
        self.aggiorna_logo() 

        ctk.CTkLabel(self.sidebar, text="QUOTIDIANO", font=ctk.CTkFont(family="Montserrat", size=12, weight="bold"), text_color=("#86868B", "#98989D")).grid(row=1, column=0, padx=24, pady=(0, 10), sticky="w")

        self.views = {} 
        self.bottoni_menu = {}
        self.current_view_name = None
        self.current_frame = None

        # --- MENU PRINCIPALE RICOMPATTATO ---
        self.crea_bottone_menu("dashboard", "Dashboard", "dashboard", row=2)
        self.crea_bottone_menu("tornello", "Controllo Accessi", "tornello", row=3)
        self.crea_bottone_menu("soci", "Anagrafica Soci", "soci", row=4)
        self.crea_bottone_menu("calendario", "Calendario Corsi", "calendario", row=5)

        ctk.CTkLabel(self.sidebar, text="AMMINISTRAZIONE", font=ctk.CTkFont(family="Montserrat", size=12, weight="bold"), text_color=("#86868B", "#98989D")).grid(row=6, column=0, padx=24, pady=(30, 10), sticky="w")

        self.crea_bottone_menu("lezioni", "Piani Settimanali", "lezioni", row=7)
        self.crea_bottone_menu("tariffe", "Tariffario e Costi", "tariffe", row=8)
        self.crea_bottone_menu("attivita", "Gestione Attività", "attivita", row=9)
        self.crea_bottone_menu("impostazioni", "Impostazioni", "impostazioni", row=10, extra_pady=(2, 20))

        self.main_content = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        self.main_content.grid(row=0, column=1, sticky="nsew", padx=30, pady=30)
        
        self.show_view("dashboard")

    def aggiorna_logo(self):
        if self.logo_container:
            self.logo_container.destroy()

        self.logo_container = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.logo_container.grid(row=0, column=0, padx=20, pady=(30, 30), sticky="ew")
        
        percorso_logo = carica_impostazione_iniziale("percorso_logo", "")
        nome_palestra = carica_impostazione_iniziale("nome_palestra", "Palestra 3000")

        if percorso_logo and os.path.exists(percorso_logo):
            try:
                img = Image.open(percorso_logo)
                img.thumbnail((220, 100))
                ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=img.size)
                lbl_img = ctk.CTkLabel(self.logo_container, text="", image=ctk_img)
                lbl_img.pack(anchor="w", pady=(0, 10))
            except Exception:
                pass 

        self.lbl_nome_palestra = ctk.CTkLabel(self.logo_container, text=nome_palestra, font=ctk.CTkFont(family="Montserrat", size=22, weight="bold"), text_color=("#1D1D1F", "#FFFFFF"), wraplength=220, justify="left")
        self.lbl_nome_palestra.pack(anchor="w")

    def show_view(self, view_name):
        if self.current_view_name == view_name: return
        self.current_view_name = view_name
        
        for name, data in self.bottoni_menu.items():
            btn_f, l_icon, l_text = data
            if name == view_name:
                btn_f.configure(fg_color=("#F2F2F7", "#3A3A3C"))
                l_icon.configure(text_color=("#007AFF", "#0A84FF"))
                l_text.configure(text_color=("#007AFF", "#0A84FF"), font=ctk.CTkFont(family="Montserrat", size=14, weight="bold"))
            else:
                btn_f.configure(fg_color="transparent")
                l_icon.configure(text_color=("#1D1D1F", "#FFFFFF"))
                l_text.configure(text_color=("#1D1D1F", "#FFFFFF"), font=ctk.CTkFont(family="Montserrat", size=14, weight="normal"))
        
        if self.current_frame:
            self.current_frame.pack_forget()
            
        if view_name not in self.views:
            if view_name == "dashboard": self.views[view_name] = DashboardView(self.main_content, self)
            elif view_name == "soci": self.views[view_name] = SociView(self.main_content, self)
            elif view_name == "tariffe": self.views[view_name] = TariffeView(self.main_content, self)
            elif view_name == "attivita": self.views[view_name] = AttivitaView(self.main_content, self)
            elif view_name == "lezioni": self.views[view_name] = LezioniView(self.main_content, self)
            elif view_name == "calendario": self.views[view_name] = CalendarioView(self.main_content, self)
            elif view_name == "tornello": self.views[view_name] = TornelloView(self.main_content, self)
            elif view_name == "impostazioni": self.views[view_name] = SettingsView(self.main_content, self)

        self.current_frame = self.views[view_name]
        self.current_frame.pack(fill="both", expand=True)

        if hasattr(self.current_frame, "carica_dati"): self.current_frame.carica_dati()
        elif hasattr(self.current_frame, "carica_tabella"): self.current_frame.carica_tabella()
        elif hasattr(self.current_frame, "load_stats"): self.current_frame.load_stats()
        elif hasattr(self.current_frame, "disegna_calendario"): self.current_frame.disegna_calendario()

        if view_name == "tornello" and hasattr(self.current_frame, "aggiorna_contatore_sede"):
            self.current_frame.aggiorna_contatore_sede()

    def crea_bottone_menu(self, nome_icona, testo, view_name, row, extra_pady=(2,2)):
        btn_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent", corner_radius=8, height=42, cursor="hand2")
        btn_frame.grid(row=row, column=0, padx=15, pady=extra_pady, sticky="ew")
        btn_frame.pack_propagate(False)
        
        icona_img = self.carica_icona(nome_icona, 20)
        if icona_img: lbl_icon = ctk.CTkLabel(btn_frame, text="", image=icona_img, width=35, anchor="center")
        else: lbl_icon = ctk.CTkLabel(btn_frame, text="▪", font=ctk.CTkFont(family="Montserrat", size=18), text_color=("#1D1D1F", "#FFFFFF"), width=35, anchor="center")
        lbl_icon.pack(side="left", padx=(10, 0))
        
        lbl_text = ctk.CTkLabel(btn_frame, text=testo, font=ctk.CTkFont(family="Montserrat", size=14, weight="normal"), text_color=("#1D1D1F", "#FFFFFF"), anchor="w")
        lbl_text.pack(side="left", fill="x", expand=True, padx=(5, 10))
        
        def on_click(e): self.show_view(view_name)
        def on_enter(e): 
            if self.current_view_name != view_name: btn_frame.configure(fg_color=("#F2F2F7", "#3A3A3C"))
        def on_leave(e): 
            if self.current_view_name != view_name: btn_frame.configure(fg_color="transparent")

        for w in [btn_frame, lbl_icon, lbl_text]:
            w.bind("<Button-1>", on_click); w.bind("<Enter>", on_enter); w.bind("<Leave>", on_leave)
            
        self.bottoni_menu[view_name] = (btn_frame, lbl_icon, lbl_text)

    def carica_icona(self, nome_base, size):
        percorso_light = os.path.join(self.icons_dir, f"{nome_base}_black.png")
        percorso_dark = os.path.join(self.icons_dir, f"{nome_base}_white.png")
        percorso_singolo = os.path.join(self.icons_dir, f"{nome_base}.png")
        try:
            if os.path.exists(percorso_light) and os.path.exists(percorso_dark): return ctk.CTkImage(light_image=Image.open(percorso_light), dark_image=Image.open(percorso_dark), size=(size, size))
            elif os.path.exists(percorso_singolo): return ctk.CTkImage(light_image=Image.open(percorso_singolo), dark_image=Image.open(percorso_singolo), size=(size, size))
        except Exception: pass
        return None

    def avvia_ascolto_hardware(self, porta):
        if self.serial_conn and self.serial_conn.is_open:
            self.stop_serial_thread.set()
            self.serial_conn.close()
        if porta and "Nessun hardware" not in porta:
            try:
                self.serial_conn = serial.Serial(porta, 9600, timeout=1)
                self.stop_serial_thread.clear()
                threading.Thread(target=self._ciclo_ascolto, daemon=True).start()
            except Exception: pass

    def _ciclo_ascolto(self):
        while not self.stop_serial_thread.is_set():
            if self.serial_conn and self.serial_conn.in_waiting > 0:
                try:
                    dato = self.serial_conn.readline().decode('utf-8').strip()
                    scheda = ''.join(filter(str.isdigit, dato)) 
                    if scheda: self.after(0, self.gestisci_accesso_globale, scheda)
                except Exception: pass

    def riproduci_audio(self, nome_file):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        percorso = os.path.join(base_dir, "messaggi", nome_file)
        if os.path.exists(percorso):
            sistema_operativo = platform.system()
            if sistema_operativo == "Windows":
                import winsound
                winsound.PlaySound(percorso, winsound.SND_FILENAME | winsound.SND_ASYNC)
            elif sistema_operativo == "Darwin":
                subprocess.Popen(["afplay", percorso])

    def registra_log(self, messaggio):
        self.cronologia_accessi.append(messaggio)
        if self.current_view_name == "tornello" and hasattr(self.current_frame, "aggiungi_log"):
            self.current_frame.aggiungi_log(messaggio)

    def mostra_toast_notifica(self, titolo, messaggio, colore_sfondo):
        toast = ctk.CTkToplevel(self)
        toast.overrideredirect(True) 
        toast.attributes('-topmost', True) 
        x = self.winfo_screenwidth() - 380
        y = self.winfo_screenheight() - 150
        toast.geometry(f"350x100+{x}+{y}")
        toast.configure(fg_color=colore_sfondo)
        ctk.CTkLabel(toast, text=titolo, font=ctk.CTkFont(family="Montserrat", size=18, weight="bold"), text_color="white").pack(pady=(15, 5))
        ctk.CTkLabel(toast, text=messaggio, font=ctk.CTkFont(family="Montserrat", size=14), text_color="white").pack()
        self.after(3500, toast.destroy)

    def controlla_reset_giorno(self):
        oggi = datetime.now().date()
        if oggi != self.giorno_tracker:
            self.giorno_tracker = oggi
            self.soci_in_sede.clear()

    def gestisci_accesso_globale(self, scheda_str):
        if not scheda_str: return
        self.controlla_reset_giorno()
        db = SessionLocal()
        socio = db.query(Member).filter(Member.badge_number == scheda_str).first()
        ora_str = datetime.now().strftime("%H:%M:%S")

        if not socio:
            self.mostra_toast_notifica("ACCESSO NEGATO", "Scheda Non Registrata!", "#FF3B30")
            self.riproduci_audio("NonValida.wav")
            self.registra_log(f"{ora_str} > SCONOSCIUTO ( {scheda_str} ) : NEGATO (Invalida) #-")
            db.close(); return

        nome_completo = f"{socio.first_name} {socio.last_name}"
        adesso = datetime.now()

        blocco_iscr = carica_impostazione_iniziale("blocco_iscr", True)
        blocco_abb = carica_impostazione_iniziale("blocco_abb", True)
        blocco_orari = carica_impostazione_iniziale("blocco_orari", True)
        blocco_cert = carica_impostazione_iniziale("blocco_cert", False)

        if blocco_cert:
            if not socio.has_medical_certificate:
                self.mostra_toast_notifica("ACCESSO NEGATO", f"{nome_completo}\nCertificato Medico Mancante!", "#007AFF")
                self.riproduci_audio("HeyOp.wav")
                self.registra_log(f"{ora_str} > {nome_completo} ( {scheda_str} ) : NEGATO (Cert. Medico Assente) #-")
                db.close(); return
            if socio.certificate_expiration:
                try:
                    scad_cert = datetime.strptime(socio.certificate_expiration, "%d/%m/%Y") if "/" in socio.certificate_expiration else datetime.strptime(socio.certificate_expiration, "%Y-%m-%d")
                    if adesso > scad_cert:
                        self.mostra_toast_notifica("ACCESSO NEGATO", f"{nome_completo}\nCertificato Medico Scaduto!", "#007AFF")
                        self.riproduci_audio("HeyOp.wav")
                        self.registra_log(f"{ora_str} > {nome_completo} ( {scheda_str} ) : NEGATO (Cert. Medico Scaduto) #-")
                        db.close(); return
                except ValueError: pass

        if blocco_iscr and socio.enrollment_expiration:
            try:
                scad_iscr = datetime.strptime(socio.enrollment_expiration, "%d/%m/%Y") if "/" in socio.enrollment_expiration else datetime.strptime(socio.enrollment_expiration, "%Y-%m-%d")
                if adesso > scad_iscr:
                    self.mostra_toast_notifica("ACCESSO NEGATO", f"{nome_completo}\nIscrizione Annuale Scaduta!", "#FF3B30")
                    self.riproduci_audio("HeyOp.wav")
                    self.registra_log(f"{ora_str} > {nome_completo} ( {scheda_str} ) : NEGATO (Iscrizione Scaduta) #-")
                    db.close(); return
            except ValueError: pass 

        if blocco_abb and socio.membership_expiration:
            try:
                scadenza = datetime.strptime(socio.membership_expiration, "%d/%m/%Y") if "/" in socio.membership_expiration else datetime.strptime(socio.membership_expiration, "%Y-%m-%d")
                if adesso > scadenza:
                    self.mostra_toast_notifica("ACCESSO NEGATO", f"{nome_completo}\nAbbonamento Scaduto!", "#FF9500")
                    self.riproduci_audio("HeyOp.wav")
                    self.registra_log(f"{ora_str} > {nome_completo} ( {scheda_str} ) : NEGATO (Abbonamento Scaduto) #-")
                    db.close(); return
            except ValueError: pass 

        if not socio.tier:
            self.mostra_toast_notifica("ACCESSO NEGATO", f"{nome_completo}\nNessuna fascia assegnata.", "#FF9500")
            self.riproduci_audio("HeyOp.wav")
            self.registra_log(f"{ora_str} > {nome_completo} ( {scheda_str} ) : NEGATO (Senza Fascia) #-")
            db.close(); return

        tier = socio.tier

        if blocco_orari:
            try:
                ora_inizio = datetime.strptime(tier.start_time[:5], "%H:%M").time()
                ora_fine = datetime.strptime(tier.end_time[:5], "%H:%M").time()
                ora_attuale = adesso.time()
                
                if ora_inizio <= ora_fine: in_orario = ora_inizio <= ora_attuale <= ora_fine
                else: in_orario = ora_attuale >= ora_inizio or ora_attuale <= ora_fine
                    
                if not in_orario:
                    self.mostra_toast_notifica("ACCESSO NEGATO", f"{nome_completo}\nFuori orario consentito!", "#FF3B30")
                    self.riproduci_audio("FuoriOrario.wav")
                    self.registra_log(f"{ora_str} > {nome_completo} ( {scheda_str} ) : NEGATO (Fuori Orario) #-")
                    db.close()
                    return
            except ValueError: pass

        messaggio_extra = ""
        log_ingressi = "#∞"
        if tier.max_entries > 0:
            ingressi_usati = socio.entries_used if socio.entries_used else 0
            if ingressi_usati >= tier.max_entries:
                self.mostra_toast_notifica("ACCESSO NEGATO", f"{nome_completo}\nCarnet Esaurito!", "#FF3B30")
                self.riproduci_audio("FuoriOrario.wav")
                self.registra_log(f"{ora_str} > {nome_completo} ( {scheda_str} ) : NEGATO (Carnet Esaurito) #0")
                db.close(); return
            else:
                socio.entries_used = ingressi_usati + 1
                db.commit()
                ingressi_rimanenti = tier.max_entries - socio.entries_used
                messaggio_extra = f"\nIngressi residui: {ingressi_rimanenti}"
                log_ingressi = f"#{ingressi_rimanenti}"

        self.mostra_toast_notifica("ACCESSO CONSENTITO", f"Benvenuto {nome_completo}{messaggio_extra}", "#34C759")
        self.registra_log(f"{ora_str} > {nome_completo} ( {scheda_str} ) : OK {log_ingressi}")
        
        self.soci_in_sede.add(socio.id)
        if self.current_view_name == "tornello" and hasattr(self.current_frame, "aggiorna_contatore_sede"):
            self.current_frame.aggiorna_contatore_sede()

        if self.serial_conn and self.serial_conn.is_open:
            try: self.serial_conn.write(b'*') 
            except: pass
        self.riproduci_audio("BuonLavoroDonne.wav" if socio.gender == "F" else "BuonLavoro.wav")
        db.close()

    def apertura_manuale_globale(self, event=None):
        self.riproduci_audio("handopen.wav")
        if self.serial_conn and self.serial_conn.is_open:
            try: self.serial_conn.write(b'*')
            except: pass
        self.mostra_toast_notifica("APERTURA D'UFFICIO", "Ingresso autorizzato dall'operatore.", "#007AFF")


class DashboardView(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        
        self.font_titolo = ctk.CTkFont(family="Montserrat", size=34, weight="bold")
        self.font_sottotitolo = ctk.CTkFont(family="Montserrat", size=16)
        self.font_bold13 = ctk.CTkFont(family="Montserrat", weight="bold", size=13)
        self.font_norm13 = ctk.CTkFont(family="Montserrat", size=13)
        self.font_badge = ctk.CTkFont(family="Montserrat", size=11, weight="bold")
        self.font_italic = ctk.CTkFont(family="Montserrat", slant="italic")

        giorni_ita = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]
        mesi_ita = ["", "Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno", "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"]
        oggi = datetime.now()
        data_oggi = f"{giorni_ita[oggi.weekday()]}, {oggi.day} {mesi_ita[oggi.month]} {oggi.year}"

        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 20))

        ctk.CTkLabel(header_frame, text="Dashboard", font=self.font_titolo, text_color=("#1D1D1F", "#FFFFFF")).pack(anchor="w")
        ctk.CTkLabel(header_frame, text=data_oggi, font=self.font_sottotitolo, text_color=("#86868B", "#98989D")).pack(anchor="w", pady=(5, 0))

        self.cards_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.cards_frame.pack(fill="x", pady=(0, 25))
        self.cards_frame.grid_columnconfigure((0, 1, 2), weight=1)

        self.var_tot_members = ctk.StringVar(value="...")
        self.var_corsi_oggi = ctk.StringVar(value="...")
        self.var_scadenze_brevi = ctk.StringVar(value="...")

        self.create_card(self.cards_frame, 0, "Soci Attivi (In Regola)", self.var_tot_members, "soci", "#007AFF", (0, 10))
        self.create_card(self.cards_frame, 1, "Corsi Odierni", self.var_corsi_oggi, "calendario", "#FF9500", (10, 10))
        self.create_card(self.cards_frame, 2, "Scadenze Imminenti", self.var_scadenze_brevi, "impostazioni", "#FF3B30", (10, 0))

        body_layout = ctk.CTkFrame(self, fg_color="transparent")
        body_layout.pack(fill="both", expand=True)
        body_layout.grid_columnconfigure(0, weight=35) 
        body_layout.grid_columnconfigure(1, weight=65)
        body_layout.grid_rowconfigure(0, weight=1)

        left_col = ctk.CTkFrame(body_layout, fg_color="transparent")
        left_col.grid(row=0, column=0, sticky="nsew", padx=(0, 15))
        
        actions_card = ctk.CTkFrame(left_col, fg_color=("#FFFFFF", "#2C2C2E"), corner_radius=16, border_width=1, border_color=("#E5E5EA", "#3A3A3C"))
        actions_card.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(actions_card, text="⚡ Azioni Rapide", font=ctk.CTkFont(family="Montserrat", size=18, weight="bold"), text_color=("#1D1D1F", "#FFFFFF")).pack(anchor="w", padx=20, pady=(20, 15))

        self.crea_bottone_azione(actions_card, "👤 Anagrafica Soci", "#007AFF", lambda: self.app.show_view("soci"))
        self.crea_bottone_azione(actions_card, "🎫 Controllo Accessi", "#FF3B30", lambda: self.app.show_view("tornello"))
        self.crea_bottone_azione(actions_card, "📅 Calendario Corsi", "#FF9500", lambda: self.app.show_view("calendario"), is_last=True)

        corsi_card = ctk.CTkFrame(left_col, fg_color=("#FFFFFF", "#2C2C2E"), corner_radius=16, border_width=1, border_color=("#E5E5EA", "#3A3A3C"))
        corsi_card.pack(fill="both", expand=True) 
        
        ctk.CTkLabel(corsi_card, text="📍 Corsi in Programma Oggi", font=ctk.CTkFont(family="Montserrat", size=16, weight="bold"), text_color=("#1D1D1F", "#FFFFFF")).pack(anchor="w", padx=20, pady=(20, 15))
        
        self.scroll_corsi_oggi = ctk.CTkScrollableFrame(corsi_card, fg_color="transparent")
        self.scroll_corsi_oggi.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        scadenze_card = ctk.CTkFrame(body_layout, fg_color=("#FFFFFF", "#2C2C2E"), corner_radius=16, border_width=1, border_color=("#E5E5EA", "#3A3A3C"))
        scadenze_card.grid(row=0, column=1, sticky="nsew")
        
        header_scad = ctk.CTkFrame(scadenze_card, fg_color="transparent")
        header_scad.pack(fill="x", padx=20, pady=(20, 5))
        
        ctk.CTkLabel(header_scad, text="⚠️ Scadenze Mensilità", font=ctk.CTkFont(family="Montserrat", size=18, weight="bold"), text_color=("#1D1D1F", "#FFFFFF")).pack(side="left")
        ctk.CTkLabel(header_scad, text="Prossimi 2 giorni", font=ctk.CTkFont(family="Montserrat", size=12, weight="bold"), text_color="#FF3B30", fg_color=("#FFE5E5", "#4A1010"), corner_radius=6, padx=8, pady=4).pack(side="left", padx=15)
        
        ctk.CTkLabel(scadenze_card, text="Doppio click su un nome per aprire la scheda e registrare il rinnovo", font=ctk.CTkFont(family="Montserrat", size=13), text_color=("#86868B", "#98989D")).pack(anchor="w", padx=20, pady=(0, 15))

        self.scroll_scadenze = ctk.CTkScrollableFrame(scadenze_card, fg_color="transparent")
        self.scroll_scadenze.pack(fill="both", expand=True, padx=10, pady=(0, 15))

        self.load_stats()

    def apri_scheda_socio(self, socio_id):
        SocioFormWindow(self.app, refresh_callback=self.load_stats, socio_id=socio_id)

    def crea_bottone_azione(self, parent, testo, colore, comando, is_last=False):
        btn = ctk.CTkButton(parent, text=testo, command=comando, font=ctk.CTkFont(family="Montserrat", size=15, weight="bold"), fg_color=("#F8F8F9", "#3A3A3C"), text_color=colore, hover_color=("#E5E5EA", "#48484A"), border_width=0, corner_radius=10, height=48, anchor="w")
        pady_val = (0, 10) if not is_last else (0, 20)
        btn.pack(fill="x", padx=20, pady=pady_val)

    def create_card(self, parent, col, title, text_variable, nome_icona, accent_color, padx_val):
        card = ctk.CTkFrame(parent, fg_color=("#FFFFFF", "#2C2C2E"), corner_radius=16, height=130, border_width=1, border_color=("#E5E5EA", "#3A3A3C"))
        card.grid(row=0, column=col, padx=padx_val, sticky="ew")
        card.grid_propagate(False)
        
        header = ctk.CTkFrame(card, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(20, 5))
        icon_box = ctk.CTkFrame(header, width=32, height=32, corner_radius=8, fg_color=accent_color)
        icon_box.pack(side="left")
        icon_box.pack_propagate(False)
        icona_img = self.app.carica_icona(f"{nome_icona}_white", 20) or self.app.carica_icona(nome_icona, 20)
        if icona_img: ctk.CTkLabel(icon_box, text="", image=icona_img).place(relx=0.5, rely=0.5, anchor="center")
        else: ctk.CTkLabel(icon_box, text="▪", text_color="white", font=ctk.CTkFont(family="Montserrat", size=16)).place(relx=0.5, rely=0.5, anchor="center")
        ctk.CTkLabel(header, text=title, font=ctk.CTkFont(family="Montserrat", size=14, weight="bold"), text_color=("#86868B", "#98989D")).pack(side="left", padx=12)
        lbl_val = ctk.CTkLabel(card, textvariable=text_variable, font=ctk.CTkFont(family="Montserrat", size=38, weight="bold"), text_color=("#1D1D1F", "#FFFFFF"))
        lbl_val.pack(anchor="w", padx=20)

    def load_stats(self):
        db = SessionLocal()
        oggi_dt = datetime.now()
        oggi_str = oggi_dt.strftime("%Y-%m-%d")
        
        data_oggi = oggi_dt.date()
        data_domani = data_oggi + timedelta(days=1)
        data_dopodomani = data_oggi + timedelta(days=2)
        target_dates = [data_oggi, data_domani, data_dopodomani]
        
        tutti_soci = db.query(Member).all()
        soci_attivi_reali = 0
        scaduti_lista = []
        
        for socio in tutti_soci:
            if socio.membership_expiration:
                try:
                    if "/" in socio.membership_expiration:
                        scad = datetime.strptime(socio.membership_expiration, "%d/%m/%Y").date()
                    else:
                        scad = datetime.strptime(socio.membership_expiration, "%Y-%m-%d").date()
                        
                    if scad in target_dates:
                        scaduti_lista.append((socio, scad))
                except ValueError: pass

            if not socio.tier: continue
            if not socio.membership_expiration: continue
            try:
                scad_abb = datetime.strptime(socio.membership_expiration, "%d/%m/%Y") if "/" in socio.membership_expiration else datetime.strptime(socio.membership_expiration, "%Y-%m-%d")
                if oggi_dt > scad_abb: continue
            except ValueError: continue
            
            if not socio.enrollment_expiration: continue
            try:
                scad_iscr = datetime.strptime(socio.enrollment_expiration, "%d/%m/%Y") if "/" in socio.enrollment_expiration else datetime.strptime(socio.enrollment_expiration, "%Y-%m-%d")
                if oggi_dt > scad_iscr: continue
            except ValueError: continue
            
            soci_attivi_reali += 1

        scaduti_lista.sort(key=lambda x: x[1])

        self.var_tot_members.set(str(soci_attivi_reali))
        num_corsi = db.query(Lesson).filter(Lesson.date == oggi_str).count()
        self.var_corsi_oggi.set(str(num_corsi))
        self.var_scadenze_brevi.set(str(len(scaduti_lista)))
        
        for widget in self.scroll_corsi_oggi.winfo_children(): widget.destroy()
        lezioni_oggi = db.query(Lesson).filter(Lesson.date == oggi_str).order_by(Lesson.start_time).all()
        
        if not lezioni_oggi:
            ctk.CTkLabel(self.scroll_corsi_oggi, text="Nessun corso programmato oggi.", font=self.font_italic, text_color=("#86868B", "#98989D")).pack(pady=30)
        else:
            for l in lezioni_oggi:
                riga_c = ctk.CTkFrame(self.scroll_corsi_oggi, fg_color="transparent")
                riga_c.pack(fill="x", pady=6)
                
                ctk.CTkLabel(riga_c, text=f"🕒 {l.start_time[:5]}", font=self.font_bold13, text_color=("#007AFF", "#0A84FF"), width=60, anchor="w").pack(side="left")
                
                nome_corso = l.activity.name if l.activity else "Attività"
                ctk.CTkLabel(riga_c, text=nome_corso, font=self.font_bold13, text_color=("#1D1D1F", "#FFFFFF")).pack(side="left", padx=5)
                
                occupati = db.query(Booking).filter(Booking.lesson_id == l.id).count()
                badge_color = "#34C759" if occupati < l.total_seats else "#FF3B30"
                badge = ctk.CTkFrame(riga_c, fg_color=badge_color, corner_radius=6, height=22, width=50)
                badge.pack(side="right", padx=5)
                badge.pack_propagate(False)
                ctk.CTkLabel(badge, text=f"{occupati}/{l.total_seats}", text_color="white", font=self.font_badge).place(relx=0.5, rely=0.5, anchor="center")

        for widget in self.scroll_scadenze.winfo_children(): widget.destroy()
        
        if not scaduti_lista:
            ctk.CTkLabel(self.scroll_scadenze, text="Nessuna scadenza nei prossimi giorni. 🎉", font=self.font_italic, text_color=("#86868B", "#98989D")).pack(pady=40)
        else:
            for socio, data_scadenza in scaduti_lista:
                riga_s = ctk.CTkFrame(self.scroll_scadenze, fg_color=("#F8F8F9", "#3A3A3C"), height=50, corner_radius=10, cursor="hand2")
                riga_s.pack(fill="x", pady=4, padx=5)
                riga_s.pack_propagate(False)
                
                if data_scadenza == data_oggi:
                    testo_scad = "🔴 Scade OGGI"
                    colore_scad = "#FF3B30"
                elif data_scadenza == data_domani:
                    testo_scad = "🟠 Scade DOMANI"
                    colore_scad = "#FF9500"
                else:
                    testo_scad = f"🟡 Scade il {data_scadenza.strftime('%d/%m')}"
                    colore_scad = "#FF9500"

                badge_scadenza = ctk.CTkFrame(riga_s, fg_color="transparent")
                badge_scadenza.pack(side="right", padx=15)
                ctk.CTkLabel(badge_scadenza, text=testo_scad, font=ctk.CTkFont(family="Montserrat", size=12, weight="bold"), text_color=colore_scad).pack()

                nome_comp = f"{socio.first_name} {socio.last_name}"
                scheda_txt = f" [{socio.badge_number}]" if socio.badge_number else ""
                
                lbl_n = ctk.CTkLabel(riga_s, text=nome_comp + scheda_txt, font=self.font_bold13, text_color=("#1D1D1F", "#FFFFFF"))
                lbl_n.pack(side="left", padx=20)

                for w in [riga_s, lbl_n, badge_scadenza] + badge_scadenza.winfo_children():
                    w.bind("<Double-Button-1>", lambda e, sid=socio.id: self.apri_scheda_socio(sid))
                    w.bind("<Enter>", lambda e, fr=riga_s: fr.configure(fg_color=("#E5E5EA", "#48484A")))
                    w.bind("<Leave>", lambda e, fr=riga_s: fr.configure(fg_color=("#F8F8F9", "#3A3A3C")))

        db.close()

if __name__ == "__main__":
    app = App()
    app.mainloop()