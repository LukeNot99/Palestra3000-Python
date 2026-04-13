import os
import platform
import subprocess
from abc import ABC, abstractmethod

class IAudioPlayer(ABC):
    @abstractmethod
    def play(self, file_name: str): pass

class SystemAudioPlayer(IAudioPlayer):
    def __init__(self, base_path: str):
        self.base_path = base_path
        
    def play(self, file_name: str):
        # Forza un percorso assoluto compatibile con Windows
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
