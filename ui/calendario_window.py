import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime, date, timedelta
import calendar
from core.database import SessionLocal, Lesson, Booking

class CalendarioView(ctk.CTkFrame):
    def __init__(self, parent, controller=None, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.db = SessionLocal()

        self.oggi = datetime.now().date()
        self.anno_corrente = self.oggi.year
        self.mese_corrente = self.oggi.month
        self.giorno_selezionato = self.oggi
        
        self.lezione_selezionata_id = None
        self.row_frames = {}

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1) 
        self.grid_columnconfigure(1, weight=1) 
        self.grid_columnconfigure(2, weight=1) 

        # ==================== PANNELLO 1: GRIGLIA MENSILE ====================
        cal_panel = ctk.CTkFrame(self, fg_color=("#FFFFFF", "#2C2C2E"), corner_radius=16, border_width=1, border_color=("#E5E5EA", "#3A3A3C"))
        cal_panel.grid(row=0, column=0, sticky="nsew", padx=(20, 10), pady=20)

        header_cal = ctk.CTkFrame(cal_panel, fg_color="transparent")
        header_cal.pack(fill="x", pady=(20, 10), padx=15)

        ctk.CTkButton(header_cal, text="◀", width=35, height=30, fg_color=("#E5E5EA", "#3A3A3C"), text_color=("#1D1D1F", "#FFFFFF"), hover_color=("#D1D1D6", "#5C5C5E"), command=self.mese_prec).pack(side="left")
        self.lbl_mese_anno = ctk.CTkLabel(header_cal, text="Mese Anno", font=ctk.CTkFont(family="Montserrat", size=18, weight="bold"), text_color=("#1D1D1F", "#FFFFFF"))
        self.lbl_mese_anno.pack(side="left", expand=True)
        ctk.CTkButton(header_cal, text="▶", width=35, height=30, fg_color=("#E5E5EA", "#3A3A3C"), text_color=("#1D1D1F", "#FFFFFF"), hover_color=("#D1D1D6", "#5C5C5E"), command=self.mese_succ).pack(side="right")

        self.grid_giorni = ctk.CTkFrame(cal_panel, fg_color="transparent")
        self.grid_giorni.pack(pady=10, padx=15, expand=True)

        ctk.CTkButton(cal_panel, text="Torna a Oggi", width=120, height=30, fg_color="#007AFF", hover_color="#005ecb", command=self.torna_a_oggi).pack(pady=(0, 20))

        # ==================== PANNELLO 2: CORSI DEL GIORNO ====================
        corsi_panel = ctk.CTkFrame(self, fg_color="transparent")
        corsi_panel.grid(row=0, column=1, sticky="nsew", padx=10, pady=20)

        self.lbl_data_corsi = ctk.CTkLabel(corsi_panel, text="Corsi del Giorno", font=ctk.CTkFont(family="Montserrat", size=20, weight="bold"), text_color=("#1D1D1F", "#FFFFFF"))
        self.lbl_data_corsi.pack(anchor="w", pady=(0, 15))

        self.scroll_lezioni = ctk.CTkScrollableFrame(corsi_panel, fg_color="transparent")
        self.scroll_lezioni.pack(fill="both", expand=True)

        # ==================== PANNELLO 3: DETTAGLIO SALA ====================
        self.dettaglio_panel = ctk.CTkFrame(self, fg_color=("#FFFFFF", "#2C2C2E"), corner_radius=16, border_width=1, border_color=("#E5E5EA", "#3A3A3C"))
        self.dettaglio_panel.grid(row=0, column=2, sticky="nsew", padx=(10, 20), pady=20)

        self.lbl_dettaglio_titolo = ctk.CTkLabel(self.dettaglio_panel, text="Seleziona un corso", font=ctk.CTkFont(family="Montserrat", size=22, weight="bold"), text_color=("#1D1D1F", "#FFFFFF"))
        self.lbl_dettaglio_titolo.pack(pady=(20, 5), padx=15)

        self.lbl_dettaglio_orario = ctk.CTkLabel(self.dettaglio_panel, text="Per vedere i partecipanti", font=ctk.CTkFont(family="Montserrat", size=15), text_color=("#86868B", "#98989D"))
        self.lbl_dettaglio_orario.pack(pady=(0, 15))

        self.lbl_occupazione = ctk.CTkLabel(self.dettaglio_panel, text="", font=ctk.CTkFont(family="Montserrat", size=15, weight="bold"))
        self.lbl_occupazione.pack(pady=(0, 15))

        self.scroll_partecipanti = ctk.CTkScrollableFrame(self.dettaglio_panel, fg_color="transparent")
        self.scroll_partecipanti.pack(fill="both", expand=True, padx=15, pady=(0, 20))

        # Avvio Iniziale
        self.disegna_calendario()

    # --- LOGICA CALENDARIO MENSILE ---
    def mese_prec(self):
        if self.mese_corrente == 1:
            self.mese_corrente = 12
            self.anno_corrente -= 1
        else:
            self.mese_corrente -= 1
        self.disegna_calendario()

    def mese_succ(self):
        if self.mese_corrente == 12:
            self.mese_corrente = 1
            self.anno_corrente += 1
        else:
            self.mese_corrente += 1
        self.disegna_calendario()

    def torna_a_oggi(self):
        self.giorno_selezionato = self.oggi
        self.anno_corrente = self.oggi.year
        self.mese_corrente = self.oggi.month
        self.disegna_calendario()

    def seleziona_data(self, giorno):
        self.giorno_selezionato = date(self.anno_corrente, self.mese_corrente, giorno)
        self.disegna_calendario() 

    def disegna_calendario(self):
        for w in self.grid_giorni.winfo_children(): w.destroy()

        nomi_mesi = ["", "Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno", "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"]
        self.lbl_mese_anno.configure(text=f"{nomi_mesi[self.mese_corrente]} {self.anno_corrente}")

        giorni_sett = ["Lun", "Mar", "Mer", "Gio", "Ven", "Sab", "Dom"]
        for i, g in enumerate(giorni_sett):
            ctk.CTkLabel(self.grid_giorni, text=g, font=ctk.CTkFont(family="Montserrat", weight="bold"), text_color=("#86868B", "#98989D")).grid(row=0, column=i, padx=5, pady=5)

        mese_str = f"{self.anno_corrente}-{self.mese_corrente:02d}-"
        lezioni_mese = self.db.query(Lesson.date).filter(Lesson.date.like(f"{mese_str}%")).all()
        giorni_con_lezioni = {int(l[0].split("-")[2]) for l in lezioni_mese}

        cal = calendar.monthcalendar(self.anno_corrente, self.mese_corrente)

        for riga, settimana in enumerate(cal):
            for col, giorno in enumerate(settimana):
                if giorno != 0:
                    is_selected = (self.giorno_selezionato == date(self.anno_corrente, self.mese_corrente, giorno))
                    is_today = (self.oggi == date(self.anno_corrente, self.mese_corrente, giorno))
                    has_lesson = giorno in giorni_con_lezioni

                    fg_color = "transparent"
                    text_color = ("#1D1D1F", "#FFFFFF")
                    
                    # FIX DELL'ERRORE CTK: Usiamo i colori del tema invece di 'transparent' per il bordo
                    border_color = ("#FFFFFF", "#2C2C2E") # Stesso colore del pannello del calendario
                    border_width = 0

                    if has_lesson: 
                        text_color = "#34C759" 
                    
                    if is_today:
                        border_color = "#FF3B30" 
                        border_width = 2
                        
                    if is_selected:
                        fg_color = "#007AFF" 
                        text_color = "white" 
                        border_width = 0

                    btn = ctk.CTkButton(self.grid_giorni, text=str(giorno), width=40, height=40, corner_radius=20,
                                        fg_color=fg_color, text_color=text_color, hover_color=("#E5E5EA", "#3A3A3C"),
                                        border_color=border_color, border_width=border_width,
                                        font=ctk.CTkFont(family="Montserrat", size=14, weight="bold"),
                                        command=lambda g=giorno: self.seleziona_data(g))
                    btn.grid(row=riga+1, column=col, padx=4, pady=4)
        
        self.aggiorna_lista_corsi()

    # --- LOGICA COLONNA CENTRALE (Lista Corsi) ---
    def aggiorna_lista_corsi(self):
        # FIX DEFINITIVO ITALIANO: Svincoliamoci dal formato di sistema per evitare l'inglese
        giorni_ita = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]
        mesi_ita = ["", "Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno", "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"]
        
        nome_giorno = giorni_ita[self.giorno_selezionato.weekday()]
        nome_mese = mesi_ita[self.giorno_selezionato.month]
        
        # Formatta es: "Lunedì, 25 Febbraio"
        data_str_formattata = f"{nome_giorno}, {self.giorno_selezionato.day} {nome_mese}"
        self.lbl_data_corsi.configure(text=data_str_formattata)
        
        for widget in self.scroll_lezioni.winfo_children(): widget.destroy()
        self.row_frames.clear()
        self.lezione_selezionata_id = None
        self.svuota_dettaglio()

        data_db_str = self.giorno_selezionato.strftime("%Y-%m-%d")
        lezioni = self.db.query(Lesson).filter(Lesson.date == data_db_str).order_by(Lesson.start_time).all()

        if not lezioni:
            ctk.CTkLabel(self.scroll_lezioni, text="Nessun corso in programma oggi.", font=ctk.CTkFont(family="Montserrat", slant="italic"), text_color=("#86868B", "#98989D")).pack(pady=40)
            return

        for l in lezioni:
            self.crea_card_lezione(l)

    def crea_card_lezione(self, l):
        card = ctk.CTkFrame(self.scroll_lezioni, fg_color=("#FFFFFF", "#2C2C2E"), height=70, corner_radius=12, border_width=1, border_color=("#E5E5EA", "#3A3A3C"), cursor="hand2")
        card.pack(fill="x", pady=5, padx=5)
        card.pack_propagate(False)

        nome_att = l.activity.name if l.activity else "Attività"
        occupati = self.db.query(Booking).filter(Booking.lesson_id == l.id).count()

        left_side = ctk.CTkFrame(card, fg_color="transparent")
        left_side.pack(side="left", padx=15, expand=True, fill="both")

        ctk.CTkLabel(left_side, text=nome_att, font=ctk.CTkFont(family="Montserrat", size=16, weight="bold"), text_color=("#1D1D1F", "#FFFFFF"), anchor="w").pack(anchor="w", pady=(10, 0))
        ctk.CTkLabel(left_side, text=f"🕒 {l.start_time} - {l.end_time}", font=ctk.CTkFont(family="Montserrat", size=12), text_color=("#86868B", "#98989D"), anchor="w").pack(anchor="w")

        colore_badge = "#34C759" 
        if occupati >= l.total_seats: colore_badge = "#FF3B30" 
        elif occupati >= (l.total_seats * 0.8): colore_badge = "#FF9500" 

        badge = ctk.CTkFrame(card, fg_color=colore_badge, corner_radius=8, width=60, height=30)
        badge.pack(side="right", padx=15)
        badge.pack_propagate(False)
        ctk.CTkLabel(badge, text=f"{occupati}/{l.total_seats}", text_color="white", font=ctk.CTkFont(family="Montserrat", size=13, weight="bold")).place(relx=0.5, rely=0.5, anchor="center")

        elementi = [card, left_side, badge] + left_side.winfo_children() + badge.winfo_children()
        for w in elementi:
            w.bind("<Button-1>", lambda e, id=l.id: self.seleziona_lezione(id))
            w.bind("<Enter>", lambda e, f=card, id=l.id: f.configure(fg_color=("#F8F8F9", "#3A3A3C")) if self.lezione_selezionata_id != id else None)
            w.bind("<Leave>", lambda e, f=card, id=l.id: f.configure(fg_color=("#FFFFFF", "#2C2C2E")) if self.lezione_selezionata_id != id else None)

        self.row_frames[l.id] = card

    # --- LOGICA COLONNA DESTRA (Dettagli) ---
    def seleziona_lezione(self, lezione_id):
        self.lezione_selezionata_id = lezione_id
        for l_id, card in self.row_frames.items():
            if l_id == lezione_id:
                card.configure(fg_color=("#E5F1FF", "#0A2A4A"), border_color="#007AFF")
            else:
                card.configure(fg_color=("#FFFFFF", "#2C2C2E"), border_color=("#E5E5EA", "#3A3A3C"))
        
        self.carica_dettaglio_lezione(lezione_id)

    def svuota_dettaglio(self):
        self.lbl_dettaglio_titolo.configure(text="Seleziona un corso")
        self.lbl_dettaglio_orario.configure(text="Per vedere i partecipanti")
        self.lbl_occupazione.configure(text="")
        for widget in self.scroll_partecipanti.winfo_children(): widget.destroy()

    def carica_dettaglio_lezione(self, lezione_id):
        for widget in self.scroll_partecipanti.winfo_children(): widget.destroy()

        lezione = self.db.query(Lesson).filter(Lesson.id == lezione_id).first()
        prenotazioni = self.db.query(Booking).filter(Booking.lesson_id == lezione_id).all()

        nome_att = lezione.activity.name if lezione.activity else "Attività"
        self.lbl_dettaglio_titolo.configure(text=nome_att)
        self.lbl_dettaglio_orario.configure(text=f"🕒 Dalle {lezione.start_time} alle {lezione.end_time}")

        occupati = len(prenotazioni)
        testo_occ = f"Stato: {occupati} / {lezione.total_seats} Posti Occupati"
        colore_testo = "#34C759" if occupati < lezione.total_seats else "#FF3B30"
        self.lbl_occupazione.configure(text=testo_occ, text_color=colore_testo)

        if not prenotazioni:
            ctk.CTkLabel(self.scroll_partecipanti, text="Nessun iscritto al momento.", font=ctk.CTkFont(family="Montserrat", slant="italic"), text_color=("#86868B", "#98989D")).pack(pady=20)
        else:
            prenotazioni_ordinate = sorted(prenotazioni, key=lambda p: (p.member.first_name, p.member.last_name) if p.member else ("", ""))
            for i, p in enumerate(prenotazioni_ordinate):
                if p.member:
                    riga = ctk.CTkFrame(self.scroll_partecipanti, fg_color="transparent")
                    riga.pack(fill="x", pady=2, padx=5)
                    
                    num = ctk.CTkLabel(riga, text=f"{i+1}.", font=ctk.CTkFont(family="Montserrat", weight="bold"), text_color=("#86868B", "#98989D"), width=25, anchor="e")
                    num.pack(side="left", padx=(0, 10))
                    
                    nome_cognome = f"{p.member.first_name} {p.member.last_name}"
                    ctk.CTkLabel(riga, text=nome_cognome, font=ctk.CTkFont(family="Montserrat", size=14), text_color=("#1D1D1F", "#FFFFFF")).pack(side="left")
                    
                    if p.member.badge_number:
                        ctk.CTkLabel(riga, text=f"(Id: {p.member.badge_number})", font=ctk.CTkFont(family="Montserrat", size=12), text_color=("#86868B", "#98989D")).pack(side="right")
                    
                    ctk.CTkFrame(self.scroll_partecipanti, height=1, fg_color=("#E5E5EA", "#3A3A3C")).pack(fill="x")