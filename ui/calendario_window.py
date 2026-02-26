import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime, date
import calendar
from sqlalchemy import func
from core.database import SessionLocal, Lesson, Booking, Member

class PrenotazioneRapidaWindow(ctk.CTkToplevel):
    def __init__(self, parent, lesson_id, refresh_callback):
        super().__init__(parent)
        self.title("Aggiungi Partecipante")
        self.geometry("600x550")
        self.configure(fg_color=("#F2F2F7", "#1C1C1E"))
        self.lesson_id = lesson_id
        self.refresh_callback = refresh_callback
        self._search_timer = None 
        
        self.transient(parent.winfo_toplevel())
        self.grab_set()

        db = SessionLocal()
        lezione = db.query(Lesson).get(self.lesson_id)
        if not lezione: 
            db.close()
            self.destroy()
            return
            
        titolo = f"Prenota: {lezione.activity.name} ({lezione.start_time[:5]})"
        db.close()

        ctk.CTkLabel(self, text=titolo, font=ctk.CTkFont(family="Montserrat", size=18, weight="bold")).pack(pady=(20, 5))
        ctk.CTkLabel(self, text="Cerca per Nome, Cognome o Scheda:", font=ctk.CTkFont(family="Montserrat", size=13), text_color=("#86868B", "#98989D")).pack(pady=(5, 10))

        search_frame = ctk.CTkFrame(self, fg_color="transparent")
        search_frame.pack(fill="x", padx=30, pady=5)
        
        self.ent_ricerca = ctk.CTkEntry(search_frame, font=ctk.CTkFont(family="Montserrat", size=14))
        self.ent_ricerca.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.ent_ricerca.bind("<KeyRelease>", self.on_search_change)
        
        ctk.CTkButton(search_frame, text="Cerca", width=80, font=ctk.CTkFont(family="Montserrat", weight="bold"), command=self.cerca_soci).pack(side="right")

        self.scroll_risultati = ctk.CTkScrollableFrame(self, fg_color=("#FFFFFF", "#2C2C2E"), corner_radius=12, border_width=1, border_color=("#E5E5EA", "#3A3A3C"))
        self.scroll_risultati.pack(fill="both", expand=True, padx=30, pady=20)

        self.cerca_soci() 

    def on_search_change(self, event=None):
        if self._search_timer: self.after_cancel(self._search_timer)
        self._search_timer = self.after(300, self.cerca_soci) 

    def cerca_soci(self):
        for w in self.scroll_risultati.winfo_children(): w.destroy()
        
        termine = self.ent_ricerca.get().strip()
        
        db = SessionLocal()
        lezione = db.query(Lesson).get(self.lesson_id)
        soci_suggeriti = []
        mostra_suggeriti = False
        soci = []

        if termine:
            soci_db = db.query(Member).filter(
                (Member.first_name.ilike(f"%{termine}%")) |
                (Member.last_name.ilike(f"%{termine}%")) |
                (Member.badge_number.ilike(f"%{termine}%"))
            ).order_by(Member.first_name).limit(30).all()
            soci = list(soci_db)
        else:
            mostra_suggeriti = True
            soci_suggeriti = db.query(Member).\
                join(Booking).\
                join(Lesson).\
                filter(Lesson.activity_id == lezione.activity_id).\
                group_by(Member.id).\
                order_by(func.count(Booking.id).desc()).\
                limit(15).all()
            
            soci = list(soci_suggeriti)
            if len(soci) < 30:
                suggeriti_ids = [s.id for s in soci_suggeriti]
                query_altri = db.query(Member)
                if suggeriti_ids: query_altri = query_altri.filter(~Member.id.in_(suggeriti_ids))
                altri_soci = query_altri.order_by(Member.first_name).limit(30 - len(soci)).all()
                soci.extend(altri_soci)

        # Trasferisco in una lista di dict per liberare la sessione DB
        soci_data = []
        for s in soci:
            soci_data.append({
                "id": s.id,
                "first_name": s.first_name,
                "last_name": s.last_name,
                "badge_number": s.badge_number,
                "is_abituale": mostra_suggeriti and (s in soci_suggeriti)
            })
        db.close()

        if not soci_data:
            ctk.CTkLabel(self.scroll_risultati, text="Nessun socio trovato.", font=ctk.CTkFont(family="Montserrat", slant="italic"), text_color=("#86868B", "#98989D")).pack(pady=20)
            return

        if mostra_suggeriti and any(s["is_abituale"] for s in soci_data):
            ctk.CTkLabel(self.scroll_risultati, text="💡 In cima: Soci iscritti abitualmente a questo corso", font=ctk.CTkFont(family="Montserrat", size=12, slant="italic"), text_color="#007AFF").pack(pady=(5, 5), padx=10, anchor="w")

        for s in soci_data:
            riga = ctk.CTkFrame(self.scroll_risultati, fg_color="transparent")
            riga.pack(fill="x", pady=5)
            
            icona_stella = "⭐ " if s["is_abituale"] else ""
            nome_comp = f"{icona_stella}{s['first_name']} {s['last_name']}"
            if s['badge_number']: nome_comp += f" ({s['badge_number']})"
            
            ctk.CTkLabel(riga, text=nome_comp, font=ctk.CTkFont(family="Montserrat", size=14, weight="bold"), anchor="w").pack(side="left", padx=10)
            ctk.CTkButton(riga, text="Prenota", width=80, height=28, fg_color="#34C759", hover_color="#2eb350", font=ctk.CTkFont(family="Montserrat", weight="bold"), command=lambda s_id=s['id']: self.effettua_prenotazione(s_id)).pack(side="right", padx=10)
            ctk.CTkFrame(self.scroll_risultati, height=1, fg_color=("#E5E5EA", "#3A3A3C")).pack(fill="x", padx=10)

    def effettua_prenotazione(self, socio_id):
        db = SessionLocal()
        lezione = db.query(Lesson).get(self.lesson_id)
        
        esistente = db.query(Booking).filter_by(member_id=socio_id, lesson_id=self.lesson_id).first()
        if esistente:
            db.close()
            return messagebox.showwarning("Attenzione", "Il socio è già prenotato per questo corso!")
        
        occupati = db.query(Booking).filter_by(lesson_id=self.lesson_id).count()
        if occupati >= lezione.total_seats:
            if not messagebox.askyesno("Attenzione", "I posti per questo corso sono esauriti!\nVuoi forzare l'inserimento in Overbooking?"):
                db.close()
                return
                
        nuova = Booking(member_id=socio_id, lesson_id=self.lesson_id)
        db.add(nuova)
        db.commit()
        db.close()
        
        self.refresh_callback()
        self.grab_release()
        self.destroy()

