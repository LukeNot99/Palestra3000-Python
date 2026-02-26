import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime
import json
import os
from core.database import SessionLocal, Tier, Member


def read_setting(key, default):
    if os.path.exists("config.json"):
        try:
            with open("config.json", "r") as f:
                return json.load(f).get(key, default)
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
    "label_bold": ("Montserrat", 12, "bold"),
    "entry": ("Montserrat", 12, "normal"),
    "entry_bold": ("Montserrat", 12, "bold"),
    "table_header": ("Montserrat", 12, "bold"),
    "table_row": ("Montserrat", 13, "normal"),
    "button": ("Montserrat", 14, "bold"),
    "separator": ("Montserrat", 12, "normal"),
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
    """Clears and sets the value of an entry widget."""
    entry.delete(0, "end")
    entry.insert(0, value)


# ---------------------------------------------------------------------------

class TiersView(ctk.CTkFrame):
    def __init__(self, parent, controller=None, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._setup_db_and_config()
        self._setup_grid_layout()
        self._create_form_widgets()
        self._create_button_frame()
        self._create_table()
        self.load_data()

    # ── Setup ────────────────────────────────────────────────────────────────

    def _setup_db_and_config(self):
        self.db = SessionLocal()
        self.editing_tier_id  = None
        self.selected_tier_id = None
        self.row_frames       = {}
        # PRE-CARICAMENTO FONT PER PREVENIRE MEMORY LEAK
        self.row_font = _mk_font("table_row")
        self.show_cost = read_setting("mostra_costo_fasce", False)
        self.show_age  = read_setting("mostra_eta_fasce", False)
        # Dichiarati qui per evitare "Unresolved attribute" — assegnati via setattr in _create_range_frame
        self.ent_age_min:    ctk.CTkEntry | None = None
        self.ent_age_max:    ctk.CTkEntry | None = None
        self.ent_entry_time: ctk.CTkEntry | None = None
        self.ent_exit_time:  ctk.CTkEntry | None = None

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
        """Creates a frame with two entries linked by ' - '."""
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

        self.lbl_code = _mk_label(form_frame, "Sigla Fascia:")
        self.ent_code = _mk_entry(form_frame)

        self.lbl_cost = _mk_label(form_frame, "Costo (€):")
        self.ent_cost = _mk_entry(form_frame, justify="center",
                                  placeholder_text=FIELD_DEFAULTS["cost_placeholder"])

        self.lbl_age   = _mk_label(form_frame, "Età (Min - Max):")
        self.frame_age = self._create_range_frame(form_frame,
                             "ent_age_min", "ent_age_max",
                             FIELD_DEFAULTS["min_age"], FIELD_DEFAULTS["max_age"])

        self.lbl_schedule   = _mk_label(form_frame, "Orari Accesso (HH:MM):")
        self.frame_schedule = self._create_range_frame(form_frame,
                                  "ent_entry_time", "ent_exit_time",
                                  FIELD_DEFAULTS["start_time"], FIELD_DEFAULTS["end_time"])

        self.lbl_duration = _mk_label(form_frame, "Durata Abbonamento (Mesi):", color_key="text_primary")
        self.ent_duration = _mk_entry(form_frame, justify="center", font_key="entry_bold",
                                      color_key="text_accent")
        _set_entry(self.ent_duration, FIELD_DEFAULTS["duration_months"])

        self.lbl_entries = _mk_label(form_frame, "Carnet (0 = Illimitati):", color_key="text_primary")
        self.ent_entries = _mk_entry(form_frame, justify="center", font_key="entry_bold",
                                     color_key="text_accent")
        _set_entry(self.ent_entries, FIELD_DEFAULTS["max_entries"])

        self._layout_form_fields(form_frame)

    def _build_active_fields(self, form_frame) -> list:
        fields = [(self.lbl_code, self.ent_code)]
        if self.show_cost: fields.append((self.lbl_cost,     self.ent_cost))
        if self.show_age:  fields.append((self.lbl_age,      self.frame_age))
        fields.append((self.lbl_schedule, self.frame_schedule))
        fields.append((self.lbl_duration, self.ent_duration))
        fields.append((self.lbl_entries,  self.ent_entries))
        return fields

    def _layout_form_fields(self, form_frame):
        for i, (lbl, wgt) in enumerate(self._build_active_fields(form_frame)):
            row = i // 2
            col = (i % 2) * 2
            lbl.grid(row=row, column=col,     sticky="e", padx=(20, 10), pady=15)
            wgt.grid(row=row, column=col + 1, sticky="w", padx=(0, 20),  pady=15)

    def _create_button_frame(self):
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=5)

        self.btn_save = _mk_button(btn_frame, "Salva Dati",
                                   "btn_success", "btn_success_hover",
                                   self.save_tier, padx=(0, 10), width=140)
        _mk_button(btn_frame, "Svuota Form",
                   "btn_secondary", "btn_secondary_hover",
                   self.clear_form, width=120,
                   text_color=UI_COLORS["text_primary"])
        _mk_button(btn_frame, "✏️ Modifica",
                   "btn_primary", "btn_primary_hover",
                   self.load_into_form, padx=(20, 10), width=140)
        _mk_button(btn_frame, "🗑️ Elimina",
                   "btn_danger", "btn_danger_hover",
                   self.delete_tier, side="right", width=120)

    def _create_table(self):
        self.table_container = ctk.CTkFrame(self, fg_color="transparent")
        self.table_container.grid(row=2, column=0, sticky="nsew", padx=20, pady=(10, 20))

        self.cols = [("code", "Sigla Fascia", 2, "w")]
        if self.show_cost: self.cols.append(("cost",     "Costo",          1, "center"))
        if self.show_age:  self.cols.append(("age",      "Età (Min-Max)",   1, "center"))
        self.cols.extend([
            ("schedule", "Accesso/Uscita", 2, "center"),
            ("duration", "Durata",         1, "center"),
            ("entries",  "Carnet",         1, "center"),
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

    def select_row(self, t_id):
        self.selected_tier_id = t_id
        for r_id, frame in self.row_frames.items():
            if not frame.winfo_exists():
                continue
            if r_id == t_id:
                frame.configure(fg_color=UI_COLORS["bg_selected"],
                                border_color=UI_COLORS["border_selected"])
            else:
                frame.configure(fg_color=UI_COLORS["bg_primary"],
                                border_color=UI_COLORS["border_default"])

    def _get_row_values(self, t: Tier) -> list[str]:
        values = [t.name]
        if self.show_cost: values.append(f"€ {t.cost:.2f}")
        if self.show_age:  values.append(f"{t.min_age} - {t.max_age} anni")
        values.extend([
            f"{t.start_time[:5]} - {t.end_time[:5]}",
            f"{t.duration_months} Mesi",
            "Illimitati" if t.max_entries == 0 else f"{t.max_entries} Ingressi",
        ])
        return values

    def _bind_row_events(self, widgets: list, row_frame: ctk.CTkFrame, t_id: int):
        for w in widgets:
            w.bind("<Button-1>", lambda e, i=t_id: self.select_row(i))
            w.bind("<Enter>",    lambda e, f=row_frame, i=t_id: f.configure(
                fg_color=UI_COLORS["bg_secondary"])
                if f.winfo_exists() and self.selected_tier_id != i else None)
            w.bind("<Leave>",    lambda e, f=row_frame, i=t_id: f.configure(
                fg_color=UI_COLORS["bg_primary"])
                if f.winfo_exists() and self.selected_tier_id != i else None)

    def create_table_row(self, t: Tier):
        row_frame = ctk.CTkFrame(self.scroll_table, fg_color=UI_COLORS["bg_primary"],
                                 height=45, corner_radius=8, border_width=1,
                                 border_color=UI_COLORS["border_default"], cursor="hand2")
        row_frame.pack(fill="x", pady=2)
        row_frame.pack_propagate(False)

        widgets = [row_frame]
        for i, val in enumerate(self._get_row_values(t)):
            row_frame.grid_columnconfigure(i, weight=self.cols[i][2], uniform="colonna")
            lbl = ctk.CTkLabel(row_frame, text=val, font=self.row_font,
                               text_color=UI_COLORS["text_primary"], anchor=self.cols[i][3])
            lbl.grid(row=0, column=i, padx=10, pady=10, sticky="ew")
            widgets.append(lbl)

        self._bind_row_events(widgets, row_frame, t.id)
        self.row_frames[t.id] = row_frame

    def load_data(self):
        for widget in self.scroll_table.winfo_children():
            widget.destroy()
        self.row_frames.clear()
        for t in self.db.query(Tier).all():
            self.create_table_row(t)

    # ── Logica form ──────────────────────────────────────────────────────────

    def clear_form(self):
        self.ent_code.delete(0, "end")

        if self.show_age:
            _set_entry(self.ent_age_min, FIELD_DEFAULTS["min_age"])
            _set_entry(self.ent_age_max, FIELD_DEFAULTS["max_age"])
        if self.show_cost:
            self.ent_cost.delete(0, "end")

        _set_entry(self.ent_entry_time, FIELD_DEFAULTS["start_time"])
        _set_entry(self.ent_exit_time,  FIELD_DEFAULTS["end_time"])
        _set_entry(self.ent_duration,   FIELD_DEFAULTS["duration_months"])
        _set_entry(self.ent_entries,    FIELD_DEFAULTS["max_entries"])

        self.editing_tier_id  = None
        self.selected_tier_id = None
        self.btn_save.configure(text="Salva Dati",
                                fg_color=UI_COLORS["btn_success"],
                                hover_color=UI_COLORS["btn_success_hover"])
        self.load_data()

    def load_into_form(self):
        if not self.selected_tier_id:
            return messagebox.showwarning("Attenzione", "Seleziona una fascia.")
        tier = self.db.query(Tier).filter(Tier.id == self.selected_tier_id).first()
        if not tier:
            return

        self.clear_form()
        _set_entry(self.ent_code, tier.name)

        if self.show_age:
            _set_entry(self.ent_age_min, str(tier.min_age))
            _set_entry(self.ent_age_max, str(tier.max_age))
        if self.show_cost:
            _set_entry(self.ent_cost, str(tier.cost))

        _set_entry(self.ent_entry_time, tier.start_time[:5])
        _set_entry(self.ent_exit_time,  tier.end_time[:5])
        _set_entry(self.ent_duration,   str(tier.duration_months))
        _set_entry(self.ent_entries,    str(tier.max_entries))

        self.editing_tier_id = tier.id
        self.btn_save.configure(text="Aggiorna Dati",
                                fg_color=UI_COLORS["btn_primary"],
                                hover_color=UI_COLORS["btn_primary_hover"])

    def _read_form_fields(self) -> dict:
        """Reads and validates all form fields. Raises ValueError if invalid."""
        entry_time = self.ent_entry_time.get().strip()
        exit_time  = self.ent_exit_time.get().strip()
        datetime.strptime(entry_time, "%H:%M")
        datetime.strptime(exit_time,  "%H:%M")
        return {
            "code":             self.ent_code.get().strip(),
            "entry_time":       entry_time,
            "exit_time":        exit_time,
            "cost":             float(self.ent_cost.get().strip().replace(",", ".")) if self.show_cost else 0.0,
            "age_min":          int(self.ent_age_min.get().strip()) if self.show_age else 0,
            "age_max":          int(self.ent_age_max.get().strip()) if self.show_age else 999,
            "duration_months":  int(self.ent_duration.get().strip() or FIELD_DEFAULTS["duration_months"]),
            "entries":          int(self.ent_entries.get().strip()  or FIELD_DEFAULTS["max_entries"]),
        }

    def _update_tier(self, data: dict):
        tier = self.db.query(Tier).filter(Tier.id == self.editing_tier_id).first()
        if not tier:
            return
        tier.name            = data["code"]
        tier.cost            = data["cost"]
        tier.min_age         = data["age_min"]
        tier.max_age         = data["age_max"]
        tier.start_time      = data["entry_time"]
        tier.end_time        = data["exit_time"]
        tier.duration_months = data["duration_months"]
        tier.max_entries     = data["entries"]

    def _create_tier(self, data: dict):
        self.db.add(Tier(
            name=data["code"],          cost=data["cost"],
            min_age=data["age_min"],    max_age=data["age_max"],
            start_time=data["entry_time"], end_time=data["exit_time"],
            duration_months=data["duration_months"], max_entries=data["entries"],
        ))

    def save_tier(self):
        code = self.ent_code.get().strip()
        if not code:
            return messagebox.showwarning("Errore", "La sigla è obbligatoria.")
        try:
            data = self._read_form_fields()
        except ValueError as e:
            msg = ("Verifica che gli orari siano nel formato HH:MM (es. 08:30)."
                   if "time" in str(e)
                   else "Verifica che Costo, Età, Durata e Ingressi siano numeri validi.")
            return messagebox.showwarning("Errore", msg)

        if self.editing_tier_id:
            self._update_tier(data)
        else:
            self._create_tier(data)

        self.db.commit()
        self.clear_form()

    def delete_tier(self):
        if not self.selected_tier_id:
            return messagebox.showwarning("Attenzione", "Seleziona una fascia.")

        linked_members = self.db.query(Member).filter(Member.tier_id == self.selected_tier_id).count()
        if linked_members > 0:
            return messagebox.showerror("Errore",
                                        f"Ci sono {linked_members} soci iscritti con questa fascia!")

        if messagebox.askyesno("Conferma", "Sei sicuro di voler eliminare questa fascia?"):
            tier = self.db.query(Tier).filter(Tier.id == self.selected_tier_id).first()
            if tier:
                self.db.delete(tier)
                self.db.commit()
            self.clear_form()
