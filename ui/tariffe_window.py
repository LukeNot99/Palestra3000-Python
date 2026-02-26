import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime
import json
import os
from core.database import SessionLocal, Tier, Member


def leggi_impostazione(chiave, default):
    if os.path.exists("config.json"):
        try:
            with open("config.json", "r") as f:
                return json.load(f).get(chiave, default)
        except:
            pass
    return default

UI_COLORS = {
    "bg_primary": ("#FFFFFF", "#2C2C2E"),      # Background principale (form, righe tabella)
    "bg_secondary": ("#F8F8F9", "#3A3A3C"),    # Background secondario (hover)
    "bg_selected": ("#E5F1FF", "#0A2A4A"),     # Background quando selezionato
    "border_default": ("#E5E5EA", "#3A3A3C"),  # Bordi standard
    "border_selected": "#007AFF",               # Bordo quando selezionato
    "text_primary": ("#1D1D1F", "#FFFFFF"),    # Testo principale
    "text_secondary": ("#86868B", "#98989D"),  # Testo secondario (label)
    "text_accent": ("#007AFF", "#0A84FF"),     # Testo evidenziato
    "btn_primary": "#007AFF",                   # Bottone principale
    "btn_primary_hover": "#005ecb",
    "btn_secondary": ("#E5E5EA", "#3A3A3C"),
    "btn_secondary_hover": ("#D1D1D6", "#5C5C5E"),
    "btn_success": "#34C759",
    "btn_success_hover": "#2eb350",
    "btn_danger": "#FF3B30",
    "btn_danger_hover": "#e03026",
}

FIELD_DEFAULTS = {
    "min_age": "0",
    "max_age": "200",
    "start_time": "00:00",
    "end_time": "23:59",
    "duration_months": "1",
    "max_entries": "0",
    "cost_placeholder": "0.00",
}

UI_FONTS = {
    "label_bold": ("Montserrat", 12, "bold"),      # Label dei campi form
    "entry": ("Montserrat", 12, "normal"),          # Testo input
    "entry_bold": ("Montserrat", 12, "bold"),       # Testo input evidenziato
    "table_header": ("Montserrat", 12, "bold"),     # Intestazioni tabella
    "table_row": ("Montserrat", 13, "normal"),      # Righe tabella
    "button": ("Montserrat", 14, "bold"),           # Bottoni
    "separator": ("Montserrat", 12, "normal"),      # Separatori (es. " - ")
}

