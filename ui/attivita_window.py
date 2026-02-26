import customtkinter as ctk
from tkinter import messagebox
from core.database import SessionLocal, Activity, Lesson, Booking

class AttivitaView(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self.row_frames = {}
        self.selected_activity_id = None

        input_frame = ctk.CTkFrame(self, fg_color=("#FFFFFF", "#2C2C2E"), corner_radius=12, border_width=1, border_color=("#E5E5EA", "#3A3A3C"))
        input_frame.pack(fill="x", pady=(0, 20))

        ctk.CTkLabel(input_frame, text="📋 Nuova Attività", font=ctk.CTkFont(family="Montserrat", size=18, weight="bold")).pack(pady=(15, 5), padx=20, anchor="w")
        
        row = ctk.CTkFrame(input_frame, fg_color="transparent")
        row.pack(fill="x", padx=20, pady=(15, 20))
        self.ent_nome = ctk.CTkEntry(row, placeholder_text="Es. Pilates, Yoga...", width=250, font=ctk.CTkFont(family="Montserrat"))
        self.ent_nome.pack(side="left", padx=(0, 10))
        ctk.CTkButton(row, text="Inserisci", width=140, height=38, font=ctk.CTkFont(family="Montserrat", weight="bold"), fg_color="#34C759", command=self.inserisci_attivita).pack(side="left")

        self.table_container = ctk.CTkFrame(self, fg_color="transparent")
        self.table_container.pack(fill="both", expand=True, pady=(0, 10))

        header_frame = ctk.CTkFrame(self.table_container, fg_color=("#E5E5EA", "#3A3A3C"), height=35, corner_radius=6)
        header_frame.pack(fill="x", pady=(0, 5))
        header_frame.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(header_frame, text="Nome Attività", font=ctk.CTkFont(family="Montserrat", size=12, weight="bold"), anchor="w").grid(row=0, column=0, padx=20, pady=5, sticky="w")

        self.scroll_table = ctk.CTkScrollableFrame(self.table_container, fg_color="transparent")
        self.scroll_table.pack(fill="both", expand=True)

        bottom_frame = ctk.CTkFrame(self, fg_color="transparent")
        bottom_frame.pack(fill="x", pady=(0, 0))
        ctk.CTkButton(bottom_frame, text="🗑️ Elimina Selezionata", width=200, height=38, font=ctk.CTkFont(family="Montserrat", weight="bold"), fg_color="#FF3B30", command=self.elimina_attivita).pack(side="right")

        self.carica_dati()

    def seleziona_riga(self, a_id):
        self.selected_activity_id = a_id
        for r_id, f in self.row_frames.items(): 
            f.configure(fg_color=("#E5F1FF", "#0A2A4A") if r_id == a_id else ("#FFFFFF", "#2C2C2E"), border_color="#007AFF" if r_id == a_id else ("#E5E5EA", "#3A3A3C"))

    def crea_riga_tabella(self, attivita):
        f = ctk.CTkFrame(self.scroll_table, fg_color=("#FFFFFF", "#2C2C2E"), height=45, corner_radius=8, border_width=1, border_color=("#E5E5EA", "#3A3A3C"), cursor="hand2")
        f.pack(fill="x", pady=2); f.pack_propagate(False); f.grid_columnconfigure(0, weight=1)
        lbl = ctk.CTkLabel(f, text=attivita.name, font=ctk.CTkFont(family="Montserrat", size=14, weight="bold"), anchor="w")
        lbl.grid(row=0, column=0, padx=20, pady=10, sticky="w")
        for w in [f, lbl]:
            w.bind("<Button-1>", lambda e, id=attivita.id: self.seleziona_riga(id))
            w.bind("<Enter>", lambda e, fr=f, id=attivita.id: fr.configure(fg_color=("#F8F8F9", "#3A3A3C")) if self.selected_activity_id != id else None)
            w.bind("<Leave>", lambda e, fr=f, id=attivita.id: fr.configure(fg_color=("#FFFFFF", "#2C2C2E")) if self.selected_activity_id != id else None)
        self.row_frames[attivita.id] = f

    def carica_dati(self):
        for w in self.scroll_table.winfo_children(): w.destroy()
        self.row_frames.clear()
        self.selected_activity_id = None
        
        db = SessionLocal()
        for a in db.query(Activity).order_by(Activity.name).all(): 
            self.crea_riga_tabella(a)
        db.close()

    def inserisci_attivita(self):
        nome = self.ent_nome.get().strip()
        if not nome: return messagebox.showwarning("Attenzione", "Inserisci nome.")
        
        db = SessionLocal()
        if db.query(Activity).filter(Activity.name.ilike(nome)).first(): 
            db.close()
            return messagebox.showerror("Errore", "Esiste già.")
        db.add(Activity(name=nome))
        db.commit()
        db.close()
        
        self.ent_nome.delete(0, 'end')
        self.carica_dati()

    def elimina_attivita(self):
        if not self.selected_activity_id: 
            return messagebox.showwarning("Attenzione", "Seleziona un'attività dalla lista.")
            
        db = SessionLocal()
        a = db.query(Activity).filter(Activity.id == self.selected_activity_id).first()
        if not a: 
            db.close()
            return

        lezioni_collegate = db.query(Lesson).filter(Lesson.activity_id == a.id).all()
        
        if lezioni_collegate:
            msg = (f"⚠️ ATTENZIONE!\nCi sono {len(lezioni_collegate)} lezioni collegate a '{a.name}'.\n"
                   "Eliminando l'attività cancellerai anche le lezioni e le relative prenotazioni.\nProcedere?")
            if not messagebox.askyesno("Conferma", msg, icon="warning"):
                db.close()
                return
                
            for lez in lezioni_collegate:
                db.query(Booking).filter(Booking.lesson_id == lez.id).delete()
            db.query(Lesson).filter(Lesson.activity_id == a.id).delete()
        else:
            if not messagebox.askyesno("Conferma", f"Vuoi eliminare l'attività '{a.name}'?"):
                db.close()
                return

        nome_att = a.name
        db.delete(a)
        db.commit()
        db.close()
        
        self.carica_dati()
        messagebox.showinfo("Completato", f"Attività '{nome_att}' eliminata.")