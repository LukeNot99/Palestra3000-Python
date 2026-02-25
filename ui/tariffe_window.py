import customtkinter as ctk
from tkinter import messagebox
from core.database import SessionLocal, Tier, Member

# ==================== SCHEDA PRINCIPALE: TariffeView (COME FRAME!) ====================
class TariffeView(ctk.CTkFrame):
    def __init__(self, parent, controller=None, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        
        self.db = SessionLocal()
        self.tier_id_in_modifica = None
        self.row_frames = {}
        self.selected_tariffa_id = None

        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # ==================== PANNELLO FORM ====================
        form_frame = ctk.CTkFrame(self, fg_color=("#FFFFFF", "#2C2C2E"), corner_radius=12, border_width=1, border_color=("#E5E5EA", "#3A3A3C"))
        form_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=20)
        
        row1 = ctk.CTkFrame(form_frame, fg_color="transparent")
        row1.pack(pady=(15, 5), fill="x", padx=10)
        
        ctk.CTkLabel(row1, text="Sigla Fascia:", text_color=("#86868B", "#98989D"), font=ctk.CTkFont(family="Ubuntu", weight="bold")).pack(side="left", padx=5)
        self.ent_sigla = ctk.CTkEntry(row1, width=150)
        self.ent_sigla.pack(side="left", padx=5)

        ctk.CTkLabel(row1, text="Età Min:", text_color=("#86868B", "#98989D"), font=ctk.CTkFont(family="Ubuntu")).pack(side="left", padx=(20, 5))
        self.ent_eta_min = ctk.CTkEntry(row1, width=60, justify="center")
        self.ent_eta_min.insert(0, "0")
        self.ent_eta_min.pack(side="left", padx=5)

        ctk.CTkLabel(row1, text="Età Max:", text_color=("#86868B", "#98989D"), font=ctk.CTkFont(family="Ubuntu")).pack(side="left", padx=(10, 5))
        self.ent_eta_max = ctk.CTkEntry(row1, width=60, justify="center")
        self.ent_eta_max.insert(0, "200")
        self.ent_eta_max.pack(side="left", padx=5)

        row2 = ctk.CTkFrame(form_frame, fg_color="transparent")
        row2.pack(pady=(5, 5), fill="x", padx=10)

        ctk.CTkLabel(row2, text="Costo (€):", text_color=("#86868B", "#98989D"), font=ctk.CTkFont(family="Ubuntu")).pack(side="left", padx=5)
        self.ent_costo = ctk.CTkEntry(row2, width=80, justify="center", placeholder_text="0.00")
        self.ent_costo.pack(side="left", padx=5)
        
        ctk.CTkLabel(row2, text="Accesso da:", text_color=("#86868B", "#98989D"), font=ctk.CTkFont(family="Ubuntu")).pack(side="left", padx=(20, 5))
        self.ent_accesso = ctk.CTkEntry(row2, width=90, justify="center")
        self.ent_accesso.insert(0, "00:00:00")
        self.ent_accesso.pack(side="left", padx=5)

        ctk.CTkLabel(row2, text="Uscita entro:", text_color=("#86868B", "#98989D"), font=ctk.CTkFont(family="Ubuntu")).pack(side="left", padx=(10, 5))
        self.ent_uscita = ctk.CTkEntry(row2, width=90, justify="center")
        self.ent_uscita.insert(0, "23:59:59")
        self.ent_uscita.pack(side="left", padx=5)

        row3 = ctk.CTkFrame(form_frame, fg_color="transparent")
        row3.pack(pady=(5, 15), fill="x", padx=10)

        ctk.CTkLabel(row3, text="Durata Abbonamento (Mesi):", text_color=("#1D1D1F", "#FFFFFF"), font=ctk.CTkFont(family="Ubuntu", weight="bold")).pack(side="left", padx=5)
        self.ent_durata = ctk.CTkEntry(row3, width=60, justify="center", text_color=("#007AFF", "#0A84FF"), font=ctk.CTkFont(family="Ubuntu", weight="bold"))
        self.ent_durata.insert(0, "1")
        self.ent_durata.pack(side="left", padx=5)

        ctk.CTkLabel(row3, text="Carnet (0=Illimitati):", text_color=("#1D1D1F", "#FFFFFF"), font=ctk.CTkFont(family="Ubuntu", weight="bold")).pack(side="left", padx=(30, 5))
        self.ent_ingressi = ctk.CTkEntry(row3, width=60, justify="center", text_color=("#007AFF", "#0A84FF"), font=ctk.CTkFont(family="Ubuntu", weight="bold"))
        self.ent_ingressi.insert(0, "0")
        self.ent_ingressi.pack(side="left", padx=5)

        # ==================== BOTTONIERA STANDARDIZZATA ====================
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=5)

        self.btn_salva = ctk.CTkButton(btn_frame, text="Salva Dati", width=140, height=38, font=ctk.CTkFont(family="Ubuntu", size=14, weight="bold"), fg_color="#34C759", hover_color="#2eb350", command=self.salva_tariffa)
        self.btn_salva.pack(side="left", padx=(0, 10))

        ctk.CTkButton(btn_frame, text="Svuota Form", width=120, height=38, font=ctk.CTkFont(family="Ubuntu", size=14, weight="bold"), fg_color=("#E5E5EA", "#3A3A3C"), text_color=("#1D1D1F", "#FFFFFF"), hover_color=("#D1D1D6", "#5C5C5E"), command=self.svuota_form).pack(side="left")
        
        ctk.CTkButton(btn_frame, text="✏️ Modifica", width=140, height=38, font=ctk.CTkFont(family="Ubuntu", size=14, weight="bold"), fg_color="#007AFF", hover_color="#005ecb", command=self.carica_in_form).pack(side="left", padx=(20, 10))
        ctk.CTkButton(btn_frame, text="🗑️ Elimina", width=120, height=38, font=ctk.CTkFont(family="Ubuntu", size=14, weight="bold"), fg_color="#FF3B30", hover_color="#e03026", command=self.elimina_tariffa).pack(side="right")

        # ==================== DATA GRID ====================
        self.table_container = ctk.CTkFrame(self, fg_color="transparent")
        self.table_container.grid(row=2, column=0, sticky="nsew", padx=20, pady=(10, 20))
        
        # NUOVA STRUTTURA: Aggiunta informazione sull'allineamento (w=sinistra, center=centro)
        self.cols = [
            ("sigla", "Sigla Fascia", 2, "w"), 
            ("costo", "Costo", 1, "center"), 
            ("eta", "Età (Min-Max)", 1, "center"), 
            ("orari", "Accesso/Uscita", 2, "center"), 
            ("durata", "Durata", 1, "center"), 
            ("ingressi", "Carnet", 1, "center")
        ]

        header_frame = ctk.CTkFrame(self.table_container, fg_color=("#E5E5EA", "#3A3A3C"), height=35, corner_radius=6)
        header_frame.pack(fill="x", pady=(0, 5))
        
        for i, col in enumerate(self.cols):
            # IL SEGRETO E' QUI: uniform="colonna"
            header_frame.grid_columnconfigure(i, weight=col[2], uniform="colonna")
            ctk.CTkLabel(header_frame, text=col[1], font=ctk.CTkFont(family="Ubuntu", size=12, weight="bold"), text_color=("#86868B", "#98989D"), anchor=col[3]).grid(row=0, column=i, padx=10, pady=5, sticky="ew")

        self.scroll_table = ctk.CTkScrollableFrame(self.table_container, fg_color="transparent")
        self.scroll_table.pack(fill="both", expand=True)

        self.carica_dati()

    def seleziona_riga(self, t_id):
        self.selected_tariffa_id = t_id
        for r_id, frame in self.row_frames.items():
            if r_id == t_id:
                frame.configure(fg_color=("#E5F1FF", "#0A2A4A"), border_color="#007AFF")
            else:
                frame.configure(fg_color=("#FFFFFF", "#2C2C2E"), border_color=("#E5E5EA", "#3A3A3C"))

    def svuota_form(self):
        self.ent_sigla.delete(0, 'end')
        self.ent_eta_min.delete(0, 'end'); self.ent_eta_min.insert(0, "0")
        self.ent_eta_max.delete(0, 'end'); self.ent_eta_max.insert(0, "200")
        self.ent_costo.delete(0, 'end')
        self.ent_accesso.delete(0, 'end'); self.ent_accesso.insert(0, "00:00:00")
        self.ent_uscita.delete(0, 'end'); self.ent_uscita.insert(0, "23:59:59")
        self.ent_durata.delete(0, 'end'); self.ent_durata.insert(0, "1")
        self.ent_ingressi.delete(0, 'end'); self.ent_ingressi.insert(0, "0")
        self.tier_id_in_modifica = None
        self.btn_salva.configure(text="Salva Dati", fg_color="#34C759", hover_color="#2eb350")
        self.selected_tariffa_id = None
        self.carica_dati()

    def crea_riga_tabella(self, t):
        riga_frame = ctk.CTkFrame(self.scroll_table, fg_color=("#FFFFFF", "#2C2C2E"), height=45, corner_radius=8, border_width=1, border_color=("#E5E5EA", "#3A3A3C"), cursor="hand2")
        riga_frame.pack(fill="x", pady=2)
        riga_frame.pack_propagate(False)

        costo_fmt = f"€ {t.cost:.2f}"
        eta_fmt = f"{t.min_age} - {t.max_age} anni"
        orari_fmt = f"{t.start_time} - {t.end_time}"
        durata_fmt = f"{t.duration_months} Mesi"
        ingressi_fmt = "Illimitati" if t.max_entries == 0 else f"{t.max_entries} Ingressi"

        valori = [t.name, costo_fmt, eta_fmt, orari_fmt, durata_fmt, ingressi_fmt]
        elementi_riga = [riga_frame]
        
        for i, val in enumerate(valori):
            # IL SEGRETO E' ANCHE QUI: uniform="colonna" applicato ai dati
            riga_frame.grid_columnconfigure(i, weight=self.cols[i][2], uniform="colonna")
            lbl = ctk.CTkLabel(riga_frame, text=val, font=ctk.CTkFont(family="Ubuntu", size=13), text_color=("#1D1D1F", "#FFFFFF"), anchor=self.cols[i][3])
            lbl.grid(row=0, column=i, padx=10, pady=10, sticky="ew")
            elementi_riga.append(lbl)

        for w in elementi_riga:
            w.bind("<Button-1>", lambda e, id=t.id: self.seleziona_riga(id))
            w.bind("<Enter>", lambda e, f=riga_frame, id=t.id: f.configure(fg_color=("#F8F8F9", "#3A3A3C")) if self.selected_tariffa_id != id else None)
            w.bind("<Leave>", lambda e, f=riga_frame, id=t.id: f.configure(fg_color=("#FFFFFF", "#2C2C2E")) if self.selected_tariffa_id != id else None)

        self.row_frames[t.id] = riga_frame

    def carica_dati(self):
        for widget in self.scroll_table.winfo_children(): widget.destroy()
        self.row_frames.clear()
        
        tariffe = self.db.query(Tier).all()
        for t in tariffe:
            self.crea_riga_tabella(t)

    def carica_in_form(self):
        if not self.selected_tariffa_id: return messagebox.showwarning("Attenzione", "Seleziona una fascia.")
        tariffa = self.db.query(Tier).filter(Tier.id == self.selected_tariffa_id).first()
        
        if tariffa:
            self.svuota_form()
            self.ent_sigla.delete(0, 'end'); self.ent_sigla.insert(0, tariffa.name)
            self.ent_eta_min.delete(0, 'end'); self.ent_eta_min.insert(0, str(tariffa.min_age))
            self.ent_eta_max.delete(0, 'end'); self.ent_eta_max.insert(0, str(tariffa.max_age))
            self.ent_costo.delete(0, 'end'); self.ent_costo.insert(0, str(tariffa.cost))
            self.ent_accesso.delete(0, 'end'); self.ent_accesso.insert(0, tariffa.start_time)
            self.ent_uscita.delete(0, 'end'); self.ent_uscita.insert(0, tariffa.end_time)
            self.ent_durata.delete(0, 'end'); self.ent_durata.insert(0, str(tariffa.duration_months))
            self.ent_ingressi.delete(0, 'end'); self.ent_ingressi.insert(0, str(tariffa.max_entries))
            self.tier_id_in_modifica = tariffa.id
            self.btn_salva.configure(text="Aggiorna Dati", fg_color="#007AFF", hover_color="#005ecb")

    def salva_tariffa(self):
        sigla = self.ent_sigla.get().strip()
        if not sigla: return messagebox.showwarning("Errore", "La sigla è obbligatoria.")
        
        try:
            costo = float(self.ent_costo.get().strip().replace(',', '.') or 0.0)
            eta_min = int(self.ent_eta_min.get().strip() or 0)
            eta_max = int(self.ent_eta_max.get().strip() or 200)
            durata_mesi = int(self.ent_durata.get().strip() or 1)
            ingressi = int(self.ent_ingressi.get().strip() or 0)
        except ValueError:
            return messagebox.showwarning("Errore", "Verifica che Costo, Età, Durata e Ingressi siano numeri validi.")

        if self.tier_id_in_modifica:
            tariffa = self.db.query(Tier).filter(Tier.id == self.tier_id_in_modifica).first()
            if tariffa:
                tariffa.name = sigla; tariffa.cost = costo; tariffa.min_age = eta_min; tariffa.max_age = eta_max
                tariffa.start_time = self.ent_accesso.get().strip(); tariffa.end_time = self.ent_uscita.get().strip()
                tariffa.duration_months = durata_mesi; tariffa.max_entries = ingressi
        else:
            nuova_tariffa = Tier(name=sigla, cost=costo, min_age=eta_min, max_age=eta_max, start_time=self.ent_accesso.get().strip(), end_time=self.ent_uscita.get().strip(), duration_months=durata_mesi, max_entries=ingressi)
            self.db.add(nuova_tariffa)

        self.db.commit()
        self.svuota_form()
        self.carica_dati()

    def elimina_tariffa(self):
        if not self.selected_tariffa_id: return messagebox.showwarning("Attenzione", "Seleziona una fascia.")
        
        from core.database import Member 
        soci_collegati = self.db.query(Member).filter(Member.tier_id == self.selected_tariffa_id).count()
        if soci_collegati > 0: return messagebox.showerror("Errore", f"Ci sono {soci_collegati} soci iscritti con questa fascia!")

        if messagebox.askyesno("Conferma", "Sei sicuro di voler eliminare questa fascia?"):
            tariffa = self.db.query(Tier).filter(Tier.id == self.selected_tariffa_id).first()
            if tariffa:
                self.db.delete(tariffa)
                self.db.commit()
            self.svuota_form()