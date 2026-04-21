import time
from abc import ABC, abstractmethod
from datetime import datetime
from src.pkg.utility.utils import parse_date
from src.pkg.repository.member_repository import MemberRepository
from src.pkg.service.audio_service import IAudioPlayer
from src.pkg.service.hardware_service import ITurnstileHardware

class IAccessRule(ABC):
    @abstractmethod
    def check(self, member_dict: dict, settings: dict) -> tuple[bool, str, str]:
        pass

class MedicalCertificateRule(IAccessRule):
    def check(self, member: dict, settings: dict):
        if not settings.get("blocco_cert", False): return True, "", ""
        if not member.get("has_medical_certificate"):
            return False, "Certificato Medico Mancante!", "HeyOp.wav"
        exp = parse_date(member.get("certificate_expiration"))
        if exp and datetime.now() > exp:
            return False, "Certificato Medico Scaduto!", "HeyOp.wav"
        return True, "", ""

class EnrollmentRule(IAccessRule):
    def check(self, member: dict, settings: dict):
        if not settings.get("blocco_iscr", True): return True, "", ""
        exp = parse_date(member.get("enrollment_expiration"))
        if exp and datetime.now() > exp:
            return False, "Iscrizione Annuale Scaduta!", "HeyOp.wav"
        return True, "", ""

class SubscriptionRule(IAccessRule):
    def check(self, member: dict, settings: dict):
        if not settings.get("blocco_abb", True): return True, "", ""
        exp = parse_date(member.get("membership_expiration"))
        if exp and datetime.now() > exp:
            return False, "Abbonamento Scaduto!", "HeyOp.wav"
        return True, "", ""

class TimeRule(IAccessRule):
    def check(self, member: dict, settings: dict):
        if not settings.get("blocco_orari", True): return True, "", ""
        if not member.get("tier_name"): return False, "Nessuna fascia assegnata.", "HeyOp.wav"
        try:
            now = datetime.now()
            start_t = datetime.strptime(member.get("tier_start_time")[:5], "%H:%M").time()
            end_t = datetime.strptime(member.get("tier_end_time")[:5], "%H:%M").time()
            current_t = now.time()
            
            if start_t <= end_t: in_time = start_t <= current_t <= end_t
            else: in_time = current_t >= start_t or current_t <= end_t
                
            if not in_time: return False, "Fuori orario consentito!", "FuoriOrario.wav"
        except ValueError: pass
        return True, "", ""

class EntriesRule(IAccessRule):
    def check(self, member: dict, settings: dict):
        tier_max = member.get("tier_max_entries", 0)
        if not member.get("tier_name") or tier_max <= 0: return True, "", ""
        used = member.get("entries_used") or 0
        if used >= tier_max:
            return False, "Carnet Esaurito!", "FuoriOrario.wav"
        return True, "", ""

class AccessManager:
    def __init__(self, 
                 turnstile: ITurnstileHardware, 
                 audio: IAudioPlayer, 
                 member_repository: MemberRepository,
                 ui_callbacks: dict):
        self.turnstile = turnstile
        self.audio = audio
        self.member_repository = member_repository
        self.ui = ui_callbacks
        self.rules: list[IAccessRule] = []
        self.last_badge = ""
        self.last_time = 0
        self.day_tracker = datetime.now().date()
        self.members_in_facility = set()

    def register_rule(self, rule: IAccessRule):
        self.rules.append(rule)

    def process_badge(self, badge_str: str, settings: dict):
        curr_time = time.time()
        if badge_str == self.last_badge and (curr_time - self.last_time) < 2.0: return
        self.last_badge = badge_str; self.last_time = curr_time
        
        if datetime.now().date() != self.day_tracker:
            self.day_tracker = datetime.now().date()
            self.members_in_facility.clear()

        gym_prefix = "57340000000"
        search_code = None
        time_str = datetime.now().strftime("%H:%M:%S")

        # Gestione flessibile del badge:
        # 1. Se il badge completo include il prefisso (es. "573400000001234"), estrai le ultime cifre
        # 2. Se il badge è solo il numero breve (es. "1234"), usalo direttamente
        if badge_str.startswith(gym_prefix):
            # Badge completo con prefisso: estrai le ultime cifre
            search_code = badge_str[len(gym_prefix):]
        elif len(badge_str) <= 10:
            # Badge breve (solo ultime cifre): assumi sia valido (già validato dal simulatore)
            search_code = badge_str
        else:
            # Tessera senza prefisso e troppo lunga: non autentica, accesso negato
            self.ui.get("toast", lambda *args: None)("ACCESSO NEGATO", "Tessera Non Autentica!", "#FF3B30")
            self.audio.play("NonValida.wav")
            self.ui.get("log", lambda *args: None)(f"{time_str} > SCONOSCIUTO ( {badge_str} ) : NEGATO (Prefisso Mancante)")
            return

        member = self.member_repository.get_member_for_access(search_code)
        if not member:
            self.ui.get("toast", lambda *args: None)("ACCESSO NEGATO", "Scheda Non Registrata!", "#FF3B30")
            self.audio.play("NonValida.wav")
            self.ui.get("log", lambda *args: None)(f"{time_str} > SCONOSCIUTO ( {search_code} ) : NEGATO (Invalida)")
            return

        full_name = f"{member['first_name']} {member['last_name']}"

        for rule in self.rules:
            is_valid, msg, audio_file = rule.check(member, settings)
            if not is_valid:
                self.ui.get("toast", lambda *args: None)("ACCESSO NEGATO", f"{full_name}\n{msg}", "#FF3B30" if "Scaduta" in msg else "#FF9500")
                self.audio.play(audio_file)
                self.ui.get("log", lambda *args: None)(f"{time_str} > {full_name} ( {search_code} ) : NEGATO ({msg})")
                return

        extra_msg = ""
        log_entries = "#∞"
        if member.get("tier_name") and member.get("tier_max_entries", 0) > 0:
            new_used = self.member_repository.increment_entries(member["id"])
            rem = member["tier_max_entries"] - new_used
            extra_msg = f"\nIngressi residui: {rem}"
            log_entries = f"#{rem}"

        self.ui.get("toast", lambda *args: None)("ACCESSO CONSENTITO", f"Benvenuto {full_name}{extra_msg}", "#34C759")
        self.ui.get("log", lambda *args: None)(f"{time_str} > {full_name} ( {search_code} ) : OK {log_entries}")
        self.members_in_facility.add(member["id"])
        self.ui.get("update_counter", lambda *args: None)()
        
        self.turnstile.open_gate()
        
        # Chiamata Audio Dinamica in base al sesso
        self.audio.play("BuonLavoroDonne.wav" if member.get("gender") == "F" else "BuonLavoro.wav")

    def process_manual_open(self):
        self.audio.play("handopen.wav")
        self.turnstile.open_gate()
        self.ui.get("toast", lambda *args: None)("APERTURA D'UFFICIO", "Ingresso autorizzato dall'operatore.", "#007AFF")
        ora_str = datetime.now().strftime("%H:%M:%S")
        self.ui.get("log", lambda *args: None)(f"{ora_str} > APERTURA MANUALE DA OPERATORE ESEGUITA")
