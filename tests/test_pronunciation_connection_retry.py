import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from audio_engine import pronunciation_generator
from audio_engine.pronunciation_generator import (
    PronunciationGenerationError,
    PronunciationGenerator
)


class FakeAsyncResult:

    def __init__(self, outcome):
        self.outcome = outcome

    def get(self):
        if isinstance(self.outcome, Exception):
            raise self.outcome
        return self.outcome


def make_speech_sdk(outcomes):
    state = SimpleNamespace(
        outcomes=list(outcomes),
        attempts=0,
        ssml=[]
    )

    class SpeechConfig:
        def __init__(self, subscription, region):
            self.subscription = subscription
            self.region = region

        def set_speech_synthesis_output_format(self, value):
            self.output_format = value

    class AudioOutputConfig:
        def __init__(self, filename):
            self.filename = filename

    class SpeechSynthesizer:
        def __init__(self, speech_config, audio_config):
            self.speech_config = speech_config
            self.audio_config = audio_config

        def speak_ssml_async(self, ssml):
            state.attempts += 1
            state.ssml.append(ssml)
            return FakeAsyncResult(
                state.outcomes.pop(0)
            )

    sdk = SimpleNamespace(
        SpeechConfig=SpeechConfig,
        SpeechSynthesizer=SpeechSynthesizer,
        SpeechSynthesisOutputFormat=SimpleNamespace(
            Riff24Khz16BitMonoPcm="wav"
        ),
        ResultReason=SimpleNamespace(
            SynthesizingAudioCompleted="completed",
            Canceled="canceled"
        ),
        audio=SimpleNamespace(
            AudioOutputConfig=AudioOutputConfig
        )
    )

    return sdk, state


def successful_result():
    return SimpleNamespace(
        reason="completed"
    )


def canceled_result(
    error_code,
    error_details
):
    return SimpleNamespace(
        reason="canceled",
        cancellation_details=SimpleNamespace(
            reason="Error",
            error_code=error_code,
            error_details=error_details
        )
    )


def make_generator():
    generator = PronunciationGenerator.__new__(
        PronunciationGenerator
    )
    generator.api_key = "test-key"
    generator.region = "centralindia"
    return generator


class PronunciationConnectionRetryTests(unittest.TestCase):

    def _generate(self, outcomes):
        sdk, state = make_speech_sdk(outcomes)
        generator = make_generator()

        with tempfile.TemporaryDirectory() as folder:
            output_path = Path(folder) / "verification.wav"

            with (
                patch.object(
                    pronunciation_generator,
                    "speechsdk",
                    sdk
                ),
                patch.object(
                    pronunciation_generator.time,
                    "sleep"
                ) as sleep
            ):
                generator.generate(
                    "passionate",
                    output_path
                )

        return state, sleep

    def test_success_uses_one_attempt(self):
        state, sleep = self._generate([
            successful_result()
        ])

        self.assertEqual(state.attempts, 1)
        sleep.assert_not_called()

    def test_transient_dns_failure_retries_then_succeeds(self):
        transient = canceled_result(
            "ConnectionFailure",
            (
                "Connection failed (no connection to the "
                "remote host). "
                "WS_OPEN_ERROR_UNDERLYING_IO_OPEN_FAILED. "
                "DNS resolution failed."
            )
        )

        state, sleep = self._generate([
            transient,
            successful_result()
        ])

        self.assertEqual(state.attempts, 2)
        sleep.assert_called_once_with(1.0)

    def test_repeated_transient_failures_stop_at_limit(self):
        transient = canceled_result(
            "ConnectionFailure",
            "DNS resolution failed."
        )
        sdk, state = make_speech_sdk([
            transient,
            transient,
            transient
        ])
        generator = make_generator()

        with tempfile.TemporaryDirectory() as folder:
            output_path = Path(folder) / "verification.wav"

            with (
                patch.object(
                    pronunciation_generator,
                    "speechsdk",
                    sdk
                ),
                patch.object(
                    pronunciation_generator.time,
                    "sleep"
                ) as sleep
            ):
                with self.assertRaisesRegex(
                    PronunciationGenerationError,
                    "failed after 3 transient"
                ):
                    generator.generate(
                        "passionate",
                        output_path
                    )

        self.assertEqual(state.attempts, 3)
        self.assertEqual(
            [call.args[0] for call in sleep.call_args_list],
            [1.0, 2.0]
        )

    def test_authentication_failure_is_not_retried(self):
        permanent = canceled_result(
            "AuthenticationFailure",
            "HTTP 401: invalid subscription key."
        )
        sdk, state = make_speech_sdk([
            permanent
        ])
        generator = make_generator()

        with tempfile.TemporaryDirectory() as folder:
            output_path = Path(folder) / "verification.wav"

            with (
                patch.object(
                    pronunciation_generator,
                    "speechsdk",
                    sdk
                ),
                patch.object(
                    pronunciation_generator.time,
                    "sleep"
                ) as sleep
            ):
                with self.assertRaisesRegex(
                    PronunciationGenerationError,
                    "will not be retried"
                ):
                    generator.generate(
                        "passionate",
                        output_path
                    )

        self.assertEqual(state.attempts, 1)
        sleep.assert_not_called()


if __name__ == "__main__":
    unittest.main()
