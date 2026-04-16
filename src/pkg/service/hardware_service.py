import time
import serial
import threading
from abc import ABC, abstractmethod

class ITurnstileHardware(ABC):
    @abstractmethod
    def open_gate(self): pass

class IBadgeReader(ABC):
    @abstractmethod
    def start_listening(self, callback): pass
    
    @abstractmethod
    def stop(self): pass


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
