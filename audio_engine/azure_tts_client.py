from pathlib import Path
import gc
import os
import time
from uuid import uuid4
from xml.sax.saxutils import escape

from dotenv import load_dotenv
import azure.cognitiveservices.speech as speechsdk

from audio_engine.file_cleanup import safe_unlink
from config import (
    AZURE_NARRATION_VOICE,
    AZURE_NARRATION_RATE,
)


load_dotenv()


class AzureTTSGenerationError(RuntimeError):
    pass


class TransientAzureTTSError(AzureTTSGenerationError):
    pass


class AzureTTSClient:

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

    def generate_audio(
        self,
        text: str,
        output_path: Path,
        audio_type: str = "sentence",
    ):

        output_path = Path(output_path)
        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        context = self._audio_context(
            output_path,
            audio_type,
        )

        for attempt in range(
            1,
            self.MAX_ATTEMPTS + 1,
        ):
            attempt_path = self._attempt_path(
                output_path
            )

            try:
                self._synthesize_once(
                    text,
                    attempt_path,
                )
            except TransientAzureTTSError as error:
                safe_unlink(attempt_path)

                if attempt >= self.MAX_ATTEMPTS:
                    raise error from None

                print(
                    f"Azure TTS {self._transient_label(error)} "
                    f"for {context}; retrying "
                    f"{attempt}/{self.MAX_ATTEMPTS - 1}..."
                )
                time.sleep(
                    self.BACKOFF_SECONDS * attempt
                )
                continue
            except Exception:
                safe_unlink(attempt_path)
                raise

            if not safe_unlink(output_path):
                safe_unlink(attempt_path)
                raise AzureTTSGenerationError(
                    "Azure synthesis succeeded, but the partial "
                    "audio destination is still locked."
                )

            try:
                attempt_path.replace(output_path)
            except Exception:
                safe_unlink(attempt_path)
                raise

            print(
                f"Generated: {output_path}"
            )
            return

    def _synthesize_once(
        self,
        text,
        output_path,
    ):
        synthesizer = None
        future = None
        result = None

        try:
            speech_config = speechsdk.SpeechConfig(
                subscription=self.api_key,
                region=self.region,
            )
            speech_config.set_speech_synthesis_output_format(
                speechsdk
                .SpeechSynthesisOutputFormat
                .Audio24Khz48KBitRateMonoMp3
            )
            audio_config = speechsdk.audio.AudioOutputConfig(
                filename=str(output_path)
            )
            synthesizer = speechsdk.SpeechSynthesizer(
                speech_config=speech_config,
                audio_config=audio_config,
            )
            safe_text = escape(text)
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
            future = synthesizer.speak_ssml_async(ssml)
            result = future.get()

            if (
                result.reason
                == speechsdk.ResultReason
                .SynthesizingAudioCompleted
            ):
                return

            if (
                result.reason
                == speechsdk.ResultReason.Canceled
            ):
                cancellation = result.cancellation_details
                reason = getattr(
                    cancellation,
                    "reason",
                    "Error",
                )
                error_code = getattr(
                    cancellation,
                    "error_code",
                    "",
                )
                error_details = getattr(
                    cancellation,
                    "error_details",
                    "",
                )
                details = " ".join(
                    part
                    for part in (
                        str(error_code).strip(),
                        str(error_details).strip(),
                    )
                    if part
                )
                message = (
                    "Azure speech synthesis failed: "
                    f"{reason} - "
                    f"{self._concise_error(details)}"
                )

                if self._is_transient_failure(details):
                    raise TransientAzureTTSError(message)

                raise AzureTTSGenerationError(message)

            raise AzureTTSGenerationError(
                "Azure speech synthesis failed "
                f"with result: {result.reason}"
            )

        except AzureTTSGenerationError:
            raise
        except Exception as error:
            details = self._concise_error(error)

            if self._is_transient_failure(details):
                raise TransientAzureTTSError(
                    "Azure speech synthesis failed: "
                    f"{details}"
                ) from None

            raise AzureTTSGenerationError(
                "Azure speech synthesis request failed "
                "permanently: "
                f"{details}"
            ) from None
        finally:
            if synthesizer is not None:
                stop_speaking = getattr(
                    synthesizer,
                    "stop_speaking",
                    None,
                )

                if callable(stop_speaking):
                    try:
                        stop_speaking()
                    except Exception:
                        pass

            result = None
            future = None
            synthesizer = None
            gc.collect()

    @staticmethod
    def _attempt_path(output_path):
        return output_path.with_name(
            f"{output_path.stem}.azure."
            f"{uuid4().hex}.mp3"
        )

    @staticmethod
    def _audio_context(output_path, audio_type):
        stem = output_path.stem.split(".partial", 1)[0]
        label = stem or str(audio_type)
        return f"{output_path.parent.name}/{label}"

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
            "invalid voice",
            "bad request",
            "invalid argument",
            "http 400",
            "http 401",
            "http 403",
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
            "timeout",
            "server disconnected",
        )
        return any(
            marker in text
            for marker in transient_markers
        )

    @staticmethod
    def _transient_label(error):
        return (
            "timeout"
            if "timeout" in str(error).lower()
            or "timed out" in str(error).lower()
            else "connection failure"
        )

    @staticmethod
    def _concise_error(details):
        text = " ".join(
            str(details).split()
        )

        if len(text) <= 300:
            return text

        return text[:297] + "..."
