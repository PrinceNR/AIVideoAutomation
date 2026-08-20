from config import TTS_PROVIDER

from audio_engine.azure_tts_client import (
    AzureTTSClient
)

from audio_engine.elevenlabs_client import (
    ElevenLabsClient
)


class TTSClientFactory:

    @staticmethod
    def create():

        provider = (
            TTS_PROVIDER
            .strip()
            .lower()
        )

        if provider == "azure":

            print(
                "TTS provider: Azure Speech"
            )

            return AzureTTSClient()

        if provider == "elevenlabs":

            print(
                "TTS provider: ElevenLabs"
            )

            return ElevenLabsClient()

        raise ValueError(
            f"Unsupported TTS provider: "
            f"{TTS_PROVIDER}"
        )