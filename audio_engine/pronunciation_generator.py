from pathlib import Path
from xml.sax.saxutils import escape

import os

from dotenv import load_dotenv
import azure.cognitiveservices.speech as speechsdk

from config import (
    AZURE_PRONUNCIATION_VOICE,
    PRONUNCIATION_RATE
)


load_dotenv()


class PronunciationGenerator:

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

    def generate(
        self,
        word: str,
        output_path: Path
    ):

        output_path = Path(
            output_path
        )

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        speech_config = speechsdk.SpeechConfig(
            subscription=self.api_key,
            region=self.region
        )

        speech_config.set_speech_synthesis_output_format(
            speechsdk
            .SpeechSynthesisOutputFormat
            .Riff24Khz16BitMonoPcm
        )

        audio_config = (
            speechsdk.audio.AudioOutputConfig(
                filename=str(output_path)
            )
        )

        synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=speech_config,
            audio_config=audio_config
        )

        safe_word = escape(
            word
        )

        ssml = f"""
<speak
    version="1.0"
    xmlns="http://www.w3.org/2001/10/synthesis"
    xml:lang="en-IN">

    <voice name="{AZURE_PRONUNCIATION_VOICE}">

        <prosody rate="{PRONUNCIATION_RATE}">
            {safe_word}
        </prosody>

        <break time="400ms"/>

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
                f"Pronunciation generated: "
                f"{output_path}"
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
                "Pronunciation generation failed: "
                f"{cancellation.reason} - "
                f"{cancellation.error_details}"
            )

        raise RuntimeError(
            "Pronunciation generation failed: "
            f"{result.reason}"
        )