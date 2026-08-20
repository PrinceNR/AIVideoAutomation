from pathlib import Path
from xml.sax.saxutils import escape

import os
import time

from dotenv import load_dotenv
import azure.cognitiveservices.speech as speechsdk

from config import (
    AZURE_PRONUNCIATION_VOICE,
    PRONUNCIATION_RATE
)


load_dotenv()


class PronunciationGenerationError(RuntimeError):
    pass


class TransientPronunciationError(
    PronunciationGenerationError
):
    pass


class PronunciationGenerator:

    MAX_ATTEMPTS = 3
    BACKOFF_SECONDS = 1.0

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

        for attempt in range(
            1,
            self.MAX_ATTEMPTS + 1
        ):

            try:
                self._generate_once(
                    word,
                    output_path
                )
                return

            except Exception as error:
                if not isinstance(
                    error,
                    PronunciationGenerationError
                ):
                    details = self._concise_error(
                        error
                    )

                    if self._is_transient_failure(
                        details
                    ):
                        error = TransientPronunciationError(
                            details
                        )
                    else:
                        error = PronunciationGenerationError(
                            "Azure pronunciation request "
                            "failed permanently: "
                            f"{details}"
                        )

                output_path.unlink(
                    missing_ok=True
                )

                if not isinstance(
                    error,
                    TransientPronunciationError
                ):
                    raise error from None

                if attempt >= self.MAX_ATTEMPTS:
                    raise PronunciationGenerationError(
                        "Azure pronunciation generation "
                        "failed after "
                        f"{self.MAX_ATTEMPTS} transient "
                        "connection attempts. Check the "
                        "network and DNS connection. "
                        f"Last error: {error}"
                    ) from None

                delay = (
                    self.BACKOFF_SECONDS
                    * attempt
                )

                print(
                    "Azure pronunciation connection "
                    f"failed for '{word}'. "
                    f"Retrying in {delay:g}s "
                    f"({attempt + 1}/"
                    f"{self.MAX_ATTEMPTS})..."
                )

                time.sleep(delay)

    def _generate_once(
        self,
        word: str,
        output_path: Path
    ):

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

        try:
            result = (
                synthesizer
                .speak_ssml_async(ssml)
                .get()
            )
        except Exception as error:
            details = str(error)

            if self._is_transient_failure(
                details
            ):
                raise TransientPronunciationError(
                    self._concise_error(details)
                ) from None

            raise PronunciationGenerationError(
                "Azure pronunciation request "
                "failed permanently: "
                f"{self._concise_error(details)}"
            ) from None

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

            error_code = getattr(
                cancellation,
                "error_code",
                ""
            )
            error_details = getattr(
                cancellation,
                "error_details",
                ""
            )
            details = (
                f"{error_code} {error_details}"
            ).strip()

            if self._is_transient_failure(
                details
            ):
                raise TransientPronunciationError(
                    self._concise_error(details)
                )

            raise PronunciationGenerationError(
                "Azure pronunciation request was "
                "rejected and will not be retried: "
                f"{self._concise_error(details)}"
            )

        raise PronunciationGenerationError(
            "Azure pronunciation generation failed "
            "with unexpected result: "
            f"{result.reason}"
        )

    @staticmethod
    def _is_transient_failure(details):

        text = str(details).lower()

        permanent_markers = (
            "authenticationfailure",
            "authentication failure",
            "unauthorized",
            "forbidden",
            "invalid subscription",
            "invalid key",
            "invalid region",
            "401",
            "403"
        )

        if any(
            marker in text
            for marker in permanent_markers
        ):
            return False

        transient_markers = (
            "connectionfailure",
            "connection failed",
            "no connection to the remote host",
            "dns resolution failed",
            "ws_open_error",
            "websocket",
            "service timeout",
            "servicetimeout",
            "service unavailable",
            "serviceunavailable",
            "timed out",
            "timeout"
        )

        return any(
            marker in text
            for marker in transient_markers
        )

    @staticmethod
    def _concise_error(details):

        text = " ".join(
            str(details).split()
        )

        if len(text) <= 300:
            return text

        return text[:297] + "..."
