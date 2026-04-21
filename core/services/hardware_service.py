"""Hardware service implementations for turnstile and badge reader."""

import os
import time
import serial
import platform
import subprocess
import threading
from abc import ABC, abstractmethod
from typing import Optional, Callable


class ITurnstileHardware(ABC):
    """Interfaccia per l'hardware del tornello."""
    
    @abstractmethod
    def open_gate(self) -> None:
        """Apre il cancello del tornello."""
        pass


class IAudioPlayer(ABC):
    """Interfaccia per il player audio."""
    
    @abstractmethod
    def play(self, file_name: str) -> None:
        """Riproduce un file audio."""
        pass


class IBadgeReader(ABC):
    """Interfaccia per il lettore di badge."""
    
    @abstractmethod
    def start_listening(self, callback: Callable[[str], None]) -> None:
        """Avvia l'ascolto dei badge."""
        pass
    
    @abstractmethod
    def stop(self) -> None:
        """Ferma l'ascolto dei badge."""
        pass


class SystemAudioPlayer(IAudioPlayer):
    """Implementazione concreta del player audio di sistema."""
    
    def __init__(self, base_path: str):
        self.base_path = base_path
        
    def play(self, file_name: str) -> None:
        """Riproduce un file audio dal percorso specificato."""
        audio_path = os.path.abspath(os.path.join(self.base_path, "messaggi", file_name))
        
        if not os.path.exists(audio_path):
            print(f"DEBUG: File non trovato - {audio_path}")
            return
            
        os_name = platform.system()
        if os_name == "Windows":
            import winsound
            flags = winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_NODEFAULT
            winsound.PlaySound(audio_path, flags)
        elif os_name == "Darwin":
            subprocess.Popen(["afplay", audio_path])


class USBRelayTurnstile(ITurnstileHardware):
    """Implementazione concreta del tornello con relè USB."""
    
    def __init__(self, port: str):
        self.port = port
        
    def open_gate(self) -> None:
        """Apre il cancello attivando il relè USB."""
        if not self.port or "Nessun hardware" in self.port:
            return
        threading.Thread(target=self._pulse, daemon=True).start()
        
    def _pulse(self) -> None:
        """Attiva il relè per aprire il cancello."""
        try:
            with serial.Serial(self.port, 9600, timeout=1) as ser:
                ser.write(b'\xA0\x01\x01\xA2')
                ser.dtr = True
                ser.rts = True
                time.sleep(0.5)
                ser.write(b'\xA0\x01\x00\xA1')
                ser.dtr = False
                ser.rts = False
        except Exception as e:
            print(f"Errore Relè USB: {e}")


class SerialBadgeReader(IBadgeReader):
    """Implementazione concreta del lettore di badge seriale."""
    
    def __init__(self, port: str):
        self.port = port
        self.conn: Optional[serial.Serial] = None
        self.stop_event = threading.Event()
        
    def start_listening(self, callback: Callable[[str], None]) -> None:
        """Avvia l'ascolto dei badge dalla porta seriale."""
        if not self.port or "Nessun hardware" in self.port:
            return
        try:
            self.conn = serial.Serial(self.port, 9600, timeout=1)
            self.stop_event.clear()
            threading.Thread(target=self._listen, args=(callback,), daemon=True).start()
        except Exception as e:
            print(f"Errore Lettore Seriale: {e}")
            
    def stop(self) -> None:
        """Ferma l'ascolto dei badge."""
        self.stop_event.set()
        if self.conn and self.conn.is_open:
            self.conn.close()
            
    def _listen(self, callback: Callable[[str], None]) -> None:
        """Loop di ascolto dei badge."""
        while not self.stop_event.is_set():
            if self.conn and self.conn.in_waiting > 0:
                try:
                    data = self.conn.readline().decode('utf-8').strip()
                    badge = ''.join(filter(str.isdigit, data))
                    if badge:
                        callback(badge)
                except Exception:
                    pass


# Factory functions per la dependency injection

def get_audio_service(base_path: str) -> IAudioPlayer:
    """Factory function per ottenere un'istanza di IAudioPlayer."""
    return SystemAudioPlayer(base_path)


def get_turnstile_service(port: str) -> ITurnstileHardware:
    """Factory function per ottenere un'istanza di ITurnstileHardware."""
    return USBRelayTurnstile(port)


def get_badge_reader_service(port: str) -> IBadgeReader:
    """Factory function per ottenere un'istanza di IBadgeReader."""
    return SerialBadgeReader(port)


# Classe legacy per compatibilità
class HardwareService:
    """Classe wrapper per compatibilità con il codice esistente."""
    
    @staticmethod
    def get_audio_player(base_path: str) -> IAudioPlayer:
        return get_audio_service(base_path)
    
    @staticmethod
    def get_turnstile(port: str) -> ITurnstileHardware:
        return get_turnstile_service(port)
    
    @staticmethod
    def get_badge_reader(port: str) -> IBadgeReader:
        return get_badge_reader_service(port)
