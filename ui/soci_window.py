import customtkinter as ctk
from tkinter import messagebox
from core.database import SessionLocal, Member, Tier
from datetime import datetime, timedelta
import calendar

# ==================== POPUP: FORM INSERIMENTO/MODIFICA ====================
class SocioFormWindow(ctk.CTkToplevel):
    def __init__(self, parent, refresh_callback, socio_id=None):
        super().__init__(parent)
        self.title("Scheda Socio")
        self.geometry("900x650") 
        self.configure(fg_color=("#F2F2F7", "#1C1C1E"))
        self.refresh_callback = refresh_callback
        self.socio_id = socio_id
        self.db = SessionLocal()
        
        self.transient(parent.winfo_toplevel())
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self.chiudi)

        lbl_titolo = ctk.CTkLabel(self, text="Scheda Anagrafica e Iscrizione", font=ctk.CTkFont(family="Ubuntu", size=22, weight="bold"), text_color="#007AFF")
        lbl_titolo.pack(pady=(15, 5))

        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_frame.pack(fill="both", expand=True, padx=20, pady=10)

        grid_container = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        grid_container.pack(fill="both", expand=True)
        grid_container.grid_columnconfigure(0, weight=1, uniform="colonna")
        grid_container.grid_columnconfigure(1, weight=1, uniform="colonna")
        grid_container.grid_rowconfigure(0, weight=1)

        comuni_unici = sorted(list(set([m.city for m in self.db.query(Member.city).filter(Member.city != None).all()])))
        luoghi_unici = sorted(list(set([m.birth_place for m in self.db.query(Member.birth_place).filter(Member.birth_place != None).all()])))

        # ---------------- COLONNA SINISTRA: ANAGRAFICA ----------------
        frame_sx = ctk.CTkFrame(grid_container, fg_color=("#FFFFFF", "#2C2C2E"), corner_radius=12, border_width=1, border_color=("#E5E5EA", "#3A3A3C"))
        frame_sx.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        ctk.CTkLabel(frame_sx, text="👤 Dati Personali", font=ctk.CTkFont(family="Ubuntu", size=16, weight="bold"), text_color=("#1D1D1F", "#FFFFFF")).pack(pady=(15, 15))

        ctk.CTkLabel(frame_sx, text="Numero Scheda:", font=ctk.CTkFont(family="Ubuntu"), text_color=("#1D1D1F", "#FFFFFF")).pack(anchor="w", padx=20)
        self.ent_scheda = ctk.CTkEntry(frame_sx, placeholder_text="Es. 000123")
        self.ent_scheda.pack(pady=(0, 15), padx=20, fill="x")

        ctk.CTkLabel(frame_sx, text="Nome:", font=ctk.CTkFont(family="Ubuntu"), text_color=("#1D1D1F", "#FFFFFF")).pack(anchor="w", padx=20)
        self.ent_nome = ctk.CTkEntry(frame_sx)
        self.ent_nome.pack(pady=(0, 15), padx=20, fill="x")

        ctk.CTkLabel(frame_sx, text="Cognome:", font=ctk.CTkFont(family="Ubuntu"), text_color=("#1D1D1F", "#FFFFFF")).pack(anchor="w", padx=20)
        self.ent_cognome = ctk.CTkEntry(frame_sx)
        self.ent_cognome.pack(pady=(0, 15), padx=20, fill="x")

        ctk.CTkLabel(frame_sx, text="Data di Nascita (GG/MM/AAAA):", font=ctk.CTkFont(family="Ubuntu"), text_color=("#1D1D1F", "#FFFFFF")).pack(anchor="w", padx=20)
        self.ent_data_nascita = ctk.CTkEntry(frame_sx, placeholder_text="Es. 15/08/1985")
        self.ent_data_nascita.pack(pady=(0, 15), padx=20, fill="x")

        ctk.CTkLabel(frame_sx, text="Luogo di Nascita:", font=ctk.CTkFont(family="Ubuntu"), text_color=("#1D1D1F", "#FFFFFF")).pack(anchor="w", padx=20)
        self.cmb_luogo_nascita = ctk.CTkComboBox(frame_sx, values=luoghi_unici)
        self.cmb_luogo_nascita.pack(pady=(0, 15), padx=20, fill="x")

        ctk.CTkLabel(frame_sx, text="Comune di Residenza:", font=ctk.CTkFont(family="Ubuntu"), text_color=("#1D1D1F", "#FFFFFF")).pack(anchor="w", padx=20)
        self.cmb_comune = ctk.CTkComboBox(frame_sx, values=comuni_unici)
        self.cmb_comune.pack(pady=(0, 15), padx=20, fill="x")

        ctk.CTkLabel(frame_sx, text="Indirizzo:", font=ctk.CTkFont(family="Ubuntu"), text_color=("#1D1D1F", "#FFFFFF")).pack(anchor="w", padx=20)
        self.ent_indirizzo = ctk.CTkEntry(frame_sx)
        self.ent_indirizzo.pack(pady=(0, 15), padx=20, fill="x")

        ctk.CTkLabel(frame_sx, text="Telefono:", font=ctk.CTkFont(family="Ubuntu"), text_color=("#1D1D1F", "#FFFFFF")).pack(anchor="w", padx=20)
        self.ent_telefono = ctk.CTkEntry(frame_sx)
        self.ent_telefono.pack(pady=(0, 15), padx=20, fill="x")

        ctk.CTkLabel(frame_sx, text="Altro Recapito (Es. Tel fisso o Parenti):", font=ctk.CTkFont(family="Ubuntu"), text_color=("#1D1D1F", "#FFFFFF")).pack(anchor="w", padx=20)
        self.ent_altro_recapito = ctk.CTkEntry(frame_sx, placeholder_text="Opzionale")
        self.ent_altro_recapito.pack(pady=(0, 15), padx=20, fill="x")

        ctk.CTkLabel(frame_sx, text="Sesso:", font=ctk.CTkFont(family="Ubuntu"), text_color=("#1D1D1F", "#FFFFFF")).pack(anchor="w", padx=20)
        self.cmb_sesso = ctk.CTkOptionMenu(frame_sx, values=["M", "F"])
        self.cmb_sesso.pack(pady=(0, 20), padx=20, fill="x")

        # ---------------- COLONNA DESTRA: ABBONAMENTO ----------------
        frame_dx = ctk.CTkFrame(grid_container, fg_color=("#FFFFFF", "#2C2C2E"), corner_radius=12, border_width=1, border_color=("#E5E5EA", "#3A3A3C"))
        frame_dx.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

        ctk.CTkLabel(frame_dx, text="🏷️ Dati Iscrizione e Abbonamento", font=ctk.CTkFont(family="Ubuntu", size=16, weight="bold"), text_color=("#1D1D1F", "#FFFFFF")).pack(pady=(15, 15))

        ctk.CTkLabel(frame_dx, text="Scadenza Iscrizione Annuale (Quota):", font=ctk.CTkFont(family="Ubuntu", weight="bold"), text_color=("#1D1D1F", "#FFFFFF")).pack(anchor="w", padx=20, pady=(0,5))
        self.ent_scadenza_iscr = ctk.CTkEntry(frame_dx, placeholder_text="Es. 30/12/2026", text_color=("#FF9500", "#FF9500"), font=ctk.CTkFont(family="Ubuntu", weight="bold"))
        self.ent_scadenza_iscr.pack(pady=(0, 25), padx=20, fill="x")

        self.tiers = self.db.query(Tier).all()
        tier_names = ["Nessuna fascia"] + [t.name for t in self.tiers]
        
        ctk.CTkLabel(frame_dx, text="Seleziona Fascia Abbonamento:", font=ctk.CTkFont(family="Ubuntu", weight="bold"), text_color=("#1D1D1F", "#FFFFFF")).pack(anchor="w", padx=20, pady=(0, 5))
        self.cmb_fascia = ctk.CTkOptionMenu(frame_dx, values=tier_names, command=self.aggiorna_fascia_selezionata)
        self.cmb_fascia.pack(pady=(0, 15), padx=20, fill="x")

        ctk.CTkLabel(frame_dx, text="Ingressi Rimanenti (Carnet):", font=ctk.CTkFont(family="Ubuntu", weight="bold"), text_color=("#1D1D1F", "#FFFFFF")).pack(anchor="w", padx=20, pady=(0,5))
        self.ent_ingressi = ctk.CTkEntry(frame_dx, placeholder_text="Es. 10 o Illimitati", font=ctk.CTkFont(family="Ubuntu", weight="bold"), text_color=("#007AFF", "#0A84FF"))
        self.ent_ingressi.pack(pady=(0, 15), padx=20, fill="x")

        ctk.CTkLabel(frame_dx, text="Data PARTENZA Mensilità:", font=ctk.CTkFont(family="Ubuntu"), text_color=("#1D1D1F", "#FFFFFF")).pack(anchor="w", padx=20, pady=(0,5))
        self.ent_partenza_mensilita = ctk.CTkEntry(frame_dx, placeholder_text="Data inizio", text_color=("#1D1D1F", "#FFFFFF"), font=ctk.CTkFont(family="Ubuntu"))
        self.ent_partenza_mensilita.pack(pady=(0, 15), padx=20, fill="x")
        self.ent_partenza_mensilita.bind("<Return>", lambda e: self.calcola_scadenza_automatica())
        self.ent_partenza_mensilita.bind("<FocusOut>", lambda e: self.calcola_scadenza_automatica())

        ctk.CTkLabel(frame_dx, text="Data SCADENZA Mensilità (Calcolo Auto):", font=ctk.CTkFont(family="Ubuntu"), text_color=("#1D1D1F", "#FFFFFF")).pack(anchor="w", padx=20, pady=(0,5))
        self.ent_scadenza_mensilita = ctk.CTkEntry(frame_dx, placeholder_text="Scadenza fine abbonamento", text_color=("#1D1D1F", "#FFFFFF"), font=ctk.CTkFont(family="Ubuntu", weight="bold"))
        self.ent_scadenza_mensilita.pack(pady=(0, 30), padx=20, fill="x")

        ctk.CTkLabel(frame_dx, text="Dati Medici (Promemoria non bloccante):", font=ctk.CTkFont(family="Ubuntu", weight="bold"), text_color=("#86868B", "#98989D")).pack(anchor="w", padx=20, pady=(0,10))
        self.chk_certificato = ctk.CTkCheckBox(frame_dx, text="Certificato Medico Consegnato", font=ctk.CTkFont(family="Ubuntu"), text_color=("#1D1D1F", "#FFFFFF"))
        self.chk_certificato.pack(pady=(0, 15), padx=20, anchor="w")

        ctk.CTkLabel(frame_dx, text="Scadenza Certificato (GG/MM/AAAA):", font=ctk.CTkFont(family="Ubuntu"), text_color=("#1D1D1F", "#FFFFFF")).pack(anchor="w", padx=20)
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
        
        ctk.CTkButton(btn_frame, text="OK / Salva", width=140, height=38, font=ctk.CTkFont(family="Ubuntu", size=14, weight="bold"), fg_color="#34C759", hover_color="#2eb350", command=self.salva_socio).pack(side="left")
        ctk.CTkButton(btn_frame, text="Annulla", width=140, height=38, font=ctk.CTkFont(family="Ubuntu", size=14, weight="bold"), fg_color=("#E5E5EA", "#3A3A3C"), text_color=("#1D1D1F", "#FFFFFF"), hover_color=("#D1D1D6", "#5C5C5E"), command=self.chiudi).pack(side="right")

    def chiudi(self):
        self.db.close()
        self.grab_release()
        self.destroy()

    def aggiorna_fascia_selezionata(self, fascia_scelta):
        tier = next((t for t in self.tiers if t.name == fascia_scelta), None)
        
        self.ent_ingressi.configure(state="normal")
        self.ent_ingressi.delete(0, 'end')
        
        if tier:
            if tier.max_entries > 0:
                self.ent_ingressi.insert(0, str(tier.max_entries))
            else:
                self.ent_ingressi.insert(0, "Illimitati")
                self.ent_ingressi.configure(state="disabled") 
        else:
            self.ent_ingressi.configure(state="disabled")
            
        self.calcola_scadenza_automatica()

    def calcola_scadenza_automatica(self):
        fascia_scelta = self.cmb_fascia.get()
        if fascia_scelta == "Nessuna fascia": return
            
        partenza_str = self.ent_partenza_mensilita.get().strip()
        if not partenza_str: return
            
        # Recupera la durata esatta in mesi della fascia selezionata
        tier = next((t for t in self.tiers if t.name == fascia_scelta), None)
        mesi_durata = tier.duration_months if tier else 1
            
        try:
            if "/" in partenza_str: d_partenza = datetime.strptime(partenza_str, "%d/%m/%Y")
            else: d_partenza = datetime.strptime(partenza_str, "%Y-%m-%d")
            
            # Nuovo Algoritmo Matematico Robusto per aggiungere N mesi
            mese_target = d_partenza.month - 1 + mesi_durata
            anno_succ = d_partenza.year + (mese_target // 12)
            mese_succ = (mese_target % 12) + 1
            
            # Evita l'errore del "31 Febbraio"
            giorni_nel_mese_dest = calendar.monthrange(anno_succ, mese_succ)[1]
            giorno = min(d_partenza.day, giorni_nel_mese_dest) 
            
            d_scadenza = datetime(anno_succ, mese_succ, giorno)
            
            self.ent_scadenza_mensilita.delete(0, 'end')
            self.ent_scadenza_mensilita.insert(0, d_scadenza.strftime("%d/%m/%Y"))
        except ValueError:
            pass 

    def carica_dati_socio(self):
        socio = self.db.query(Member).filter(Member.id == self.socio_id).first()
        if socio:
            if socio.badge_number: self.ent_scheda.insert(0, socio.badge_number)
            self.ent_nome.insert(0, socio.first_name)
            self.ent_cognome.insert(0, socio.last_name)
            if socio.birth_date: self.ent_data_nascita.insert(0, socio.birth_date)
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

    def salva_socio(self):
        nome = self.ent_nome.get().strip()
        cognome = self.ent_cognome.get().strip()
        scheda = self.ent_scheda.get().strip()
        
        if not nome or not cognome:
            return messagebox.showwarning("Errore", "Nome e Cognome sono obbligatori!")
            
        if scheda:
            esistente = self.db.query(Member).filter(Member.badge_number == scheda, Member.id != self.socio_id).first()
            if esistente:
                return messagebox.showerror("Errore", f"Il Numero Scheda {scheda} è già assegnato a {esistente.first_name}!")
        
        fascia_selezionata = self.cmb_fascia.get()
        tier = next((t for t in self.tiers if t.name == fascia_selezionata), None)
        tier_id = tier.id if tier else None
        
        if self.socio_id: socio = self.db.query(Member).filter(Member.id == self.socio_id).first()
        else:
            socio = Member()
            self.db.add(socio)
            
        socio.badge_number = scheda if scheda else None
        socio.first_name = nome
        socio.last_name = cognome
        socio.birth_date = self.ent_data_nascita.get().strip()
        socio.birth_place = self.cmb_luogo_nascita.get().strip()
        socio.city = self.cmb_comune.get().strip()
        socio.address = self.ent_indirizzo.get().strip()
        socio.phone = self.ent_telefono.get().strip()
        socio.other_contact = self.ent_altro_recapito.get().strip()
        socio.gender = self.cmb_sesso.get()
        
        socio.enrollment_expiration = self.ent_scadenza_iscr.get().strip()
        socio.membership_start = self.ent_partenza_mensilita.get().strip()
        socio.membership_expiration = self.ent_scadenza_mensilita.get().strip()
        socio.has_medical_certificate = self.chk_certificato.get() == 1
        socio.certificate_expiration = self.ent_scadenza_cert.get().strip()
        
        socio.tier_id = tier_id
        
        if tier and tier.max_entries > 0:
            val_ingressi = self.ent_ingressi.get().strip()
            try:
                rimanenti = int(val_ingressi)
                socio.entries_used = max(0, tier.max_entries - rimanenti)
            except ValueError:
                return messagebox.showwarning("Errore", "Il numero di ingressi rimanenti deve essere un numero valido.")
        else:
            socio.entries_used = 0
        
        self.db.commit()
        self.db.close()
        self.refresh_callback()
        self.chiudi()


# ==================== SCHEDA PRINCIPALE: SociView (COME FRAME!) ====================
class SociView(ctk.CTkFrame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, fg_color="transparent")
        
        self.db = SessionLocal()
        
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.row_frames = {} 
        self.selected_socio_id = None

        search_frame = ctk.CTkFrame(self, fg_color=("#FFFFFF", "#2C2C2E"), corner_radius=12, border_width=1, border_color=("#E5E5EA", "#3A3A3C"))
        search_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=20)

        comuni_unici = sorted(list(set([m.city for m in self.db.query(Member.city).filter(Member.city != None).all()])))
        tiers = self.db.query(Tier).all()
        tier_names = ["Tutte"] + [t.name for t in tiers]

        ctk.CTkLabel(search_frame, text="Scheda:", font=ctk.CTkFont(family="Ubuntu"), text_color=("#86868B", "#98989D")).grid(row=0, column=0, padx=10, pady=(15, 10), sticky="e")
        self.src_scheda = ctk.CTkEntry(search_frame, width=120)
        self.src_scheda.grid(row=0, column=1, padx=5, pady=(15, 10), sticky="w")
        
        ctk.CTkLabel(search_frame, text="Fascia:", font=ctk.CTkFont(family="Ubuntu"), text_color=("#86868B", "#98989D")).grid(row=0, column=2, padx=10, pady=(15, 10), sticky="e")
        self.src_fascia = ctk.CTkComboBox(search_frame, values=tier_names, width=150)
        self.src_fascia.set("Tutte")
        self.src_fascia.grid(row=0, column=3, padx=5, pady=(15, 10), sticky="w")

        btn_cerca = ctk.CTkButton(search_frame, text="Cerca", width=120, height=36, font=ctk.CTkFont(family="Ubuntu", size=14, weight="bold"), fg_color="#007AFF", hover_color="#005ecb", command=self.carica_dati)
        btn_cerca.grid(row=0, column=4, padx=(20, 5), pady=(15, 10))

        btn_annulla = ctk.CTkButton(search_frame, text="Resetta", width=120, height=36, font=ctk.CTkFont(family="Ubuntu", size=14, weight="bold"), fg_color=("#E5E5EA", "#3A3A3C"), text_color=("#1D1D1F", "#FFFFFF"), hover_color=("#D1D1D6", "#5C5C5E"), command=self.reset_ricerca)
        btn_annulla.grid(row=0, column=5, padx=5, pady=(15, 10))

        ctk.CTkLabel(search_frame, text="Nome:", font=ctk.CTkFont(family="Ubuntu"), text_color=("#86868B", "#98989D")).grid(row=1, column=0, padx=10, pady=(0, 15), sticky="e")
        self.src_nome = ctk.CTkEntry(search_frame, width=150)
        self.src_nome.grid(row=1, column=1, padx=5, pady=(0, 15), sticky="w")

        ctk.CTkLabel(search_frame, text="Cognome:", font=ctk.CTkFont(family="Ubuntu"), text_color=("#86868B", "#98989D")).grid(row=1, column=2, padx=10, pady=(0, 15), sticky="e")
        self.src_cognome = ctk.CTkEntry(search_frame, width=150)
        self.src_cognome.grid(row=1, column=3, padx=5, pady=(0, 15), sticky="w")

        ctk.CTkLabel(search_frame, text="Telefono:", font=ctk.CTkFont(family="Ubuntu"), text_color=("#86868B", "#98989D")).grid(row=1, column=4, padx=10, pady=(0, 15), sticky="e")
        self.src_telefono = ctk.CTkEntry(search_frame, width=150)
        self.src_telefono.grid(row=1, column=5, padx=5, pady=(0, 15), sticky="w")

        ctk.CTkLabel(search_frame, text="Comune:", font=ctk.CTkFont(family="Ubuntu"), text_color=("#86868B", "#98989D")).grid(row=2, column=0, padx=10, pady=(0, 15), sticky="e")
        self.src_comune = ctk.CTkComboBox(search_frame, values=[""] + comuni_unici, width=150)
        self.src_comune.set("")
        self.src_comune.grid(row=2, column=1, padx=5, pady=(0, 15), sticky="w")

        self.table_container = ctk.CTkFrame(self, fg_color="transparent")
        self.table_container.grid(row=2, column=0, sticky="nsew", padx=20, pady=(0, 10))
        
        self.cols = [("scheda", "Scheda", 1), ("nome", "Nome", 2), ("cognome", "Cognome", 2), 
                     ("fascia", "Fascia", 1), ("scadenza", "Scad. Abb.", 1), ("scad_iscr", "Scad. Iscr.", 1)]

        header_frame = ctk.CTkFrame(self.table_container, fg_color=("#E5E5EA", "#3A3A3C"), height=35, corner_radius=6)
        header_frame.pack(fill="x", pady=(0, 5))
        
        for i, col in enumerate(self.cols):
            header_frame.grid_columnconfigure(i, weight=col[2])
            ctk.CTkLabel(header_frame, text=col[1], font=ctk.CTkFont(family="Ubuntu", size=12, weight="bold"), text_color=("#86868B", "#98989D"), anchor="w").grid(row=0, column=i, padx=10, pady=5, sticky="w")

        self.scroll_table = ctk.CTkScrollableFrame(self.table_container, fg_color="transparent")
        self.scroll_table.pack(fill="both", expand=True)

        bottom_frame = ctk.CTkFrame(self, fg_color="transparent")
        bottom_frame.grid(row=3, column=0, sticky="ew", padx=20, pady=15)

        ctk.CTkButton(bottom_frame, text="+ Nuovo Socio", width=150, height=38, font=ctk.CTkFont(family="Ubuntu", size=14, weight="bold"), fg_color="#34C759", hover_color="#2eb350", command=self.apri_form_nuovo).pack(side="left", padx=(0, 10))
        ctk.CTkButton(bottom_frame, text="✏️ Modifica", width=150, height=38, font=ctk.CTkFont(family="Ubuntu", size=14, weight="bold"), fg_color="#007AFF", hover_color="#005ecb", command=self.apri_form_modifica).pack(side="left", padx=10)
        ctk.CTkButton(bottom_frame, text="🗑️ Elimina", width=150, height=38, font=ctk.CTkFont(family="Ubuntu", size=14, weight="bold"), fg_color="#FF3B30", hover_color="#e03026", command=self.elimina_socio).pack(side="right")

        self.carica_dati()

    def reset_ricerca(self):
        self.src_scheda.delete(0, 'end')
        self.src_fascia.set("Tutte")
        self.src_nome.delete(0, 'end')
        self.src_cognome.delete(0, 'end')
        self.src_telefono.delete(0, 'end') 
        self.src_comune.set("")
        self.carica_dati()

    def seleziona_riga(self, socio_id):
        self.selected_socio_id = socio_id
        for s_id, frame in self.row_frames.items():
            if s_id == socio_id:
                frame.configure(fg_color=("#E5F1FF", "#0A2A4A"), border_color="#007AFF")
            else:
                frame.configure(fg_color=("#FFFFFF", "#2C2C2E"), border_color=("#E5E5EA", "#3A3A3C"))

    def crea_riga_tabella(self, socio):
        riga_frame = ctk.CTkFrame(self.scroll_table, fg_color=("#FFFFFF", "#2C2C2E"), height=45, corner_radius=8, border_width=1, border_color=("#E5E5EA", "#3A3A3C"), cursor="hand2")
        riga_frame.pack(fill="x", pady=2)
        riga_frame.pack_propagate(False)

        valori = [
            socio.badge_number if socio.badge_number else "-",
            socio.first_name,
            socio.last_name,
            socio.tier.name if socio.tier else "Nessuna",
            socio.membership_expiration if socio.membership_expiration else "N/D",
            socio.enrollment_expiration if socio.enrollment_expiration else "N/D"
        ]

        elementi_riga = [riga_frame]
        
        for i, val in enumerate(valori):
            riga_frame.grid_columnconfigure(i, weight=self.cols[i][2])
            lbl = ctk.CTkLabel(riga_frame, text=val, font=ctk.CTkFont(family="Ubuntu", size=13), text_color=("#1D1D1F", "#FFFFFF"), anchor="w")
            lbl.grid(row=0, column=i, padx=10, pady=10, sticky="w")
            elementi_riga.append(lbl)

        # EVENTO DOPPIO CLIC sulla riga
        for w in elementi_riga:
            w.bind("<Button-1>", lambda e, s_id=socio.id: self.seleziona_riga(s_id))
            w.bind("<Double-Button-1>", lambda e, s_id=socio.id: self.apri_form_modifica(force_id=s_id))
            w.bind("<Enter>", lambda e, f=riga_frame, s_id=socio.id: f.configure(fg_color=("#F8F8F9", "#3A3A3C")) if self.selected_socio_id != s_id else None)
            w.bind("<Leave>", lambda e, f=riga_frame, s_id=socio.id: f.configure(fg_color=("#FFFFFF", "#2C2C2E")) if self.selected_socio_id != s_id else None)

        self.row_frames[socio.id] = riga_frame

    def carica_dati(self):
        for widget in self.scroll_table.winfo_children():
            widget.destroy()
        
        self.row_frames.clear()
        self.selected_socio_id = None

        query = self.db.query(Member)

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
        
        comune = self.src_comune.get().strip()
        if comune: query = query.filter(Member.city.ilike(f"%{comune}%"))

        soci = query.all()
        for socio in soci:
            self.crea_riga_tabella(socio)

    def apri_form_nuovo(self):
        SocioFormWindow(self, refresh_callback=self.carica_dati)

    def apri_form_modifica(self, force_id=None):
        target_id = force_id or self.selected_socio_id
        if not target_id: 
            return messagebox.showwarning("Attenzione", "Seleziona prima un socio dalla lista.")
        SocioFormWindow(self, refresh_callback=self.carica_dati, socio_id=target_id)

    def elimina_socio(self):
        if not self.selected_socio_id: return messagebox.showwarning("Attenzione", "Seleziona prima un socio dalla lista.")
            
        socio = self.db.query(Member).filter(Member.id == self.selected_socio_id).first()

        if socio and messagebox.askyesno("Conferma", f"Vuoi eliminare definitivamente {socio.first_name} {socio.last_name}?"):
            self.db.delete(socio)
            self.db.commit()
            self.carica_dati()