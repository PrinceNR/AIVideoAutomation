from pathlib import Path
import os
from xml.sax.saxutils import escape

from dotenv import load_dotenv
import azure.cognitiveservices.speech as speechsdk

from config import (
    AZURE_NARRATION_VOICE,
    AZURE_NARRATION_RATE
)


load_dotenv()


class AzureTTSClient:

    def __init__(self):

        self.api_key = os.getenv(
            "AZURE_SPEECH_KEY"
        )

        self.region = os.getenv(
            "AZURE_SPEECH_REGION"
        )

        if not self.api_key:
            raise ValueError(
                "AZURE_SPEECH_KEY not found in .env"
            )

        if not self.region:
            raise ValueError(
                "AZURE_SPEECH_REGION not found in .env"
            )

    def generate_audio(
        self,
        text: str,
        output_path: Path,
        audio_type: str = "sentence"
    ):

        output_path = Path(
            output_path
        )

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        speech_config = (
            speechsdk.SpeechConfig(
                subscription=self.api_key,
                region=self.region
            )
        )

        speech_config.set_speech_synthesis_output_format(
            speechsdk
            .SpeechSynthesisOutputFormat
            .Audio24Khz48KBitRateMonoMp3
        )

        audio_config = (
            speechsdk.audio.AudioOutputConfig(
                filename=str(output_path)
            )
        )

        synthesizer = (
            speechsdk.SpeechSynthesizer(
                speech_config=speech_config,
                audio_config=audio_config
            )
        )

        safe_text = escape(
            text
        )

        ssml = f"""
<speak
    version="1.0"
    xmlns="http://www.w3.org/2001/10/synthesis"
    xml:lang="en-IN">

    <voice name="{AZURE_NARRATION_VOICE}">

        <prosody rate="{AZURE_NARRATION_RATE}">
            {safe_text}
        </prosody>

    </voice>

</speak>
"""

        result = (
            synthesizer
            .speak_ssml_async(ssml)
            .get()
        )

        if (
            result.reason
            == speechsdk.ResultReason
            .SynthesizingAudioCompleted
        ):

            print(
                f"Generated: {output_path}"
            )

            return

        if (
            result.reason
            == speechsdk.ResultReason.Canceled
        ):

            cancellation = (
                result.cancellation_details
            )

            raise RuntimeError(
                "Azure speech synthesis failed: "
                f"{cancellation.reason} - "
                f"{cancellation.error_details}"
            )

        raise RuntimeError(
            "Azure speech synthesis failed "
            f"with result: {result.reason}"
        )