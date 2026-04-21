"""Audio service module (legacy compatibility)."""

from core.services.hardware_service import IAudioPlayer, SystemAudioPlayer, get_audio_service

# Alias per compatibilità
AudioService = HardwareService = type('HardwareService', (), {
    'get_audio_player': staticmethod(get_audio_service)
})

__all__ = ["IAudioPlayer", "SystemAudioPlayer", "get_audio_service", "AudioService"]
