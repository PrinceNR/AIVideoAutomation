from pathlib import Path

from audio_engine.elevenlabs_client import ElevenLabsClient
from models.word import Word


class AudioGenerator:

    def __init__(self):
        self.client = ElevenLabsClient()

    def generate_word_audio(
        self,
        word: Word,
        lesson_folder: Path
    ):

        audio_folder = lesson_folder / "audio" / word.word.lower()

        audio_folder.mkdir(
            parents=True,
            exist_ok=True
        )

        audio_tasks = {
            "pronunciation.mp3": word.word,
            "meaning.mp3": word.meaning,
            "present_sentence.mp3": word.present_sentence,
            "past_sentence.mp3": word.past_sentence,
            "future_sentence.mp3": word.future_sentence,
        }
        for filename, text in audio_tasks.items():

            try:
                self.client.generate_audio(
                    text=text,
                    output_path=audio_folder / filename
                )
            except Exception as e:
                print(f"Failed to generate {filename}: {e}")

