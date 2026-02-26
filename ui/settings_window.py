import customtkinter as ctk
from tkinter import filedialog, messagebox
import json
import os

class SettingsView(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self.config_file = "config.json"
        self.config = self.carica_config()

        ctk.CTkLabel(self, text="⚙️ Impostazioni di Sistema", font=ctk.CTkFont(family="Montserrat", size=24, weight="bold"), text_color=("#1D1D1F", "#FFFFFF")).pack(anchor="w", padx=20, pady=(20, 10))

        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_frame.pack(fill="both", expand=True, padx=10)

        # --- SEZIONE 1: PALESTRA ---
        frame_palestra = ctk.CTkFrame(self.scroll_frame, fg_color=("#FFFFFF", "#2C2C2E"), corner_radius=12, border_width=1, border_color=("#E5E5EA", "#3A3A3C"))
        frame_palestra.pack(fill="x", pady=10, padx=10)
        ctk.CTkLabel(frame_palestra, text="Dati Palestra", font=ctk.CTkFont(family="Montserrat", size=16, weight="bold")).pack(anchor="w", padx=20, pady=(15, 10))

        self.ent_nome = self.crea_campo(frame_palestra, "Nome Palestra:", self.config.get("nome_palestra", "Palestra 3000"))
        
        row_logo = ctk.CTkFrame(frame_palestra, fg_color="transparent")
        row_logo.pack(fill="x", padx=20, pady=(5, 15))
        ctk.CTkLabel(row_logo, text="Logo Palestra (PNG/JPG):", font=ctk.CTkFont(family="Montserrat", weight="bold"), width=220, anchor="w").pack(side="left")
        self.ent_logo = ctk.CTkEntry(row_logo, width=300, font=ctk.CTkFont(family="Montserrat"))
        self.ent_logo.insert(0, self.config.get("percorso_logo", ""))
        self.ent_logo.pack(side="left", padx=(0, 10))
        ctk.CTkButton(row_logo, text="Scegli File", width=100, command=self.scegli_logo, fg_color=("#E5E5EA", "#3A3A3C"), text_color=("#1D1D1F", "#FFFFFF"), hover_color=("#D1D1D6", "#5C5C5E")).pack(side="left")

        # --- SEZIONE 2: HARDWARE E TORNELLO ---
        frame_hw = ctk.CTkFrame(self.scroll_frame, fg_color=("#FFFFFF", "#2C2C2E"), corner_radius=12, border_width=1, border_color=("#E5E5EA", "#3A3A3C"))
        frame_hw.pack(fill="x", pady=10, padx=10)
        ctk.CTkLabel(frame_hw, text="Hardware e Lettore Badge", font=ctk.CTkFont(family="Montserrat", size=16, weight="bold")).pack(anchor="w", padx=20, pady=(15, 10))

        row_hw = ctk.CTkFrame(frame_hw, fg_color="transparent")
        row_hw.pack(fill="x", padx=20, pady=(0, 15))
        ctk.CTkLabel(row_hw, text="Porta Seriale (Es. COM3 o /dev/ttyUSB0):", font=ctk.CTkFont(family="Montserrat", weight="bold"), width=320, anchor="w").pack(side="left")
        self.ent_porta = ctk.CTkEntry(row_hw, width=200, font=ctk.CTkFont(family="Montserrat"))
        self.ent_porta.insert(0, self.config.get("porta_tornello", "Nessun hardware"))
        self.ent_porta.pack(side="left")

        # --- SEZIONE 3: REGOLE ACCESSO ---
        frame_regole = ctk.CTkFrame(self.scroll_frame, fg_color=("#FFFFFF", "#2C2C2E"), corner_radius=12, border_width=1, border_color=("#E5E5EA", "#3A3A3C"))
        frame_regole.pack(fill="x", pady=10, padx=10)
        ctk.CTkLabel(frame_regole, text="Regole di Accesso (Cosa blocca il tornello?)", font=ctk.CTkFont(family="Montserrat", size=16, weight="bold")).pack(anchor="w", padx=20, pady=(15, 10))

        self.chk_iscr = ctk.CTkCheckBox(frame_regole, text="Blocca se Iscrizione Annuale scaduta", font=ctk.CTkFont(family="Montserrat"))
        if self.config.get("blocco_iscr", True): self.chk_iscr.select()
        self.chk_iscr.pack(anchor="w", padx=20, pady=5)

        self.chk_abb = ctk.CTkCheckBox(frame_regole, text="Blocca se Abbonamento Mensile scaduto", font=ctk.CTkFont(family="Montserrat"))
        if self.config.get("blocco_abb", True): self.chk_abb.select()
        self.chk_abb.pack(anchor="w", padx=20, pady=5)

        self.chk_orari = ctk.CTkCheckBox(frame_regole, text="Blocca se fuori dall'orario della propria fascia", font=ctk.CTkFont(family="Montserrat"))
        if self.config.get("blocco_orari", True): self.chk_orari.select()
        self.chk_orari.pack(anchor="w", padx=20, pady=5)

        self.chk_cert = ctk.CTkCheckBox(frame_regole, text="Blocca se Certificato Medico mancante o scaduto", font=ctk.CTkFont(family="Montserrat"))
        if self.config.get("blocco_cert", False): self.chk_cert.select()
        self.chk_cert.pack(anchor="w", padx=20, pady=(5, 15))

        # --- SEZIONE 4: INTERFACCIA ---
        frame_ui = ctk.CTkFrame(self.scroll_frame, fg_color=("#FFFFFF", "#2C2C2E"), corner_radius=12, border_width=1, border_color=("#E5E5EA", "#3A3A3C"))
        frame_ui.pack(fill="x", pady=10, padx=10)
        ctk.CTkLabel(frame_ui, text="Interfaccia e Visualizzazione", font=ctk.CTkFont(family="Montserrat", size=16, weight="bold")).pack(anchor="w", padx=20, pady=(15, 10))

        row_tema = ctk.CTkFrame(frame_ui, fg_color="transparent")
        row_tema.pack(fill="x", padx=20, pady=5)
        ctk.CTkLabel(row_tema, text="Tema Colori:", font=ctk.CTkFont(family="Montserrat", weight="bold"), width=220, anchor="w").pack(side="left")
        self.cmb_tema = ctk.CTkOptionMenu(row_tema, values=["Light", "Dark", "System"], command=self.cambia_tema)
        self.cmb_tema.set(self.config.get("tema", "Light"))
        self.cmb_tema.pack(side="left")

        self.chk_mostra_costo = ctk.CTkCheckBox(frame_ui, text="Mostra colonna 'Costo' nella tabella Tariffe", font=ctk.CTkFont(family="Montserrat"))
        if self.config.get("mostra_costo_fasce", False): self.chk_mostra_costo.select()
        self.chk_mostra_costo.pack(anchor="w", padx=20, pady=5)

        self.chk_mostra_eta = ctk.CTkCheckBox(frame_ui, text="Mostra colonne 'Età' nella tabella Tariffe", font=ctk.CTkFont(family="Montserrat"))
        if self.config.get("mostra_eta_fasce", False): self.chk_mostra_eta.select()
        self.chk_mostra_eta.pack(anchor="w", padx=20, pady=(5, 15))

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=20)
        ctk.CTkButton(btn_frame, text="Salva Impostazioni", width=200, height=45, font=ctk.CTkFont(family="Montserrat", size=16, weight="bold"), fg_color="#34C759", hover_color="#2eb350", command=self.salva_impostazioni).pack(side="right")

    def crea_campo(self, parent, label_text, default_value):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=20, pady=5)
        ctk.CTkLabel(row, text=label_text, font=ctk.CTkFont(family="Montserrat", weight="bold"), width=220, anchor="w").pack(side="left")
        ent = ctk.CTkEntry(row, width=300, font=ctk.CTkFont(family="Montserrat"))
        ent.insert(0, default_value)
        ent.pack(side="left")
        return ent

    def scegli_logo(self):
        file = filedialog.askopenfilename(filetypes=[("Immagini", "*.png *.jpg *.jpeg")])
        if file:
            self.ent_logo.delete(0, 'end')
            self.ent_logo.insert(0, file)

    def cambia_tema(self, scelta):
        ctk.set_appearance_mode(scelta)

    def carica_config(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r") as f: return json.load(f)
            except: return {}
        return {}

    def salva_impostazioni(self):
        config = {
            "nome_palestra": self.ent_nome.get().strip(),
            "percorso_logo": self.ent_logo.get().strip(),
            "porta_tornello": self.ent_porta.get().strip(),
            "blocco_iscr": self.chk_iscr.get() == 1,
            "blocco_abb": self.chk_abb.get() == 1,
            "blocco_orari": self.chk_orari.get() == 1,
            "blocco_cert": self.chk_cert.get() == 1,
            "tema": self.cmb_tema.get(),
            "mostra_costo_fasce": self.chk_mostra_costo.get() == 1,
            "mostra_eta_fasce": self.chk_mostra_eta.get() == 1
        }
        try:
            with open(self.config_file, "w") as f:
                json.dump(config, f, indent=4)
            messagebox.showinfo("Successo", "Impostazioni salvate correttamente!\nAlcune modifiche (come il logo) saranno visibili al riavvio.")
            self.app.aggiorna_logo()
        except Exception as e:
            messagebox.showerror("Errore", f"Impossibile salvare le impostazioni:\n{e}")