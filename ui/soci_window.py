import customtkinter as ctk
from tkinter import messagebox
from core.database import SessionLocal, Member, Tier
from datetime import datetime, timedelta
import calendar
from core.utils import parse_date, is_valid_date  # IMPORTIAMO L'UTILITY

class SocioFormWindow(ctk.CTkToplevel):
    def __init__(self, parent, refresh_callback, socio_id=None):
        super().__init__(parent)
        self.title("Scheda Socio")
        self.geometry("900x650") 
        self.configure(fg_color=("#F2F2F7", "#1C1C1E"))
        self.refresh_callback = refresh_callback
        self.socio_id = socio_id
        
        self.transient(parent.winfo_toplevel())
        self.grab_set()

        lbl_titolo = ctk.CTkLabel(self, text="Scheda Anagrafica e Iscrizione", font=ctk.CTkFont(family="Montserrat", size=22, weight="bold"), text_color="#007AFF")
        lbl_titolo.pack(pady=(15, 5))

        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_frame.pack(fill="both", expand=True, padx=20, pady=10)

        grid_container = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        grid_container.pack(fill="both", expand=True)
        grid_container.grid_columnconfigure(0, weight=1, uniform="colonna")
        grid_container.grid_columnconfigure(1, weight=1, uniform="colonna")
        grid_container.grid_rowconfigure(0, weight=1)

        db = SessionLocal()
        comuni_unici = sorted(list(set([m.city for m in db.query(Member.city).filter(Member.city != None).all()])))
        luoghi_unici = sorted(list(set([m.birth_place for m in db.query(Member.birth_place).filter(Member.birth_place != None).all()])))
        
        tiers_db = db.query(Tier).all()
        self.tiers_data = [{"id": t.id, "name": t.name, "max_entries": t.max_entries, "duration_months": t.duration_months} for t in tiers_db]
        tier_names = ["Nessuna fascia"] + [t["name"] for t in self.tiers_data]
        db.close()

        frame_sx = ctk.CTkFrame(grid_container, fg_color=("#FFFFFF", "#2C2C2E"), corner_radius=12, border_width=1, border_color=("#E5E5EA", "#3A3A3C"))
        frame_sx.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        ctk.CTkLabel(frame_sx, text="👤 Dati Personali", font=ctk.CTkFont(family="Montserrat", size=16, weight="bold"), text_color=("#1D1D1F", "#FFFFFF")).pack(pady=(15, 15))

        ctk.CTkLabel(frame_sx, text="Numero Scheda:", font=ctk.CTkFont(family="Montserrat"), text_color=("#1D1D1F", "#FFFFFF")).pack(anchor="w", padx=20)
        self.ent_scheda = ctk.CTkEntry(frame_sx, placeholder_text="Es. 000123")
        self.ent_scheda.pack(pady=(0, 15), padx=20, fill="x")

        ctk.CTkLabel(frame_sx, text="Nome:", font=ctk.CTkFont(family="Montserrat"), text_color=("#1D1D1F", "#FFFFFF")).pack(anchor="w", padx=20)
        self.ent_nome = ctk.CTkEntry(frame_sx)
        self.ent_nome.pack(pady=(0, 15), padx=20, fill="x")

        ctk.CTkLabel(frame_sx, text="Cognome:", font=ctk.CTkFont(family="Montserrat"), text_color=("#1D1D1F", "#FFFFFF")).pack(anchor="w", padx=20)
        self.ent_cognome = ctk.CTkEntry(frame_sx)
        self.ent_cognome.pack(pady=(0, 15), padx=20, fill="x")

        lbl_nascita_container = ctk.CTkFrame(frame_sx, fg_color="transparent")
        lbl_nascita_container.pack(anchor="w", padx=20, fill="x")
        ctk.CTkLabel(lbl_nascita_container, text="Data di Nascita (GG/MM/AAAA):", font=ctk.CTkFont(family="Montserrat"), text_color=("#1D1D1F", "#FFFFFF")).pack(side="left")
        self.lbl_eta = ctk.CTkLabel(lbl_nascita_container, text="", font=ctk.CTkFont(family="Montserrat", weight="bold"), text_color="#007AFF")
        self.lbl_eta.pack(side="right")

        self.ent_data_nascita = ctk.CTkEntry(frame_sx, placeholder_text="Es. 15/08/1985")
        self.ent_data_nascita.pack(pady=(0, 15), padx=20, fill="x")
        self.ent_data_nascita.bind("<KeyRelease>", self.calcola_eta_live)
        self.ent_data_nascita.bind("<FocusOut>", self.calcola_eta_live)

        ctk.CTkLabel(frame_sx, text="Luogo di Nascita:", font=ctk.CTkFont(family="Montserrat"), text_color=("#1D1D1F", "#FFFFFF")).pack(anchor="w", padx=20)
        self.cmb_luogo_nascita = ctk.CTkComboBox(frame_sx, values=luoghi_unici)
        self.cmb_luogo_nascita.pack(pady=(0, 15), padx=20, fill="x")

        ctk.CTkLabel(frame_sx, text="Comune di Residenza:", font=ctk.CTkFont(family="Montserrat"), text_color=("#1D1D1F", "#FFFFFF")).pack(anchor="w", padx=20)
        self.cmb_comune = ctk.CTkComboBox(frame_sx, values=comuni_unici)
        self.cmb_comune.pack(pady=(0, 15), padx=20, fill="x")

        ctk.CTkLabel(frame_sx, text="Indirizzo:", font=ctk.CTkFont(family="Montserrat"), text_color=("#1D1D1F", "#FFFFFF")).pack(anchor="w", padx=20)
        self.ent_indirizzo = ctk.CTkEntry(frame_sx)
        self.ent_indirizzo.pack(pady=(0, 15), padx=20, fill="x")

        ctk.CTkLabel(frame_sx, text="Telefono:", font=ctk.CTkFont(family="Montserrat"), text_color=("#1D1D1F", "#FFFFFF")).pack(anchor="w", padx=20)
        self.ent_telefono = ctk.CTkEntry(frame_sx)
        self.ent_telefono.pack(pady=(0, 15), padx=20, fill="x")

        ctk.CTkLabel(frame_sx, text="Altro Recapito (Es. Tel fisso o Parenti):", font=ctk.CTkFont(family="Montserrat"), text_color=("#1D1D1F", "#FFFFFF")).pack(anchor="w", padx=20)
        self.ent_altro_recapito = ctk.CTkEntry(frame_sx, placeholder_text="Opzionale")
        self.ent_altro_recapito.pack(pady=(0, 15), padx=20, fill="x")

        ctk.CTkLabel(frame_sx, text="Sesso:", font=ctk.CTkFont(family="Montserrat"), text_color=("#1D1D1F", "#FFFFFF")).pack(anchor="w", padx=20)
        self.cmb_sesso = ctk.CTkOptionMenu(frame_sx, values=["M", "F"])
        self.cmb_sesso.pack(pady=(0, 20), padx=20, fill="x")

        frame_dx = ctk.CTkFrame(grid_container, fg_color=("#FFFFFF", "#2C2C2E"), corner_radius=12, border_width=1, border_color=("#E5E5EA", "#3A3A3C"))
        frame_dx.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

        ctk.CTkLabel(frame_dx, text="🏷️ Dati Iscrizione e Abbonamento", font=ctk.CTkFont(family="Montserrat", size=16, weight="bold"), text_color=("#1D1D1F", "#FFFFFF")).pack(pady=(15, 15))

        ctk.CTkLabel(frame_dx, text="Scadenza Iscrizione Annuale (Quota):", font=ctk.CTkFont(family="Montserrat", weight="bold"), text_color=("#1D1D1F", "#FFFFFF")).pack(anchor="w", padx=20, pady=(0,5))
        self.ent_scadenza_iscr = ctk.CTkEntry(frame_dx, placeholder_text="Es. 30/12/2026", text_color=("#FF9500", "#FF9500"), font=ctk.CTkFont(family="Montserrat", weight="bold"))
        self.ent_scadenza_iscr.pack(pady=(0, 25), padx=20, fill="x")

        ctk.CTkLabel(frame_dx, text="Seleziona Fascia Abbonamento:", font=ctk.CTkFont(family="Montserrat", weight="bold"), text_color=("#1D1D1F", "#FFFFFF")).pack(anchor="w", padx=20, pady=(0, 5))
        self.cmb_fascia = ctk.CTkOptionMenu(frame_dx, values=tier_names, command=self.aggiorna_fascia_selezionata)
        self.cmb_fascia.pack(pady=(0, 15), padx=20, fill="x")

        ctk.CTkLabel(frame_dx, text="Ingressi Rimanenti (Carnet):", font=ctk.CTkFont(family="Montserrat", weight="bold"), text_color=("#1D1D1F", "#FFFFFF")).pack(anchor="w", padx=20, pady=(0,5))
        self.ent_ingressi = ctk.CTkEntry(frame_dx, placeholder_text="Es. 10 o Illimitati", font=ctk.CTkFont(family="Montserrat", weight="bold"), text_color=("#007AFF", "#0A84FF"))
        self.ent_ingressi.pack(pady=(0, 15), padx=20, fill="x")

        ctk.CTkLabel(frame_dx, text="Data PARTENZA Mensilità:", font=ctk.CTkFont(family="Montserrat"), text_color=("#1D1D1F", "#FFFFFF")).pack(anchor="w", padx=20, pady=(0,5))
        self.ent_partenza_mensilita = ctk.CTkEntry(frame_dx, placeholder_text="Data inizio", text_color=("#1D1D1F", "#FFFFFF"), font=ctk.CTkFont(family="Montserrat"))
        self.ent_partenza_mensilita.pack(pady=(0, 15), padx=20, fill="x")
        self.ent_partenza_mensilita.bind("<Return>", lambda e: self.calcola_scadenza_automatica())
        self.ent_partenza_mensilita.bind("<FocusOut>", lambda e: self.calcola_scadenza_automatica())

        ctk.CTkLabel(frame_dx, text="Data SCADENZA Mensilità (Calcolo Auto):", font=ctk.CTkFont(family="Montserrat"), text_color=("#1D1D1F", "#FFFFFF")).pack(anchor="w", padx=20, pady=(0,5))
        self.ent_scadenza_mensilita = ctk.CTkEntry(frame_dx, placeholder_text="Scadenza fine abbonamento", text_color=("#1D1D1F", "#FFFFFF"), font=ctk.CTkFont(family="Montserrat", weight="bold"))
        self.ent_scadenza_mensilita.pack(pady=(0, 30), padx=20, fill="x")

        ctk.CTkLabel(frame_dx, text="Dati Medici (Promemoria non bloccante):", font=ctk.CTkFont(family="Montserrat", weight="bold"), text_color=("#86868B", "#98989D")).pack(anchor="w", padx=20, pady=(0,10))
        self.chk_certificato = ctk.CTkCheckBox(frame_dx, text="Certificato Medico Consegnato", font=ctk.CTkFont(family="Montserrat"), text_color=("#1D1D1F", "#FFFFFF"))
        self.chk_certificato.pack(pady=(0, 15), padx=20, anchor="w")

        ctk.CTkLabel(frame_dx, text="Scadenza Certificato (GG/MM/AAAA):", font=ctk.CTkFont(family="Montserrat"), text_color=("#1D1D1F", "#FFFFFF")).pack(anchor="w", padx=20)
        self.ent_scadenza_cert = ctk.CTkEntry(frame_dx)
        self.ent_scadenza_cert.pack(pady=(0, 20), padx=20, fill="x")

        if self.socio_id:
            self.carica_dati_socio()
        else:
            self.cmb_luogo_nascita.set("")
            self.cmb_comune.set("")
            self.ent_ingressi.configure(state="disabled") 
            oggi = datetime.now()
            self.ent_partenza_mensilita.insert(0, oggi.strftime("%d/%m/%Y"))
            scadenza_iscr = oggi + timedelta(days=365)
            self.ent_scadenza_iscr.insert(0, scadenza_iscr.strftime("%d/%m/%Y"))

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=(15, 20), fill="x", padx=40)
        
        ctk.CTkButton(btn_frame, text="OK / Salva", width=140, height=38, font=ctk.CTkFont(family="Montserrat", size=14, weight="bold"), fg_color="#34C759", hover_color="#2eb350", command=self.salva_socio).pack(side="left")
        ctk.CTkButton(btn_frame, text="Annulla", width=140, height=38, font=ctk.CTkFont(family="Montserrat", size=14, weight="bold"), fg_color=("#E5E5EA", "#3A3A3C"), text_color=("#1D1D1F", "#FFFFFF"), hover_color=("#D1D1D6", "#5C5C5E"), command=self.destroy).pack(side="right")

    # --- USO UTILS PER DATE ---
    def calcola_eta_live(self, event=None):
        data_str = self.ent_data_nascita.get().strip()
        nascita = parse_date(data_str)
        if not nascita:
            self.lbl_eta.configure(text="")
            return
            
        oggi = datetime.now()
        eta = oggi.year - nascita.year - ((oggi.month, oggi.day) < (nascita.month, nascita.day))
        self.lbl_eta.configure(text=f"Età: {eta} anni")

    def aggiorna_fascia_selezionata(self, fascia_scelta):
        tier_dict = next((t for t in self.tiers_data if t["name"] == fascia_scelta), None)
        self.ent_ingressi.configure(state="normal")
        self.ent_ingressi.delete(0, 'end')
        
        if tier_dict:
            if tier_dict["max_entries"] > 0: self.ent_ingressi.insert(0, str(tier_dict["max_entries"]))
            else:
                self.ent_ingressi.insert(0, "Illimitati")
                self.ent_ingressi.configure(state="disabled") 
        else:
            self.ent_ingressi.configure(state="disabled")
            
        self.calcola_scadenza_automatica()

    def calcola_scadenza_automatica(self):
        fascia_scelta = self.cmb_fascia.get()
        if fascia_scelta == "Nessuna fascia": return
        
        d_partenza = parse_date(self.ent_partenza_mensilita.get())
        if not d_partenza: return
        
        tier_dict = next((t for t in self.tiers_data if t["name"] == fascia_scelta), None)
        mesi_durata = tier_dict["duration_months"] if tier_dict else 1
            
        mese_target = d_partenza.month - 1 + mesi_durata
        anno_succ = d_partenza.year + (mese_target // 12)
        mese_succ = (mese_target % 12) + 1
        
        giorni_nel_mese_dest = calendar.monthrange(anno_succ, mese_succ)[1]
        giorno = min(d_partenza.day, giorni_nel_mese_dest) 
        
        d_scadenza = datetime(anno_succ, mese_succ, giorno)
        
        self.ent_scadenza_mensilita.delete(0, 'end')
        self.ent_scadenza_mensilita.insert(0, d_scadenza.strftime("%d/%m/%Y"))

    def carica_dati_socio(self):
        db = SessionLocal()
        socio = db.query(Member).filter(Member.id == self.socio_id).first()
        if socio:
            if socio.badge_number: self.ent_scheda.insert(0, socio.badge_number)
            self.ent_nome.insert(0, socio.first_name)
            self.ent_cognome.insert(0, socio.last_name)
            if socio.birth_date: 
                self.ent_data_nascita.insert(0, socio.birth_date)
                self.calcola_eta_live()
            if socio.birth_place: self.cmb_luogo_nascita.set(socio.birth_place)
            if socio.city: self.cmb_comune.set(socio.city)
            if socio.address: self.ent_indirizzo.insert(0, socio.address)
            if socio.phone: self.ent_telefono.insert(0, socio.phone)
            if socio.other_contact: self.ent_altro_recapito.insert(0, socio.other_contact)
            self.cmb_sesso.set(socio.gender)
            
            if socio.enrollment_expiration: self.ent_scadenza_iscr.insert(0, socio.enrollment_expiration)
            if socio.membership_start: self.ent_partenza_mensilita.insert(0, socio.membership_start)
            if socio.membership_expiration: self.ent_scadenza_mensilita.insert(0, socio.membership_expiration)
            
            if socio.tier: 
                self.cmb_fascia.set(socio.tier.name)
                self.ent_ingressi.configure(state="normal")
                self.ent_ingressi.delete(0, 'end')
                if socio.tier.max_entries > 0:
                    rimanenti = socio.tier.max_entries - (socio.entries_used or 0)
                    self.ent_ingressi.insert(0, str(rimanenti))
                else:
                    self.ent_ingressi.insert(0, "Illimitati")
                    self.ent_ingressi.configure(state="disabled")
            
            if socio.has_medical_certificate: self.chk_certificato.select()
            if socio.certificate_expiration: self.ent_scadenza_cert.insert(0, socio.certificate_expiration)
        db.close()

    def salva_socio(self):
        nome = self.ent_nome.get().strip()
        cognome = self.ent_cognome.get().strip()
        scheda = self.ent_scheda.get().strip()
        
        if not nome or not cognome: return messagebox.showwarning("Errore", "Nome e Cognome sono obbligatori!")
        
        db = SessionLocal()
        if scheda:
            esistente = db.query(Member).filter(Member.badge_number == scheda, Member.id != self.socio_id).first()
            if esistente: 
                db.close()
                return messagebox.showerror("Errore", f"Il Numero Scheda {scheda} è già assegnato a {esistente.first_name}!")
        
        d_nascita = self.ent_data_nascita.get().strip()
        d_iscr = self.ent_scadenza_iscr.get().strip()
        d_partenza = self.ent_partenza_mensilita.get().strip()
        d_scadenza = self.ent_scadenza_mensilita.get().strip()
        d_cert = self.ent_scadenza_cert.get().strip()
        
        # USA IS_VALID_DATE DA UTILS.PY
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

        fascia_selezionata = self.cmb_fascia.get()
        tier_dict = next((t for t in self.tiers_data if t["name"] == fascia_selezionata), None)
        
        if self.socio_id: socio = db.query(Member).filter(Member.id == self.socio_id).first()
        else:
            socio = Member()
            db.add(socio)
            
        socio.badge_number = scheda if scheda else None
        socio.first_name = nome
        socio.last_name = cognome
        socio.birth_date = d_nascita
        socio.birth_place = self.cmb_luogo_nascita.get().strip()
        socio.city = self.cmb_comune.get().strip()
        socio.address = self.ent_indirizzo.get().strip()
        socio.phone = self.ent_telefono.get().strip()
        socio.other_contact = self.ent_altro_recapito.get().strip()
        socio.gender = self.cmb_sesso.get()
        
        socio.enrollment_expiration = d_iscr
        socio.membership_start = d_partenza
        socio.membership_expiration = d_scadenza
        socio.has_medical_certificate = self.chk_certificato.get() == 1
        socio.certificate_expiration = d_cert
        socio.tier_id = tier_dict["id"] if tier_dict else None
        
        if tier_dict and tier_dict["max_entries"] > 0:
            val_ingressi = self.ent_ingressi.get().strip()
            try:
                rimanenti = int(val_ingressi)
                socio.entries_used = max(0, tier_dict["max_entries"] - rimanenti)
            except ValueError: 
                db.close()
                return messagebox.showwarning("Errore", "Il numero di ingressi rimanenti deve essere un numero valido.")
        else:
            socio.entries_used = 0
        
        db.commit()
        db.close()
        self.refresh_callback()
        self.destroy()

class SociView(ctk.CTkFrame):
    def __init__(self, parent, controller=None, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        
        self.font_riga = ctk.CTkFont(family="Montserrat", size=13)
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.row_frames = {} 
        self.selected_socio_id = None
        
        self.pagina_corrente = 1
        self.elementi_per_pagina = 50

        search_frame = ctk.CTkFrame(self, fg_color=("#FFFFFF", "#2C2C2E"), corner_radius=12, border_width=1, border_color=("#E5E5EA", "#3A3A3C"))
        search_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=20)

        db = SessionLocal()
        tiers = db.query(Tier).all()
        tier_names = ["Tutte"] + [t.name for t in tiers]
        db.close()

        row1 = ctk.CTkFrame(search_frame, fg_color="transparent")
        row1.pack(pady=(15, 5), fill="x", padx=15)

        ctk.CTkLabel(row1, text="Nome:", font=ctk.CTkFont(family="Montserrat", weight="bold"), text_color=("#86868B", "#98989D")).pack(side="left", padx=(0, 5))
        self.src_nome = ctk.CTkEntry(row1, width=160, font=ctk.CTkFont(family="Montserrat"))
        self.src_nome.pack(side="left", padx=(0, 20))

        ctk.CTkLabel(row1, text="Cognome:", font=ctk.CTkFont(family="Montserrat", weight="bold"), text_color=("#86868B", "#98989D")).pack(side="left", padx=(0, 5))
        self.src_cognome = ctk.CTkEntry(row1, width=160, font=ctk.CTkFont(family="Montserrat"))
        self.src_cognome.pack(side="left", padx=(0, 20))

        ctk.CTkLabel(row1, text="Telefono:", font=ctk.CTkFont(family="Montserrat", weight="bold"), text_color=("#86868B", "#98989D")).pack(side="left", padx=(0, 5))
        self.src_telefono = ctk.CTkEntry(row1, width=160, font=ctk.CTkFont(family="Montserrat"))
        self.src_telefono.pack(side="left", padx=(0, 20))

        row2 = ctk.CTkFrame(search_frame, fg_color="transparent")
        row2.pack(pady=(5, 15), fill="x", padx=15)

        ctk.CTkLabel(row2, text="Num. Scheda:", font=ctk.CTkFont(family="Montserrat", weight="bold"), text_color=("#86868B", "#98989D")).pack(side="left", padx=(0, 5))
        self.src_scheda = ctk.CTkEntry(row2, width=120, font=ctk.CTkFont(family="Montserrat"))
        self.src_scheda.pack(side="left", padx=(0, 20))

        ctk.CTkLabel(row2, text="Fascia Abbonamento:", font=ctk.CTkFont(family="Montserrat", weight="bold"), text_color=("#86868B", "#98989D")).pack(side="left", padx=(0, 5))
        self.src_fascia = ctk.CTkComboBox(row2, values=tier_names, width=160, font=ctk.CTkFont(family="Montserrat"))
        self.src_fascia.set("Tutte")
        self.src_fascia.pack(side="left", padx=(0, 20))

        btn_annulla = ctk.CTkButton(row2, text="Resetta", width=100, height=32, font=ctk.CTkFont(family="Montserrat", weight="bold"), fg_color=("#E5E5EA", "#3A3A3C"), text_color=("#1D1D1F", "#FFFFFF"), hover_color=("#D1D1D6", "#5C5C5E"), command=self.reset_ricerca)
        btn_annulla.pack(side="right", padx=(10, 0))

        btn_cerca = ctk.CTkButton(row2, text="Cerca", width=100, height=32, font=ctk.CTkFont(family="Montserrat", weight="bold"), fg_color="#007AFF", hover_color="#005ecb", command=lambda: self.carica_dati(reset_page=True))
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
        
        self.btn_prev = ctk.CTkButton(self.pagination_frame, text="◀ Precedente", width=120, height=28, font=ctk.CTkFont(family="Montserrat", weight="bold"), fg_color=("#E5E5EA", "#3A3A3C"), text_color=("#1D1D1F", "#FFFFFF"), hover_color=("#D1D1D6", "#5C5C5E"), command=self.pagina_precedente)
        self.btn_prev.pack(side="left")
        
        self.lbl_page = ctk.CTkLabel(self.pagination_frame, text="Pagina 1 di 1", font=ctk.CTkFont(family="Montserrat", size=13, weight="bold"), text_color=("#86868B", "#98989D"))
        self.lbl_page.pack(side="left", expand=True)
        
        self.btn_next = ctk.CTkButton(self.pagination_frame, text="Successiva ▶", width=120, height=28, font=ctk.CTkFont(family="Montserrat", weight="bold"), fg_color=("#E5E5EA", "#3A3A3C"), text_color=("#1D1D1F", "#FFFFFF"), hover_color=("#D1D1D6", "#5C5C5E"), command=self.pagina_successiva)
        self.btn_next.pack(side="right")

        self.scroll_table = ctk.CTkScrollableFrame(self.table_container, fg_color="transparent")
        self.scroll_table.pack(side="top", fill="both", expand=True)

        bottom_frame = ctk.CTkFrame(self, fg_color="transparent")
        bottom_frame.grid(row=3, column=0, sticky="ew", padx=20, pady=15)

        ctk.CTkButton(bottom_frame, text="+ Nuovo Socio", width=150, height=38, font=ctk.CTkFont(family="Montserrat", size=14, weight="bold"), fg_color="#34C759", hover_color="#2eb350", command=self.apri_form_nuovo).pack(side="left", padx=(0, 10))
        ctk.CTkButton(bottom_frame, text="✏️ Modifica", width=150, height=38, font=ctk.CTkFont(family="Montserrat", size=14, weight="bold"), fg_color="#007AFF", hover_color="#005ecb", command=self.apri_form_modifica).pack(side="left", padx=10)
        ctk.CTkButton(bottom_frame, text="🗑️ Elimina", width=150, height=38, font=ctk.CTkFont(family="Montserrat", size=14, weight="bold"), fg_color="#FF3B30", hover_color="#e03026", command=self.elimina_socio).pack(side="right")

        self.carica_dati(reset_page=True)

    def pagina_precedente(self):
        if self.pagina_corrente > 1:
            self.pagina_corrente -= 1
            self.carica_dati(reset_page=False)

    def pagina_successiva(self):
        self.pagina_corrente += 1
        self.carica_dati(reset_page=False)

    def reset_ricerca(self):
        self.src_scheda.delete(0, 'end')
        self.src_fascia.set("Tutte")
        self.src_nome.delete(0, 'end')
        self.src_cognome.delete(0, 'end')
        self.src_telefono.delete(0, 'end') 
        self.carica_dati(reset_page=True)

    def seleziona_riga(self, socio_id):
        self.selected_socio_id = socio_id
        for s_id, frame in self.row_frames.items():
            if frame.winfo_exists():
                if s_id == socio_id:
                    frame.configure(fg_color=("#E5F1FF", "#0A2A4A"), border_color="#007AFF")
                else:
                    frame.configure(fg_color=("#FFFFFF", "#2C2C2E"), border_color=("#E5E5EA", "#3A3A3C"))

    def crea_riga_tabella(self, socio_data):
        riga_frame = ctk.CTkFrame(self.scroll_table, fg_color=("#FFFFFF", "#2C2C2E"), height=45, corner_radius=8, border_width=1, border_color=("#E5E5EA", "#3A3A3C"), cursor="hand2")
        riga_frame.pack(fill="x", pady=2)
        riga_frame.pack_propagate(False)

        valori = [
            socio_data["scheda"],
            socio_data["nome"],
            socio_data["cognome"],
            socio_data["fascia"],
            socio_data["scad_abb"],
            socio_data["scad_iscr"]
        ]

        elementi_riga = [riga_frame]
        
        for i, val in enumerate(valori):
            riga_frame.grid_columnconfigure(i, weight=self.cols[i][2], uniform="colonna")
            lbl = ctk.CTkLabel(riga_frame, text=val, font=self.font_riga, text_color=("#1D1D1F", "#FFFFFF"), anchor=self.cols[i][3])
            lbl.grid(row=0, column=i, padx=10, pady=10, sticky="ew")
            elementi_riga.append(lbl)

        s_id = socio_data["id"]
        for w in elementi_riga:
            w.bind("<Button-1>", lambda e, s=s_id: self.seleziona_riga(s))
            w.bind("<Double-Button-1>", lambda e, s=s_id: self.apri_form_modifica(force_id=s))
            w.bind("<Enter>", lambda e, f=riga_frame, s=s_id: f.configure(fg_color=("#F8F8F9", "#3A3A3C")) if f.winfo_exists() and self.selected_socio_id != s else None)
            w.bind("<Leave>", lambda e, f=riga_frame, s=s_id: f.configure(fg_color=("#FFFFFF", "#2C2C2E")) if f.winfo_exists() and self.selected_socio_id != s else None)

        self.row_frames[s_id] = riga_frame

    def carica_dati(self, reset_page=False):
        if reset_page:
            self.pagina_corrente = 1
            
        for widget in self.scroll_table.winfo_children():
            widget.destroy()
        
        self.row_frames.clear()
        self.selected_socio_id = None

        db = SessionLocal()
        query = db.query(Member)

        scheda = self.src_scheda.get().strip()
        if scheda: query = query.filter(Member.badge_number.ilike(f"%{scheda}%"))
        
        fascia = self.src_fascia.get()
        if fascia != "Tutte": query = query.join(Tier).filter(Tier.name == fascia)
        
        nome = self.src_nome.get().strip()
        if nome: query = query.filter(Member.first_name.ilike(f"%{nome}%"))
        
        cognome = self.src_cognome.get().strip()
        if cognome: query = query.filter(Member.last_name.ilike(f"%{cognome}%"))
        
        telefono = self.src_telefono.get().strip()
        if telefono: query = query.filter(Member.phone.ilike(f"%{telefono}%"))

        totale_soci = query.count()
        totale_pagine = max(1, (totale_soci + self.elementi_per_pagina - 1) // self.elementi_per_pagina)
        
        if self.pagina_corrente > totale_pagine:
            self.pagina_corrente = totale_pagine

        soci_db = query.order_by(Member.first_name, Member.last_name).offset((self.pagina_corrente - 1) * self.elementi_per_pagina).limit(self.elementi_per_pagina).all()
        
        soci_data = []
        for s in soci_db:
            soci_data.append({
                "id": s.id,
                "scheda": s.badge_number if s.badge_number else "-",
                "nome": s.first_name,
                "cognome": s.last_name,
                "fascia": s.tier.name if s.tier else "Nessuna",
                "scad_abb": s.membership_expiration if s.membership_expiration else "N/D",
                "scad_iscr": s.enrollment_expiration if s.enrollment_expiration else "N/D"
            })
        db.close()

        for s_data in soci_data:
            self.crea_riga_tabella(s_data)
            
        self.lbl_page.configure(text=f"Pagina {self.pagina_corrente} di {totale_pagine} (Totale: {totale_soci} soci)")
        self.btn_prev.configure(state="normal" if self.pagina_corrente > 1 else "disabled")
        self.btn_next.configure(state="normal" if self.pagina_corrente < totale_pagine else "disabled")

    def apri_form_nuovo(self):
        SocioFormWindow(self, refresh_callback=lambda: self.carica_dati(reset_page=False))

    def apri_form_modifica(self, force_id=None):
        target_id = force_id or self.selected_socio_id
        if not target_id: 
            return messagebox.showwarning("Attenzione", "Seleziona prima un socio dalla lista.")
        SocioFormWindow(self, refresh_callback=lambda: self.carica_dati(reset_page=False), socio_id=target_id)

    def elimina_socio(self):
        if not self.selected_socio_id: return messagebox.showwarning("Attenzione", "Seleziona prima un socio dalla lista.")
        
        db = SessionLocal()
        socio = db.query(Member).filter(Member.id == self.selected_socio_id).first()

        if socio and messagebox.askyesno("Conferma", f"Vuoi eliminare definitivamente {socio.first_name} {socio.last_name}?"):
            db.delete(socio)
            db.commit()
            
        db.close()
        self.carica_dati(reset_page=False)