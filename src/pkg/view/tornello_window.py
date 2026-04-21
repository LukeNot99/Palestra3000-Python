import customtkinter as ctk
from src.pkg.config.app_config import ConfigManager

class TurnstileView(ctk.CTkFrame):
    def __init__(self, parent, access_manager, access_history, app=None, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.access_manager = access_manager
        self.access_history = access_history
        self.app = app

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
            # L'operatore inserisce solo le ultime cifre (es. "1234")
            # Il sistema aggiunge automaticamente il prefisso per simulare il badge completo
            gym_prefix = "57340000000"
            if not badge_str.startswith(gym_prefix):
                full_badge = gym_prefix + badge_str
            else:
                full_badge = badge_str
            
            settings = ConfigManager.load_all()
            self.access_manager.process_badge(full_badge, settings)
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
        member_id = None
        
        if "OK" in message: 
            tag_name = "successo"
            parts = message.split("(")
            if len(parts) >= 2:
                name_part = parts[0].split(">")[1].strip() if ">" in parts[0] else ""
                full_name_parts = name_part.strip().rsplit(" ", 1)
                if len(full_name_parts) >= 2:
                    last_name = full_name_parts[-1]
                    first_names = " ".join(full_name_parts[:-1])
                    member_id = self.get_member_id_by_name(first_names, last_name)
        elif "NEGATO" in message: 
            tag_name = "errore"
            parts = message.split("(")
            if len(parts) >= 2:
                name_part = parts[0].split(">")[1].strip() if ">" in parts[0] else ""
                full_name_parts = name_part.strip().rsplit(" ", 1)
                if len(full_name_parts) >= 2:
                    last_name = full_name_parts[-1]
                    first_names = " ".join(full_name_parts[:-1])
                    member_id = self.get_member_id_by_name(first_names, last_name)
        elif "MANUALE" in message: 
            tag_name = "info"
        
        self.txt_log.tag_config("successo", foreground="#34C759")
        self.txt_log.tag_config("errore", foreground="#FF3B30")
        self.txt_log.tag_config("info", foreground="#007AFF")
        
        if tag_name == "normale":
            self.txt_log.insert("end", message + "\n")
        else:
            if member_id:
                self.txt_log.insert("end", message + "\n", tag_name, f"member_{member_id}")
                self.txt_log.tag_bind(f"member_{member_id}", "<Double-Button-1>", lambda e: self.open_member_from_log(member_id))
            else:
                self.txt_log.insert("end", message + "\n", tag_name)
            
        self.txt_log.see("end")
        self.txt_log.configure(state="disabled")
        
        if not skip_history:
            if message not in self.access_history:
                self.access_history.append(message)

    def get_member_id_by_name(self, first_name, last_name):
        try:
            member_repo = self.app.di.get_member_repository()
            member = member_repo.get_member_by_name(first_name, last_name)
            return member.id if member else None
        except Exception:
            return None

    def open_member_from_log(self, member_id):
        if self.app and hasattr(self.app, 'show_view'):
            self.app.show_view("members")
            if "members" in self.app.views and hasattr(self.app.views["members"], 'open_member_form'):
                self.app.views["members"].open_member_form(member_id)
