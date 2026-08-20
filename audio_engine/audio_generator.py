from pathlib import Path

from audio_engine.tts_client_factory import (
    TTSClientFactory
)

from audio_engine.pronunciation_service import (
    PronunciationService
)

from models.word import Word


class AudioGenerator:

    def __init__(self):

        self.client = (
            TTSClientFactory.create()
        )

        self.pronunciation_service = (
            PronunciationService()
        )

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

        self.pronunciation_service.generate_verified(
            word=word.word,
            output_path=pronunciation_path
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

            try:

                self.client.generate_audio(
                    text=text,
                    output_path=(
                        audio_folder
                        / filename
                    ),
                    audio_type=audio_type
                )

            except Exception as e:

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