class TariffeView(ctk.CTkFrame):
    def __init__(self, parent, controller=None, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._setup_db_and_config()
        self._setup_grid_layout()
        self._create_form_widgets()
        self._create_button_frame()
        self._create_table()
        self.carica_dati()

    def _create_form_widgets(self):
        form_frame = self._create_form_frame()

        self.lbl_sigla = ctk.CTkLabel(form_frame, text="Sigla Fascia:", text_color=UI_COLORS["text_secondary"],
                                      font=ctk.CTkFont(family="Montserrat", weight="bold"))
        self.ent_sigla = ctk.CTkEntry(form_frame, width=180, font=ctk.CTkFont(family="Montserrat"))

        self.lbl_costo = ctk.CTkLabel(form_frame, text="Costo (€):", text_color=UI_COLORS["text_secondary"],
                                      font=ctk.CTkFont(family="Montserrat", weight="bold"))
        self.ent_costo = ctk.CTkEntry(form_frame, width=180, justify="center", placeholder_text=FIELD_DEFAULTS["cost_placeholder"],
                                      font=ctk.CTkFont(family="Montserrat"))

        self.lbl_eta = ctk.CTkLabel(form_frame, text="Età (Min - Max):", text_color=UI_COLORS["text_secondary"],
                                    font=ctk.CTkFont(family="Montserrat", weight="bold"))
        self.frame_eta = ctk.CTkFrame(form_frame, fg_color="transparent")
        self.ent_eta_min = ctk.CTkEntry(self.frame_eta, width=70, justify="center",
                                        font=ctk.CTkFont(family="Montserrat"))
        self.ent_eta_min.insert(0, FIELD_DEFAULTS["min_age"])
        self.ent_eta_min.pack(side="left")
        ctk.CTkLabel(self.frame_eta, text=" - ", font=ctk.CTkFont(family="Montserrat")).pack(side="left", padx=5)
        self.ent_eta_max = ctk.CTkEntry(self.frame_eta, width=70, justify="center",
                                        font=ctk.CTkFont(family="Montserrat"))
        self.ent_eta_max.insert(0, FIELD_DEFAULTS["max_age"])
        self.ent_eta_max.pack(side="left")

        self.lbl_orari = ctk.CTkLabel(form_frame, text="Orari Accesso (HH:MM):", text_color=UI_COLORS["text_secondary"],
                                      font=ctk.CTkFont(family="Montserrat", weight="bold"))
        self.frame_orari = ctk.CTkFrame(form_frame, fg_color="transparent")
        self.ent_accesso = ctk.CTkEntry(self.frame_orari, width=70, justify="center",
                                        font=ctk.CTkFont(family="Montserrat"))
        self.ent_accesso.insert(0, FIELD_DEFAULTS["start_time"])
        self.ent_accesso.pack(side="left")
        ctk.CTkLabel(self.frame_orari, text=" - ", font=ctk.CTkFont(family="Montserrat")).pack(side="left", padx=5)
        self.ent_uscita = ctk.CTkEntry(self.frame_orari, width=70, justify="center",
                                       font=ctk.CTkFont(family="Montserrat"))
        self.ent_uscita.insert(0, FIELD_DEFAULTS["end_time"])
        self.ent_uscita.pack(side="left")

        self.lbl_durata = ctk.CTkLabel(form_frame, text="Durata Abbonamento (Mesi):", text_color=UI_COLORS["text_primary"],
                                       font=ctk.CTkFont(family="Montserrat", weight="bold"))
        self.ent_durata = ctk.CTkEntry(form_frame, width=180, justify="center", text_color=UI_COLORS["text_accent"],
                                       font=ctk.CTkFont(family="Montserrat", weight="bold"))
        self.ent_durata.insert(0, FIELD_DEFAULTS["duration_months"])

        self.lbl_ingressi = ctk.CTkLabel(form_frame, text="Carnet (0 = Illimitati):", text_color=UI_COLORS["text_primary"],
                                         font=ctk.CTkFont(family="Montserrat", weight="bold"))
        self.ent_ingressi = ctk.CTkEntry(form_frame, width=180, justify="center", text_color=UI_COLORS["text_accent"],
                                         font=ctk.CTkFont(family="Montserrat", weight="bold"))
        self.ent_ingressi.insert(0, FIELD_DEFAULTS["max_entries"])

        active_fields = [(self.lbl_sigla, self.ent_sigla)]
        if self.mostra_costo: active_fields.append((self.lbl_costo, self.ent_costo))
        if self.mostra_eta: active_fields.append((self.lbl_eta, self.frame_eta))
        active_fields.append((self.lbl_orari, self.frame_orari))
        active_fields.append((self.lbl_durata, self.ent_durata))
        active_fields.append((self.lbl_ingressi, self.ent_ingressi))

        for i, (lbl, wgt) in enumerate(active_fields):
            riga = i // 2
            col = (i % 2) * 2
            lbl.grid(row=riga, column=col, sticky="e", padx=(20, 10), pady=15)
            wgt.grid(row=riga, column=col + 1, sticky="w", padx=(0, 20), pady=15)

    def _create_button_frame(self):
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=5)

        self.btn_salva = ctk.CTkButton(btn_frame, text="Salva Dati", width=140, height=38,
                                       font=ctk.CTkFont(family="Montserrat", size=14, weight="bold"),
                                       fg_color=UI_COLORS["btn_success"], hover_color=UI_COLORS["btn_success_hover"],
                                       command=self.salva_tariffa)
        self.btn_salva.pack(side="left", padx=(0, 10))

        ctk.CTkButton(btn_frame, text="Svuota Form", width=120, height=38,
                      font=ctk.CTkFont(family="Montserrat", size=14, weight="bold"), fg_color=UI_COLORS["btn_secondary"],
                      text_color=UI_COLORS["text_primary"], hover_color=UI_COLORS["btn_secondary_hover"],
                      command=self.svuota_form).pack(side="left")

        ctk.CTkButton(btn_frame, text="✏️ Modifica", width=140, height=38,
                      font=ctk.CTkFont(family="Montserrat", size=14, weight="bold"), fg_color=UI_COLORS["btn_primary"],
                      hover_color=UI_COLORS["btn_primary_hover"], command=self.carica_in_form).pack(side="left", padx=(20, 10))

        ctk.CTkButton(btn_frame, text="🗑️ Elimina", width=120, height=38,
                      font=ctk.CTkFont(family="Montserrat", size=14, weight="bold"), fg_color=UI_COLORS["btn_danger"],
                      hover_color=UI_COLORS["btn_danger_hover"], command=self.elimina_tariffa).pack(side="right")

    def _create_table(self):
        self.table_container = ctk.CTkFrame(self, fg_color="transparent")
        self.table_container.grid(row=2, column=0, sticky="nsew", padx=20, pady=(10, 20))

        self.cols = [("sigla", "Sigla Fascia", 2, "w")]
        if self.mostra_costo: self.cols.append(("costo", "Costo", 1, "center"))
        if self.mostra_eta: self.cols.append(("eta", "Età (Min-Max)", 1, "center"))
        self.cols.extend([
            ("orari", "Accesso/Uscita", 2, "center"),
            ("durata", "Durata", 1, "center"),
            ("ingressi", "Carnet", 1, "center")
        ])

        header_frame = ctk.CTkFrame(self.table_container, fg_color=UI_COLORS["border_default"], height=35, corner_radius=6)
        header_frame.pack(fill="x", pady=(0, 5))

        for i, col in enumerate(self.cols):
            header_frame.grid_columnconfigure(i, weight=col[2], uniform="colonna")
            ctk.CTkLabel(header_frame, text=col[1], font=ctk.CTkFont(family="Montserrat", size=12, weight="bold"),
                         text_color=UI_COLORS["text_secondary"], anchor=col[3]).grid(row=0, column=i, padx=10, pady=5,
                                                                                     sticky="ew")

        self.scroll_table = ctk.CTkScrollableFrame(self.table_container, fg_color="transparent")
        self.scroll_table.pack(fill="both", expand=True)


    def _create_form_frame(self):
        form_frame = ctk.CTkFrame(self, fg_color=UI_COLORS["bg_primary"], corner_radius=12, border_width=1,
                     border_color=UI_COLORS["border_default"])
        form_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=20)
        form_frame.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform="colonna")
        return form_frame

    def _setup_grid_layout(self, _row_index=2, _clm_index=0, _weight_value=1):
        self.grid_rowconfigure(_row_index, weight=_weight_value)
        self.grid_columnconfigure(_clm_index, weight=_weight_value)

    def _setup_db_and_config(self):
        self.db = SessionLocal()
        self.tier_id_in_modifica = None
        self.row_frames = {}
        self.selected_tariffa_id = None

        # PRE-CARICAMENTO FONT PER PREVENIRE MEMORY LEAK!
        self.font_riga = ctk.CTkFont(family=UI_FONTS["table_row"][0], size=UI_FONTS["table_row"][1],
                                     weight=UI_FONTS["table_row"][2])

        self.mostra_costo = leggi_impostazione("mostra_costo_fasce", False)
        self.mostra_eta = leggi_impostazione("mostra_eta_fasce", False)


    def seleziona_riga(self, t_id):
        self.selected_tariffa_id = t_id
        for r_id, frame in self.row_frames.items():
            if frame.winfo_exists():
                if r_id == t_id:
                    frame.configure(fg_color=UI_COLORS["bg_selected"], border_color=UI_COLORS["border_selected"])
                else:
                    frame.configure(fg_color=UI_COLORS["bg_primary"], border_color=UI_COLORS["border_default"])

    def svuota_form(self):
        self.ent_sigla.delete(0, 'end')

        if self.mostra_eta:
            self.ent_eta_min.delete(0, 'end');
            self.ent_eta_min.insert(0, FIELD_DEFAULTS["min_age"])
            self.ent_eta_max.delete(0, 'end');
            self.ent_eta_max.insert(0, FIELD_DEFAULTS["max_age"])

        if self.mostra_costo:
            self.ent_costo.delete(0, 'end')

        self.ent_accesso.delete(0, 'end');
        self.ent_accesso.insert(0, FIELD_DEFAULTS["start_time"])
        self.ent_uscita.delete(0, 'end');
        self.ent_uscita.insert(0, FIELD_DEFAULTS["end_time"])
        self.ent_durata.delete(0, 'end');
        self.ent_durata.insert(0, FIELD_DEFAULTS["duration_months"])
        self.ent_ingressi.delete(0, 'end');
        self.ent_ingressi.insert(0, FIELD_DEFAULTS["max_entries"])

        self.tier_id_in_modifica = None
        self.btn_salva.configure(text="Salva Dati", fg_color=UI_COLORS["btn_success"], hover_color=UI_COLORS["btn_success_hover"])
        self.selected_tariffa_id = None
        self.carica_dati()

    def crea_riga_tabella(self, t):
        riga_frame = ctk.CTkFrame(self.scroll_table, fg_color=UI_COLORS["bg_primary"], height=45, corner_radius=8,
                                  border_width=1, border_color=UI_COLORS["border_default"], cursor="hand2")
        riga_frame.pack(fill="x", pady=2)
        riga_frame.pack_propagate(False)

        valori = [t.name]
        if self.mostra_costo: valori.append(f"€ {t.cost:.2f}")
        if self.mostra_eta: valori.append(f"{t.min_age} - {t.max_age} anni")
        valori.extend([
            f"{t.start_time[:5]} - {t.end_time[:5]}",
            f"{t.duration_months} Mesi",
            "Illimitati" if t.max_entries == 0 else f"{t.max_entries} Ingressi"
        ])

        elementi_riga = [riga_frame]

        for i, val in enumerate(valori):
            riga_frame.grid_columnconfigure(i, weight=self.cols[i][2], uniform="colonna")
            # UTILIZZO DEL FONT CACHED PER EVITARE CRASH
            lbl = ctk.CTkLabel(riga_frame, text=val, font=self.font_riga, text_color=UI_COLORS["text_primary"],
                               anchor=self.cols[i][3])
            lbl.grid(row=0, column=i, padx=10, pady=10, sticky="ew")
            elementi_riga.append(lbl)

        # AGGIUNTA SICUREZZA WINFO_EXISTS AGLI EVENTI MOUSE
        for w in elementi_riga:
            w.bind("<Button-1>", lambda e, id=t.id: self.seleziona_riga(id))
            w.bind("<Enter>", lambda e, f=riga_frame, id=t.id: f.configure(
                fg_color=UI_COLORS["bg_secondary"]) if f.winfo_exists() and self.selected_tariffa_id != id else None)
            w.bind("<Leave>", lambda e, f=riga_frame, id=t.id: f.configure(
                fg_color=UI_COLORS["bg_primary"]) if f.winfo_exists() and self.selected_tariffa_id != id else None)

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
            self.ent_sigla.delete(0, 'end');
            self.ent_sigla.insert(0, tariffa.name)

            if self.mostra_eta:
                self.ent_eta_min.delete(0, 'end');
                self.ent_eta_min.insert(0, str(tariffa.min_age))
                self.ent_eta_max.delete(0, 'end');
                self.ent_eta_max.insert(0, str(tariffa.max_age))

            if self.mostra_costo:
                self.ent_costo.delete(0, 'end');
                self.ent_costo.insert(0, str(tariffa.cost))

            self.ent_accesso.delete(0, 'end');
            self.ent_accesso.insert(0, tariffa.start_time[:5])
            self.ent_uscita.delete(0, 'end');
            self.ent_uscita.insert(0, tariffa.end_time[:5])

            self.ent_durata.delete(0, 'end');
            self.ent_durata.insert(0, str(tariffa.duration_months))
            self.ent_ingressi.delete(0, 'end');
            self.ent_ingressi.insert(0, str(tariffa.max_entries))
            self.tier_id_in_modifica = tariffa.id
            self.btn_salva.configure(text="Aggiorna Dati", fg_color=UI_COLORS["btn_primary"], hover_color=UI_COLORS["btn_primary_hover"])

    def salva_tariffa(self):
        sigla = self.ent_sigla.get().strip()
        if not sigla: return messagebox.showwarning("Errore", "La sigla è obbligatoria.")

        accesso = self.ent_accesso.get().strip()
        uscita = self.ent_uscita.get().strip()

        try:
            datetime.strptime(accesso, "%H:%M")
            datetime.strptime(uscita, "%H:%M")
        except ValueError:
            return messagebox.showwarning("Errore Orario",
                                          "Verifica che gli orari di accesso e uscita siano nel formato ore e minuti: HH:MM (es. 08:30).")

        try:
            costo = float(self.ent_costo.get().strip().replace(',', '.')) if self.mostra_costo else 0.0
            eta_min = int(self.ent_eta_min.get().strip()) if self.mostra_eta else 0
            eta_max = int(self.ent_eta_max.get().strip()) if self.mostra_eta else 999
            durata_mesi = int(self.ent_durata.get().strip() or FIELD_DEFAULTS["duration_months"])
            ingressi = int(self.ent_ingressi.get().strip() or FIELD_DEFAULTS["max_entries"])
        except ValueError:
            return messagebox.showwarning("Errore", "Verifica che Costo, Età, Durata e Ingressi siano numeri validi.")

        if self.tier_id_in_modifica:
            tariffa = self.db.query(Tier).filter(Tier.id == self.tier_id_in_modifica).first()
            if tariffa:
                tariffa.name = sigla;
                tariffa.cost = costo;
                tariffa.min_age = eta_min;
                tariffa.max_age = eta_max
                tariffa.start_time = accesso;
                tariffa.end_time = uscita
                tariffa.duration_months = durata_mesi;
                tariffa.max_entries = ingressi
        else:
            nuova_tariffa = Tier(name=sigla, cost=costo, min_age=eta_min, max_age=eta_max, start_time=accesso,
                                 end_time=uscita, duration_months=durata_mesi, max_entries=ingressi)
            self.db.add(nuova_tariffa)

        self.db.commit()
        self.svuota_form()
        self.carica_dati()

    def elimina_tariffa(self):
        if not self.selected_tariffa_id: return messagebox.showwarning("Attenzione", "Seleziona una fascia.")

        from core.database import Member
        soci_collegati = self.db.query(Member).filter(Member.tier_id == self.selected_tariffa_id).count()
        if soci_collegati > 0: return messagebox.showerror("Errore",
                                                           f"Ci sono {soci_collegati} soci iscritti con questa fascia!")

        if messagebox.askyesno("Conferma", "Sei sicuro di voler eliminare questa fascia?"):
            tariffa = self.db.query(Tier).filter(Tier.id == self.selected_tariffa_id).first()
            if tariffa:
                self.db.delete(tariffa)
                self.db.commit()
            self.svuota_form()
