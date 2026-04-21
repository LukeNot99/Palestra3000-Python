"""Access service for managing gym access control with rules engine."""

import time
from datetime import datetime
from typing import Dict, List, Any, Callable, Tuple
from abc import ABC, abstractmethod

from core.services.hardware_service import ITurnstileHardware, IAudioPlayer
from core.repositories.member_repository import MemberRepository
from core.utils import parse_date


class IAccessRule(ABC):
    """Interfaccia per le regole di accesso."""
    
    @abstractmethod
    def check(self, member_dict: Dict[str, Any], settings: Dict[str, Any]) -> Tuple[bool, str, str]:
        """
        Verifica se un membro soddisfa la regola.
        
        Returns:
            Tuple[bool, str, str]: (valido, messaggio, file_audio)
        """
        pass


class MedicalCertificateRule(IAccessRule):
    """Regola per verificare il certificato medico."""
    
    def check(self, member: Dict[str, Any], settings: Dict[str, Any]) -> Tuple[bool, str, str]:
        if not settings.get("blocco_cert", False):
            return True, "", ""
        if not member.get("has_medical_certificate"):
            return False, "Certificato Medico Mancante!", "HeyOp.wav"
        exp = parse_date(member.get("certificate_expiration"))
        if exp and datetime.now() > exp:
            return False, "Certificato Medico Scaduto!", "HeyOp.wav"
        return True, "", ""


class EnrollmentRule(IAccessRule):
    """Regola per verificare l'iscrizione annuale."""
    
    def check(self, member: Dict[str, Any], settings: Dict[str, Any]) -> Tuple[bool, str, str]:
        if not settings.get("blocco_iscr", True):
            return True, "", ""
        exp = parse_date(member.get("enrollment_expiration"))
        if exp and datetime.now() > exp:
            return False, "Iscrizione Annuale Scaduta!", "HeyOp.wav"
        return True, "", ""


class SubscriptionRule(IAccessRule):
    """Regola per verificare l'abbonamento."""
    
    def check(self, member: Dict[str, Any], settings: Dict[str, Any]) -> Tuple[bool, str, str]:
        if not settings.get("blocco_abb", True):
            return True, "", ""
        exp = parse_date(member.get("membership_expiration"))
        if exp and datetime.now() > exp:
            return False, "Abbonamento Scaduto!", "HeyOp.wav"
        return True, "", ""


class TimeRule(IAccessRule):
    """Regola per verificare l'orario di accesso."""
    
    def check(self, member: Dict[str, Any], settings: Dict[str, Any]) -> Tuple[bool, str, str]:
        if not settings.get("blocco_orari", True):
            return True, "", ""
        if not member.get("tier_name"):
            return False, "Nessuna fascia assegnata.", "HeyOp.wav"
        try:
            now = datetime.now()
            start_t = datetime.strptime(member.get("tier_start_time")[:5], "%H:%M").time()
            end_t = datetime.strptime(member.get("tier_end_time")[:5], "%H:%M").time()
            current_t = now.time()
            
            if start_t <= end_t:
                in_time = start_t <= current_t <= end_t
            else:
                in_time = current_t >= start_t or current_t <= end_t
                    
            if not in_time:
                return False, "Fuori orario consentito!", "FuoriOrario.wav"
        except ValueError:
            pass
        return True, "", ""


class EntriesRule(IAccessRule):
    """Regola per verificare gli ingressi disponibili."""
    
    def check(self, member: Dict[str, Any], settings: Dict[str, Any]) -> Tuple[bool, str, str]:
        tier_max = member.get("tier_max_entries", 0)
        if not member.get("tier_name") or tier_max <= 0:
            return True, "", ""
        used = member.get("entries_used") or 0
        if used >= tier_max:
            return False, "Carnet Esaurito!", "FuoriOrario.wav"
        return True, "", ""


