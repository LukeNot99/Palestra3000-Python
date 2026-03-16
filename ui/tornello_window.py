import customtkinter as ctk

class TurnstileView(ctk.CTkFrame):
    def __init__(self, parent, access_manager, access_history, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.access_manager = access_manager
        self.access_history = access_history

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        header_frame.grid_columnconfigure(1, weight=1) 

        self.card_in_facility = ctk.CTkFrame(header_frame, fg_color="#007AFF", corner_radius=12)
        self.card_in_facility.grid(row=0, column=0, sticky="w", padx=(0, 20))
        
        ctk.CTkLabel(self.card_in_facility, text="INGRESSI UNICI DI OGGI", font=ctk.CTkFont(family="Montserrat", size=11, weight="bold"), text_color="#E5F1FF").pack(pady=(10, 0), padx=20)
        self.lbl_counter = ctk.CTkLabel(self.card_in_facility, text="0", font=ctk.CTkFont(family="Montserrat", size=38, weight="bold"), text_color="white")
        self.lbl_counter.pack(pady=(0, 10), padx=20)

        manual_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        manual_frame.grid(row=0, column=1, sticky="w")
        
        ctk.CTkLabel(manual_frame, text="Simula Lettura Badge:", font=ctk.CTkFont(family="Montserrat", size=13, weight="bold"), text_color=("#86868B", "#98989D")).pack(anchor="w", pady=(0, 5))
        
        input_box = ctk.CTkFrame(manual_frame, fg_color="transparent")
        input_box.pack(fill="x")
        
        self.ent_manual = ctk.CTkEntry(input_box, placeholder_text="Num. Scheda...", font=ctk.CTkFont(family="Montserrat", size=14), width=180)
        self.ent_manual.pack(side="left", padx=(0, 10))
        self.ent_manual.bind("<Return>", self.simulate_badge) 
        
        ctk.CTkButton(input_box, text="Simula", width=80, height=30, font=ctk.CTkFont(family="Montserrat", weight="bold"), fg_color=("#E5E5EA", "#3A3A3C"), text_color=("#1D1D1F", "#FFFFFF"), hover_color=("#D1D1D6", "#5C5C5E"), command=self.simulate_badge).pack(side="left")

        actions_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        actions_frame.grid(row=0, column=2, sticky="e")

        ctk.CTkButton(actions_frame, text="🟢 Apri (F12)", width=140, height=45, font=ctk.CTkFont(family="Montserrat", size=14, weight="bold"), fg_color="#34C759", hover_color="#2eb350", command=self.manual_open).pack(side="left", padx=10)
        ctk.CTkButton(actions_frame, text="🗑️ Pulisci Log", width=140, height=45, font=ctk.CTkFont(family="Montserrat", size=14, weight="bold"), fg_color="#FF3B30", hover_color="#e03026", command=self.clear_log).pack(side="left")

        log_frame = ctk.CTkFrame(self, fg_color=("#FFFFFF", "#2C2C2E"), corner_radius=12, border_width=1, border_color=("#E5E5EA", "#3A3A3C"))
        log_frame.grid(row=1, column=0, sticky="nsew")

        log_title = ctk.CTkLabel(log_frame, text="📄 Registro Accessi", font=ctk.CTkFont(family="Montserrat", size=16, weight="bold"), text_color=("#1D1D1F", "#FFFFFF"))
        log_title.pack(anchor="w", padx=20, pady=(15, 10))
        
        ctk.CTkFrame(log_frame, height=1, fg_color=("#E5E5EA", "#3A3A3C")).pack(fill="x", padx=10)

        self.txt_log = ctk.CTkTextbox(log_frame, fg_color="transparent", text_color=("#1D1D1F", "#FFFFFF"), font=ctk.CTkFont(family="Consolas", size=14), wrap="word")
        self.txt_log.pack(fill="both", expand=True, padx=15, pady=15)
        self.txt_log.configure(state="disabled")

        self.update_in_facility_counter()

        for row in self.access_history:
            self.add_log(row, skip_history=True)

        self.bind("<Map>", self.force_scroll_down)

    def force_scroll_down(self, event=None):
        self.txt_log.see("end")

    def simulate_badge(self, event=None):
        badge_str = self.ent_manual.get().strip()
        if badge_str:
            # Delegata la responsabilità al Business Layer! (Inversione di dipendenza)
            import json, os # Lazy load just to grab settings mock
            settings = {}
            cfg_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "config.json")
            if os.path.exists(cfg_path):
                with open(cfg_path, "r") as f: settings = json.load(f)
                
            self.access_manager.process_badge(badge_str, settings)
            self.ent_manual.delete(0, 'end')

    def manual_open(self):
        self.access_manager.process_manual_open()

    def clear_log(self):
        self.txt_log.configure(state="normal")
        self.txt_log.delete("1.0", "end")
        self.txt_log.configure(state="disabled")
        self.access_history.clear()

    def update_in_facility_counter(self):
        num_presenti = len(self.access_manager.members_in_facility)
        self.lbl_counter.configure(text=str(num_presenti))

    def add_log(self, message, skip_history=False):
        self.txt_log.configure(state="normal")
        
        tag_name = "normale"
        if "OK" in message: tag_name = "successo"
        elif "NEGATO" in message: tag_name = "errore"
        elif "MANUALE" in message: tag_name = "info"
        
        self.txt_log.tag_config("successo", foreground="#34C759")
        self.txt_log.tag_config("errore", foreground="#FF3B30")
        self.txt_log.tag_config("info", foreground="#007AFF")
        
        if tag_name == "normale":
            self.txt_log.insert("end", message + "\n")
        else:
            self.txt_log.insert("end", message + "\n", tag_name)
            
        self.txt_log.see("end")
        self.txt_log.configure(state="disabled")
        
        if not skip_history:
            if message not in self.access_history:
                self.access_history.append(message)