import customtkinter as ctk
from tkinter import filedialog, messagebox
import shutil
import os
from datetime import datetime
import json
import serial.tools.list_ports 

CONFIG_FILE = "config.json"

def salva_impostazione(chiave, valore):
    config = {}
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            try: config = json.load(f)
            except: pass
    
    config[chiave] = valore
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f)

def leggi_impostazione(chiave, default):
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            try: return json.load(f).get(chiave, default)
            except: pass
    return default


# ==================== SCHEDA PRINCIPALE: SettingsView (COME FRAME!) ====================
class SettingsView(ctk.CTkFrame):
    def __init__(self, parent, controller=None, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.controller = controller 
        
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True)

        lbl_titolo = ctk.CTkLabel(self.scroll, text="Impostazioni di Sistema", font=ctk.CTkFont(family="Ubuntu", size=28, weight="bold"), text_color=("#1D1D1F", "#FFFFFF"))
        lbl_titolo.pack(pady=(20, 20), padx=30, anchor="w")

        # ==================== HARDWARE E TORNELLO ====================
        hw_frame = ctk.CTkFrame(self.scroll, fg_color=("#FFFFFF", "#2C2C2E"), corner_radius=12, border_width=1, border_color=("#E5E5EA", "#3A3A3C"))
        hw_frame.pack(padx=30, pady=(0, 15), fill="x")
        
        ctk.CTkLabel(hw_frame, text="🔌 Lettore Schede (Tornello)", font=ctk.CTkFont(family="Ubuntu", size=16, weight="bold"), text_color=("#1D1D1F", "#FFFFFF")).pack(pady=(20, 5), padx=20, anchor="w")
        ctk.CTkLabel(hw_frame, text="Seleziona la porta COM del lettore. Il software resterà in ascolto perenne in background.", font=ctk.CTkFont(family="Ubuntu", size=12), text_color=("#86868B", "#98989D")).pack(padx=20, anchor="w")
        
        box_hw = ctk.CTkFrame(hw_frame, fg_color="transparent")
        box_hw.pack(pady=(10, 20), padx=20, fill="x")

        porte = [p.device for p in serial.tools.list_ports.comports()]
        if not porte: porte = ["Nessun hardware rilevato"]
        
        self.cmb_porta = ctk.CTkComboBox(box_hw, values=porte, width=200, font=ctk.CTkFont(family="Ubuntu", size=14))
        self.cmb_porta.set(leggi_impostazione("porta_tornello", porte[0]))
        self.cmb_porta.pack(side="left")
        
        ctk.CTkButton(box_hw, text="Connetti / Salva", width=120, height=36, font=ctk.CTkFont(family="Ubuntu", size=13, weight="bold"), fg_color="#34C759", hover_color="#2eb350", command=self.salva_porta).pack(side="left", padx=10)

        # ==================== CARD NOME PALESTRA ====================
        pers_frame = ctk.CTkFrame(self.scroll, fg_color=("#FFFFFF", "#2C2C2E"), corner_radius=12, border_width=1, border_color=("#E5E5EA", "#3A3A3C"))
        pers_frame.pack(padx=30, pady=(0, 15), fill="x")
        
        ctk.CTkLabel(pers_frame, text="🏷️ Nome Palestra", font=ctk.CTkFont(family="Ubuntu", size=16, weight="bold"), text_color=("#1D1D1F", "#FFFFFF")).pack(pady=(20, 5), padx=20, anchor="w")
        
        input_frame = ctk.CTkFrame(pers_frame, fg_color="transparent")
        input_frame.pack(pady=(10, 20), padx=20, fill="x")
        
        self.ent_nome_palestra = ctk.CTkEntry(input_frame, width=280, font=ctk.CTkFont(family="Ubuntu", size=14))
        self.ent_nome_palestra.insert(0, leggi_impostazione("nome_palestra", "Palestra 3000"))
        self.ent_nome_palestra.pack(side="left")
        
        ctk.CTkButton(input_frame, text="Salva", width=100, height=36, font=ctk.CTkFont(family="Ubuntu", size=13, weight="bold"), fg_color="#007AFF", hover_color="#005ecb", command=self.salva_nome).pack(side="left", padx=10)

        # ==================== CARD TEMA VISIVO ====================
        theme_frame = ctk.CTkFrame(self.scroll, fg_color=("#FFFFFF", "#2C2C2E"), corner_radius=12, border_width=1, border_color=("#E5E5EA", "#3A3A3C"))
        theme_frame.pack(padx=30, pady=(0, 15), fill="x")
        
        ctk.CTkLabel(theme_frame, text="🎨 Aspetto e Tema", font=ctk.CTkFont(family="Ubuntu", size=16, weight="bold"), text_color=("#1D1D1F", "#FFFFFF")).pack(pady=(20, 5), padx=20, anchor="w")
        
        tema_attuale = leggi_impostazione("tema", "Light")
        self.theme_var = ctk.StringVar(value=tema_attuale)
        
        self.seg_theme = ctk.CTkSegmentedButton(theme_frame, values=["Light", "Dark", "System"], variable=self.theme_var, command=self.cambia_tema, selected_color="#007AFF", selected_hover_color="#005ecb")
        self.seg_theme.pack(pady=(15, 20), padx=20, fill="x")

        # ==================== CARD DATABASE ====================
        db_frame = ctk.CTkFrame(self.scroll, fg_color=("#FFFFFF", "#2C2C2E"), corner_radius=12, border_width=1, border_color=("#E5E5EA", "#3A3A3C"))
        db_frame.pack(padx=30, pady=(0, 20), fill="x")

        ctk.CTkLabel(db_frame, text="💾 Gestione Database Locale", font=ctk.CTkFont(family="Ubuntu", size=16, weight="bold"), text_color=("#1D1D1F", "#FFFFFF")).pack(pady=(20, 5), padx=20, anchor="w")
        
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.db_path = os.path.join(base_dir, "palestra3000.db")
        
        if os.path.exists(self.db_path):
            dim_kb = os.path.getsize(self.db_path) / 1024
            stato_testo = f"Stato: Connesso  |  Dimensione: {dim_kb:.2f} KB"
            colore_stato = "#34C759" 
        else:
            stato_testo = "Stato: Database non trovato!"
            colore_stato = "#FF3B30" 

        ctk.CTkLabel(db_frame, text=stato_testo, text_color=colore_stato, font=ctk.CTkFont(family="Ubuntu", weight="bold")).pack(padx=20, anchor="w")

        btn_db_frame = ctk.CTkFrame(db_frame, fg_color="transparent")
        btn_db_frame.pack(pady=(15, 20), padx=20, fill="x")

        ctk.CTkButton(btn_db_frame, text="Crea Backup", width=140, height=38, font=ctk.CTkFont(family="Ubuntu", size=14, weight="bold"), fg_color="#007AFF", hover_color="#005ecb", command=self.esegui_backup).pack(side="left")
        ctk.CTkButton(btn_db_frame, text="Ripristina Dati", width=140, height=38, font=ctk.CTkFont(family="Ubuntu", size=14, weight="bold"), fg_color="#FF9500", hover_color="#d35400", command=self.ripristina_backup).pack(side="right")

    # --- FUNZIONALITA' ---
    def salva_porta(self):
        porta = self.cmb_porta.get()
        salva_impostazione("porta_tornello", porta)
        if self.controller and hasattr(self.controller, "avvia_ascolto_hardware"):
            self.controller.avvia_ascolto_hardware(porta)
        messagebox.showinfo("Salvato", f"Lettore impostato sulla porta {porta}.\nIn ascolto in background.")

    def salva_nome(self):
        nuovo_nome = self.ent_nome_palestra.get().strip()
        if nuovo_nome:
            salva_impostazione("nome_palestra", nuovo_nome)
            if self.controller and hasattr(self.controller, "logo"):
                self.controller.logo.configure(text=nuovo_nome)
            messagebox.showinfo("Salvato", "Nome palestra aggiornato con successo!")

    def cambia_tema(self, nuovo_tema):
        ctk.set_appearance_mode(nuovo_tema)
        salva_impostazione("tema", nuovo_tema)

    def esegui_backup(self):
        if not os.path.exists(self.db_path):
            return messagebox.showerror("Errore", "Nessun database da salvare!")
            
        data_odierna = datetime.now().strftime("%Y%m%d_%H%M")
        percorso_salvataggio = filedialog.asksaveasfilename(
            defaultextension=".db", initialfile=f"backup_palestra_{data_odierna}.db",
            title="Salva il Backup del Database", filetypes=[("Database SQLite", "*.db")]
        )
        if percorso_salvataggio:
            try:
                shutil.copy2(self.db_path, percorso_salvataggio)
                messagebox.showinfo("Completato", f"Backup salvato in:\n{percorso_salvataggio}")
            except Exception as e:
                messagebox.showerror("Errore", f"Impossibile creare il backup:\n{e}")

    def ripristina_backup(self):
        if messagebox.askyesno("Attenzione", "Il ripristino sovrascriverà TUTTI i dati attuali.\nVuoi procedere?"):
            percorso_file = filedialog.askopenfilename(title="Seleziona il file di Backup", filetypes=[("Database SQLite", "*.db")])
            if percorso_file:
                try:
                    shutil.copy2(percorso_file, self.db_path)
                    messagebox.showinfo("Completato", "Database ripristinato!\n\nRiavvia il programma per caricare i nuovi dati.")
                except Exception as e:
                    messagebox.showerror("Errore", f"Impossibile ripristinare il database:\n{e}")

# Alias di sicurezza per evitare problemi di import
SettingsWindow = SettingsView