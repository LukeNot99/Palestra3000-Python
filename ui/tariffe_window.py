import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime
from core.repositories import TierRepository
from core.config.settings import Settings

class TiersView(ctk.CTkFrame):
    def __init__(self, parent, controller=None, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.tier_id_in_modifica = None
        self.row_frames = {}
        self.selected_tier_id = None
        self.font_row = ctk.CTkFont(family="Montserrat", size=13)
        self.settings = Settings()
        self.show_cost = self.settings.get("mostra_costo_fasce", False)
        self.show_age = self.settings.get("mostra_eta_fasce", False)

        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        form_frame = ctk.CTkFrame(self, fg_color=("#FFFFFF", "#2C2C2E"), corner_radius=12, border_width=1, border_color=("#E5E5EA", "#3A3A3C"))
        form_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=20)
        form_frame.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform="colonna")

        self.lbl_tier_name = ctk.CTkLabel(form_frame, text="Sigla Fascia:", text_color=("#86868B", "#98989D"), font=ctk.CTkFont(family="Montserrat", weight="bold"))
        self.ent_tier_name = ctk.CTkEntry(form_frame, width=180, font=ctk.CTkFont(family="Montserrat"))

        self.lbl_cost = ctk.CTkLabel(form_frame, text="Costo (€):", text_color=("#86868B", "#98989D"), font=ctk.CTkFont(family="Montserrat", weight="bold"))
        self.ent_cost = ctk.CTkEntry(form_frame, width=180, justify="center", placeholder_text="0.00", font=ctk.CTkFont(family="Montserrat"))

        self.lbl_age = ctk.CTkLabel(form_frame, text="Età (Min - Max):", text_color=("#86868B", "#98989D"), font=ctk.CTkFont(family="Montserrat", weight="bold"))
        self.frame_age = ctk.CTkFrame(form_frame, fg_color="transparent")
        self.ent_min_age = ctk.CTkEntry(self.frame_age, width=70, justify="center", font=ctk.CTkFont(family="Montserrat")); self.ent_min_age.insert(0, "0"); self.ent_min_age.pack(side="left")
        ctk.CTkLabel(self.frame_age, text=" - ", font=ctk.CTkFont(family="Montserrat")).pack(side="left", padx=5)
        self.ent_max_age = ctk.CTkEntry(self.frame_age, width=70, justify="center", font=ctk.CTkFont(family="Montserrat")); self.ent_max_age.insert(0, "200"); self.ent_max_age.pack(side="left")

        self.lbl_hours = ctk.CTkLabel(form_frame, text="Orari Accesso (HH:MM):", text_color=("#86868B", "#98989D"), font=ctk.CTkFont(family="Montserrat", weight="bold"))
        self.frame_hours = ctk.CTkFrame(form_frame, fg_color="transparent")
        self.ent_start_time = ctk.CTkEntry(self.frame_hours, width=70, justify="center", font=ctk.CTkFont(family="Montserrat")); self.ent_start_time.insert(0, "00:00"); self.ent_start_time.pack(side="left")
        ctk.CTkLabel(self.frame_hours, text=" - ", font=ctk.CTkFont(family="Montserrat")).pack(side="left", padx=5)
        self.ent_end_time = ctk.CTkEntry(self.frame_hours, width=70, justify="center", font=ctk.CTkFont(family="Montserrat")); self.ent_end_time.insert(0, "23:59"); self.ent_end_time.pack(side="left")

        self.lbl_duration = ctk.CTkLabel(form_frame, text="Durata Abbonamento (Mesi):", text_color=("#1D1D1F", "#FFFFFF"), font=ctk.CTkFont(family="Montserrat", weight="bold"))
        self.ent_duration = ctk.CTkEntry(form_frame, width=180, justify="center", text_color=("#007AFF", "#0A84FF"), font=ctk.CTkFont(family="Montserrat", weight="bold")); self.ent_duration.insert(0, "1")

        self.lbl_entries = ctk.CTkLabel(form_frame, text="Carnet (0 = Illimitati):", text_color=("#1D1D1F", "#FFFFFF"), font=ctk.CTkFont(family="Montserrat", weight="bold"))
        self.ent_entries = ctk.CTkEntry(form_frame, width=180, justify="center", text_color=("#007AFF", "#0A84FF"), font=ctk.CTkFont(family="Montserrat", weight="bold")); self.ent_entries.insert(0, "0")

        active_fields = [(self.lbl_tier_name, self.ent_tier_name)]
        if self.show_cost: active_fields.append((self.lbl_cost, self.ent_cost))
        if self.show_age: active_fields.append((self.lbl_age, self.frame_age))
        active_fields.append((self.lbl_hours, self.frame_hours))
        active_fields.append((self.lbl_duration, self.ent_duration))
        active_fields.append((self.lbl_entries, self.ent_entries))

        for i, (lbl, wgt) in enumerate(active_fields):
            riga = i // 2
            col = (i % 2) * 2
            lbl.grid(row=riga, column=col, sticky="e", padx=(20, 10), pady=15)
            wgt.grid(row=riga, column=col+1, sticky="w", padx=(0, 20), pady=15)

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=5)

        self.btn_save = ctk.CTkButton(btn_frame, text="Salva Dati", width=140, height=38, font=ctk.CTkFont(family="Montserrat", size=14, weight="bold"), fg_color="#34C759", hover_color="#2eb350", command=self.save_tier)
        self.btn_save.pack(side="left", padx=(0, 10))

        ctk.CTkButton(btn_frame, text="Svuota Form", width=120, height=38, font=ctk.CTkFont(family="Montserrat", size=14, weight="bold"), fg_color=("#E5E5EA", "#3A3A3C"), text_color=("#1D1D1F", "#FFFFFF"), hover_color=("#D1D1D6", "#5C5C5E"), command=self.clear_form).pack(side="left")
        
        ctk.CTkButton(btn_frame, text="✏️ Modifica", width=140, height=38, font=ctk.CTkFont(family="Montserrat", size=14, weight="bold"), fg_color="#007AFF", hover_color="#005ecb", command=self.load_into_form).pack(side="left", padx=(20, 10))
        ctk.CTkButton(btn_frame, text="🗑️ Elimina", width=120, height=38, font=ctk.CTkFont(family="Montserrat", size=14, weight="bold"), fg_color="#FF3B30", hover_color="#e03026", command=self.delete_tier).pack(side="right")

        self.table_container = ctk.CTkFrame(self, fg_color="transparent")
        self.table_container.grid(row=2, column=0, sticky="nsew", padx=20, pady=(10, 20))
        
        self.cols = [("sigla", "Sigla Fascia", 2, "w")]
        if self.show_cost: self.cols.append(("costo", "Costo", 1, "center"))
        if self.show_age: self.cols.append(("eta", "Età (Min-Max)", 1, "center"))
        self.cols.extend([
            ("orari", "Accesso/Uscita", 2, "center"), 
            ("durata", "Durata", 1, "center"), 
            ("ingressi", "Carnet", 1, "center")
        ])

        header_frame = ctk.CTkFrame(self.table_container, fg_color=("#E5E5EA", "#3A3A3C"), height=35, corner_radius=6)
        header_frame.pack(fill="x", pady=(0, 5))
        
        for i, col in enumerate(self.cols):
            header_frame.grid_columnconfigure(i, weight=col[2], uniform="colonna")
            ctk.CTkLabel(header_frame, text=col[1], font=ctk.CTkFont(family="Montserrat", size=12, weight="bold"), text_color=("#86868B", "#98989D"), anchor=col[3]).grid(row=0, column=i, padx=10, pady=5, sticky="ew")

        self.scroll_table = ctk.CTkScrollableFrame(self.table_container, fg_color="transparent")
        self.scroll_table.pack(fill="both", expand=True)

        self.load_data()

    def select_row(self, t_id):
        self.selected_tier_id = t_id
        for r_id, frame in self.row_frames.items():
            if frame.winfo_exists():
                if r_id == t_id:
                    frame.configure(fg_color=("#E5F1FF", "#0A2A4A"), border_color="#007AFF")
                else:
                    frame.configure(fg_color=("#FFFFFF", "#2C2C2E"), border_color=("#E5E5EA", "#3A3A3C"))

    def clear_form(self):
        self.ent_tier_name.delete(0, 'end')
        if self.show_age:
            self.ent_min_age.delete(0, 'end'); self.ent_min_age.insert(0, "0")
            self.ent_max_age.delete(0, 'end'); self.ent_max_age.insert(0, "200")
        if self.show_cost: self.ent_cost.delete(0, 'end')
        self.ent_start_time.delete(0, 'end'); self.ent_start_time.insert(0, "00:00")
        self.ent_end_time.delete(0, 'end'); self.ent_end_time.insert(0, "23:59")
        self.ent_duration.delete(0, 'end'); self.ent_duration.insert(0, "1")
        self.ent_entries.delete(0, 'end'); self.ent_entries.insert(0, "0")
        
        self.tier_id_in_modifica = None
        self.btn_save.configure(text="Salva Dati", fg_color="#34C759", hover_color="#2eb350")
        self.selected_tier_id = None
        self.load_data()

    def create_table_row(self, t):
        row_frame = ctk.CTkFrame(self.scroll_table, fg_color=("#FFFFFF", "#2C2C2E"), height=45, corner_radius=8, border_width=1, border_color=("#E5E5EA", "#3A3A3C"), cursor="hand2")
        row_frame.pack(fill="x", pady=2)
        row_frame.pack_propagate(False)

        valori = [t["name"]]
        if self.show_cost: valori.append(f"€ {t['cost']:.2f}")
        if self.show_age: valori.append(f"{t['min_age']} - {t['max_age']} anni")
        valori.extend([
            f"{t['start_time'][:5]} - {t['end_time'][:5]}",
            f"{t['duration_months']} Mesi",
            "Illimitati" if t['max_entries'] == 0 else f"{t['max_entries']} Ingressi"
        ])

        row_elements = [row_frame]
        for i, val in enumerate(valori):
            row_frame.grid_columnconfigure(i, weight=self.cols[i][2], uniform="colonna")
            lbl = ctk.CTkLabel(row_frame, text=val, font=self.font_row, text_color=("#1D1D1F", "#FFFFFF"), anchor=self.cols[i][3])
            lbl.grid(row=0, column=i, padx=10, pady=10, sticky="ew")
            row_elements.append(lbl)

        for w in row_elements:
            w.bind("<Button-1>", lambda e, id=t["id"]: self.select_row(id))
            w.bind("<Enter>", lambda e, f=row_frame, id=t["id"]: f.configure(fg_color=("#F8F8F9", "#3A3A3C")) if f.winfo_exists() and self.selected_tier_id != id else None)
            w.bind("<Leave>", lambda e, f=row_frame, id=t["id"]: f.configure(fg_color=("#FFFFFF", "#2C2C2E")) if f.winfo_exists() and self.selected_tier_id != id else None)

        self.row_frames[t["id"]] = row_frame

    def load_data(self):
        for widget in self.scroll_table.winfo_children(): widget.destroy()
        self.row_frames.clear()
        
        tariffe = TierRepository.get_all()
        for t in tariffe:
            self.create_table_row(t)

    def load_into_form(self):
        if not self.selected_tier_id: return messagebox.showwarning("Attenzione", "Seleziona una fascia.")
        
        tariffa = TierRepository.get_by_id(self.selected_tier_id)
        if tariffa:
            self.clear_form()
            self.ent_tier_name.delete(0, 'end'); self.ent_tier_name.insert(0, tariffa["name"])
            if self.show_age:
                self.ent_min_age.delete(0, 'end'); self.ent_min_age.insert(0, str(tariffa["min_age"]))
                self.ent_max_age.delete(0, 'end'); self.ent_max_age.insert(0, str(tariffa["max_age"]))
            if self.show_cost:
                self.ent_cost.delete(0, 'end'); self.ent_cost.insert(0, str(tariffa["cost"]))
            self.ent_start_time.delete(0, 'end'); self.ent_start_time.insert(0, tariffa["start_time"][:5])
            self.ent_end_time.delete(0, 'end'); self.ent_end_time.insert(0, tariffa["end_time"][:5])
            self.ent_duration.delete(0, 'end'); self.ent_duration.insert(0, str(tariffa["duration_months"]))
            self.ent_entries.delete(0, 'end'); self.ent_entries.insert(0, str(tariffa["max_entries"]))
            
            self.tier_id_in_modifica = tariffa["id"]
            self.btn_save.configure(text="Aggiorna Dati", fg_color="#007AFF", hover_color="#005ecb")

    def save_tier(self):
        sigla = self.ent_tier_name.get().strip()
        if not sigla: return messagebox.showwarning("Errore", "La sigla è obbligatoria.")
        accesso = self.ent_start_time.get().strip()
        uscita = self.ent_end_time.get().strip()
        
        try:
            datetime.strptime(accesso, "%H:%M")
            datetime.strptime(uscita, "%H:%M")
        except ValueError:
            return messagebox.showwarning("Errore Orario", "Verifica gli orari di accesso e uscita nel formato HH:MM.")

        try:
            costo = float(self.ent_cost.get().strip().replace(',', '.')) if self.show_cost else 0.0
            eta_min = int(self.ent_min_age.get().strip()) if self.show_age else 0
            eta_max = int(self.ent_max_age.get().strip()) if self.show_age else 999
            durata_mesi = int(self.ent_duration.get().strip() or 1)
            ingressi = int(self.ent_entries.get().strip() or 0)
            
            if costo < 0 or eta_min < 0 or eta_max < 0 or durata_mesi < 1 or ingressi < 0:
                return messagebox.showwarning("Errore Logico", "Valori negativi o nulli (la durata deve essere minimo 1).")
            if eta_max < eta_min:
                return messagebox.showwarning("Errore Logico", "L'età massima non può essere inferiore all'età minima.")
        except ValueError:
            return messagebox.showwarning("Errore", "Verifica che Costo, Età, Durata e Ingressi siano numeri validi.")

        data = {
            "name": sigla, "cost": costo, "min_age": eta_min, "max_age": eta_max,
            "start_time": accesso, "end_time": uscita, "duration_months": durata_mesi,
            "max_entries": ingressi
        }
        
        TierRepository.save(data, self.tier_id_in_modifica)
        self.clear_form()
        self.load_data()

    def delete_tier(self):
        if not self.selected_tier_id: return messagebox.showwarning("Attenzione", "Seleziona una fascia.")
        
        soci_collegati = TierRepository.count_linked_members(self.selected_tier_id)
        if soci_collegati > 0: 
            return messagebox.showerror("Errore", f"Ci sono {soci_collegati} soci iscritti con questa fascia!")

        if messagebox.askyesno("Conferma", "Sei sicuro di voler eliminare questa fascia?"):
            TierRepository.delete(self.selected_tier_id)
            self.clear_form()
            self.load_data()