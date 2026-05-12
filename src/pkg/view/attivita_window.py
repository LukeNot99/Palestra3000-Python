import customtkinter as ctk
from tkinter import messagebox

class ActivitiesView(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self.activity_repository = self.app.di.get_activity_repository()
        self.row_frames = {}
        self.selected_activity_id = None

        input_frame = ctk.CTkFrame(self, fg_color=("#FFFFFF", "#2C2C2E"), corner_radius=12, border_width=1, border_color=("#E5E5EA", "#3A3A3C"))
        input_frame.pack(fill="x", pady=(0, 20))

        ctk.CTkLabel(input_frame, text="📋 Nuova Attività", font=ctk.CTkFont(family="Montserrat", size=18, weight="bold")).pack(pady=(15, 5), padx=20, anchor="w")
        
        row = ctk.CTkFrame(input_frame, fg_color="transparent")
        row.pack(fill="x", padx=20, pady=(15, 20))
        self.ent_name = ctk.CTkEntry(row, placeholder_text="Es. Pilates, Yoga...", width=250, font=ctk.CTkFont(family="Montserrat"))
        self.ent_name.pack(side="left", padx=(0, 10))
        ctk.CTkButton(row, text="Inserisci", width=140, height=38, font=ctk.CTkFont(family="Montserrat", weight="bold"), fg_color="#34C759", command=self.insert_activity).pack(side="left")

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
        ctk.CTkButton(bottom_frame, text="🗑️ Elimina Selezionata", width=200, height=38, font=ctk.CTkFont(family="Montserrat", weight="bold"), fg_color="#FF3B30", command=self.delete_activity).pack(side="right")

        self.load_data()

    def select_row(self, a_id):
        self.selected_activity_id = a_id
        for r_id, f in self.row_frames.items(): 
            f.configure(fg_color=("#E5F1FF", "#0A2A4A") if r_id == a_id else ("#FFFFFF", "#2C2C2E"), border_color="#007AFF" if r_id == a_id else ("#E5E5EA", "#3A3A3C"))

    def create_table_row(self, activity_data):
        f = ctk.CTkFrame(self.scroll_table, fg_color=("#FFFFFF", "#2C2C2E"), height=45, corner_radius=8, border_width=1, border_color=("#E5E5EA", "#3A3A3C"), cursor="hand2")
        f.pack(fill="x", pady=2); f.pack_propagate(False); f.grid_columnconfigure(0, weight=1)
        
        lbl = ctk.CTkLabel(f, text=activity_data["name"], font=ctk.CTkFont(family="Montserrat", size=14, weight="bold"), anchor="w")
        lbl.grid(row=0, column=0, padx=20, pady=10, sticky="w")
        
        for w in [f, lbl]:
            w.bind("<Button-1>", lambda e, id=activity_data["id"]: self.select_row(id))
            w.bind("<Enter>", lambda e, fr=f, id=activity_data["id"]: fr.configure(fg_color=("#F8F8F9", "#3A3A3C")) if self.selected_activity_id != id else None)
            w.bind("<Leave>", lambda e, fr=f, id=activity_data["id"]: fr.configure(fg_color=("#FFFFFF", "#2C2C2E")) if self.selected_activity_id != id else None)
        
        self.row_frames[activity_data["id"]] = f

    def load_data(self):
        for w in self.scroll_table.winfo_children(): w.destroy()
        self.row_frames.clear()
        self.selected_activity_id = None
        
        activities = self.activity_repository.get_all()
        for a in activities: 
            self.create_table_row(a)

    def insert_activity(self):
        act_name = self.ent_name.get().strip()
        if not act_name: return messagebox.showwarning("Attenzione", "Inserisci nome.")
        
        if self.activity_repository.check_exists(act_name): 
            return messagebox.showerror("Errore", "Esiste già.")
            
        self.activity_repository.save(act_name)
        self.ent_name.delete(0, 'end')
        self.load_data()

    def delete_activity(self):
        if not self.selected_activity_id: 
            return messagebox.showwarning("Attenzione", "Seleziona un'attività dalla lista.")
            
        linked_lessons_count = self.activity_repository.get_linked_lessons_count(self.selected_activity_id)
        force_cascade = False
        
        if linked_lessons_count > 0:
            msg = (f"⚠️ ATTENZIONE!\nCi sono {linked_lessons_count} lezioni collegate a questa attività.\n"
                   "Eliminandola cancellerai anche le lezioni e le relative prenotazioni.\nProcedere?")
            if not messagebox.askyesno("Conferma", msg, icon="warning"): return
            force_cascade = True
        else:
            if not messagebox.askyesno("Conferma", f"Vuoi eliminare questa attività?"): return

        success = self.activity_repository.delete(self.selected_activity_id, force_cascade=force_cascade)
        if success:
            self.load_data()
            messagebox.showinfo("Completato", "Attività eliminata con successo.")