class AccessService:
    """Servizio centralizzato per la gestione degli accessi."""
    
    def __init__(self, turnstile: ITurnstileHardware, audio: IAudioPlayer, 
                 ui_callbacks: Dict[str, Callable], member_repository: MemberRepository):
        self.turnstile = turnstile
        self.audio = audio
        self.ui = ui_callbacks
        self.rules: List[IAccessRule] = []
        self.member_repository = member_repository
        self.last_badge = ""
        self.last_time = 0.0
        self.day_tracker = datetime.now().date()
        self.members_in_facility = set()
    
    def register_rule(self, rule: IAccessRule) -> None:
        """Registra una regola di accesso."""
        self.rules.append(rule)
    
    def process_badge(self, badge_str: str, settings: Dict[str, Any]) -> None:
        """Processa un badge letto dal tornello."""
        curr_time = time.time()
        if badge_str == self.last_badge and (curr_time - self.last_time) < 2.0:
            return
        self.last_badge = badge_str
        self.last_time = curr_time
        
        if datetime.now().date() != self.day_tracker:
            self.day_tracker = datetime.now().date()
            self.members_in_facility.clear()
        
        gym_prefix = "57340000000"
        search_code = badge_str
        time_str = datetime.now().strftime("%H:%M:%S")
        
        if len(badge_str) > 4:
            if badge_str.startswith(gym_prefix):
                search_code = badge_str[len(gym_prefix):]
            else:
                self.ui["toast"]("ACCESSO NEGATO", "Tessera non riconosciuta!", "#FF3B30")
                self.audio.play("NonValida.wav")
                self.ui["log"](f"{time_str} > SCONOSCIUTO ( {badge_str} ) : NEGATO (Prefisso Errato)")
                return
        
        member = self.member_repository.get_member_for_access(search_code)
        if not member:
            self.ui["toast"]("ACCESSO NEGATO", "Scheda Non Registrata!", "#FF3B30")
            self.audio.play("NonValida.wav")
            self.ui["log"](f"{time_str} > SCONOSCIUTO ( {search_code} ) : NEGATO (Invalida)")
            return
        
        full_name = f"{member['first_name']} {member['last_name']}"
        
        for rule in self.rules:
            is_valid, msg, audio_file = rule.check(member, settings)
            if not is_valid:
                self.ui["toast"]("ACCESSO NEGATO", f"{full_name}\n{msg}", 
                                "#FF3B30" if "Scaduta" in msg else "#FF9500")
                self.audio.play(audio_file)
                self.ui["log"](f"{time_str} > {full_name} ( {search_code} ) : NEGATO ({msg})")
                return
        
        extra_msg = ""
        log_entries = "#∞"
        if member.get("tier_name") and member.get("tier_max_entries", 0) > 0:
            new_used = self.member_repository.increment_entries(member["id"])
            rem = member["tier_max_entries"] - new_used
            extra_msg = f"\nIngressi residui: {rem}"
            log_entries = f"#{rem}"
        
        self.ui["toast"]("ACCESSO CONSENTITO", f"Benvenuto {full_name}{extra_msg}", "#34C759")
        self.ui["log"](f"{time_str} > {full_name} ( {search_code} ) : OK {log_entries}")
        self.members_in_facility.add(member["id"])
        self.ui["update_counter"]()
        
        self.turnstile.open_gate()
        
        # Chiamata Audio Dinamica in base al sesso
        self.audio.play("BuonLavoroDonne.wav" if member["gender"] == "F" else "BuonLavoro.wav")
    
    def process_manual_open(self) -> None:
        """Apre manualmente il tornello dall'operatore."""
        self.audio.play("handopen.wav")
        self.turnstile.open_gate()
        self.ui["toast"]("APERTURA D'UFFICIO", "Ingresso autorizzato dall'operatore.", "#007AFF")
        ora_str = datetime.now().strftime("%H:%M:%S")
        self.ui["log"](f"{ora_str} > APERTURA MANUALE DA OPERATORE ESEGUITA")


# Factory function per la dependency injection

def get_access_service(turnstile: ITurnstileHardware, audio: IAudioPlayer, 
                       ui_callbacks: Dict[str, Callable], 
                       member_repository: MemberRepository) -> AccessService:
    """Factory function per creare un'istanza di AccessService con tutte le regole registrate."""
    service = AccessService(turnstile, audio, ui_callbacks, member_repository)
    
    # Registra tutte le regole di default
    service.register_rule(MedicalCertificateRule())
    service.register_rule(EnrollmentRule())
    service.register_rule(SubscriptionRule())
    service.register_rule(TimeRule())
    service.register_rule(EntriesRule())
    
    return service
