import customtkinter as ctk
from tkinter import filedialog, messagebox
import shutil
import os
from datetime import datetime
import json
import serial.tools.list_ports 

CONFIG_FILE = "config.json"

def salva_impostazione(chiave, valore):
    try:
        config = json.load(open(CONFIG_FILE, "r")) if os.path.exists(CONFIG_FILE) else {}
        config[chiave] = valore; json.dump(config, open(CONFIG_FILE, "w"))
    except: pass

def leggi_impostazione(chiave, default):
    try: return json.load(open(CONFIG_FILE, "r")).get(chiave, default) if os.path.exists(CONFIG_FILE) else default
    except: return default

class SettingsView(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app

        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True)

        ctk.CTkLabel(self.scroll, text="Impostazioni", font=ctk.CTkFont(family="Ubuntu", size=28, weight="bold")).pack(pady=(0, 20), anchor="w")

        hw = ctk.CTkFrame(self.scroll, fg_color=("#FFFFFF", "#2C2C2E"), corner_radius=12, border_width=1, border_color=("#E5E5EA", "#3A3A3C")); hw.pack(pady=(0, 15), fill="x")
        ctk.CTkLabel(hw, text="🔌 Tornello", font=ctk.CTkFont(family="Ubuntu", size=16, weight="bold")).pack(pady=(20, 5), padx=20, anchor="w")
        box = ctk.CTkFrame(hw, fg_color="transparent"); box.pack(pady=(10, 20), padx=20, fill="x")
        porte = [p.device for p in serial.tools.list_ports.comports()] or ["Nessuno"]
        self.cmb_porta = ctk.CTkComboBox(box, values=porte, width=200, font=ctk.CTkFont(family="Ubuntu", size=14)); self.cmb_porta.set(leggi_impostazione("porta_tornello", porte[0])); self.cmb_porta.pack(side="left")
        ctk.CTkButton(box, text="Salva", width=120, height=36, font=ctk.CTkFont(family="Ubuntu", weight="bold"), fg_color="#34C759", command=self.salva_porta).pack(side="left", padx=10)

        pers = ctk.CTkFrame(self.scroll, fg_color=("#FFFFFF", "#2C2C2E"), corner_radius=12, border_width=1, border_color=("#E5E5EA", "#3A3A3C")); pers.pack(pady=(0, 15), fill="x")
        ctk.CTkLabel(pers, text="🏷️ Nome Palestra", font=ctk.CTkFont(family="Ubuntu", size=16, weight="bold")).pack(pady=(20, 5), padx=20, anchor="w")
        box2 = ctk.CTkFrame(pers, fg_color="transparent"); box2.pack(pady=(10, 20), padx=20, fill="x")
        self.ent_nome = ctk.CTkEntry(box2, width=280, font=ctk.CTkFont(family="Ubuntu", size=14)); self.ent_nome.insert(0, leggi_impostazione("nome_palestra", "Palestra 3000")); self.ent_nome.pack(side="left")
        ctk.CTkButton(box2, text="Salva", width=100, height=36, font=ctk.CTkFont(family="Ubuntu", weight="bold"), fg_color="#007AFF", command=self.salva_nome).pack(side="left", padx=10)

        tm = ctk.CTkFrame(self.scroll, fg_color=("#FFFFFF", "#2C2C2E"), corner_radius=12, border_width=1, border_color=("#E5E5EA", "#3A3A3C")); tm.pack(pady=(0, 15), fill="x")
        ctk.CTkLabel(tm, text="🎨 Tema", font=ctk.CTkFont(family="Ubuntu", size=16, weight="bold")).pack(pady=(20, 5), padx=20, anchor="w")
        self.theme_var = ctk.StringVar(value=leggi_impostazione("tema", "Light"))
        ctk.CTkSegmentedButton(tm, values=["Light", "Dark", "System"], variable=self.theme_var, command=self.cambia_tema).pack(pady=(15, 20), padx=20, fill="x")

        dbf = ctk.CTkFrame(self.scroll, fg_color=("#FFFFFF", "#2C2C2E"), corner_radius=12, border_width=1, border_color=("#E5E5EA", "#3A3A3C")); dbf.pack(pady=(0, 20), fill="x")
        ctk.CTkLabel(dbf, text="💾 Database", font=ctk.CTkFont(family="Ubuntu", size=16, weight="bold")).pack(pady=(20, 5), padx=20, anchor="w")
        self.db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "palestra3000.db")
        box3 = ctk.CTkFrame(dbf, fg_color="transparent"); box3.pack(pady=(15, 20), padx=20, fill="x")
        ctk.CTkButton(box3, text="Backup", width=140, height=38, font=ctk.CTkFont(family="Ubuntu", weight="bold"), fg_color="#007AFF", command=self.esegui_backup).pack(side="left")

    def salva_porta(self):
        p = self.cmb_porta.get(); salva_impostazione("porta_tornello", p); self.app.avvia_ascolto_hardware(p); messagebox.showinfo("Salvato", "In ascolto.")
    def salva_nome(self):
        n = self.ent_nome.get().strip(); salva_impostazione("nome_palestra", n); self.app.logo.configure(text=n)
    def cambia_tema(self, t):
        ctk.set_appearance_mode(t); salva_impostazione("tema", t)
    def esegui_backup(self):
        if not os.path.exists(self.db_path): return
        dst = filedialog.asksaveasfilename(defaultextension=".db", initialfile=f"backup_{datetime.now().strftime('%Y%m%d')}.db", filetypes=[("DB", "*.db")])
        if dst: shutil.copy2(self.db_path, dst); messagebox.showinfo("Ok", "Salvato!")