from pathlib import Path
from uuid import uuid4

from audio_engine.tts_client_factory import (
    TTSClientFactory
)

from audio_engine.pronunciation_service import (
    PronunciationService
)
from audio_engine.audio_file_validator import (
    AudioFileValidator
)
from audio_engine.file_cleanup import safe_unlink

from models.word import Word


class AudioGenerator:

    def __init__(self):

        self.client = (
            TTSClientFactory.create()
        )

        self.pronunciation_service = (
            PronunciationService()
        )

        self.audio_validator = AudioFileValidator()

    def generate_word_audio(
        self,
        word: Word,
        lesson_folder: Path
    ):

        audio_folder = (
            lesson_folder
            / "audio"
            / word.word.lower()
        )

        audio_folder.mkdir(
            parents=True,
            exist_ok=True
        )

        # ---------------------------------
        # VERIFIED WORD PRONUNCIATION
        # ---------------------------------

        pronunciation_path = (
            audio_folder
            / "pronunciation.mp3"
        )

        if self.audio_validator.is_valid_mp3(
            pronunciation_path
        ):
            print(
                "Skipping pronunciation for "
                f"{word.word}; existing audio is valid."
            )
        else:
            safe_unlink(pronunciation_path)
            temporary_path = self._temporary_path(
                pronunciation_path
            )

            try:
                self.pronunciation_service.generate_verified(
                    word=word.word,
                    output_path=temporary_path
                )

                if not self.audio_validator.is_valid_mp3(
                    temporary_path
                ):
                    raise RuntimeError(
                        "generated pronunciation audio "
                        "is invalid"
                    )

                temporary_path.replace(
                    pronunciation_path
                )
            except Exception as error:
                self._cleanup_after_failure(
                    temporary_path
                )
                print(
                    "Pronunciation generation failed for "
                    f"{word.word}: {error}"
                )

        # ---------------------------------
        # NORMAL NARRATION
        # ---------------------------------

        audio_tasks = {
            "meaning.mp3": (
                word.meaning,
                "meaning"
            ),

            "present_sentence.mp3": (
                word.present_sentence,
                "sentence"
            ),

            "past_sentence.mp3": (
                word.past_sentence,
                "sentence"
            ),

            "future_sentence.mp3": (
                word.future_sentence,
                "sentence"
            ),
        }

        for filename, (
            text,
            audio_type
        ) in audio_tasks.items():

            output_path = audio_folder / filename

            if self.audio_validator.is_valid_mp3(
                output_path
            ):
                print(
                    f"Skipping {filename} for "
                    f"{word.word}; existing audio is valid."
                )
                continue

            safe_unlink(output_path)
            temporary_path = self._temporary_path(
                output_path
            )

            try:

                self.client.generate_audio(
                    text=text,
                    output_path=temporary_path,
                    audio_type=audio_type
                )

                if not self.audio_validator.is_valid_mp3(
                    temporary_path
                ):
                    raise RuntimeError(
                        "generated audio is invalid"
                    )

                temporary_path.replace(output_path)

            except Exception as e:
                self._cleanup_after_failure(
                    temporary_path
                )

                print(
                    f"Failed to generate "
                    f"{filename}: {e}"
                )

        word.audio_folder = str(
            audio_folder
        )

        word.default_audio = str(
            pronunciation_path
        )

    @staticmethod
    def _temporary_path(output_path):
        output_path = Path(output_path)
        deterministic_path = output_path.with_name(
            f"{output_path.stem}.partial.mp3"
        )

        if safe_unlink(deterministic_path):
            return deterministic_path

        return output_path.with_name(
            f"{output_path.stem}.partial."
            f"{uuid4().hex}.mp3"
        )

    @staticmethod
    def _cleanup_after_failure(temporary_path):
        try:
            safe_unlink(temporary_path)
        except Exception:
            # Cleanup must never replace the synthesis/validation error.
            print(
                "WARNING: Temporary audio cleanup failed; "
                "the original audio error was preserved."
            )
