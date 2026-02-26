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
        except Exception:
            pass
    return default

UI_COLORS = {
    "bg_primary": ("#FFFFFF", "#2C2C2E"),
    "bg_secondary": ("#F8F8F9", "#3A3A3C"),
    "bg_selected": ("#E5F1FF", "#0A2A4A"),
    "border_default": ("#E5E5EA", "#3A3A3C"),
    "border_selected": "#007AFF",
    "text_primary": ("#1D1D1F", "#FFFFFF"),
    "text_secondary": ("#86868B", "#98989D"),
    "text_accent": ("#007AFF", "#0A84FF"),
    "btn_primary": "#007AFF",
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
    "label_bold":   ("Montserrat", 12, "bold"),
    "entry":        ("Montserrat", 12, "normal"),
    "entry_bold":   ("Montserrat", 12, "bold"),
    "table_header": ("Montserrat", 12, "bold"),
    "table_row":    ("Montserrat", 13, "normal"),
    "button":       ("Montserrat", 14, "bold"),
    "separator":    ("Montserrat", 12, "normal"),
}


# ---------------------------------------------------------------------------
# Helper di costruzione widget — eliminano il boilerplate CTkFont inline
# ---------------------------------------------------------------------------

def _mk_font(key: str) -> ctk.CTkFont:
    f = UI_FONTS[key]
    return ctk.CTkFont(family=f[0], size=f[1], weight=f[2])

def _mk_label(parent, text: str, font_key: str = "label_bold",
              color_key: str = "text_secondary", **kwargs) -> ctk.CTkLabel:
    return ctk.CTkLabel(parent, text=text, font=_mk_font(font_key),
                        text_color=UI_COLORS[color_key], **kwargs)

def _mk_entry(parent, width: int = 180, font_key: str = "entry",
              color_key: str | None = None, **kwargs) -> ctk.CTkEntry:
    kw = dict(width=width, font=_mk_font(font_key))
    if color_key:
        kw["text_color"] = UI_COLORS[color_key]
    kw.update(kwargs)
    return ctk.CTkEntry(parent, **kw)

def _mk_button(parent, text: str, fg_key: str, hover_key: str,
               command, side: str = "left", padx=0, **kwargs) -> ctk.CTkButton:
    btn = ctk.CTkButton(parent, text=text, height=38, font=_mk_font("button"),
                        fg_color=UI_COLORS[fg_key], hover_color=UI_COLORS[hover_key],
                        command=command, **kwargs)
    btn.pack(side=side, padx=padx)
    return btn

def _set_entry(entry: ctk.CTkEntry, value: str) -> None:
    """Svuota e imposta il valore di un entry in una riga."""
    entry.delete(0, "end")
    entry.insert(0, value)


# ---------------------------------------------------------------------------

