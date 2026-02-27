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

        # --- SEZIONE 2: HARDWARE (LETTORE E RELÈ) CON AUTO-DISCOVERY ---
        frame_hw = ctk.CTkFrame(self.scroll_frame, fg_color=("#FFFFFF", "#2C2C2E"), corner_radius=12, border_width=1, border_color=("#E5E5EA", "#3A3A3C"))
        frame_hw.pack(fill="x", pady=10, padx=10)
        
        header_hw = ctk.CTkFrame(frame_hw, fg_color="transparent")
        header_hw.pack(fill="x", padx=20, pady=(15, 10))
        ctk.CTkLabel(header_hw, text="Hardware (Lettore e Tornello)", font=ctk.CTkFont(family="Montserrat", size=16, weight="bold")).pack(side="left")
        ctk.CTkButton(header_hw, text="🔄 Aggiorna Porte", width=120, height=28, font=ctk.CTkFont(family="Montserrat", size=12, weight="bold"), fg_color=("#E5E5EA", "#3A3A3C"), text_color=("#1D1D1F", "#FFFFFF"), hover_color=("#D1D1D6", "#5C5C5E"), command=self.aggiorna_menu_porte).pack(side="right")

        # Ottiene la lista delle porte COM attualmente collegate al PC
        self.porte_disponibili = self.get_available_ports()

        row_lettore = ctk.CTkFrame(frame_hw, fg_color="transparent")
        row_lettore.pack(fill="x", padx=20, pady=(0, 5))
        ctk.CTkLabel(row_lettore, text="Porta Lettore Badge:", font=ctk.CTkFont(family="Montserrat", weight="bold"), width=220, anchor="w").pack(side="left")
        self.cmb_porta_lettore = ctk.CTkOptionMenu(row_lettore, values=self.porte_disponibili, width=250, font=ctk.CTkFont(family="Montserrat"))
        self.cmb_porta_lettore.set(self.config.get("porta_lettore", "Nessun hardware"))
        self.cmb_porta_lettore.pack(side="left", padx=(0, 10))
        ctk.CTkButton(row_lettore, text="Test Lettore", width=100, fg_color="#007AFF", hover_color="#005ecb", font=ctk.CTkFont(family="Montserrat", weight="bold"), command=self.esegui_test_lettore).pack(side="left")

        row_rele = ctk.CTkFrame(frame_hw, fg_color="transparent")
        row_rele.pack(fill="x", padx=20, pady=(5, 15))
        ctk.CTkLabel(row_rele, text="Porta Relè Tornello:", font=ctk.CTkFont(family="Montserrat", weight="bold"), width=220, anchor="w").pack(side="left")
        self.cmb_porta_rele = ctk.CTkOptionMenu(row_rele, values=self.porte_disponibili, width=250, font=ctk.CTkFont(family="Montserrat"))
        self.cmb_porta_rele.set(self.config.get("porta_rele", "Nessun hardware"))
        self.cmb_porta_rele.pack(side="left", padx=(0, 10))
        ctk.CTkButton(row_rele, text="Test Tornello", width=100, fg_color="#FF9500", hover_color="#d67e00", font=ctk.CTkFont(family="Montserrat", weight="bold"), command=self.esegui_test_rele).pack(side="left")

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

    # ================== FUNZIONI HARDWARE ==================
    def get_available_ports(self):
        ports = ["Nessun hardware"]
        for port in serial.tools.list_ports.comports():
            ports.append(port.device) # Es: "COM3"
        return ports

    def aggiorna_menu_porte(self):
        nuove_porte = self.get_available_ports()
        self.cmb_porta_lettore.configure(values=nuove_porte)
        self.cmb_porta_rele.configure(values=nuove_porte)
        messagebox.showinfo("Aggiornamento", "Lista porte aggiornata con successo. Controlla i menu a tendina.")

    def esegui_test_lettore(self):
        porta = self.cmb_porta_lettore.get()
        if porta == "Nessun hardware" or not porta:
            return messagebox.showwarning("Attenzione", "Seleziona una porta valida dal menu a tendina.")

        # Stoppiamo momentaneamente l'ascolto principale del programma per non creare conflitti sulla porta
        if self.app.serial_reader_conn and self.app.serial_reader_conn.is_open:
            self.app.stop_serial_thread.set()
            self.app.serial_reader_conn.close()

        # Creiamo un popup di attesa elegante
        test_win = ctk.CTkToplevel(self)
        test_win.title("Test Lettore Badge")
        test_win.geometry("400x200")
        test_win.configure(fg_color=("#F2F2F7", "#1C1C1E"))
        test_win.transient(self.winfo_toplevel())
        test_win.grab_set()

        lbl_status = ctk.CTkLabel(test_win, text="In attesa...\n\nStriscia o avvicina una tessera al lettore.", font=ctk.CTkFont(family="Montserrat", size=16, weight="bold"), text_color=("#1D1D1F", "#FFFFFF"))
        lbl_status.pack(expand=True)

        stop_test_event = threading.Event()

        # --- FIX: FUNZIONI SICURE PER AGGIORNARE LA GRAFICA DAL THREAD ---
        def update_success(card):
            if test_win.winfo_exists():
                lbl_status.configure(text=f"✅ TEST SUPERATO!\n\nTessera letta: {card}", text_color="#34C759")
                self.after(3000, test_win.destroy)

        def update_error(err_msg):
            if test_win.winfo_exists():
                lbl_status.configure(text=f"❌ Errore di Connessione:\n\n{err_msg}", text_color="#FF3B30")

        def ascolta_test():
            try:
                with serial.Serial(porta, 9600, timeout=1) as ser:
                    while not stop_test_event.is_set():
                        if ser.in_waiting > 0:
                            data = ser.readline().decode('utf-8').strip()
                            card = ''.join(filter(str.isdigit, data))
                            if card:
                                # Chiamiamo update_success() nel Thread principale usando after(0)
                                self.after(0, update_success, card)
                                return
            except Exception as e:
                # Se l'utente non ha chiuso la finestra intenzionalmente, mostriamo l'errore
                if not stop_test_event.is_set():
                    self.after(0, update_error, str(e))

        # Avviamo il thread di test
        threading.Thread(target=ascolta_test, daemon=True).start()

        def on_close():
            stop_test_event.set()
            test_win.destroy()
            # Riaccendiamo l'ascolto principale del programma
            self.app.avvia_ascolto_lettore(self.config.get("porta_lettore", ""))

        test_win.protocol("WM_DELETE_WINDOW", on_close)

    def esegui_test_rele(self):
        porta = self.cmb_porta_rele.get()
        if porta == "Nessun hardware" or not porta:
            return messagebox.showwarning("Attenzione", "Seleziona una porta valida dal menu a tendina.")

        try:
            # Apriamo la porta, spariamo il comando e chiudiamo
            with serial.Serial(porta, 9600, timeout=1) as ser:
                comando_on = b'\xA0\x01\x01\xA2'
                comando_off = b'\xA0\x01\x00\xA1'
                
                ser.write(comando_on)
                ser.dtr = True; ser.rts = True
                
                time.sleep(0.5) # Pausa di mezzo secondo (il tornello si sblocca)
                
                ser.write(comando_off)
                ser.dtr = False; ser.rts = False

            messagebox.showinfo("Test Tornello", "Impulso inviato con successo sulla porta!\n\nHai sentito il relè fare 'Click' e il tornello sbloccarsi?")
        except Exception as e:
            messagebox.showerror("Errore di Connessione", f"Impossibile comunicare con il Relè sulla porta {porta}:\n\n{str(e)}")

    # =======================================================

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
            "porta_lettore": self.cmb_porta_lettore.get(),
            "porta_rele": self.cmb_porta_rele.get(),
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
            messagebox.showinfo("Successo", "Impostazioni salvate correttamente!\nRiavvia il programma per applicare definitivamente le modifiche hardware.")
            self.app.aggiorna_logo()
        except Exception as e:
            messagebox.showerror("Errore", f"Impossibile salvare le impostazioni:\n{e}")