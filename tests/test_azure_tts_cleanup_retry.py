import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from audio_engine import audio_generator
from audio_engine import azure_tts_client
from audio_engine import file_cleanup
from audio_engine.audio_generator import AudioGenerator
from audio_engine.azure_tts_client import (
    AzureTTSClient,
    AzureTTSGenerationError,
    TransientAzureTTSError,
)


class FakeFuture:

    def __init__(self, outcome):
        self.outcome = outcome

    def get(self):
        if isinstance(self.outcome, Exception):
            raise self.outcome
        return self.outcome


def successful_result():
    return SimpleNamespace(reason="completed")


def canceled_result(error_code, error_details):
    return SimpleNamespace(
        reason="canceled",
        cancellation_details=SimpleNamespace(
            reason="Error",
            error_code=error_code,
            error_details=error_details,
        ),
    )


def make_speech_sdk(outcomes):
    state = SimpleNamespace(
        outcomes=list(outcomes),
        attempts=0,
        paths=[],
        stop_calls=0,
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
            self.audio_config = audio_config

        def speak_ssml_async(self, ssml):
            state.attempts += 1
            path = Path(self.audio_config.filename)
            state.paths.append(path)
            outcome = state.outcomes.pop(0)
            path.write_bytes(
                b"valid mp3"
                if getattr(outcome, "reason", None) == "completed"
                else b"failed partial"
            )
            return FakeFuture(outcome)

        def stop_speaking(self):
            state.stop_calls += 1

    sdk = SimpleNamespace(
        SpeechConfig=SpeechConfig,
        SpeechSynthesizer=SpeechSynthesizer,
        SpeechSynthesisOutputFormat=SimpleNamespace(
            Audio24Khz48KBitRateMonoMp3="mp3"
        ),
        ResultReason=SimpleNamespace(
            SynthesizingAudioCompleted="completed",
            Canceled="canceled",
        ),
        audio=SimpleNamespace(
            AudioOutputConfig=AudioOutputConfig
        ),
    )
    return sdk, state


def make_client():
    client = AzureTTSClient.__new__(AzureTTSClient)
    client.api_key = "test-key"
    client.region = "centralindia"
    return client


def make_word(word="quintessential"):
    return SimpleNamespace(
        word=word,
        meaning="the most typical example",
        present_sentence="This is a quintessential example.",
        past_sentence="It was a quintessential example.",
        future_sentence="It will be a quintessential example.",
        audio_folder=None,
        default_audio=None,
    )


def make_generator():
    generator = AudioGenerator.__new__(AudioGenerator)
    generator.client = Mock()
    generator.pronunciation_service = Mock()
    generator.audio_validator = Mock()
    return generator


class AzureTTSCleanupRetryTests(unittest.TestCase):

    def test_transient_timeout_retries_and_produces_final_audio(self):
        timeout = canceled_result(
            "ServiceTimeout",
            "Timeout while synthesizing. Current RTF: 5.20342",
        )
        sdk, state = make_speech_sdk([
            timeout,
            successful_result(),
        ])
        client = make_client()

        with tempfile.TemporaryDirectory() as folder:
            output_path = (
                Path(folder)
                / "quintessential"
                / "meaning.partial.mp3"
            )

            with (
                patch.object(azure_tts_client, "speechsdk", sdk),
                patch.object(azure_tts_client.time, "sleep") as sleep,
            ):
                client.generate_audio(
                    "the most typical example",
                    output_path,
                    "meaning",
                )

            self.assertEqual(output_path.read_bytes(), b"valid mp3")
            self.assertEqual(state.attempts, 2)
            self.assertEqual(state.stop_calls, 2)
            self.assertEqual(len(set(state.paths)), 2)
            self.assertTrue(
                all(not path.exists() for path in state.paths)
            )
            sleep.assert_called_once_with(1.0)

    def test_repeated_timeout_never_promotes_failed_partial(self):
        timeout = canceled_result(
            "ServiceTimeout",
            "Timeout while synthesizing.",
        )
        sdk, state = make_speech_sdk([
            timeout,
            timeout,
            timeout,
        ])
        client = make_client()

        with tempfile.TemporaryDirectory() as folder:
            output_path = Path(folder) / "meaning.partial.mp3"

            with (
                patch.object(azure_tts_client, "speechsdk", sdk),
                patch.object(azure_tts_client.time, "sleep"),
            ):
                with self.assertRaisesRegex(
                    TransientAzureTTSError,
                    "Timeout while synthesizing",
                ):
                    client.generate_audio(
                        "meaning",
                        output_path,
                        "meaning",
                    )

            self.assertFalse(output_path.exists())
            self.assertEqual(state.attempts, 3)
            self.assertTrue(
                all(not path.exists() for path in state.paths)
            )

    def test_permanent_authentication_failure_is_not_retried(self):
        permanent = canceled_result(
            "AuthenticationFailure",
            "HTTP 401: invalid subscription key.",
        )
        sdk, state = make_speech_sdk([permanent])
        client = make_client()

        with tempfile.TemporaryDirectory() as folder:
            output_path = Path(folder) / "meaning.partial.mp3"

            with (
                patch.object(azure_tts_client, "speechsdk", sdk),
                patch.object(azure_tts_client.time, "sleep") as sleep,
            ):
                with self.assertRaisesRegex(
                    AzureTTSGenerationError,
                    "invalid subscription key",
                ):
                    client.generate_audio(
                        "meaning",
                        output_path,
                        "meaning",
                    )

            self.assertEqual(state.attempts, 1)
            sleep.assert_not_called()
            self.assertFalse(output_path.exists())

    def test_locked_cleanup_retries_are_bounded(self):
        locked = PermissionError(
            13,
            "The process cannot access the file",
        )
        locked.winerror = 32
        output = io.StringIO()

        with (
            patch.object(
                Path,
                "unlink",
                side_effect=locked,
            ) as unlink,
            patch.object(file_cleanup.time, "sleep") as sleep,
            redirect_stdout(output),
        ):
            removed = file_cleanup.safe_unlink(
                Path("meaning.partial.mp3")
            )

        self.assertFalse(removed)
        self.assertEqual(unlink.call_count, 3)
        self.assertEqual(sleep.call_count, 2)
        self.assertIn("cleanup deferred", output.getvalue())

    def test_cleanup_error_does_not_replace_synthesis_error(self):
        generator = make_generator()
        generator.client.generate_audio.side_effect = RuntimeError(
            "Azure speech synthesis failed: Error - "
            "Timeout while synthesizing."
        )
        generator.audio_validator.is_valid_mp3.side_effect = (
            lambda path: Path(path).name
            not in {"meaning.mp3", "meaning.partial.mp3"}
        )
        output = io.StringIO()
        cleanup_calls = 0

        def cleanup(path):
            nonlocal cleanup_calls
            cleanup_calls += 1

            if cleanup_calls == 3:
                raise PermissionError(13, "file is locked")

            return True

        with tempfile.TemporaryDirectory() as folder:
            with (
                patch.object(audio_generator, "safe_unlink", cleanup),
                redirect_stdout(output),
            ):
                generator.generate_word_audio(
                    make_word(),
                    Path(folder),
                )

        self.assertIn("Timeout while synthesizing", output.getvalue())
        self.assertIn("original audio error was preserved", output.getvalue())
        self.assertNotIn("Failed to generate meaning.mp3: [Errno", output.getvalue())

    def test_valid_existing_audio_is_skipped(self):
        generator = make_generator()
        generator.audio_validator.is_valid_mp3.return_value = True

        with tempfile.TemporaryDirectory() as folder:
            generator.generate_word_audio(
                make_word(),
                Path(folder),
            )

        generator.pronunciation_service.generate_verified.assert_not_called()
        generator.client.generate_audio.assert_not_called()

    def test_corrupt_audio_and_stale_partial_regenerate_atomically(self):
        generator = make_generator()

        with tempfile.TemporaryDirectory() as folder:
            audio_folder = (
                Path(folder)
                / "audio"
                / "quintessential"
            )
            audio_folder.mkdir(parents=True)

            for filename in (
                "pronunciation.mp3",
                "present_sentence.mp3",
                "past_sentence.mp3",
                "future_sentence.mp3",
            ):
                (audio_folder / filename).write_bytes(b"valid mp3")

            meaning_path = audio_folder / "meaning.mp3"
            meaning_path.write_bytes(b"corrupt")
            stale_partial = audio_folder / "meaning.partial.mp3"
            stale_partial.write_bytes(b"stale partial")

            generator.audio_validator.is_valid_mp3.side_effect = (
                lambda path: (
                    Path(path).is_file()
                    and Path(path).read_bytes() == b"valid mp3"
                )
            )
            generator.client.generate_audio.side_effect = (
                lambda text, output_path, audio_type: (
                    Path(output_path).write_bytes(b"valid mp3")
                )
            )

            generator.generate_word_audio(
                make_word(),
                Path(folder),
            )

            self.assertEqual(
                meaning_path.read_bytes(),
                b"valid mp3",
            )
            self.assertFalse(stale_partial.exists())
            self.assertEqual(
                generator.client.generate_audio.call_count,
                1,
            )


if __name__ == "__main__":
    unittest.main()