class TariffeView(ctk.CTkFrame):
    def __init__(self, parent, controller=None, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._setup_db_and_config()
        self._setup_grid_layout()
        self._create_form_widgets()
        self._create_button_frame()
        self._create_table()
        self.carica_dati()

    # ── Setup ────────────────────────────────────────────────────────────────

    def _setup_db_and_config(self):
        self.db = SessionLocal()
        self.tier_id_in_modifica = None
        self.row_frames = {}
        self.selected_tariffa_id = None
        # PRE-CARICAMENTO FONT PER PREVENIRE MEMORY LEAK
        self.font_riga = _mk_font("table_row")
        self.mostra_costo = leggi_impostazione("mostra_costo_fasce", False)
        self.mostra_eta   = leggi_impostazione("mostra_eta_fasce", False)

    def _setup_grid_layout(self):
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

    # ── Costruzione UI ───────────────────────────────────────────────────────

    def _create_form_frame(self) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(self, fg_color=UI_COLORS["bg_primary"], corner_radius=12,
                             border_width=1, border_color=UI_COLORS["border_default"])
        frame.grid(row=0, column=0, sticky="ew", padx=20, pady=20)
        frame.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform="colonna")
        return frame

    def _create_range_frame(self, parent, entry_min_attr: str, entry_max_attr: str,
                            default_min: str, default_max: str) -> ctk.CTkFrame:
        """Crea un frame con due entry collegati da ' - '."""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        ent_min = _mk_entry(frame, width=70, justify="center")
        _set_entry(ent_min, default_min)
        ent_min.pack(side="left")
        _mk_label(frame, " - ", font_key="separator", color_key="text_primary").pack(side="left", padx=5)
        ent_max = _mk_entry(frame, width=70, justify="center")
        _set_entry(ent_max, default_max)
        ent_max.pack(side="left")
        setattr(self, entry_min_attr, ent_min)
        setattr(self, entry_max_attr, ent_max)
        return frame

    def _create_form_widgets(self):
        form_frame = self._create_form_frame()

        self.lbl_sigla = _mk_label(form_frame, "Sigla Fascia:")
        self.ent_sigla = _mk_entry(form_frame)

        self.lbl_costo = _mk_label(form_frame, "Costo (€):")
        self.ent_costo = _mk_entry(form_frame, justify="center",
                                   placeholder_text=FIELD_DEFAULTS["cost_placeholder"])

        self.lbl_eta   = _mk_label(form_frame, "Età (Min - Max):")
        self.frame_eta = self._create_range_frame(form_frame,
                             "ent_eta_min", "ent_eta_max",
                             FIELD_DEFAULTS["min_age"], FIELD_DEFAULTS["max_age"])

        self.lbl_orari   = _mk_label(form_frame, "Orari Accesso (HH:MM):")
        self.frame_orari = self._create_range_frame(form_frame,
                               "ent_accesso", "ent_uscita",
                               FIELD_DEFAULTS["start_time"], FIELD_DEFAULTS["end_time"])

        self.lbl_durata  = _mk_label(form_frame, "Durata Abbonamento (Mesi):", color_key="text_primary")
        self.ent_durata  = _mk_entry(form_frame, justify="center", font_key="entry_bold",
                                     color_key="text_accent")
        _set_entry(self.ent_durata, FIELD_DEFAULTS["duration_months"])

        self.lbl_ingressi = _mk_label(form_frame, "Carnet (0 = Illimitati):", color_key="text_primary")
        self.ent_ingressi = _mk_entry(form_frame, justify="center", font_key="entry_bold",
                                      color_key="text_accent")
        _set_entry(self.ent_ingressi, FIELD_DEFAULTS["max_entries"])

        self._layout_form_fields(form_frame)

    def _build_active_fields(self, form_frame) -> list:
        fields = [(self.lbl_sigla, self.ent_sigla)]
        if self.mostra_costo: fields.append((self.lbl_costo, self.ent_costo))
        if self.mostra_eta:   fields.append((self.lbl_eta,   self.frame_eta))
        fields.append((self.lbl_orari,    self.frame_orari))
        fields.append((self.lbl_durata,   self.ent_durata))
        fields.append((self.lbl_ingressi, self.ent_ingressi))
        return fields

    def _layout_form_fields(self, form_frame):
        for i, (lbl, wgt) in enumerate(self._build_active_fields(form_frame)):
            riga = i // 2
            col  = (i % 2) * 2
            lbl.grid(row=riga, column=col,     sticky="e", padx=(20, 10), pady=15)
            wgt.grid(row=riga, column=col + 1, sticky="w", padx=(0, 20),  pady=15)

    def _create_button_frame(self):
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=5)

        self.btn_salva = _mk_button(btn_frame, "Salva Dati",
                                    "btn_success", "btn_success_hover",
                                    self.salva_tariffa, padx=(0, 10), width=140)
        _mk_button(btn_frame, "Svuota Form",
                   "btn_secondary", "btn_secondary_hover",
                   self.svuota_form, width=120,
                   text_color=UI_COLORS["text_primary"])
        _mk_button(btn_frame, "✏️ Modifica",
                   "btn_primary", "btn_primary_hover",
                   self.carica_in_form, padx=(20, 10), width=140)
        _mk_button(btn_frame, "🗑️ Elimina",
                   "btn_danger", "btn_danger_hover",
                   self.elimina_tariffa, side="right", width=120)

    def _create_table(self):
        self.table_container = ctk.CTkFrame(self, fg_color="transparent")
        self.table_container.grid(row=2, column=0, sticky="nsew", padx=20, pady=(10, 20))

        self.cols = [("sigla", "Sigla Fascia", 2, "w")]
        if self.mostra_costo: self.cols.append(("costo",  "Costo",          1, "center"))
        if self.mostra_eta:   self.cols.append(("eta",    "Età (Min-Max)",   1, "center"))
        self.cols.extend([
            ("orari",    "Accesso/Uscita", 2, "center"),
            ("durata",   "Durata",         1, "center"),
            ("ingressi", "Carnet",         1, "center"),
        ])

        header_frame = ctk.CTkFrame(self.table_container, fg_color=UI_COLORS["border_default"],
                                    height=35, corner_radius=6)
        header_frame.pack(fill="x", pady=(0, 5))

        for i, col in enumerate(self.cols):
            header_frame.grid_columnconfigure(i, weight=col[2], uniform="colonna")
            _mk_label(header_frame, col[1], font_key="table_header",
                      color_key="text_secondary", anchor=col[3]
                      ).grid(row=0, column=i, padx=10, pady=5, sticky="ew")

        self.scroll_table = ctk.CTkScrollableFrame(self.table_container, fg_color="transparent")
        self.scroll_table.pack(fill="both", expand=True)

    # ── Logica tabella ───────────────────────────────────────────────────────

    def seleziona_riga(self, t_id):
        self.selected_tariffa_id = t_id
        for r_id, frame in self.row_frames.items():
            if not frame.winfo_exists():
                continue
            if r_id == t_id:
                frame.configure(fg_color=UI_COLORS["bg_selected"],
                                border_color=UI_COLORS["border_selected"])
            else:
                frame.configure(fg_color=UI_COLORS["bg_primary"],
                                border_color=UI_COLORS["border_default"])

    def _get_valori_riga(self, t: Tier) -> list[str]:
        valori = [t.name]
        if self.mostra_costo: valori.append(f"€ {t.cost:.2f}")
        if self.mostra_eta:   valori.append(f"{t.min_age} - {t.max_age} anni")
        valori.extend([
            f"{t.start_time[:5]} - {t.end_time[:5]}",
            f"{t.duration_months} Mesi",
            "Illimitati" if t.max_entries == 0 else f"{t.max_entries} Ingressi",
        ])
        return valori

    def _bind_eventi_riga(self, widgets: list, riga_frame: ctk.CTkFrame, t_id: int):
        for w in widgets:
            w.bind("<Button-1>", lambda e, i=t_id: self.seleziona_riga(i))
            w.bind("<Enter>",    lambda e, f=riga_frame, i=t_id: f.configure(
                fg_color=UI_COLORS["bg_secondary"])
                if f.winfo_exists() and self.selected_tariffa_id != i else None)
            w.bind("<Leave>",    lambda e, f=riga_frame, i=t_id: f.configure(
                fg_color=UI_COLORS["bg_primary"])
                if f.winfo_exists() and self.selected_tariffa_id != i else None)

    def crea_riga_tabella(self, t: Tier):
        riga_frame = ctk.CTkFrame(self.scroll_table, fg_color=UI_COLORS["bg_primary"],
                                  height=45, corner_radius=8, border_width=1,
                                  border_color=UI_COLORS["border_default"], cursor="hand2")
        riga_frame.pack(fill="x", pady=2)
        riga_frame.pack_propagate(False)

        elementi = [riga_frame]
        for i, val in enumerate(self._get_valori_riga(t)):
            riga_frame.grid_columnconfigure(i, weight=self.cols[i][2], uniform="colonna")
            lbl = ctk.CTkLabel(riga_frame, text=val, font=self.font_riga,
                               text_color=UI_COLORS["text_primary"], anchor=self.cols[i][3])
            lbl.grid(row=0, column=i, padx=10, pady=10, sticky="ew")
            elementi.append(lbl)

        self._bind_eventi_riga(elementi, riga_frame, t.id)
        self.row_frames[t.id] = riga_frame

    def carica_dati(self):
        for widget in self.scroll_table.winfo_children():
            widget.destroy()
        self.row_frames.clear()
        for t in self.db.query(Tier).all():
            self.crea_riga_tabella(t)

    # ── Logica form ──────────────────────────────────────────────────────────

    def svuota_form(self):
        self.ent_sigla.delete(0, "end")

        if self.mostra_eta:
            _set_entry(self.ent_eta_min, FIELD_DEFAULTS["min_age"])
            _set_entry(self.ent_eta_max, FIELD_DEFAULTS["max_age"])
        if self.mostra_costo:
            self.ent_costo.delete(0, "end")

        _set_entry(self.ent_accesso,  FIELD_DEFAULTS["start_time"])
        _set_entry(self.ent_uscita,   FIELD_DEFAULTS["end_time"])
        _set_entry(self.ent_durata,   FIELD_DEFAULTS["duration_months"])
        _set_entry(self.ent_ingressi, FIELD_DEFAULTS["max_entries"])

        self.tier_id_in_modifica = None
        self.selected_tariffa_id = None
        self.btn_salva.configure(text="Salva Dati",
                                 fg_color=UI_COLORS["btn_success"],
                                 hover_color=UI_COLORS["btn_success_hover"])
        self.carica_dati()

    def carica_in_form(self):
        if not self.selected_tariffa_id:
            return messagebox.showwarning("Attenzione", "Seleziona una fascia.")
        tariffa = self.db.query(Tier).filter(Tier.id == self.selected_tariffa_id).first()
        if not tariffa:
            return

        self.svuota_form()
        _set_entry(self.ent_sigla, tariffa.name)

        if self.mostra_eta:
            _set_entry(self.ent_eta_min, str(tariffa.min_age))
            _set_entry(self.ent_eta_max, str(tariffa.max_age))
        if self.mostra_costo:
            _set_entry(self.ent_costo, str(tariffa.cost))

        _set_entry(self.ent_accesso,  tariffa.start_time[:5])
        _set_entry(self.ent_uscita,   tariffa.end_time[:5])
        _set_entry(self.ent_durata,   str(tariffa.duration_months))
        _set_entry(self.ent_ingressi, str(tariffa.max_entries))

        self.tier_id_in_modifica = tariffa.id
        self.btn_salva.configure(text="Aggiorna Dati",
                                 fg_color=UI_COLORS["btn_primary"],
                                 hover_color=UI_COLORS["btn_primary_hover"])

    def _leggi_campi_form(self) -> dict:
        """Legge e valida tutti i campi del form. Solleva ValueError se non validi."""
        accesso = self.ent_accesso.get().strip()
        uscita  = self.ent_uscita.get().strip()
        datetime.strptime(accesso, "%H:%M")
        datetime.strptime(uscita,  "%H:%M")
        return {
            "sigla":       self.ent_sigla.get().strip(),
            "accesso":     accesso,
            "uscita":      uscita,
            "costo":       float(self.ent_costo.get().strip().replace(",", ".")) if self.mostra_costo else 0.0,
            "eta_min":     int(self.ent_eta_min.get().strip()) if self.mostra_eta else 0,
            "eta_max":     int(self.ent_eta_max.get().strip()) if self.mostra_eta else 999,
            "durata_mesi": int(self.ent_durata.get().strip()   or FIELD_DEFAULTS["duration_months"]),
            "ingressi":    int(self.ent_ingressi.get().strip()  or FIELD_DEFAULTS["max_entries"]),
        }

    def _aggiorna_tier(self, dati: dict):
        tariffa = self.db.query(Tier).filter(Tier.id == self.tier_id_in_modifica).first()
        if not tariffa:
            return
        tariffa.name            = dati["sigla"]
        tariffa.cost            = dati["costo"]
        tariffa.min_age         = dati["eta_min"]
        tariffa.max_age         = dati["eta_max"]
        tariffa.start_time      = dati["accesso"]
        tariffa.end_time        = dati["uscita"]
        tariffa.duration_months = dati["durata_mesi"]
        tariffa.max_entries     = dati["ingressi"]

    def _crea_tier(self, dati: dict):
        self.db.add(Tier(
            name=dati["sigla"],       cost=dati["costo"],
            min_age=dati["eta_min"],  max_age=dati["eta_max"],
            start_time=dati["accesso"], end_time=dati["uscita"],
            duration_months=dati["durata_mesi"], max_entries=dati["ingressi"],
        ))

    def salva_tariffa(self):
        sigla = self.ent_sigla.get().strip()
        if not sigla:
            return messagebox.showwarning("Errore", "La sigla è obbligatoria.")
        try:
            dati = self._leggi_campi_form()
        except ValueError as e:
            msg = ("Verifica che gli orari siano nel formato HH:MM (es. 08:30)."
                   if "time" in str(e)
                   else "Verifica che Costo, Età, Durata e Ingressi siano numeri validi.")
            return messagebox.showwarning("Errore", msg)

        if self.tier_id_in_modifica:
            self._aggiorna_tier(dati)
        else:
            self._crea_tier(dati)

        self.db.commit()
        self.svuota_form()

    def elimina_tariffa(self):
        if not self.selected_tariffa_id:
            return messagebox.showwarning("Attenzione", "Seleziona una fascia.")

        soci_collegati = self.db.query(Member).filter(Member.tier_id == self.selected_tariffa_id).count()
        if soci_collegati > 0:
            return messagebox.showerror("Errore",
                                        f"Ci sono {soci_collegati} soci iscritti con questa fascia!")

        if messagebox.askyesno("Conferma", "Sei sicuro di voler eliminare questa fascia?"):
            tariffa = self.db.query(Tier).filter(Tier.id == self.selected_tariffa_id).first()
            if tariffa:
                self.db.delete(tariffa)
                self.db.commit()
            self.svuota_form()
