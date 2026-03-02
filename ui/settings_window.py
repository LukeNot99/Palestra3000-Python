import customtkinter as ctk
from tkinter import filedialog, messagebox
import json
import os
import serial
import serial.tools.list_ports
import threading
import time

class SettingsView(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self.config_file = "config.json"
        self.config = self.load_config()

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

        # --- SEZIONE 2: HARDWARE (LETTORE E RELÈ) CON AUTO-DISCOVERY ---
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

        self.chk_show_cost = ctk.CTkCheckBox(frame_ui, text="Mostra colonna 'Costo' nella tabella Tariffe", font=ctk.CTkFont(family="Montserrat"))
        if self.config.get("mostra_costo_fasce", False): self.chk_show_cost.select()
        self.chk_show_cost.pack(anchor="w", padx=20, pady=5)

        self.chk_show_age = ctk.CTkCheckBox(frame_ui, text="Mostra colonne 'Età' nella tabella Tariffe", font=ctk.CTkFont(family="Montserrat"))
        if self.config.get("mostra_eta_fasce", False): self.chk_show_age.select()
        self.chk_show_age.pack(anchor="w", padx=20, pady=(5, 15))

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
        messagebox.showinfo("Aggiornamento", "Lista porte aggiornata con successo. Controlla i menu a tendina.")

    def run_reader_test(self):
        port = self.cmb_reader_port.get()
        if port == "Nessun hardware" or not port:
            return messagebox.showwarning("Attenzione", "Seleziona una porta valida dal menu a tendina.")

        if self.app.serial_reader_conn and self.app.serial_reader_conn.is_open:
            self.app.stop_serial_thread.set()
            self.app.serial_reader_conn.close()

        test_win = ctk.CTkToplevel(self)
        test_win.title("Test Lettore Badge")
        test_win.geometry("400x200")
        test_win.configure(fg_color=("#F2F2F7", "#1C1C1E"))
        test_win.transient(self.winfo_toplevel())
        test_win.grab_set()

        lbl_status = ctk.CTkLabel(test_win, text="In attesa...\n\nStriscia o avvicina una tessera al lettore.", font=ctk.CTkFont(family="Montserrat", size=16, weight="bold"), text_color=("#1D1D1F", "#FFFFFF"))
        lbl_status.pack(expand=True)

        stop_test_event = threading.Event()

        def update_success(card):
            if test_win.winfo_exists():
                gym_prefix = "57340000000"
                if card.startswith(gym_prefix):
                    clean_number = card[len(gym_prefix):]
                    msg = f"✅ TEST SUPERATO E TESSERA AUTENTICATA!\n\nStringa letta: {card}\nNumero da inserire in Anagrafica: {clean_number}"
                else:
                    msg = f"✅ TEST LETTORE SUPERATO!\n\nATTENZIONE: Questa tessera ({card})\nnon sembra avere il prefisso della tua palestra."
                
                lbl_status.configure(text=msg, text_color="#34C759")
                self.after(5000, test_win.destroy)

        def update_error(err_msg):
            if test_win.winfo_exists():
                lbl_status.configure(text=f"❌ Errore di Connessione:\n\n{err_msg}", text_color="#FF3B30")

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
            self.app.start_reader_listener(self.config.get("porta_lettore", ""))

        test_win.protocol("WM_DELETE_WINDOW", on_close)

    def run_relay_test(self):
        port = self.cmb_relay_port.get()
        if port == "Nessun hardware" or not port:
            return messagebox.showwarning("Attenzione", "Seleziona una porta valida dal menu a tendina.")

        try:
            with serial.Serial(port, 9600, timeout=1) as ser:
                cmd_on = b'\xA0\x01\x01\xA2'
                cmd_off = b'\xA0\x01\x00\xA1'
                
                ser.write(cmd_on)
                ser.dtr = True; ser.rts = True
                
                time.sleep(0.5) 
                
                ser.write(cmd_off)
                ser.dtr = False; ser.rts = False

            messagebox.showinfo("Test Tornello", "Impulso inviato con successo sulla porta!\n\nHai sentito il relè fare 'Click' e il tornello sbloccarsi?")
        except Exception as e:
            messagebox.showerror("Errore di Connessione", f"Impossibile comunicare con il Relè sulla porta {port}:\n\n{str(e)}")

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

    def load_config(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r") as f: return json.load(f)
            except: return {}
        return {}

    def save_settings(self):
        config = {
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
            "mostra_eta_fasce": self.chk_show_age.get() == 1
        }
        try:
            with open(self.config_file, "w") as f:
                json.dump(config, f, indent=4)
            messagebox.showinfo("Successo", "Impostazioni salvate correttamente!\nRiavvia il programma per applicare definitivamente le modifiche hardware.")
            self.app.update_logo()
        except Exception as e:
            messagebox.showerror("Errore", f"Impossibile salvare le impostazioni:\n{e}")