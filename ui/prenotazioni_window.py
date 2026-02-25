import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime
from core.database import SessionLocal, Booking, Member, Lesson

class PrenotazioneFormWindow(ctk.CTkToplevel):
    def __init__(self, parent, refresh_callback):
        super().__init__(parent)
        self.title("Nuova Prenotazione")
        self.geometry("550x650")
        self.configure(fg_color=("#F2F2F7", "#1C1C1E"))
        self.refresh_callback = refresh_callback
        self.transient(parent.winfo_toplevel())
        self.grab_set()

        ctk.CTkLabel(self, text="Nuova Prenotazione", font=ctk.CTkFont(family="Ubuntu", size=22, weight="bold")).pack(pady=(20, 10))
        self.db = SessionLocal()
        self.socio_selezionato = ctk.IntVar(value=0)
        self.lezione_selezionata = ctk.IntVar(value=0)
        self.soci = self.db.query(Member).order_by(Member.first_name).all()
        self.lezioni = self.db.query(Lesson).filter(Lesson.date >= datetime.now().strftime("%Y-%m-%d")).order_by(Lesson.date, Lesson.start_time).all()

        f_socio = ctk.CTkFrame(self, fg_color="transparent"); f_socio.pack(fill="x", padx=30, pady=(10, 5))
        ctk.CTkLabel(f_socio, text="1. Socio:", font=ctk.CTkFont(family="Ubuntu", weight="bold")).pack(side="left")
        self.ent_ricerca_socio = ctk.CTkEntry(f_socio, placeholder_text="Cerca...", width=250); self.ent_ricerca_socio.pack(side="right")
        self.ent_ricerca_socio.bind("<KeyRelease>", self.filtra_soci)
        self.scroll_soci = ctk.CTkScrollableFrame(self, height=150, fg_color=("#FFFFFF", "#2C2C2E"), border_width=1, border_color=("#E5E5EA", "#3A3A3C")); self.scroll_soci.pack(fill="x", padx=30, pady=(0, 15)); self.filtra_soci() 

        f_lez = ctk.CTkFrame(self, fg_color="transparent"); f_lez.pack(fill="x", padx=30, pady=(10, 5))
        ctk.CTkLabel(f_lez, text="2. Lezione:", font=ctk.CTkFont(family="Ubuntu", weight="bold")).pack(side="left")
        self.ent_ricerca_lez = ctk.CTkEntry(f_lez, placeholder_text="Cerca...", width=250); self.ent_ricerca_lez.pack(side="right")
        self.ent_ricerca_lez.bind("<KeyRelease>", self.filtra_lezioni)
        self.scroll_lezioni = ctk.CTkScrollableFrame(self, height=150, fg_color=("#FFFFFF", "#2C2C2E"), border_width=1, border_color=("#E5E5EA", "#3A3A3C")); self.scroll_lezioni.pack(fill="x", padx=30, pady=(0, 20)); self.filtra_lezioni() 

        ctk.CTkButton(self, text="Conferma", width=200, height=38, font=ctk.CTkFont(family="Ubuntu", weight="bold"), fg_color="#34C759", command=self.salva_prenotazione).pack(pady=10)

    def filtra_soci(self, event=None):
        t = self.ent_ricerca_socio.get().lower(); trovati = 0
        for w in self.scroll_soci.winfo_children(): w.destroy()
        for s in self.soci:
            if t in f"{s.first_name} {s.last_name} {s.badge_number or ''}".lower():
                rb = ctk.CTkRadioButton(self.scroll_soci, text=f"Scheda: {s.badge_number or '-'} | {s.first_name} {s.last_name}", variable=self.socio_selezionato, value=s.id, font=ctk.CTkFont(family="Ubuntu"))
                rb.pack(anchor="w", pady=5, padx=10); trovati += 1
        if not trovati: ctk.CTkLabel(self.scroll_soci, text="Nessun socio.", font=ctk.CTkFont(family="Ubuntu", slant="italic")).pack(pady=10)

    def filtra_lezioni(self, event=None):
        t = self.ent_ricerca_lez.get().lower(); trovati = 0
        for w in self.scroll_lezioni.winfo_children(): w.destroy()
        for l in self.lezioni:
            att = l.activity.name if l.activity else '?'
            d_ita = datetime.strptime(l.date, "%Y-%m-%d").strftime("%d/%m/%Y")
            if t in f"{att} {d_ita} {l.start_time}".lower():
                occ = self.db.query(Booking).filter(Booking.lesson_id == l.id).count()
                testo = f"{d_ita} ore {l.start_time} - {att} [{occ}/{l.total_seats}]"
                rb = ctk.CTkRadioButton(self.scroll_lezioni, text=testo, variable=self.lezione_selezionata, value=l.id, font=ctk.CTkFont(family="Ubuntu"))
                if occ >= l.total_seats: rb.configure(state="disabled", text=testo + " (ESAURITA)")
                rb.pack(anchor="w", pady=5, padx=10); trovati += 1
        if not trovati: ctk.CTkLabel(self.scroll_lezioni, text="Nessuna lezione.", font=ctk.CTkFont(family="Ubuntu", slant="italic")).pack(pady=10)

    def salva_prenotazione(self):
        s_id = self.socio_selezionato.get(); l_id = self.lezione_selezionata.get()
        if not s_id or not l_id: return messagebox.showwarning("Errore", "Seleziona entrambi.")
        socio = self.db.query(Member).filter(Member.id == s_id).first(); lezione = self.db.query(Lesson).filter(Lesson.id == l_id).first()

        if not socio.membership_expiration: return messagebox.showerror("Bloccato", "Abbonamento mancante.")
        try:
            s_socio = datetime.strptime(socio.membership_expiration, "%d/%m/%Y" if "/" in socio.membership_expiration else "%Y-%m-%d").date()
            d_lez = datetime.strptime(lezione.date, "%Y-%m-%d").date()
            if s_socio < d_lez: return messagebox.showerror("Bloccato", f"L'abbonamento scade il {s_socio.strftime('%d/%m/%Y')}.")
        except ValueError: return messagebox.showerror("Errore", "Formato data errato.")

        if self.db.query(Booking).filter(Booking.lesson_id == l_id).count() >= lezione.total_seats: return messagebox.showerror("Esaurito", "Al completo!")
        if self.db.query(Booking).filter(Booking.member_id == s_id, Booking.lesson_id == l_id).first(): return messagebox.showwarning("Attenzione", "Già prenotato.")

        self.db.add(Booking(member_id=s_id, lesson_id=l_id)); self.db.commit(); self.db.close()
        self.refresh_callback(); self.destroy()

