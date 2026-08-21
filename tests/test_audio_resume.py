import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from audio_engine.audio_file_validator import AudioFileValidator
from audio_engine.audio_generator import AudioGenerator


class AudioResumeTests(unittest.TestCase):

    def test_validator_rejects_zero_byte_and_decode_failure(self):
        with tempfile.TemporaryDirectory() as folder:
            audio_path = Path(folder) / "audio.mp3"
            audio_path.write_bytes(b"")
            self.assertFalse(AudioFileValidator.is_valid_mp3(audio_path))

            audio_path.write_bytes(b"not an mp3")
            with patch(
                "audio_engine.audio_file_validator.shutil.which",
                return_value="ffprobe"
            ), patch(
                "audio_engine.audio_file_validator.subprocess.run"
            ) as run:
                run.return_value = SimpleNamespace(
                    returncode=1,
                    stdout=""
                )
                self.assertFalse(
                    AudioFileValidator.is_valid_mp3(audio_path)
                )

    def test_reuses_valid_files_and_regenerates_invalid_file(self):
        with tempfile.TemporaryDirectory() as folder:
            generator = AudioGenerator.__new__(AudioGenerator)
            generator.client = Mock()
            generator.pronunciation_service = Mock()
            generator.audio_validator = Mock()

            valid_paths = {
                "pronunciation.mp3",
                "meaning.mp3",
                "present_sentence.mp3",
                "past_sentence.mp3",
                "future_sentence.partial.mp3"
            }
            generator.audio_validator.is_valid_mp3.side_effect = (
                lambda path: Path(path).name in valid_paths
            )

            def generate_audio(text, output_path, audio_type):
                Path(output_path).write_bytes(b"complete mp3")

            generator.client.generate_audio.side_effect = generate_audio
            word = SimpleNamespace(
                word="hesitate",
                meaning="meaning",
                present_sentence="present",
                past_sentence="past",
                future_sentence="future",
                audio_folder=None,
                default_audio=None
            )

            generator.generate_word_audio(word, Path(folder))

            generator.pronunciation_service.generate_verified.assert_not_called()
            generator.client.generate_audio.assert_called_once()
            self.assertEqual(
                generator.client.generate_audio.call_args.kwargs["text"],
                "future"
            )
            self.assertTrue(
                (Path(folder) / "audio" / "hesitate" /
                 "future_sentence.mp3").is_file()
            )

    def test_pronunciation_failure_is_controlled(self):
        with tempfile.TemporaryDirectory() as folder:
            generator = AudioGenerator.__new__(AudioGenerator)
            generator.client = Mock()
            generator.pronunciation_service = Mock()
            generator.pronunciation_service.generate_verified.side_effect = (
                RuntimeError("verification canceled")
            )
            generator.audio_validator = Mock()
            generator.audio_validator.is_valid_mp3.return_value = False
            word = SimpleNamespace(
                word="hesitate",
                meaning="meaning",
                present_sentence="present",
                past_sentence="past",
                future_sentence="future",
                audio_folder=None,
                default_audio=None
            )

            generator.generate_word_audio(word, Path(folder))

            self.assertFalse(
                (Path(folder) / "audio" / "hesitate" /
                 "pronunciation.mp3").exists()
            )


if __name__ == "__main__":
    unittest.main()