class CalendarioView(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        
        oggi = datetime.now()
        self.current_year = oggi.year
        self.current_month = oggi.month
        self.selected_date = oggi.date()
        self.selected_lesson_id = None
        self.mesi_ita = ["", "Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno", "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"]

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=0, minsize=350)
        self.grid_columnconfigure(1, weight=0, minsize=350)
        self.grid_columnconfigure(2, weight=1)

        self.cal_frame = ctk.CTkFrame(self, fg_color=("#FFFFFF", "#2C2C2E"), corner_radius=12, border_width=1, border_color=("#E5E5EA", "#3A3A3C"))
        self.cal_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        nav_frame = ctk.CTkFrame(self.cal_frame, fg_color="transparent")
        nav_frame.pack(fill="x", pady=20, padx=20)
        
        ctk.CTkButton(nav_frame, text="◀", width=30, fg_color="transparent", text_color=("#1D1D1F", "#FFFFFF"), font=ctk.CTkFont(family="Montserrat", size=18, weight="bold"), hover_color=("#F2F2F7", "#3A3A3C"), command=self.mese_precedente).pack(side="left")
        self.lbl_mese_anno = ctk.CTkLabel(nav_frame, text="", font=ctk.CTkFont(family="Montserrat", size=18, weight="bold"))
        self.lbl_mese_anno.pack(side="left", expand=True)
        ctk.CTkButton(nav_frame, text="▶", width=30, fg_color="transparent", text_color=("#1D1D1F", "#FFFFFF"), font=ctk.CTkFont(family="Montserrat", size=18, weight="bold"), hover_color=("#F2F2F7", "#3A3A3C"), command=self.mese_successivo).pack(side="right")

        giorni_frame = ctk.CTkFrame(self.cal_frame, fg_color="transparent")
        giorni_frame.pack(fill="x", padx=10)
        for i, g in enumerate(["Lun", "Mar", "Mer", "Gio", "Ven", "Sab", "Dom"]):
            giorni_frame.grid_columnconfigure(i, weight=1)
            ctk.CTkLabel(giorni_frame, text=g, font=ctk.CTkFont(family="Montserrat", size=12, weight="bold"), text_color=("#86868B", "#98989D")).grid(row=0, column=i, pady=5)

        self.grid_giorni = ctk.CTkFrame(self.cal_frame, fg_color="transparent")
        self.grid_giorni.pack(fill="both", expand=True, padx=10, pady=(0, 20))
        for i in range(7): self.grid_giorni.grid_columnconfigure(i, weight=1)
        for i in range(6): self.grid_giorni.grid_rowconfigure(i, weight=1)

        self.les_frame = ctk.CTkFrame(self, fg_color=("#FFFFFF", "#2C2C2E"), corner_radius=12, border_width=1, border_color=("#E5E5EA", "#3A3A3C"))
        self.les_frame.grid(row=0, column=1, sticky="nsew", padx=(0, 10))
        
        self.lbl_data_corsi = ctk.CTkLabel(self.les_frame, text="Corsi del Giorno", font=ctk.CTkFont(family="Montserrat", size=16, weight="bold"))
        self.lbl_data_corsi.pack(pady=(20, 10), padx=20, anchor="w")
        
        self.scroll_corsi = ctk.CTkScrollableFrame(self.les_frame, fg_color="transparent")
        self.scroll_corsi.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.det_frame = ctk.CTkFrame(self, fg_color=("#FFFFFF", "#2C2C2E"), corner_radius=12, border_width=1, border_color=("#E5E5EA", "#3A3A3C"))
        self.det_frame.grid(row=0, column=2, sticky="nsew")
        
        self.lbl_dettaglio_corso = ctk.CTkLabel(self.det_frame, text="Nessun corso selezionato", font=ctk.CTkFont(family="Montserrat", size=18, weight="bold"), text_color=("#1D1D1F", "#FFFFFF"))
        self.lbl_dettaglio_corso.pack(pady=(20, 5), padx=20, anchor="w")
        
        self.lbl_info_corso = ctk.CTkLabel(self.det_frame, text="Seleziona un corso dalla colonna centrale", font=ctk.CTkFont(family="Montserrat", size=13), text_color=("#86868B", "#98989D"))
        self.lbl_info_corso.pack(padx=20, anchor="w", pady=(0, 10))

        self.scroll_prenotati = ctk.CTkScrollableFrame(self.det_frame, fg_color="transparent")
        self.scroll_prenotati.pack(fill="both", expand=True, padx=10)

        self.btn_aggiungi_pren = ctk.CTkButton(self.det_frame, text="+ Aggiungi Prenotazione", height=45, font=ctk.CTkFont(family="Montserrat", size=16, weight="bold"), fg_color="#34C759", hover_color="#2eb350", command=self.apri_popup_prenotazione)
        self.btn_aggiungi_pren.pack(fill="x", padx=20, pady=20)
        self.btn_aggiungi_pren.pack_forget() 

        self.disegna_calendario()

    def mese_precedente(self):
        if self.current_month == 1: self.current_month = 12; self.current_year -= 1
        else: self.current_month -= 1
        self.disegna_calendario()

    def mese_successivo(self):
        if self.current_month == 12: self.current_month = 1; self.current_year += 1
        else: self.current_month += 1
        self.disegna_calendario()

    def disegna_calendario(self):
        self.lbl_mese_anno.configure(text=f"{self.mesi_ita[self.current_month]} {self.current_year}")
        for w in self.grid_giorni.winfo_children(): w.destroy()

        cal = calendar.monthcalendar(self.current_year, self.current_month)
        oggi = datetime.now().date()

        for riga, settimana in enumerate(cal):
            for col, giorno in enumerate(settimana):
                if giorno != 0:
                    data_corrente = date(self.current_year, self.current_month, giorno)
                    
                    if data_corrente == self.selected_date: bg_color = "#007AFF"; txt_color = "white"
                    elif data_corrente == oggi: bg_color = ("#E5E5EA", "#3A3A3C"); txt_color = ("#1D1D1F", "#FFFFFF")
                    else: bg_color = "transparent"; txt_color = ("#1D1D1F", "#FFFFFF")

                    btn = ctk.CTkButton(self.grid_giorni, text=str(giorno), width=35, height=35, corner_radius=17, fg_color=bg_color, text_color=txt_color, font=ctk.CTkFont(family="Montserrat", size=14, weight="bold"), hover_color=("#F2F2F7", "#3A3A3C") if bg_color == "transparent" else bg_color, command=lambda d=data_corrente: self.seleziona_giorno(d))
                    btn.grid(row=riga, column=col, padx=2, pady=2)

        self.carica_corsi_giorno()

    def seleziona_giorno(self, data_selezionata):
        self.selected_date = data_selezionata
        self.selected_lesson_id = None
        self.disegna_calendario()
        self.pulisci_dettagli()

    def carica_corsi_giorno(self):
        for w in self.scroll_corsi.winfo_children(): w.destroy()
        
        data_str = self.selected_date.strftime("%Y-%m-%d")
        self.lbl_data_corsi.configure(text=f"Corsi del {self.selected_date.strftime('%d/%m/%Y')}")

        db = SessionLocal()
        lezioni = db.query(Lesson).filter(Lesson.date == data_str).order_by(Lesson.start_time).all()
        
        lez_data = []
        for l in lezioni:
            occupati = db.query(Booking).filter_by(lesson_id=l.id).count()
            lez_data.append({
                "id": l.id,
                "start_time": l.start_time[:5],
                "end_time": l.end_time[:5],
                "activity_name": l.activity.name,
                "total_seats": l.total_seats,
                "occupati": occupati
            })
        db.close()

        if not lez_data:
            ctk.CTkLabel(self.scroll_corsi, text="Nessun corso programmato.", font=ctk.CTkFont(family="Montserrat", slant="italic"), text_color=("#86868B", "#98989D")).pack(pady=40)
            return

        for l in lez_data:
            f = ctk.CTkFrame(self.scroll_corsi, fg_color=("#E5F1FF", "#0A2A4A") if self.selected_lesson_id == l["id"] else "transparent", corner_radius=8, cursor="hand2")
            f.pack(fill="x", pady=2)
            
            ctk.CTkLabel(f, text=l["start_time"], font=ctk.CTkFont(family="Montserrat", size=14, weight="bold"), text_color=("#007AFF", "#0A84FF")).pack(side="left", padx=(15, 10), pady=12)
            
            info_frame = ctk.CTkFrame(f, fg_color="transparent")
            info_frame.pack(side="left", fill="x", expand=True)
            ctk.CTkLabel(info_frame, text=l["activity_name"], font=ctk.CTkFont(family="Montserrat", size=14, weight="bold"), anchor="w").pack(fill="x")
            
            badge_color = "#34C759" if l["occupati"] < l["total_seats"] else "#FF3B30"
            badge = ctk.CTkFrame(f, fg_color=badge_color, corner_radius=6, height=22, width=60)
            badge.pack(side="right", padx=15)
            badge.pack_propagate(False)
            ctk.CTkLabel(badge, text=f"{l['occupati']}/{l['total_seats']}", text_color="white", font=ctk.CTkFont(family="Montserrat", size=12, weight="bold")).place(relx=0.5, rely=0.5, anchor="center")

            for widget in [f, info_frame] + info_frame.winfo_children():
                widget.bind("<Button-1>", lambda e, l_id=l["id"]: self.mostra_dettagli_lezione(l_id))

    def pulisci_dettagli(self):
        self.lbl_dettaglio_corso.configure(text="Nessun corso selezionato")
        self.lbl_info_corso.configure(text="Seleziona un corso dalla colonna centrale")
        for w in self.scroll_prenotati.winfo_children(): w.destroy()
        self.btn_aggiungi_pren.pack_forget()

    def mostra_dettagli_lezione(self, lesson_id):
        self.selected_lesson_id = lesson_id
        self.carica_corsi_giorno() 
        
        db = SessionLocal()
        lezione = db.query(Lesson).get(lesson_id)
        if lezione:
            self.lbl_dettaglio_corso.configure(text=lezione.activity.name)
            self.lbl_info_corso.configure(text=f"Orario: {lezione.start_time[:5]} - {lezione.end_time[:5]}")
            self.btn_aggiungi_pren.pack(fill="x", padx=20, pady=20)
        db.close()

        self.carica_lista_prenotati()

    def carica_lista_prenotati(self):
        for w in self.scroll_prenotati.winfo_children(): w.destroy()
        if not self.selected_lesson_id: return
        
        db = SessionLocal()
        prenotazioni = db.query(Booking).filter_by(lesson_id=self.selected_lesson_id).join(Member).order_by(Member.first_name).all()
        pren_data = [{"id": p.id, "nome_comp": f"{p.member.first_name} {p.member.last_name}"} for p in prenotazioni]
        db.close()
        
        if not pren_data:
            ctk.CTkLabel(self.scroll_prenotati, text="Nessun socio prenotato.", font=ctk.CTkFont(family="Montserrat", slant="italic"), text_color=("#86868B", "#98989D")).pack(pady=40)
            return

        for p in pren_data:
            f = ctk.CTkFrame(self.scroll_prenotati, fg_color="transparent")
            f.pack(fill="x", pady=2)
            
            ctk.CTkLabel(f, text=p["nome_comp"], font=ctk.CTkFont(family="Montserrat", size=14, weight="bold")).pack(side="left", padx=10, pady=8)
            ctk.CTkButton(f, text="X", width=28, height=28, fg_color="#FF3B30", hover_color="#c0392b", font=ctk.CTkFont(family="Montserrat", weight="bold"), command=lambda b_id=p["id"]: self.rimuovi_prenotazione(b_id)).pack(side="right", padx=10)
            ctk.CTkFrame(self.scroll_prenotati, height=1, fg_color=("#E5E5EA", "#3A3A3C")).pack(fill="x", padx=10)

    def rimuovi_prenotazione(self, booking_id):
        if messagebox.askyesno("Conferma", "Vuoi annullare questa prenotazione?"):
            db = SessionLocal()
            b = db.query(Booking).get(booking_id)
            if b:
                db.delete(b)
                db.commit()
            db.close()
            self.carica_lista_prenotati()
            self.carica_corsi_giorno() 

    def apri_popup_prenotazione(self):
        if not self.selected_lesson_id: return
        def on_refresh():
            self.carica_lista_prenotati()
            self.carica_corsi_giorno()
            
        PrenotazioneRapidaWindow(self, self.selected_lesson_id, on_refresh)