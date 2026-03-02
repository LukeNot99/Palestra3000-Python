import customtkinter as ctk
from tkinter import messagebox
from core.database import SessionLocal, Member, Tier
from datetime import datetime, timedelta
import calendar
from core.utils import parse_date, is_valid_date, is_valid_phone, calculate_partial_cf, generate_invoice_html

class MemberFormWindow(ctk.CTkToplevel):
    def __init__(self, parent, refresh_callback, member_id=None):
        super().__init__(parent)
        self.title("Scheda Socio")
        self.geometry("950x700") 
        self.configure(fg_color=("#F2F2F7", "#1C1C1E"))
        self.refresh_callback = refresh_callback
        self.member_id = member_id
        
        self.cf_modified_manually = False 
        
        self.transient(parent.winfo_toplevel())
        self.grab_set()

        lbl_title = ctk.CTkLabel(self, text="Scheda Anagrafica e Iscrizione", font=ctk.CTkFont(family="Montserrat", size=22, weight="bold"), text_color="#007AFF")
        lbl_title.pack(pady=(15, 5))

        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_frame.pack(fill="both", expand=True, padx=20, pady=10)

        grid_container = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        grid_container.pack(fill="both", expand=True)
        grid_container.grid_columnconfigure(0, weight=1, uniform="colonna")
        grid_container.grid_columnconfigure(1, weight=1, uniform="colonna")
        grid_container.grid_rowconfigure(0, weight=1)

        db = SessionLocal()
        unique_cities = sorted(list(set([m.city for m in db.query(Member.city).filter(Member.city != None).all()])))
        unique_birth_places = sorted(list(set([m.birth_place for m in db.query(Member.birth_place).filter(Member.birth_place != None).all()])))
        
        tiers_db = db.query(Tier).all()
        self.tiers_data = [{"id": t.id, "name": t.name, "max_entries": t.max_entries, "duration_months": t.duration_months} for t in tiers_db]
        tier_names = ["Nessuna fascia"] + [t["name"] for t in self.tiers_data]
        db.close()

        frame_left = ctk.CTkFrame(grid_container, fg_color=("#FFFFFF", "#2C2C2E"), corner_radius=12, border_width=1, border_color=("#E5E5EA", "#3A3A3C"))
        frame_left.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        ctk.CTkLabel(frame_left, text="👤 Dati Personali", font=ctk.CTkFont(family="Montserrat", size=16, weight="bold"), text_color=("#1D1D1F", "#FFFFFF")).pack(pady=(15, 15))

        ctk.CTkLabel(frame_left, text="Numero Scheda:", font=ctk.CTkFont(family="Montserrat"), text_color=("#1D1D1F", "#FFFFFF")).pack(anchor="w", padx=20)
        self.ent_badge = ctk.CTkEntry(frame_left, placeholder_text="Es. 000123")
        self.ent_badge.pack(pady=(0, 10), padx=20, fill="x")

        ctk.CTkLabel(frame_left, text="Nome:", font=ctk.CTkFont(family="Montserrat"), text_color=("#1D1D1F", "#FFFFFF")).pack(anchor="w", padx=20)
        self.ent_first_name = ctk.CTkEntry(frame_left)
        self.ent_first_name.pack(pady=(0, 10), padx=20, fill="x")
        self.ent_first_name.bind("<KeyRelease>", self.update_cf_live)

        ctk.CTkLabel(frame_left, text="Cognome:", font=ctk.CTkFont(family="Montserrat"), text_color=("#1D1D1F", "#FFFFFF")).pack(anchor="w", padx=20)
        self.ent_last_name = ctk.CTkEntry(frame_left)
        self.ent_last_name.pack(pady=(0, 10), padx=20, fill="x")
        self.ent_last_name.bind("<KeyRelease>", self.update_cf_live)

        lbl_birth_container = ctk.CTkFrame(frame_left, fg_color="transparent")
        lbl_birth_container.pack(anchor="w", padx=20, fill="x")
        ctk.CTkLabel(lbl_birth_container, text="Data di Nascita (GG/MM/AAAA):", font=ctk.CTkFont(family="Montserrat"), text_color=("#1D1D1F", "#FFFFFF")).pack(side="left")
        self.lbl_age = ctk.CTkLabel(lbl_birth_container, text="", font=ctk.CTkFont(family="Montserrat", weight="bold"), text_color="#007AFF")
        self.lbl_age.pack(side="right")

        self.ent_birth_date = ctk.CTkEntry(frame_left, placeholder_text="Es. 15/08/1985")
        self.ent_birth_date.pack(pady=(0, 10), padx=20, fill="x")
        self.ent_birth_date.bind("<KeyRelease>", self.update_age_and_cf)
        self.ent_birth_date.bind("<FocusOut>", self.update_age_and_cf)

        ctk.CTkLabel(frame_left, text="Codice Fiscale:", font=ctk.CTkFont(family="Montserrat", weight="bold"), text_color=("#007AFF", "#0A84FF")).pack(anchor="w", padx=20)
        self.ent_cf = ctk.CTkEntry(frame_left, placeholder_text="Completare le X finali", text_color=("#007AFF", "#0A84FF"), font=ctk.CTkFont(family="Consolas", weight="bold"))
        self.ent_cf.pack(pady=(0, 10), padx=20, fill="x")
        self.ent_cf.bind("<KeyRelease>", self.flag_cf_modified)

        ctk.CTkLabel(frame_left, text="Sesso:", font=ctk.CTkFont(family="Montserrat"), text_color=("#1D1D1F", "#FFFFFF")).pack(anchor="w", padx=20)
        self.cmb_gender = ctk.CTkOptionMenu(frame_left, values=["M", "F"], command=self.update_cf_live)
        self.cmb_gender.pack(pady=(0, 10), padx=20, fill="x")

        ctk.CTkLabel(frame_left, text="Luogo di Nascita:", font=ctk.CTkFont(family="Montserrat"), text_color=("#1D1D1F", "#FFFFFF")).pack(anchor="w", padx=20)
        self.cmb_birth_place = ctk.CTkComboBox(frame_left, values=unique_birth_places)
        self.cmb_birth_place.pack(pady=(0, 10), padx=20, fill="x")

        ctk.CTkLabel(frame_left, text="Comune di Residenza:", font=ctk.CTkFont(family="Montserrat"), text_color=("#1D1D1F", "#FFFFFF")).pack(anchor="w", padx=20)
        self.cmb_city = ctk.CTkComboBox(frame_left, values=unique_cities)
        self.cmb_city.pack(pady=(0, 10), padx=20, fill="x")

        ctk.CTkLabel(frame_left, text="Indirizzo:", font=ctk.CTkFont(family="Montserrat"), text_color=("#1D1D1F", "#FFFFFF")).pack(anchor="w", padx=20)
        self.ent_address = ctk.CTkEntry(frame_left)
        self.ent_address.pack(pady=(0, 10), padx=20, fill="x")

        ctk.CTkLabel(frame_left, text="Telefono:", font=ctk.CTkFont(family="Montserrat"), text_color=("#1D1D1F", "#FFFFFF")).pack(anchor="w", padx=20)
        self.ent_phone = ctk.CTkEntry(frame_left)
        self.ent_phone.pack(pady=(0, 10), padx=20, fill="x")

        ctk.CTkLabel(frame_left, text="Altro Recapito (Es. Tel fisso o Parenti):", font=ctk.CTkFont(family="Montserrat"), text_color=("#1D1D1F", "#FFFFFF")).pack(anchor="w", padx=20)
        self.ent_other_contact = ctk.CTkEntry(frame_left, placeholder_text="Opzionale")
        self.ent_other_contact.pack(pady=(0, 20), padx=20, fill="x")


        frame_right = ctk.CTkFrame(grid_container, fg_color=("#FFFFFF", "#2C2C2E"), corner_radius=12, border_width=1, border_color=("#E5E5EA", "#3A3A3C"))
        frame_right.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

        ctk.CTkLabel(frame_right, text="🏷️ Dati Iscrizione e Abbonamento", font=ctk.CTkFont(family="Montserrat", size=16, weight="bold"), text_color=("#1D1D1F", "#FFFFFF")).pack(pady=(15, 15))

        ctk.CTkLabel(frame_right, text="Scadenza Iscrizione Annuale (Quota):", font=ctk.CTkFont(family="Montserrat", weight="bold"), text_color=("#1D1D1F", "#FFFFFF")).pack(anchor="w", padx=20, pady=(0,5))
        self.ent_enrollment_exp = ctk.CTkEntry(frame_right, placeholder_text="Es. 30/12/2026", text_color=("#FF9500", "#FF9500"), font=ctk.CTkFont(family="Montserrat", weight="bold"))
        self.ent_enrollment_exp.pack(pady=(0, 25), padx=20, fill="x")

        ctk.CTkLabel(frame_right, text="Seleziona Fascia Abbonamento:", font=ctk.CTkFont(family="Montserrat", weight="bold"), text_color=("#1D1D1F", "#FFFFFF")).pack(anchor="w", padx=20, pady=(0, 5))
        self.cmb_tier = ctk.CTkOptionMenu(frame_right, values=tier_names, command=self.update_selected_tier)
        self.cmb_tier.pack(pady=(0, 15), padx=20, fill="x")

        ctk.CTkLabel(frame_right, text="Ingressi Rimanenti (Carnet):", font=ctk.CTkFont(family="Montserrat", weight="bold"), text_color=("#1D1D1F", "#FFFFFF")).pack(anchor="w", padx=20, pady=(0,5))
        self.ent_entries = ctk.CTkEntry(frame_right, placeholder_text="Es. 10 o Illimitati", font=ctk.CTkFont(family="Montserrat", weight="bold"), text_color=("#007AFF", "#0A84FF"))
        self.ent_entries.pack(pady=(0, 15), padx=20, fill="x")

        ctk.CTkLabel(frame_right, text="Data PARTENZA Mensilità:", font=ctk.CTkFont(family="Montserrat"), text_color=("#1D1D1F", "#FFFFFF")).pack(anchor="w", padx=20, pady=(0,5))
        self.ent_membership_start = ctk.CTkEntry(frame_right, placeholder_text="Data inizio", text_color=("#1D1D1F", "#FFFFFF"), font=ctk.CTkFont(family="Montserrat"))
        self.ent_membership_start.pack(pady=(0, 15), padx=20, fill="x")
        self.ent_membership_start.bind("<Return>", lambda e: self.calculate_auto_expiration())
        self.ent_membership_start.bind("<FocusOut>", lambda e: self.calculate_auto_expiration())

        ctk.CTkLabel(frame_right, text="Data SCADENZA Mensilità (Calcolo Auto):", font=ctk.CTkFont(family="Montserrat"), text_color=("#1D1D1F", "#FFFFFF")).pack(anchor="w", padx=20, pady=(0,5))
        self.ent_membership_exp = ctk.CTkEntry(frame_right, placeholder_text="Scadenza fine abbonamento", text_color=("#1D1D1F", "#FFFFFF"), font=ctk.CTkFont(family="Montserrat", weight="bold"))
        self.ent_membership_exp.pack(pady=(0, 30), padx=20, fill="x")

        ctk.CTkLabel(frame_right, text="Dati Medici (Promemoria non bloccante):", font=ctk.CTkFont(family="Montserrat", weight="bold"), text_color=("#86868B", "#98989D")).pack(anchor="w", padx=20, pady=(0,10))
        self.chk_certificate = ctk.CTkCheckBox(frame_right, text="Certificato Medico Consegnato", font=ctk.CTkFont(family="Montserrat"), text_color=("#1D1D1F", "#FFFFFF"))
        self.chk_certificate.pack(pady=(0, 15), padx=20, anchor="w")

        ctk.CTkLabel(frame_right, text="Scadenza Certificato (GG/MM/AAAA):", font=ctk.CTkFont(family="Montserrat"), text_color=("#1D1D1F", "#FFFFFF")).pack(anchor="w", padx=20)
        self.ent_cert_exp = ctk.CTkEntry(frame_right)
        self.ent_cert_exp.pack(pady=(0, 20), padx=20, fill="x")

        if self.member_id:
            self.load_member_data()
        else:
            self.cmb_birth_place.set("")
            self.cmb_city.set("")
            self.ent_entries.configure(state="disabled") 
            oggi = datetime.now()
            self.ent_membership_start.insert(0, oggi.strftime("%d/%m/%Y"))
            scadenza_iscr = oggi + timedelta(days=365)
            self.ent_enrollment_exp.insert(0, scadenza_iscr.strftime("%d/%m/%Y"))

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=(15, 20), fill="x", padx=40)
        
        ctk.CTkButton(btn_frame, text="OK / Salva", width=140, height=38, font=ctk.CTkFont(family="Montserrat", size=14, weight="bold"), fg_color="#34C759", hover_color="#2eb350", command=self.save_member).pack(side="left")
        
        if self.member_id:
            ctk.CTkButton(btn_frame, text="📄 Genera Ricevuta", width=160, height=38, font=ctk.CTkFont(family="Montserrat", size=14, weight="bold"), fg_color="#8e44ad", hover_color="#9b59b6", command=self.generate_receipt).pack(side="left", padx=15)
        
        ctk.CTkButton(btn_frame, text="Annulla", width=140, height=38, font=ctk.CTkFont(family="Montserrat", size=14, weight="bold"), fg_color=("#E5E5EA", "#3A3A3C"), text_color=("#1D1D1F", "#FFFFFF"), hover_color=("#D1D1D6", "#5C5C5E"), command=self.close_window).pack(side="right")

    def flag_cf_modified(self, event=None):
        self.cf_modified_manually = True

    def update_age_and_cf(self, event=None):
        self.calculate_age_live()
        self.update_cf_live()

    def update_cf_live(self, event=None):
        if self.cf_modified_manually: return 
        nome = self.ent_first_name.get().strip()
        cognome = self.ent_last_name.get().strip()
        d_nascita = self.ent_birth_date.get().strip()
        sesso = self.cmb_gender.get()
        
        cf_parziale = calculate_partial_cf(nome, cognome, d_nascita, sesso)
        if cf_parziale:
            self.ent_cf.delete(0, 'end')
            self.ent_cf.insert(0, cf_parziale)

    def generate_receipt(self):
        self.save_member(exit_after=False)
        db = SessionLocal()
        socio = db.query(Member).get(self.member_id)
        if socio:
            generate_invoice_html(socio)
        db.close()

    def close_window(self):
        self.grab_release()
        self.destroy()

    def calculate_age_live(self, event=None):
        data_str = self.ent_birth_date.get().strip()
        nascita = parse_date(data_str)
        if not nascita:
            self.lbl_age.configure(text="")
            return
            
        oggi = datetime.now()
        eta = oggi.year - nascita.year - ((oggi.month, oggi.day) < (nascita.month, nascita.day))
        self.lbl_age.configure(text=f"Età: {eta} anni")

    def update_selected_tier(self, selected_tier):
        tier_dict = next((t for t in self.tiers_data if t["name"] == selected_tier), None)
        self.ent_entries.configure(state="normal")
        self.ent_entries.delete(0, 'end')
        
        if tier_dict:
            if tier_dict["max_entries"] > 0: self.ent_entries.insert(0, str(tier_dict["max_entries"]))
            else:
                self.ent_entries.insert(0, "Illimitati")
                self.ent_entries.configure(state="disabled") 
        else:
            self.ent_entries.configure(state="disabled")
            
        self.calculate_auto_expiration()

    def calculate_auto_expiration(self):
        selected_tier = self.cmb_tier.get()
        if selected_tier == "Nessuna fascia": return
        
        d_partenza = parse_date(self.ent_membership_start.get())
        if not d_partenza: return
        
        tier_dict = next((t for t in self.tiers_data if t["name"] == selected_tier), None)
        mesi_durata = tier_dict["duration_months"] if tier_dict else 1
            
        mese_target = d_partenza.month - 1 + mesi_durata
        anno_succ = d_partenza.year + (mese_target // 12)
        mese_succ = (mese_target % 12) + 1
        
        giorni_nel_mese_dest = calendar.monthrange(anno_succ, mese_succ)[1]
        giorno = min(d_partenza.day, giorni_nel_mese_dest) 
        
        d_scadenza = datetime(anno_succ, mese_succ, giorno)
        
        self.ent_membership_exp.delete(0, 'end')
        self.ent_membership_exp.insert(0, d_scadenza.strftime("%d/%m/%Y"))

    def load_member_data(self):
        db = SessionLocal()
        socio = db.query(Member).filter(Member.id == self.member_id).first()
        if socio:
            if socio.badge_number: self.ent_badge.insert(0, socio.badge_number)
            self.ent_first_name.insert(0, socio.first_name)
            self.ent_last_name.insert(0, socio.last_name)
            
            if socio.codice_fiscale:
                self.ent_cf.insert(0, socio.codice_fiscale)
                self.cf_modified_manually = True 
                
            if socio.birth_date: 
                self.ent_birth_date.insert(0, socio.birth_date)
                self.calculate_age_live()
            if socio.birth_place: self.cmb_birth_place.set(socio.birth_place)
            if socio.city: self.cmb_city.set(socio.city)
            if socio.address: self.ent_address.insert(0, socio.address)
            if socio.phone: self.ent_phone.insert(0, socio.phone)
            if socio.other_contact: self.ent_other_contact.insert(0, socio.other_contact)
            self.cmb_gender.set(socio.gender)
            
            if socio.enrollment_expiration: self.ent_enrollment_exp.insert(0, socio.enrollment_expiration)
            if socio.membership_start: self.ent_membership_start.insert(0, socio.membership_start)
            if socio.membership_expiration: self.ent_membership_exp.insert(0, socio.membership_expiration)
            
            if socio.tier: 
                self.cmb_tier.set(socio.tier.name)
                self.ent_entries.configure(state="normal")
                self.ent_entries.delete(0, 'end')
                if socio.tier.max_entries > 0:
                    rimanenti = socio.tier.max_entries - (socio.entries_used or 0)
                    self.ent_entries.insert(0, str(rimanenti))
                else:
                    self.ent_entries.insert(0, "Illimitati")
                    self.ent_entries.configure(state="disabled")
            
            if socio.has_medical_certificate: self.chk_certificate.select()
            if socio.certificate_expiration: self.ent_cert_exp.insert(0, socio.certificate_expiration)
        db.close()

    def save_member(self, exit_after=True):
        nome = self.ent_first_name.get().strip()
        cognome = self.ent_last_name.get().strip()
        scheda = self.ent_badge.get().strip()
        cf = self.ent_cf.get().strip().upper()
        telefono = self.ent_phone.get().strip()
        
        if not nome or not cognome: return messagebox.showwarning("Errore", "Nome e Cognome sono obbligatori!")
        
        # --- VERIFICA REGEX TELEFONO ---
        if not is_valid_phone(telefono):
            return messagebox.showwarning("Errore Formato", "Il numero di telefono inserito non è valido.\nInserisci un formato corretto (es. +39 333 1234567 o 0836 123456).")
        
        db = SessionLocal()
        if scheda:
            esistente = db.query(Member).filter(Member.badge_number == scheda, Member.id != self.member_id).first()
            if esistente: 
                db.close()
                return messagebox.showerror("Errore", f"Il Numero Scheda {scheda} è già assegnato a {esistente.first_name}!")
        
        d_nascita = self.ent_birth_date.get().strip()
        d_iscr = self.ent_enrollment_exp.get().strip()
        d_partenza = self.ent_membership_start.get().strip()
        d_scadenza = self.ent_membership_exp.get().strip()
        d_cert = self.ent_cert_exp.get().strip()
        
        if not is_valid_date(d_nascita): 
            db.close()
            return messagebox.showwarning("Errore Data", "Data di nascita non valida.\nUsa il formato GG/MM/AAAA (es. 15/08/1985). Attenzione ai mesi di 30/31 giorni o bisestili.")
        if not is_valid_date(d_iscr): 
            db.close()
            return messagebox.showwarning("Errore Data", "Scadenza iscrizione non valida.\nUsa il formato GG/MM/AAAA")
        if not is_valid_date(d_partenza): 
            db.close()
            return messagebox.showwarning("Errore Data", "Data partenza mensilità non valida.\nUsa il formato GG/MM/AAAA")
        if not is_valid_date(d_scadenza): 
            db.close()
            return messagebox.showwarning("Errore Data", "Data scadenza mensilità non valida.\nUsa il formato GG/MM/AAAA")
        if not is_valid_date(d_cert): 
            db.close()
            return messagebox.showwarning("Errore Data", "Scadenza certificato non valida.\nUsa il formato GG/MM/AAAA")

        fascia_selezionata = self.cmb_tier.get()
        tier_dict = next((t for t in self.tiers_data if t["name"] == fascia_selezionata), None)
        
        if self.member_id: socio = db.query(Member).filter(Member.id == self.member_id).first()
        else:
            socio = Member()
            db.add(socio)
            
        socio.badge_number = scheda if scheda else None
        socio.first_name = nome
        socio.last_name = cognome
        socio.codice_fiscale = cf 
        socio.birth_date = d_nascita
        socio.birth_place = self.cmb_birth_place.get().strip()
        socio.city = self.cmb_city.get().strip()
        socio.address = self.ent_address.get().strip()
        socio.phone = telefono
        socio.other_contact = self.ent_other_contact.get().strip()
        socio.gender = self.cmb_gender.get()
        
        socio.enrollment_expiration = d_iscr
        socio.membership_start = d_partenza
        socio.membership_expiration = d_scadenza
        socio.has_medical_certificate = self.chk_certificate.get() == 1
        socio.certificate_expiration = d_cert
        socio.tier_id = tier_dict["id"] if tier_dict else None
        
        if tier_dict and tier_dict["max_entries"] > 0:
            val_ingressi = self.ent_entries.get().strip()
            try:
                rimanenti = int(val_ingressi)
                socio.entries_used = max(0, tier_dict["max_entries"] - rimanenti)
            except ValueError: 
                db.close()
                return messagebox.showwarning("Errore", "Il numero di ingressi rimanenti deve essere un numero valido.")
        else:
            socio.entries_used = 0
        
        db.commit()
        
        if not self.member_id:
            self.member_id = socio.id
            
        db.close()
        self.refresh_callback()
        
        if exit_after:
            self.close_window()


class MembersView(ctk.CTkFrame):
    def __init__(self, parent, controller=None, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        
        self.font_row = ctk.CTkFont(family="Montserrat", size=13)
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.row_frames = {} 
        self.selected_member_id = None
        
        self.current_page = 1
        self.items_per_page = 50

        search_frame = ctk.CTkFrame(self, fg_color=("#FFFFFF", "#2C2C2E"), corner_radius=12, border_width=1, border_color=("#E5E5EA", "#3A3A3C"))
        search_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=20)

        db = SessionLocal()
        tiers = db.query(Tier).all()
        tier_names = ["Tutte"] + [t.name for t in tiers]
        db.close()

        row1 = ctk.CTkFrame(search_frame, fg_color="transparent")
        row1.pack(pady=(15, 5), fill="x", padx=15)

        ctk.CTkLabel(row1, text="Nome:", font=ctk.CTkFont(family="Montserrat", weight="bold"), text_color=("#86868B", "#98989D")).pack(side="left", padx=(0, 5))
        self.src_name = ctk.CTkEntry(row1, width=160, font=ctk.CTkFont(family="Montserrat"))
        self.src_name.pack(side="left", padx=(0, 20))

        ctk.CTkLabel(row1, text="Cognome:", font=ctk.CTkFont(family="Montserrat", weight="bold"), text_color=("#86868B", "#98989D")).pack(side="left", padx=(0, 5))
        self.src_surname = ctk.CTkEntry(row1, width=160, font=ctk.CTkFont(family="Montserrat"))
        self.src_surname.pack(side="left", padx=(0, 20))

        ctk.CTkLabel(row1, text="Telefono:", font=ctk.CTkFont(family="Montserrat", weight="bold"), text_color=("#86868B", "#98989D")).pack(side="left", padx=(0, 5))
        self.src_phone = ctk.CTkEntry(row1, width=160, font=ctk.CTkFont(family="Montserrat"))
        self.src_phone.pack(side="left", padx=(0, 20))

        row2 = ctk.CTkFrame(search_frame, fg_color="transparent")
        row2.pack(pady=(5, 15), fill="x", padx=15)

        ctk.CTkLabel(row2, text="Num. Scheda:", font=ctk.CTkFont(family="Montserrat", weight="bold"), text_color=("#86868B", "#98989D")).pack(side="left", padx=(0, 5))
        self.src_badge = ctk.CTkEntry(row2, width=120, font=ctk.CTkFont(family="Montserrat"))
        self.src_badge.pack(side="left", padx=(0, 20))

        ctk.CTkLabel(row2, text="Fascia Abbonamento:", font=ctk.CTkFont(family="Montserrat", weight="bold"), text_color=("#86868B", "#98989D")).pack(side="left", padx=(0, 5))
        self.src_tier = ctk.CTkComboBox(row2, values=tier_names, width=160, font=ctk.CTkFont(family="Montserrat"))
        self.src_tier.set("Tutte")
        self.src_tier.pack(side="left", padx=(0, 20))

        btn_annulla = ctk.CTkButton(row2, text="Resetta", width=100, height=32, font=ctk.CTkFont(family="Montserrat", weight="bold"), fg_color=("#E5E5EA", "#3A3A3C"), text_color=("#1D1D1F", "#FFFFFF"), hover_color=("#D1D1D6", "#5C5C5E"), command=self.reset_search)
        btn_annulla.pack(side="right", padx=(10, 0))

        btn_cerca = ctk.CTkButton(row2, text="Cerca", width=100, height=32, font=ctk.CTkFont(family="Montserrat", weight="bold"), fg_color="#007AFF", hover_color="#005ecb", command=lambda: self.load_data(reset_page=True))
        btn_cerca.pack(side="right")

        self.table_container = ctk.CTkFrame(self, fg_color="transparent")
        self.table_container.grid(row=2, column=0, sticky="nsew", padx=20, pady=(0, 10))
        
        self.cols = [
            ("scheda", "Scheda", 1, "center"), 
            ("nome", "Nome", 2, "w"), 
            ("cognome", "Cognome", 2, "w"), 
            ("fascia", "Fascia", 1, "center"), 
            ("scadenza", "Scad. Abb.", 1, "center"), 
            ("scad_iscr", "Scad. Iscr.", 1, "center")
        ]

        header_frame = ctk.CTkFrame(self.table_container, fg_color=("#E5E5EA", "#3A3A3C"), height=35, corner_radius=6)
        header_frame.pack(side="top", fill="x", pady=(0, 5))
        
        for i, col in enumerate(self.cols):
            header_frame.grid_columnconfigure(i, weight=col[2], uniform="colonna")
            ctk.CTkLabel(header_frame, text=col[1], font=ctk.CTkFont(family="Montserrat", size=12, weight="bold"), text_color=("#86868B", "#98989D"), anchor=col[3]).grid(row=0, column=i, padx=10, pady=5, sticky="ew")

        self.pagination_frame = ctk.CTkFrame(self.table_container, fg_color="transparent", height=30)
        self.pagination_frame.pack(side="bottom", fill="x", pady=(5, 0))
        
        self.btn_prev = ctk.CTkButton(self.pagination_frame, text="◀ Precedente", width=120, height=28, font=ctk.CTkFont(family="Montserrat", weight="bold"), fg_color=("#E5E5EA", "#3A3A3C"), text_color=("#1D1D1F", "#FFFFFF"), hover_color=("#D1D1D6", "#5C5C5E"), command=self.prev_page)
        self.btn_prev.pack(side="left")
        
        self.lbl_page = ctk.CTkLabel(self.pagination_frame, text="Pagina 1 di 1", font=ctk.CTkFont(family="Montserrat", size=13, weight="bold"), text_color=("#86868B", "#98989D"))
        self.lbl_page.pack(side="left", expand=True)
        
        self.btn_next = ctk.CTkButton(self.pagination_frame, text="Successiva ▶", width=120, height=28, font=ctk.CTkFont(family="Montserrat", weight="bold"), fg_color=("#E5E5EA", "#3A3A3C"), text_color=("#1D1D1F", "#FFFFFF"), hover_color=("#D1D1D6", "#5C5C5E"), command=self.next_page)
        self.btn_next.pack(side="right")

        self.scroll_table = ctk.CTkScrollableFrame(self.table_container, fg_color="transparent")
        self.scroll_table.pack(side="top", fill="both", expand=True)

        bottom_frame = ctk.CTkFrame(self, fg_color="transparent")
        bottom_frame.grid(row=3, column=0, sticky="ew", padx=20, pady=15)

        ctk.CTkButton(bottom_frame, text="+ Nuovo Socio", width=150, height=38, font=ctk.CTkFont(family="Montserrat", size=14, weight="bold"), fg_color="#34C759", hover_color="#2eb350", command=self.open_new_form).pack(side="left", padx=(0, 10))
        ctk.CTkButton(bottom_frame, text="✏️ Modifica", width=150, height=38, font=ctk.CTkFont(family="Montserrat", size=14, weight="bold"), fg_color="#007AFF", hover_color="#005ecb", command=self.open_edit_form).pack(side="left", padx=10)
        ctk.CTkButton(bottom_frame, text="🗑️ Elimina", width=150, height=38, font=ctk.CTkFont(family="Montserrat", size=14, weight="bold"), fg_color="#FF3B30", hover_color="#e03026", command=self.delete_member).pack(side="right")

        self.load_data(reset_page=True)

    def prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self.load_data(reset_page=False)

    def next_page(self):
        self.current_page += 1
        self.load_data(reset_page=False)

    def reset_search(self):
        self.src_badge.delete(0, 'end')
        self.src_tier.set("Tutte")
        self.src_name.delete(0, 'end')
        self.src_surname.delete(0, 'end')
        self.src_phone.delete(0, 'end') 
        self.load_data(reset_page=True)

    def select_row(self, member_id):
        self.selected_member_id = member_id
        for s_id, frame in self.row_frames.items():
            if frame.winfo_exists():
                if s_id == member_id:
                    frame.configure(fg_color=("#E5F1FF", "#0A2A4A"), border_color="#007AFF")
                else:
                    frame.configure(fg_color=("#FFFFFF", "#2C2C2E"), border_color=("#E5E5EA", "#3A3A3C"))

    def create_table_row(self, member_data):
        row_frame = ctk.CTkFrame(self.scroll_table, fg_color=("#FFFFFF", "#2C2C2E"), height=45, corner_radius=8, border_width=1, border_color=("#E5E5EA", "#3A3A3C"), cursor="hand2")
        row_frame.pack(fill="x", pady=2)
        row_frame.pack_propagate(False)

        valori = [
            member_data["scheda"],
            member_data["nome"],
            member_data["cognome"],
            member_data["fascia"],
            member_data["scad_abb"],
            member_data["scad_iscr"]
        ]

        elementi_riga = [row_frame]
        
        for i, val in enumerate(valori):
            row_frame.grid_columnconfigure(i, weight=self.cols[i][2], uniform="colonna")
            lbl = ctk.CTkLabel(row_frame, text=val, font=self.font_row, text_color=("#1D1D1F", "#FFFFFF"), anchor=self.cols[i][3])
            lbl.grid(row=0, column=i, padx=10, pady=10, sticky="ew")
            elementi_riga.append(lbl)

        s_id = member_data["id"]
        for w in elementi_riga:
            w.bind("<Button-1>", lambda e, s=s_id: self.select_row(s))
            w.bind("<Double-Button-1>", lambda e, s=s_id: self.open_edit_form(force_id=s))
            w.bind("<Enter>", lambda e, f=row_frame, s=s_id: f.configure(fg_color=("#F8F8F9", "#3A3A3C")) if f.winfo_exists() and self.selected_member_id != s else None)
            w.bind("<Leave>", lambda e, f=row_frame, s=s_id: f.configure(fg_color=("#FFFFFF", "#2C2C2E")) if f.winfo_exists() and self.selected_member_id != s else None)

        self.row_frames[s_id] = row_frame

    def load_data(self, reset_page=False):
        if reset_page:
            self.current_page = 1
            
        for widget in self.scroll_table.winfo_children():
            widget.destroy()
        
        self.row_frames.clear()
        self.selected_member_id = None

        db = SessionLocal()
        query = db.query(Member)

        badge = self.src_badge.get().strip()
        if badge: query = query.filter(Member.badge_number.ilike(f"%{badge}%"))
        
        tier = self.src_tier.get()
        if tier != "Tutte": query = query.join(Tier).filter(Tier.name == tier)
        
        name = self.src_name.get().strip()
        if name: query = query.filter(Member.first_name.ilike(f"%{name}%"))
        
        surname = self.src_surname.get().strip()
        if surname: query = query.filter(Member.last_name.ilike(f"%{surname}%"))
        
        phone = self.src_phone.get().strip()
        if phone: query = query.filter(Member.phone.ilike(f"%{phone}%"))

        total_members = query.count()
        total_pages = max(1, (total_members + self.items_per_page - 1) // self.items_per_page)
        
        if self.current_page > total_pages:
            self.current_page = total_pages

        members_db = query.order_by(Member.first_name, Member.last_name).offset((self.current_page - 1) * self.items_per_page).limit(self.items_per_page).all()
        
        members_data = []
        for s in members_db:
            members_data.append({
                "id": s.id,
                "scheda": s.badge_number if s.badge_number else "-",
                "nome": s.first_name,
                "cognome": s.last_name,
                "fascia": s.tier.name if s.tier else "Nessuna",
                "scad_abb": s.membership_expiration if s.membership_expiration else "N/D",
                "scad_iscr": s.enrollment_expiration if s.enrollment_expiration else "N/D"
            })
        db.close()

        for m_data in members_data:
            self.create_table_row(m_data)
            
        self.lbl_page.configure(text=f"Pagina {self.current_page} di {total_pages} (Totale: {total_members} soci)")
        self.btn_prev.configure(state="normal" if self.current_page > 1 else "disabled")
        self.btn_next.configure(state="normal" if self.current_page < total_pages else "disabled")

    def open_new_form(self):
        MemberFormWindow(self, refresh_callback=lambda: self.load_data(reset_page=False))

    def open_edit_form(self, force_id=None):
        target_id = force_id or self.selected_member_id
        if not target_id: 
            return messagebox.showwarning("Attenzione", "Seleziona prima un socio dalla lista.")
        MemberFormWindow(self, refresh_callback=lambda: self.load_data(reset_page=False), member_id=target_id)

    def delete_member(self):
        if not self.selected_member_id: return messagebox.showwarning("Attenzione", "Seleziona prima un socio dalla lista.")
        
        db = SessionLocal()
        socio = db.query(Member).filter(Member.id == self.selected_member_id).first()

        if socio and messagebox.askyesno("Conferma", f"Vuoi eliminare definitivamente {socio.first_name} {socio.last_name}?"):
            db.delete(socio)
            db.commit()
            
        db.close()
        self.load_data(reset_page=False)