import customtkinter as ctk
from tkinter import messagebox
import calendar
from datetime import datetime, date
from core.database import SessionLocal, Lesson, Activity

class LezioniView(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self.db = SessionLocal()
        self.row_frames = {}
        self.selected_lesson_id = None

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        left_frame = ctk.CTkFrame(self, width=240, fg_color=("#FFFFFF", "#2C2C2E"), corner_radius=12, border_width=1, border_color=("#E5E5EA", "#3A3A3C"))
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 20))
        
        mese_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        mese_frame.pack(pady=15)
        ctk.CTkLabel(mese_frame, text="Mese:", font=ctk.CTkFont(family="Ubuntu")).grid(row=0, column=0, padx=5, pady=5)
        self.cmb_mese = ctk.CTkOptionMenu(mese_frame, values=[f"{i:02d}" for i in range(1, 13)], width=80); self.cmb_mese.set(f"{datetime.now().month:02d}"); self.cmb_mese.grid(row=0, column=1, padx=5, pady=5)
        ctk.CTkLabel(mese_frame, text="Anno:", font=ctk.CTkFont(family="Ubuntu")).grid(row=1, column=0, padx=5, pady=5)
        self.cmb_anno = ctk.CTkOptionMenu(mese_frame, values=[str(datetime.now().year), str(datetime.now().year + 1)], width=80); self.cmb_anno.set(str(datetime.now().year)); self.cmb_anno.grid(row=1, column=1, padx=5, pady=5)

        ctk.CTkLabel(left_frame, text="Giorni:", font=ctk.CTkFont(family="Ubuntu", weight="bold")).pack(pady=(15, 5))
        self.giorni_vars = {i: ctk.IntVar() for i in range(7)}
        for i, nome in enumerate(["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]):
            ctk.CTkCheckBox(left_frame, text=nome, variable=self.giorni_vars[i], font=ctk.CTkFont(family="Ubuntu")).pack(anchor="w", padx=30, pady=3)

        ctk.CTkLabel(left_frame, text="Inizio (19:00):", font=ctk.CTkFont(family="Ubuntu")).pack(pady=(15, 0))
        self.ent_inizio = ctk.CTkEntry(left_frame, justify="center"); self.ent_inizio.pack(pady=5)
        ctk.CTkLabel(left_frame, text="Fine (20:00):", font=ctk.CTkFont(family="Ubuntu")).pack(pady=(5, 0))
        self.ent_fine = ctk.CTkEntry(left_frame, justify="center"); self.ent_fine.pack(pady=5)
        ctk.CTkLabel(left_frame, text="Posti:", font=ctk.CTkFont(family="Ubuntu")).pack(pady=(5, 0))
        self.ent_posti = ctk.CTkEntry(left_frame, justify="center"); self.ent_posti.insert(0, "60"); self.ent_posti.pack(pady=5)

        ctk.CTkButton(left_frame, text="Genera", width=160, height=38, font=ctk.CTkFont(family="Ubuntu", weight="bold"), fg_color="#34C759", command=self.genera_lezioni).pack(pady=20)

        right_frame = ctk.CTkFrame(self, fg_color="transparent")
        right_frame.grid(row=0, column=1, sticky="nsew")
        right_frame.grid_rowconfigure(1, weight=1)
        right_frame.grid_columnconfigure(0, weight=1)

        self.tabview = ctk.CTkTabview(right_frame, fg_color=("#FFFFFF", "#2C2C2E"), segmented_button_selected_color="#007AFF")
        self.tabview.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        self.activities = self.db.query(Activity).all()
        for a in self.activities: self.tabview.add(a.name)
        self.tabview._segmented_button.configure(command=self.carica_tabella)

        self.table_container = ctk.CTkFrame(right_frame, fg_color="transparent")
        self.table_container.grid(row=1, column=0, sticky="nsew")
        self.cols = [("data", "Data", 2), ("giorno", "Giorno", 2), ("orario", "Orario", 3), ("posti", "Posti", 1)]
        header_tab = ctk.CTkFrame(self.table_container, fg_color=("#E5E5EA", "#3A3A3C"), height=35, corner_radius=6)
        header_tab.pack(fill="x", pady=(0, 5))
        for i, col in enumerate(self.cols):
            header_tab.grid_columnconfigure(i, weight=col[2])
            ctk.CTkLabel(header_tab, text=col[1], font=ctk.CTkFont(family="Ubuntu", size=12, weight="bold")).grid(row=0, column=i, padx=10, pady=5, sticky="w")

        self.scroll_table = ctk.CTkScrollableFrame(self.table_container, fg_color="transparent")
        self.scroll_table.pack(fill="both", expand=True)

        ctk.CTkButton(right_frame, text="🗑️ Elimina", width=180, height=38, font=ctk.CTkFont(family="Ubuntu", weight="bold"), fg_color="#FF3B30", command=self.elimina_lezione).grid(row=2, column=0, pady=15, sticky="e")

        self.carica_tabella()

    def seleziona_riga(self, l_id):
        self.selected_lesson_id = l_id
        for r_id, f in self.row_frames.items(): f.configure(fg_color=("#E5F1FF", "#0A2A4A") if r_id == l_id else ("#FFFFFF", "#2C2C2E"), border_color="#007AFF" if r_id == l_id else ("#E5E5EA", "#3A3A3C"))

    def crea_riga_tabella(self, l):
        f = ctk.CTkFrame(self.scroll_table, fg_color=("#FFFFFF", "#2C2C2E"), height=45, corner_radius=8, border_width=1, border_color=("#E5E5EA", "#3A3A3C"), cursor="hand2")
        f.pack(fill="x", pady=2); f.pack_propagate(False)
        valori = [datetime.strptime(l.date, "%Y-%m-%d").strftime("%d/%m/%Y") if l.date else "-", l.day_of_week, f"{l.start_time} - {l.end_time}", str(l.total_seats)]
        elems = [f]
        for i, val in enumerate(valori):
            f.grid_columnconfigure(i, weight=self.cols[i][2])
            lbl = ctk.CTkLabel(f, text=val, font=ctk.CTkFont(family="Ubuntu", size=13)); lbl.grid(row=0, column=i, padx=10, pady=10, sticky="w"); elems.append(lbl)
        for w in elems:
            w.bind("<Button-1>", lambda e, id=l.id: self.seleziona_riga(id))
            w.bind("<Enter>", lambda e, fr=f, id=l.id: fr.configure(fg_color=("#F8F8F9", "#3A3A3C")) if self.selected_lesson_id != id else None)
            w.bind("<Leave>", lambda e, fr=f, id=l.id: fr.configure(fg_color=("#FFFFFF", "#2C2C2E")) if self.selected_lesson_id != id else None)
        self.row_frames[l.id] = f

    def carica_tabella(self, *args):
        for w in self.scroll_table.winfo_children(): w.destroy()
        self.row_frames.clear(); self.selected_lesson_id = None
        if not self.activities: return
        att_id = next((a.id for a in self.activities if a.name == self.tabview.get()), None)
        if att_id:
            for l in self.db.query(Lesson).filter(Lesson.activity_id == att_id).order_by(Lesson.date, Lesson.start_time).all(): self.crea_riga_tabella(l)

    def genera_lezioni(self):
        att_id = next((a.id for a in self.activities if a.name == self.tabview.get()), None)
        m = int(self.cmb_mese.get()); y = int(self.cmb_anno.get()); ini = self.ent_inizio.get().strip(); fin = self.ent_fine.get().strip(); p = self.ent_posti.get().strip()
        if not ini or not fin or not p.isdigit(): return messagebox.showwarning("Errore", "Verifica dati.")
        g_scelti = [i for i in range(7) if self.giorni_vars[i].get() == 1]
        if not g_scelti: return messagebox.showwarning("Errore", "Spunta giorni.")

        g_nomi = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]; count = 0
        for g in range(1, calendar.monthrange(y, m)[1] + 1):
            dt = date(y, m, g)
            if dt.weekday() in g_scelti:
                ds = dt.strftime("%Y-%m-%d")
                if not self.db.query(Lesson).filter(Lesson.date == ds, Lesson.start_time == ini, Lesson.activity_id == att_id).first():
                    self.db.add(Lesson(date=ds, day_of_week=g_nomi[dt.weekday()], start_time=ini, end_time=fin, total_seats=int(p), activity_id=att_id))
                    count += 1
        self.db.commit(); messagebox.showinfo("Completato", f"Generate {count} lezioni!"); self.carica_tabella()

    def elimina_lezione(self):
        if not self.selected_lesson_id: return messagebox.showwarning("Attenzione", "Seleziona lezione.")
        if messagebox.askyesno("Conferma", "Annullare lezione?"):
            l = self.db.query(Lesson).filter(Lesson.id == self.selected_lesson_id).first()
            if l: self.db.delete(l); self.db.commit(); self.carica_tabella()

    def destroy(self):
        self.db.close()
        super().destroy()