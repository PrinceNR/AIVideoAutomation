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
        # Generate pronunciation
        self.client.generate_audio(
            text=word.word,
            output_path=audio_folder / "pronunciation.mp3"
        )

        # Generate sentence audio
        for index, sentence in enumerate(word.sentences, start=1):

            filename = f"sentence{index}.mp3"

            self.client.generate_audio(
                text=sentence,
                output_path=audio_folder / filename
            )


        print(f"Finished downloading audio for {word.word}")