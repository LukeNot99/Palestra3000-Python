import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime, date, timedelta
from core.database import SessionLocal, Lesson, Activity
from core.utils import parse_date  # IMPORTIAMO L'UTILITY

class LezioniView(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self.row_frames = {}
        self.selected_lesson_ids = set()

        self.font_riga = ctk.CTkFont(family="Montserrat", size=13)

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        left_frame = ctk.CTkFrame(self, width=240, fg_color=("#FFFFFF", "#2C2C2E"), corner_radius=12, border_width=1, border_color=("#E5E5EA", "#3A3A3C"))
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 20))
        
        ctk.CTkLabel(left_frame, text="📅 Periodo Generazione", font=ctk.CTkFont(family="Montserrat", size=16, weight="bold")).pack(pady=(20, 5))
        
        self.ent_data_inizio = ctk.CTkEntry(left_frame, placeholder_text="Dal: GG/MM/AAAA", justify="center")
        self.ent_data_inizio.pack(pady=5, padx=20, fill="x")
        self.ent_data_inizio.insert(0, datetime.now().strftime("%d/%m/%Y")) 
        
        self.ent_data_fine = ctk.CTkEntry(left_frame, placeholder_text="Al: GG/MM/AAAA", justify="center")
        self.ent_data_fine.pack(pady=5, padx=20, fill="x")
        futuro = datetime.now() + timedelta(days=30)
        self.ent_data_fine.insert(0, futuro.strftime("%d/%m/%Y"))

        ctk.CTkLabel(left_frame, text="Giorni della Settimana:", font=ctk.CTkFont(family="Montserrat", weight="bold")).pack(pady=(15, 5))
        self.giorni_vars = {i: ctk.IntVar() for i in range(7)}
        for i, nome in enumerate(["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]):
            ctk.CTkCheckBox(left_frame, text=nome, variable=self.giorni_vars[i], font=ctk.CTkFont(family="Montserrat")).pack(anchor="w", padx=30, pady=3)

        ctk.CTkLabel(left_frame, text="Inizio (19:00):", font=ctk.CTkFont(family="Montserrat", weight="bold")).pack(pady=(15, 0))
        self.ent_inizio = ctk.CTkEntry(left_frame, justify="center"); self.ent_inizio.pack(pady=5, padx=20, fill="x")
        
        ctk.CTkLabel(left_frame, text="Fine (20:00):", font=ctk.CTkFont(family="Montserrat", weight="bold")).pack(pady=(5, 0))
        self.ent_fine = ctk.CTkEntry(left_frame, justify="center"); self.ent_fine.pack(pady=5, padx=20, fill="x")
        
        ctk.CTkLabel(left_frame, text="Posti:", font=ctk.CTkFont(family="Montserrat", weight="bold")).pack(pady=(5, 0))
        self.ent_posti = ctk.CTkEntry(left_frame, justify="center"); self.ent_posti.insert(0, "60"); self.ent_posti.pack(pady=5, padx=20, fill="x")

        ctk.CTkButton(left_frame, text="⚡ Genera Periodo", width=160, height=38, font=ctk.CTkFont(family="Montserrat", weight="bold"), fg_color="#34C759", hover_color="#2eb350", command=self.genera_lezioni).pack(pady=20)

        right_frame = ctk.CTkFrame(self, fg_color="transparent")
        right_frame.grid(row=0, column=1, sticky="nsew")
        right_frame.grid_rowconfigure(1, weight=1)
        right_frame.grid_columnconfigure(0, weight=1)

        top_right = ctk.CTkFrame(right_frame, fg_color="transparent")
        top_right.grid(row=0, column=0, sticky="ew", pady=(0, 15))
        
        ctk.CTkLabel(top_right, text="Attività:", font=ctk.CTkFont(family="Montserrat", size=14, weight="bold"), text_color=("#1D1D1F", "#FFFFFF")).pack(side="left", padx=(0, 5))
        
        db = SessionLocal()
        activities = db.query(Activity).order_by(Activity.name).all()
        act_names = [a.name for a in activities] if activities else ["Nessuna attività registrata"]
        db.close()
        
        self.cmb_attivita = ctk.CTkOptionMenu(top_right, values=act_names, font=ctk.CTkFont(family="Montserrat", size=14), width=180, fg_color="#007AFF", command=self.carica_tabella)
        self.cmb_attivita.pack(side="left", padx=(0, 20))

        ctk.CTkLabel(top_right, text="Mostra:", font=ctk.CTkFont(family="Montserrat", size=14, weight="bold"), text_color=("#1D1D1F", "#FFFFFF")).pack(side="left", padx=(0, 5))
        
        mesi_str = [f"{i:02d}" for i in range(1, 13)]
        anno_oggi = datetime.now().year
        anni_str = [str(anno_oggi - 1), str(anno_oggi), str(anno_oggi + 1), str(anno_oggi + 2)]

        self.cmb_filtro_mese = ctk.CTkOptionMenu(top_right, values=mesi_str, width=70, font=ctk.CTkFont(family="Montserrat", size=14), command=self.carica_tabella)
        self.cmb_filtro_mese.set(f"{datetime.now().month:02d}")
        self.cmb_filtro_mese.pack(side="left", padx=(0, 5))

        self.cmb_filtro_anno = ctk.CTkOptionMenu(top_right, values=anni_str, width=80, font=ctk.CTkFont(family="Montserrat", size=14), command=self.carica_tabella)
        self.cmb_filtro_anno.set(str(anno_oggi))
        self.cmb_filtro_anno.pack(side="left")

        self.table_container = ctk.CTkFrame(right_frame, fg_color="transparent")
        self.table_container.grid(row=1, column=0, sticky="nsew")
        
        self.cols = [
            ("data", "Data", 2, "w"), 
            ("giorno", "Giorno", 2, "w"), 
            ("orario", "Orario", 3, "center"), 
            ("posti", "Posti Totali", 1, "center")
        ]
        
        header_tab = ctk.CTkFrame(self.table_container, fg_color=("#E5E5EA", "#3A3A3C"), height=35, corner_radius=6)
        header_tab.pack(fill="x", pady=(0, 5))
        for i, col in enumerate(self.cols):
            header_tab.grid_columnconfigure(i, weight=col[2], uniform="colonna")
            ctk.CTkLabel(header_tab, text=col[1], font=ctk.CTkFont(family="Montserrat", size=12, weight="bold"), anchor=col[3]).grid(row=0, column=i, padx=10, pady=5, sticky="ew")

        self.scroll_table = ctk.CTkScrollableFrame(self.table_container, fg_color="transparent")
        self.scroll_table.pack(fill="both", expand=True)

        ctk.CTkLabel(right_frame, text="💡 Suggerimento: Tieni premuto 'Ctrl' (Windows) o 'Cmd' (Mac) per selezionare più lezioni.", font=ctk.CTkFont(family="Montserrat", size=12, slant="italic"), text_color=("#86868B", "#98989D")).grid(row=2, column=0, pady=(15, 0), sticky="w")
        ctk.CTkButton(right_frame, text="🗑️ Elimina Selezionate", width=200, height=38, font=ctk.CTkFont(family="Montserrat", weight="bold"), fg_color="#FF3B30", hover_color="#c0392b", command=self.elimina_lezione).grid(row=2, column=0, pady=(15, 0), sticky="e")

        self.carica_tabella()

    def seleziona_riga(self, l_id, multi=False):
        if multi:
            if l_id in self.selected_lesson_ids: self.selected_lesson_ids.remove(l_id)
            else: self.selected_lesson_ids.add(l_id)
        else:
            self.selected_lesson_ids = {l_id}
            
        for r_id, f in self.row_frames.items():
            if f.winfo_exists():
                if r_id in self.selected_lesson_ids:
                    f.configure(fg_color=("#E5F1FF", "#0A2A4A"), border_color="#007AFF")
                else:
                    f.configure(fg_color=("#FFFFFF", "#2C2C2E"), border_color=("#E5E5EA", "#3A3A3C"))

    def crea_riga_tabella(self, l_data):
        f = ctk.CTkFrame(self.scroll_table, fg_color=("#FFFFFF", "#2C2C2E"), height=45, corner_radius=8, border_width=1, border_color=("#E5E5EA", "#3A3A3C"), cursor="hand2")
        f.pack(fill="x", pady=2); f.pack_propagate(False)
        
        valori = [
            l_data["data"], 
            l_data["giorno"], 
            l_data["orario"], 
            l_data["posti"]
        ]
        elems = [f]
        for i, val in enumerate(valori):
            f.grid_columnconfigure(i, weight=self.cols[i][2], uniform="colonna")
            lbl = ctk.CTkLabel(f, text=val, font=self.font_riga, anchor=self.cols[i][3])
            lbl.grid(row=0, column=i, padx=10, pady=10, sticky="ew")
            elems.append(lbl)
            
        l_id = l_data["id"]
        for w in elems:
            w.bind("<Button-1>", lambda e, lid=l_id: self.seleziona_riga(lid, multi=False))
            w.bind("<Control-Button-1>", lambda e, lid=l_id: self.seleziona_riga(lid, multi=True)) 
            w.bind("<Command-Button-1>", lambda e, lid=l_id: self.seleziona_riga(lid, multi=True)) 
            w.bind("<Enter>", lambda e, fr=f, lid=l_id: fr.configure(fg_color=("#F8F8F9", "#3A3A3C")) if fr.winfo_exists() and lid not in self.selected_lesson_ids else None)
            w.bind("<Leave>", lambda e, fr=f, lid=l_id: fr.configure(fg_color=("#FFFFFF", "#2C2C2E")) if fr.winfo_exists() and lid not in self.selected_lesson_ids else None)
        
        self.row_frames[l_id] = f

    def carica_tabella(self, *args):
        for w in self.scroll_table.winfo_children(): w.destroy()
        self.row_frames.clear()
        self.selected_lesson_ids.clear() 

        db = SessionLocal()
        activities = db.query(Activity).order_by(Activity.name).all()
        act_names = [a.name for a in activities] if activities else ["Nessuna attività registrata"]
        
        self.cmb_attivita.configure(values=act_names)
        if self.cmb_attivita.get() not in act_names:
            self.cmb_attivita.set(act_names[0])
        
        nome_att = self.cmb_attivita.get()
        if nome_att == "Nessuna attività registrata": 
            db.close()
            return

        att_id = next((a.id for a in activities if a.name == nome_att), None)
        if att_id:
            mese_selezionato = self.cmb_filtro_mese.get()
            anno_selezionato = self.cmb_filtro_anno.get()
            filtro_data = f"{anno_selezionato}-{mese_selezionato}-"

            lezioni = db.query(Lesson).filter(
                Lesson.activity_id == att_id,
                Lesson.date.like(f"{filtro_data}%")
            ).order_by(Lesson.date, Lesson.start_time).all()

            lez_data = []
            for l in lezioni:
                lez_data.append({
                    "id": l.id,
                    "data": datetime.strptime(l.date, "%Y-%m-%d").strftime("%d/%m/%Y") if l.date else "-",
                    "giorno": l.day_of_week,
                    "orario": f"{l.start_time} - {l.end_time}",
                    "posti": str(l.total_seats)
                })
        else:
            lez_data = []
        db.close()

        for l_d in lez_data:
            self.crea_riga_tabella(l_d)

    def genera_lezioni(self):
        nome_att = self.cmb_attivita.get()
        if nome_att == "Nessuna attività registrata":
            return messagebox.showwarning("Attenzione", "Devi prima creare almeno un'attività nella sezione 'Gestione Attività'!")

        ini = self.ent_inizio.get().strip()
        fin = self.ent_fine.get().strip()
        p = self.ent_posti.get().strip()
        
        if not ini or not fin or not p.isdigit(): 
            return messagebox.showwarning("Errore", "Verifica che i posti siano un numero valido e che gli orari non siano vuoti.")
        if int(p) <= 0:
            return messagebox.showwarning("Errore Logico", "Il numero di posti deve essere maggiore di zero.")
            
        try:
            ora_ini_dt = datetime.strptime(ini, "%H:%M")
            ora_fin_dt = datetime.strptime(fin, "%H:%M")
            if ora_ini_dt >= ora_fin_dt: return messagebox.showwarning("Errore Logico", "L'orario di fine lezione deve essere successivo all'orario di inizio.")
        except ValueError: return messagebox.showwarning("Errore Orario", "Inserisci orari validi nel formato HH:MM (es. 19:00 o 08:30).")
            
        # --- UTILIZZO UTILS.PY PER VALIDAZIONE DATA SICURA ---
        d_inizio = parse_date(self.ent_data_inizio.get())
        d_fine = parse_date(self.ent_data_fine.get())

        if not d_inizio or not d_fine:
            return messagebox.showwarning("Errore Data", "Le date inserite non sono valide (Usa formato GG/MM/AAAA).")
        
        d_inizio = d_inizio.date()
        d_fine = d_fine.date()
        
        if d_inizio > d_fine: 
            return messagebox.showwarning("Errore Logico", "La data 'Dal' non può essere successiva alla data 'Al'.")
        # -----------------------------------------------------

        g_scelti = [i for i in range(7) if self.giorni_vars[i].get() == 1]
        if not g_scelti: return messagebox.showwarning("Errore", "Spunta almeno un giorno della settimana.")

        g_nomi = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]
        count = 0
        
        db = SessionLocal()
        att = db.query(Activity).filter(Activity.name == nome_att).first()
        if not att:
            db.close()
            return
        att_id = att.id

        current_date = d_inizio
        while current_date <= d_fine:
            if current_date.weekday() in g_scelti:
                ds = current_date.strftime("%Y-%m-%d")
                if not db.query(Lesson).filter(Lesson.date == ds, Lesson.start_time == ini, Lesson.activity_id == att_id).first():
                    db.add(Lesson(date=ds, day_of_week=g_nomi[current_date.weekday()], start_time=ini, end_time=fin, total_seats=int(p), activity_id=att_id))
                    count += 1
            current_date += timedelta(days=1)
            
        db.commit()
        db.close()
        
        messagebox.showinfo("Completato", f"Pianificazione conclusa.\nSono state generate {count} nuove lezioni!")
        self.cmb_filtro_mese.set(f"{d_inizio.month:02d}")
        self.cmb_filtro_anno.set(str(d_inizio.year))
        self.carica_tabella()

    def elimina_lezione(self):
        if not self.selected_lesson_ids: 
            return messagebox.showwarning("Attenzione", "Seleziona almeno una lezione prima di eliminare.")
            
        messaggio = f"Vuoi davvero eliminare le {len(self.selected_lesson_ids)} lezioni selezionate?" if len(self.selected_lesson_ids) > 1 else "Vuoi annullare la lezione selezionata?"
        
        if messagebox.askyesno("Conferma", messaggio):
            db = SessionLocal()
            for l_id in self.selected_lesson_ids:
                l = db.query(Lesson).filter(Lesson.id == l_id).first()
                if l: db.delete(l)
            db.commit()
            db.close()
            
            self.selected_lesson_ids.clear()
            self.carica_tabella()