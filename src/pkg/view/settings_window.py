import customtkinter as ctk
from tkinter import filedialog, messagebox
import serial
import serial.tools.list_ports
import threading
import time
from src.pkg.config.app_config import ConfigManager

class SettingsView(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self.config = ConfigManager.load_all()

        ctk.CTkLabel(self, text="⚙️ Impostazioni di Sistema", font=ctk.CTkFont(family="Montserrat", size=24, weight="bold"), text_color=("#1D1D1F", "#FFFFFF")).pack(anchor="w", padx=20, pady=(20, 10))

        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_frame.pack(fill="both", expand=True, padx=10)

        # --- SEZIONE 1: PALESTRA ---
        frame_gym = ctk.CTkFrame(self.scroll_frame, fg_color=("#FFFFFF", "#2C2C2E"), corner_radius=12, border_width=1, border_color=("#E5E5EA", "#3A3A3C"))
        frame_gym.pack(fill="x", pady=10, padx=10)
        ctk.CTkLabel(frame_gym, text="Dati Palestra", font=ctk.CTkFont(family="Montserrat", size=16, weight="bold")).pack(anchor="w", padx=20, pady=(15, 10))

        self.ent_name = self.create_field(frame_gym, "Nome Palestra:", self.config.get("nome_palestra", "Palestra 3000"))
        
        row_logo = ctk.CTkFrame(frame_gym, fg_color="transparent")
        row_logo.pack(fill="x", padx=20, pady=(5, 15))
        ctk.CTkLabel(row_logo, text="Logo Palestra (PNG/JPG):", font=ctk.CTkFont(family="Montserrat", weight="bold"), width=220, anchor="w").pack(side="left")
        self.ent_logo = ctk.CTkEntry(row_logo, width=300, font=ctk.CTkFont(family="Montserrat"))
        self.ent_logo.insert(0, self.config.get("percorso_logo", ""))
        self.ent_logo.pack(side="left", padx=(0, 10))
        ctk.CTkButton(row_logo, text="Scegli File", width=100, command=self.choose_logo, fg_color=("#E5E5EA", "#3A3A3C"), text_color=("#1D1D1F", "#FFFFFF"), hover_color=("#D1D1D6", "#5C5C5E")).pack(side="left")

        # --- SEZIONE 2: HARDWARE ---
        frame_hw = ctk.CTkFrame(self.scroll_frame, fg_color=("#FFFFFF", "#2C2C2E"), corner_radius=12, border_width=1, border_color=("#E5E5EA", "#3A3A3C"))
        frame_hw.pack(fill="x", pady=10, padx=10)
        
        header_hw = ctk.CTkFrame(frame_hw, fg_color="transparent")
        header_hw.pack(fill="x", padx=20, pady=(15, 10))
        ctk.CTkLabel(header_hw, text="Hardware (Lettore e Tornello)", font=ctk.CTkFont(family="Montserrat", size=16, weight="bold")).pack(side="left")
        ctk.CTkButton(header_hw, text="🔄 Aggiorna Porte", width=120, height=28, font=ctk.CTkFont(family="Montserrat", size=12, weight="bold"), fg_color=("#E5E5EA", "#3A3A3C"), text_color=("#1D1D1F", "#FFFFFF"), hover_color=("#D1D1D6", "#5C5C5E"), command=self.update_ports_menu).pack(side="right")

        self.available_ports = self.get_available_ports()

        row_reader = ctk.CTkFrame(frame_hw, fg_color="transparent")
        row_reader.pack(fill="x", padx=20, pady=(0, 5))
        ctk.CTkLabel(row_reader, text="Porta Lettore Badge:", font=ctk.CTkFont(family="Montserrat", weight="bold"), width=220, anchor="w").pack(side="left")
        self.cmb_reader_port = ctk.CTkOptionMenu(row_reader, values=self.available_ports, width=250, font=ctk.CTkFont(family="Montserrat"))
        self.cmb_reader_port.set(self.config.get("porta_lettore", "Nessun hardware"))
        self.cmb_reader_port.pack(side="left", padx=(0, 10))
        ctk.CTkButton(row_reader, text="Test Lettore", width=100, fg_color="#007AFF", hover_color="#005ecb", font=ctk.CTkFont(family="Montserrat", weight="bold"), command=self.run_reader_test).pack(side="left")

        row_relay = ctk.CTkFrame(frame_hw, fg_color="transparent")
        row_relay.pack(fill="x", padx=20, pady=(5, 15))
        ctk.CTkLabel(row_relay, text="Porta Relè Tornello:", font=ctk.CTkFont(family="Montserrat", weight="bold"), width=220, anchor="w").pack(side="left")
        self.cmb_relay_port = ctk.CTkOptionMenu(row_relay, values=self.available_ports, width=250, font=ctk.CTkFont(family="Montserrat"))
        self.cmb_relay_port.set(self.config.get("porta_rele", "Nessun hardware"))
        self.cmb_relay_port.pack(side="left", padx=(0, 10))
        ctk.CTkButton(row_relay, text="Test Tornello", width=100, fg_color="#FF9500", hover_color="#d67e00", font=ctk.CTkFont(family="Montserrat", weight="bold"), command=self.run_relay_test).pack(side="left")

        # --- SEZIONE 3: REGOLE ACCESSO ---
        frame_rules = ctk.CTkFrame(self.scroll_frame, fg_color=("#FFFFFF", "#2C2C2E"), corner_radius=12, border_width=1, border_color=("#E5E5EA", "#3A3A3C"))
        frame_rules.pack(fill="x", pady=10, padx=10)
        ctk.CTkLabel(frame_rules, text="Regole di Accesso (Cosa blocca il tornello?)", font=ctk.CTkFont(family="Montserrat", size=16, weight="bold")).pack(anchor="w", padx=20, pady=(15, 10))

        self.chk_enr = ctk.CTkCheckBox(frame_rules, text="Blocca se Iscrizione Annuale scaduta", font=ctk.CTkFont(family="Montserrat"))
        if self.config.get("blocco_iscr", True): self.chk_enr.select()
        self.chk_enr.pack(anchor="w", padx=20, pady=5)

        self.chk_sub = ctk.CTkCheckBox(frame_rules, text="Blocca se Abbonamento Mensile scaduto", font=ctk.CTkFont(family="Montserrat"))
        if self.config.get("blocco_abb", True): self.chk_sub.select()
        self.chk_sub.pack(anchor="w", padx=20, pady=5)

        self.chk_time = ctk.CTkCheckBox(frame_rules, text="Blocca se fuori dall'orario della propria fascia", font=ctk.CTkFont(family="Montserrat"))
        if self.config.get("blocco_orari", True): self.chk_time.select()
        self.chk_time.pack(anchor="w", padx=20, pady=5)

        self.chk_cert = ctk.CTkCheckBox(frame_rules, text="Blocca se Certificato Medico mancante o scaduto", font=ctk.CTkFont(family="Montserrat"))
        if self.config.get("blocco_cert", False): self.chk_cert.select()
        self.chk_cert.pack(anchor="w", padx=20, pady=(5, 15))

        # --- SEZIONE 3B: CONFIGURAZIONE TESSERE ---
        frame_badge = ctk.CTkFrame(self.scroll_frame, fg_color=("#FFFFFF", "#2C2C2E"), corner_radius=12, border_width=1, border_color=("#E5E5EA", "#3A3A3C"))
        frame_badge.pack(fill="x", pady=10, padx=10)
        ctk.CTkLabel(frame_badge, text="🎫 Configurazione Tessere", font=ctk.CTkFont(family="Montserrat", size=16, weight="bold")).pack(anchor="w", padx=20, pady=(15, 10))

        row_prefix = ctk.CTkFrame(frame_badge, fg_color="transparent")
        row_prefix.pack(fill="x", padx=20, pady=(0, 15))
        ctk.CTkLabel(row_prefix, text="Prefisso Badge Palestra:", font=ctk.CTkFont(family="Montserrat", weight="bold"), width=220, anchor="w").pack(side="left")
        self.ent_badge_prefix = ctk.CTkEntry(row_prefix, width=200, font=ctk.CTkFont(family="Montserrat"))
        self.ent_badge_prefix.insert(0, ConfigManager.get_badge_prefix())
        self.ent_badge_prefix.pack(side="left", padx=(0, 10))
        ctk.CTkLabel(row_prefix, text="(Es. 57340000000)", font=ctk.CTkFont(family="Montserrat", size=11), text_color=("#86868B", "#98989D")).pack(side="left")

        # --- SEZIONE 3C: ALERT SCADENZE ---
        frame_alerts = ctk.CTkFrame(self.scroll_frame, fg_color=("#FFFFFF", "#2C2C2E"), corner_radius=12, border_width=1, border_color=("#E5E5EA", "#3A3A3C"))
        frame_alerts.pack(fill="x", pady=10, padx=10)
        ctk.CTkLabel(frame_alerts, text="⏰ Alert Scadenze", font=ctk.CTkFont(family="Montserrat", size=16, weight="bold")).pack(anchor="w", padx=20, pady=(15, 10))

        row_alert_days = ctk.CTkFrame(frame_alerts, fg_color="transparent")
        row_alert_days.pack(fill="x", padx=20, pady=(0, 15))
        ctk.CTkLabel(row_alert_days, text="Giorni Alert Scadenza:", font=ctk.CTkFont(family="Montserrat", weight="bold"), width=220, anchor="w").pack(side="left")
        self.ent_alert_days = ctk.CTkEntry(row_alert_days, width=80, font=ctk.CTkFont(family="Montserrat"))
        self.ent_alert_days.insert(0, str(ConfigManager.get_scadenza_alert_giorni()))
        self.ent_alert_days.pack(side="left", padx=(0, 10))
        ctk.CTkLabel(row_alert_days, text="(giorni prima della scadenza)", font=ctk.CTkFont(family="Montserrat", size=11), text_color=("#86868B", "#98989D")).pack(side="left")

        # --- SEZIONE 4: INTERFACCIA ---
        frame_ui = ctk.CTkFrame(self.scroll_frame, fg_color=("#FFFFFF", "#2C2C2E"), corner_radius=12, border_width=1, border_color=("#E5E5EA", "#3A3A3C"))
        frame_ui.pack(fill="x", pady=10, padx=10)
        ctk.CTkLabel(frame_ui, text="Interfaccia e Visualizzazione", font=ctk.CTkFont(family="Montserrat", size=16, weight="bold")).pack(anchor="w", padx=20, pady=(15, 10))

        row_theme = ctk.CTkFrame(frame_ui, fg_color="transparent")
        row_theme.pack(fill="x", padx=20, pady=5)
        ctk.CTkLabel(row_theme, text="Tema Colori:", font=ctk.CTkFont(family="Montserrat", weight="bold"), width=220, anchor="w").pack(side="left")
        self.cmb_theme = ctk.CTkOptionMenu(row_theme, values=["Light", "Dark", "System"], command=self.change_theme)
        self.cmb_theme.set(self.config.get("tema", "Light"))
        self.cmb_theme.pack(side="left")

        # Sezione colori personalizzati
        row_colors = ctk.CTkFrame(frame_ui, fg_color="transparent")
        row_colors.pack(fill="x", padx=20, pady=(10, 5))
        ctk.CTkLabel(row_colors, text="Colore Primario:", font=ctk.CTkFont(family="Montserrat", weight="bold"), width=220, anchor="w").pack(side="left")
        
        colors = ConfigManager.get_colors()
        self.ent_primary_color = ctk.CTkEntry(row_colors, width=120, font=ctk.CTkFont(family="Montserrat"))
        self.ent_primary_color.insert(0, colors.get("primary", "#007AFF"))
        self.ent_primary_color.pack(side="left", padx=(0, 5))
        ctk.CTkButton(row_colors, text="🎨 Scegli", width=80, command=self.choose_primary_color, 
                     fg_color=("#E5E5EA", "#3A3A3C"), text_color=("#1D1D1F", "#FFFFFF"),
                     hover_color=("#D1D1D6", "#5C5C5E")).pack(side="left")

        self.chk_show_cost = ctk.CTkCheckBox(frame_ui, text="Mostra colonna 'Costo' nella tabella Tariffe", font=ctk.CTkFont(family="Montserrat"))
        if self.config.get("mostra_costo_fasce", False): self.chk_show_cost.select()
        self.chk_show_cost.pack(anchor="w", padx=20, pady=5)

        self.chk_show_age = ctk.CTkCheckBox(frame_ui, text="Mostra colonne 'Età' nella tabella Tariffe", font=ctk.CTkFont(family="Montserrat"))
        if self.config.get("mostra_eta_fasce", False): self.chk_show_age.select()
        self.chk_show_age.pack(anchor="w", padx=20, pady=(5, 15))

        # --- SEZIONE 5: GESTIONE DATABASE ---
        from src.pkg.config.db_config import DatabaseConfig
        frame_db = ctk.CTkFrame(self.scroll_frame, fg_color=("#FFFFFF", "#2C2C2E"), corner_radius=12, border_width=1, border_color=("#E5E5EA", "#3A3A3C"))
        frame_db.pack(fill="x", pady=10, padx=10)
        ctk.CTkLabel(frame_db, text="🗄️ Gestione Database", font=ctk.CTkFont(family="Montserrat", size=16, weight="bold")).pack(anchor="w", padx=20, pady=(15, 10))
        
        # Info database
        db_config = DatabaseConfig()
        db_path = db_config.db_path
        import os
        if os.path.exists(db_path):
            size_kb = os.path.getsize(db_path) / 1024
            import datetime
            modified = datetime.datetime.fromtimestamp(os.path.getmtime(db_path)).strftime("%Y-%m-%d %H:%M:%S")
            info_text = f"Percorso: {db_path}\nDimensione: {size_kb:.1f} KB\nUltima modifica: {modified}"
        else:
            info_text = "Database non trovato."
        
        ctk.CTkLabel(frame_db, text=info_text, font=ctk.CTkFont(family="Montserrat", size=12), justify="left").pack(anchor="w", padx=20, pady=(5, 10))
        
        # Pulsanti gestione database
        btn_db_frame = ctk.CTkFrame(frame_db, fg_color="transparent")
        btn_db_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        ctk.CTkButton(btn_db_frame, text="💾 Crea Backup", width=140, height=35, 
                     font=ctk.CTkFont(family="Montserrat", weight="bold"), 
                     fg_color="#34C759", hover_color="#2eb350",
                     command=self.create_backup).pack(side="left", padx=(0, 10))
        
        ctk.CTkButton(btn_db_frame, text="📂 Ripristina Backup", width=140, height=35,
                     font=ctk.CTkFont(family="Montserrat", weight="bold"),
                     fg_color="#FF9500", hover_color="#d67e00",
                     command=self.restore_backup).pack(side="left")

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=20)
        ctk.CTkButton(btn_frame, text="Salva Impostazioni", width=200, height=45, font=ctk.CTkFont(family="Montserrat", size=16, weight="bold"), fg_color="#34C759", hover_color="#2eb350", command=self.save_settings).pack(side="right")

    def get_available_ports(self):
        ports = ["Nessun hardware"]
        for port in serial.tools.list_ports.comports():
            ports.append(port.device)
        return ports

    def update_ports_menu(self):
        new_ports = self.get_available_ports()
        self.cmb_reader_port.configure(values=new_ports)
        self.cmb_relay_port.configure(values=new_ports)
        messagebox.showinfo("Aggiornamento", "Lista porte aggiornata con successo.")

    def run_reader_test(self):
        port = self.cmb_reader_port.get()
        if port == "Nessun hardware" or not port:
            return messagebox.showwarning("Attenzione", "Seleziona una porta valida.")

        if self.app.reader_hw:
            self.app.reader_hw.stop()

        test_win = ctk.CTkToplevel(self)
        test_win.title("Test Lettore Badge")
        test_win.geometry("400x200")
        test_win.configure(fg_color=("#F2F2F7", "#1C1C1E"))
        test_win.transient(self.winfo_toplevel())
        test_win.grab_set()

        lbl_status = ctk.CTkLabel(test_win, text="In attesa...\n\nStriscia o avvicina una tessera.", font=ctk.CTkFont(family="Montserrat", size=16, weight="bold"), text_color=("#1D1D1F", "#FFFFFF"))
        lbl_status.pack(expand=True)
        stop_test_event = threading.Event()

        def update_success(card):
            if test_win.winfo_exists():
                gym_prefix = "57340000000"
                if card.startswith(gym_prefix):
                    clean_number = card[len(gym_prefix):]
                    msg = f"✅ TEST SUPERATO E AUTENTICATO!\n\nLettura: {card}\nNumero da inserire: {clean_number}"
                else:
                    msg = f"✅ TEST SUPERATO!\n\nATTENZIONE: Questa tessera ({card})\nnon ha il prefisso corretto."
                lbl_status.configure(text=msg, text_color="#34C759")
                self.after(5000, test_win.destroy)

        def update_error(err_msg):
            if test_win.winfo_exists():
                lbl_status.configure(text=f"❌ Errore:\n\n{err_msg}", text_color="#FF3B30")

        def listen_for_test():
            try:
                with serial.Serial(port, 9600, timeout=1) as ser:
                    while not stop_test_event.is_set():
                        if ser.in_waiting > 0:
                            data = ser.readline().decode('utf-8').strip()
                            card = ''.join(filter(str.isdigit, data))
                            if card:
                                self.after(0, update_success, card)
                                return
            except Exception as e:
                if not stop_test_event.is_set():
                    self.after(0, update_error, str(e))

        threading.Thread(target=listen_for_test, daemon=True).start()

        def on_close():
            stop_test_event.set()
            test_win.destroy()
            self.app.reader_hw.start_listening(
                lambda badge: self.app.after(0, self.app.access_manager.process_badge, badge, self.app.get_current_settings())
            )

        test_win.protocol("WM_DELETE_WINDOW", on_close)

    def run_relay_test(self):
        port = self.cmb_relay_port.get()
        if port == "Nessun hardware" or not port:
            return messagebox.showwarning("Attenzione", "Seleziona una porta valida.")
        try:
            with serial.Serial(port, 9600, timeout=1) as ser:
                ser.write(b'\xA0\x01\x01\xA2')
                ser.dtr = True; ser.rts = True
                time.sleep(0.5) 
                ser.write(b'\xA0\x01\x00\xA1')
                ser.dtr = False; ser.rts = False
            messagebox.showinfo("Test", "Impulso inviato con successo!")
        except Exception as e:
            messagebox.showerror("Errore", f"Impossibile comunicare:\n\n{str(e)}")

    def create_field(self, parent, label_text, default_value):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=20, pady=5)
        ctk.CTkLabel(row, text=label_text, font=ctk.CTkFont(family="Montserrat", weight="bold"), width=220, anchor="w").pack(side="left")
        ent = ctk.CTkEntry(row, width=300, font=ctk.CTkFont(family="Montserrat"))
        ent.insert(0, default_value)
        ent.pack(side="left")
        return ent

    def choose_logo(self):
        file = filedialog.askopenfilename(filetypes=[("Immagini", "*.png *.jpg *.jpeg")])
        if file:
            self.ent_logo.delete(0, 'end')
            self.ent_logo.insert(0, file)

    def change_theme(self, choice):
        ctk.set_appearance_mode(choice)

    def choose_primary_color(self):
        """Apre il selettore colore per scegliere il colore primario."""
        from tkinter import colorchooser
        current_color = self.ent_primary_color.get()
        color = colorchooser.askcolor(color=current_color, title="Scegli Colore Primario")
        if color[1]:  # Se l'utente ha selezionato un colore
            self.ent_primary_color.delete(0, 'end')
            self.ent_primary_color.insert(0, color[1])

    def save_settings(self):
        config_dict = {
            "nome_palestra": self.ent_name.get().strip(),
            "percorso_logo": self.ent_logo.get().strip(),
            "porta_lettore": self.cmb_reader_port.get(),
            "porta_rele": self.cmb_relay_port.get(),
            "blocco_iscr": self.chk_enr.get() == 1,
            "blocco_abb": self.chk_sub.get() == 1,
            "blocco_orari": self.chk_time.get() == 1,
            "blocco_cert": self.chk_cert.get() == 1,
            "tema": self.cmb_theme.get(),
            "mostra_costo_fasce": self.chk_show_cost.get() == 1,
            "mostra_eta_fasce": self.chk_show_age.get() == 1,
            # Nuovi campi configurabili
            "badge_prefix": self.ent_badge_prefix.get().strip(),
            "scadenza_alert_giorni": int(self.ent_alert_days.get()) if self.ent_alert_days.get().isdigit() else 2,
            "colors": {"primary": self.ent_primary_color.get().strip()}
        }
        try:
            ConfigManager.save_all(config_dict)
            messagebox.showinfo("Successo", "Impostazioni salvate! Riavvia per applicare modifiche HW.")
            self.app.update_logo()
        except Exception as e:
            messagebox.showerror("Errore", f"Impossibile salvare:\n{e}")

    def create_backup(self):
        """Crea un backup del database."""
        from src.pkg.config.db_config import DatabaseConfig
        import shutil
        import datetime
        import os
        
        db_config = DatabaseConfig()
        db_path = db_config.db_path
        
        if not os.path.exists(db_path):
            return messagebox.showerror("Errore", "Database non trovato.")
        
        # Crea cartella backup se non esiste
        backup_dir = os.path.join(os.path.dirname(db_path), "backups")
        os.makedirs(backup_dir, exist_ok=True)
        
        # Genera nome file con timestamp
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"backup_{timestamp}.db"
        backup_path = os.path.join(backup_dir, backup_filename)
        
        try:
            shutil.copy2(db_path, backup_path)
            messagebox.showinfo("Backup completato", f"Backup creato con successo:\n{backup_filename}")
        except Exception as e:
            messagebox.showerror("Errore backup", f"Impossibile creare il backup:\n{str(e)}")

    def restore_backup(self):
        """Ripristina il database da un backup."""
        from src.pkg.config.db_config import DatabaseConfig
        import shutil
        import os
        
        db_config = DatabaseConfig()
        db_path = db_config.db_path
        backup_dir = os.path.join(os.path.dirname(db_path), "backups")
        
        # Se non ci sono backup, avvisa l'utente
        if not os.path.exists(backup_dir):
            return messagebox.showwarning("Nessun backup", "Non sono presenti backup nella cartella.")
        
        backups = [f for f in os.listdir(backup_dir) if f.startswith("backup_") and f.endswith(".db")]
        if not backups:
            return messagebox.showwarning("Nessun backup", "Non sono presenti backup nella cartella.")
        
        # Crea una finestra di dialogo personalizzata per scegliere il backup
        dialog = ctk.CTkToplevel(self)
        dialog.title("Seleziona Backup")
        dialog.geometry("500x400")
        dialog.configure(fg_color=("#F2F2F7", "#1C1C1E"))
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()
        
        ctk.CTkLabel(dialog, text="Seleziona un backup da ripristinare:", 
                    font=ctk.CTkFont(family="Montserrat", size=14, weight="bold")).pack(pady=(20, 10))
        
        # Lista dei backup
        listbox_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        listbox_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        selected_backup = {"path": None}
        
        def select_backup(backup_path):
            selected_backup["path"] = backup_path
        
        for backup in sorted(backups, reverse=True):
            backup_path = os.path.join(backup_dir, backup)
            size_kb = os.path.getsize(backup_path) / 1024
            btn_text = f"{backup} ({size_kb:.1f} KB)"
            btn = ctk.CTkButton(listbox_frame, text=btn_text, width=450, anchor="w",
                               font=ctk.CTkFont(family="Montserrat", size=11),
                               fg_color=("#FFFFFF", "#2C2C2E"),
                               hover_color=("#E5E5EA", "#3A3A3C"),
                               command=lambda p=backup_path: select_backup(p))
            btn.pack(fill="x", pady=2)
        
        def confirm_restore():
            if not selected_backup["path"]:
                return messagebox.showwarning("Attenzione", "Seleziona un backup.")
            
            if messagebox.askyesno("Conferma ripristino", "Sei sicuro di voler ripristinare questo backup?\\n\\nIl database attuale verrà sovrascritto.", icon="warning"):
                try:
                    # Chiudi eventuali connessioni al database
                    db_config.close_all_sessions()
                    # Copia il backup sul database
                    shutil.copy2(selected_backup["path"], db_path)
                    messagebox.showinfo("Ripristino completato", "Database ripristinato con successo.\\n\\nRiavvia l'applicazione.")
                    dialog.destroy()
                except Exception as e:
                    messagebox.showerror("Errore ripristino", f"Impossibile ripristinare il backup:\n{str(e)}")
        
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(0, 20))
        ctk.CTkButton(btn_frame, text="Annulla", width=100, command=dialog.destroy,
                     fg_color=("#E5E5EA", "#3A3A3C"), text_color=("#1D1D1F", "#FFFFFF")).pack(side="left")
        ctk.CTkButton(btn_frame, text="Ripristina", width=120, command=confirm_restore,
                     fg_color="#FF9500", hover_color="#d67e00").pack(side="right")