class PrenotazioniView(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self.db = SessionLocal()
        self.row_frames = {}
        self.selected_booking_id = None

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        top = ctk.CTkFrame(self, fg_color="transparent"); top.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        ctk.CTkLabel(top, text="Prenotazioni Attive", font=ctk.CTkFont(family="Ubuntu", size=24, weight="bold")).pack(side="left")
        ctk.CTkButton(top, text="+ Nuova", width=150, height=38, font=ctk.CTkFont(family="Ubuntu", weight="bold"), fg_color="#34C759", command=self.apri_form).pack(side="right")

        self.table_container = ctk.CTkFrame(self, fg_color="transparent"); self.table_container.grid(row=1, column=0, sticky="nsew")
        self.cols = [("socio", "Socio", 2), ("attivita", "Attività", 2), ("data", "Data", 1), ("ora", "Ora", 1)]
        h = ctk.CTkFrame(self.table_container, fg_color=("#E5E5EA", "#3A3A3C"), height=35, corner_radius=6); h.pack(fill="x", pady=(0, 5))
        for i, col in enumerate(self.cols):
            h.grid_columnconfigure(i, weight=col[2])
            ctk.CTkLabel(h, text=col[1], font=ctk.CTkFont(family="Ubuntu", size=12, weight="bold")).grid(row=0, column=i, padx=10, pady=5, sticky="w")
        self.scroll_table = ctk.CTkScrollableFrame(self.table_container, fg_color="transparent"); self.scroll_table.pack(fill="both", expand=True)

        ctk.CTkButton(self, text="🗑️ Annulla Prenotazione", width=200, height=38, font=ctk.CTkFont(family="Ubuntu", weight="bold"), fg_color="#FF3B30", command=self.elimina_prenotazione).grid(row=2, column=0, pady=15, sticky="e")
        self.carica_dati()

    def seleziona_riga(self, b_id):
        self.selected_booking_id = b_id
        for r_id, f in self.row_frames.items(): f.configure(fg_color=("#E5F1FF", "#0A2A4A") if r_id == b_id else ("#FFFFFF", "#2C2C2E"), border_color="#007AFF" if r_id == b_id else ("#E5E5EA", "#3A3A3C"))

    def crea_riga_tabella(self, p):
        f = ctk.CTkFrame(self.scroll_table, fg_color=("#FFFFFF", "#2C2C2E"), height=45, corner_radius=8, border_width=1, border_color=("#E5E5EA", "#3A3A3C"), cursor="hand2")
        f.pack(fill="x", pady=2); f.pack_propagate(False)
        v = [f"{p.member.first_name} {p.member.last_name}" if p.member else "?", p.lesson.activity.name if p.lesson and p.lesson.activity else "?", datetime.strptime(p.lesson.date, "%Y-%m-%d").strftime("%d/%m/%Y") if p.lesson else "-", p.lesson.start_time if p.lesson else "-"]
        el = [f]
        for i, val in enumerate(v):
            f.grid_columnconfigure(i, weight=self.cols[i][2])
            l = ctk.CTkLabel(f, text=val, font=ctk.CTkFont(family="Ubuntu", size=13)); l.grid(row=0, column=i, padx=10, pady=10, sticky="w"); el.append(l)
        for w in el:
            w.bind("<Button-1>", lambda e, id=p.id: self.seleziona_riga(id))
            w.bind("<Enter>", lambda e, fr=f, id=p.id: fr.configure(fg_color=("#F8F8F9", "#3A3A3C")) if self.selected_booking_id != id else None)
            w.bind("<Leave>", lambda e, fr=f, id=p.id: fr.configure(fg_color=("#FFFFFF", "#2C2C2E")) if self.selected_booking_id != id else None)
        self.row_frames[p.id] = f

    def carica_dati(self):
        for w in self.scroll_table.winfo_children(): w.destroy()
        self.row_frames.clear(); self.selected_booking_id = None
        for p in self.db.query(Booking).join(Lesson).filter(Lesson.date >= datetime.now().strftime("%Y-%m-%d")).order_by(Lesson.date, Lesson.start_time).all(): self.crea_riga_tabella(p)

    def apri_form(self): PrenotazioneFormWindow(self, refresh_callback=self.carica_dati)
    def elimina_prenotazione(self):
        if not self.selected_booking_id: return messagebox.showwarning("Attenzione", "Seleziona.")
        if messagebox.askyesno("Conferma", "Annullare?"):
            b = self.db.query(Booking).filter(Booking.id == self.selected_booking_id).first()
            if b: self.db.delete(b); self.db.commit(); self.carica_dati()

    def destroy(self):
        self.db.close()
        super().destroy()