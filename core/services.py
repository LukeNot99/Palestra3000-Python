import os
import time
import serial
import platform
import subprocess
import threading
from abc import ABC, abstractmethod
from datetime import datetime
from core.utils import parse_date
from core.repositories import MemberRepository

# =====================================================================
# 1. DEPENDENCY INVERSION (DIP) & INTERFACE SEGREGATION (ISP)
# =====================================================================
class ITurnstileHardware(ABC):
    @abstractmethod
    def open_gate(self): pass

class IAudioPlayer(ABC):
    @abstractmethod
    def play(self, file_name: str): pass

class IBadgeReader(ABC):
    @abstractmethod
    def start_listening(self, callback): pass
    
    @abstractmethod
    def stop(self): pass


# =====================================================================
# 2. SINGLE RESPONSIBILITY (SRP) - Implementazioni Concrete
# =====================================================================
class SystemAudioPlayer(IAudioPlayer):
    def __init__(self, base_path: str):
        self.base_path = base_path
        
    def play(self, file_name: str):
        audio_path = os.path.join(self.base_path, "messaggi", file_name)
        if not os.path.exists(audio_path): return
        os_name = platform.system()
        if os_name == "Windows":
            import winsound
            winsound.PlaySound(audio_path, winsound.SND_FILENAME | winsound.SND_ASYNC)
        elif os_name == "Darwin":
            subprocess.Popen(["afplay", audio_path])


class USBRelayTurnstile(ITurnstileHardware):
    def __init__(self, port: str):
        self.port = port
        
    def open_gate(self):
        if not self.port or "Nessun hardware" in self.port: return
        threading.Thread(target=self._pulse, daemon=True).start()
        
    def _pulse(self):
        try:
            with serial.Serial(self.port, 9600, timeout=1) as ser:
                ser.write(b'\xA0\x01\x01\xA2')
                ser.dtr = True; ser.rts = True
                time.sleep(0.5)
                ser.write(b'\xA0\x01\x00\xA1')
                ser.dtr = False; ser.rts = False
        except Exception as e:
            print(f"Errore Relè USB: {e}")


class SerialBadgeReader(IBadgeReader):
    def __init__(self, port: str):
        self.port = port
        self.conn = None
        self.stop_event = threading.Event()
        
    def start_listening(self, callback):
        if not self.port or "Nessun hardware" in self.port: return
        try:
            self.conn = serial.Serial(self.port, 9600, timeout=1)
            self.stop_event.clear()
            threading.Thread(target=self._listen, args=(callback,), daemon=True).start()
        except Exception as e:
            print(f"Errore Lettore Seriale: {e}")
            
    def stop(self):
        self.stop_event.set()
        if self.conn and self.conn.is_open:
            self.conn.close()
            
    def _listen(self, callback):
        while not self.stop_event.is_set():
            if self.conn and self.conn.in_waiting > 0:
                try:
                    data = self.conn.readline().decode('utf-8').strip()
                    badge = ''.join(filter(str.isdigit, data))
                    if badge: callback(badge)
                except Exception: pass


# =====================================================================
# 3. OPEN/CLOSED PRINCIPLE (OCP) - Rules Engine
# =====================================================================
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


# =====================================================================
# 4. GESTORE ACCESSI CENTRALIZZATO 
# =====================================================================
class AccessManager:
    def __init__(self, turnstile: ITurnstileHardware, audio: IAudioPlayer, ui_callbacks: dict):
        self.turnstile = turnstile
        self.audio = audio
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
        search_code = badge_str
        time_str = datetime.now().strftime("%H:%M:%S")

        if len(badge_str) > 4:
            if badge_str.startswith(gym_prefix): search_code = badge_str[len(gym_prefix):]
            else:
                self.ui["toast"]("ACCESSO NEGATO", "Tessera non riconosciuta!", "#FF3B30")
                self.audio.play("NonValida.wav")
                self.ui["log"](f"{time_str} > SCONOSCIUTO ( {badge_str} ) : NEGATO (Prefisso Errato)")
                return

        member = MemberRepository.get_member_for_access(search_code)
        if not member:
            self.ui["toast"]("ACCESSO NEGATO", "Scheda Non Registrata!", "#FF3B30")
            self.audio.play("NonValida.wav")
            self.ui["log"](f"{time_str} > SCONOSCIUTO ( {search_code} ) : NEGATO (Invalida)")
            return

        full_name = f"{member['first_name']} {member['last_name']}"

        for rule in self.rules:
            is_valid, msg, audio_file = rule.check(member, settings)
            if not is_valid:
                self.ui["toast"]("ACCESSO NEGATO", f"{full_name}\n{msg}", "#FF3B30" if "Scaduta" in msg else "#FF9500")
                self.audio.play(audio_file)
                self.ui["log"](f"{time_str} > {full_name} ( {search_code} ) : NEGATO ({msg})")
                return

        extra_msg = ""
        log_entries = "#∞"
        if member.get("tier_name") and member.get("tier_max_entries", 0) > 0:
            new_used = MemberRepository.increment_entries(member["id"])
            rem = member["tier_max_entries"] - new_used
            extra_msg = f"\nIngressi residui: {rem}"
            log_entries = f"#{rem}"

        self.ui["toast"]("ACCESSO CONSENTITO", f"Benvenuto {full_name}{extra_msg}", "#34C759")
        self.ui["log"](f"{time_str} > {full_name} ( {search_code} ) : OK {log_entries}")
        self.members_in_facility.add(member["id"])
        self.ui["update_counter"]()
        
        self.turnstile.open_gate()
        self.audio.play("BuonLavoroDonne.wav" if member["gender"] == "F" else "BuonLavoro.wav")

    def process_manual_open(self):
        self.audio.play("handopen.wav")
        self.turnstile.open_gate()
        self.ui["toast"]("APERTURA D'UFFICIO", "Ingresso autorizzato dall'operatore.", "#007AFF")
        ora_str = datetime.now().strftime("%H:%M:%S")
        self.ui["log"](f"{ora_str} > APERTURA MANUALE DA OPERATORE ESEGUITA")