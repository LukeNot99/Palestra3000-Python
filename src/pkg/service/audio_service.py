import os
import platform
import subprocess
import logging
from abc import ABC, abstractmethod
from ..utility.utils import resource_path

logger = logging.getLogger(__name__)

class IAudioPlayer(ABC):
    @abstractmethod
    def play(self, file_name: str): pass

class SystemAudioPlayer(IAudioPlayer):
    def __init__(self, base_path: str):
        self.base_path = base_path
        
    def play(self, file_name: str):
        # Usa resource_path per gestire correttamente PyInstaller
        audio_path = resource_path(os.path.join("messaggi", file_name))
        
        if not os.path.exists(audio_path): 
            logger.warning(f"File audio non trovato: {audio_path}")
            return
            
        os_name = platform.system()
        if os_name == "Windows":
            import winsound
            flags = winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_NODEFAULT
            winsound.PlaySound(audio_path, flags)
        elif os_name == "Darwin":
            subprocess.Popen(["afplay", audio_path])
