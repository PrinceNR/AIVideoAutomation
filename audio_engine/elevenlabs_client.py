from pathlib import Path

from elevenlabs.client import ElevenLabs
from dotenv import load_dotenv

import os

load_dotenv()


class ElevenLabsClient:

    def __init__(self):

        self.api_key = os.getenv("ELEVENLABS_API_KEY")

        if not self.api_key:
         raise ValueError("ELEVENLABS_API_KEY not found in .env")

        self.client = ElevenLabs(
             api_key=self.api_key
        )
            

    def generate_audio(
        self,
        text: str,
        output_path: Path,
        audio_type: str = "sentence"
    ):

        audio = self.client.text_to_speech.convert(
            voice_id="Xb7hH8MSUJpSbSDYk0k2",
            model_id="eleven_multilingual_v2",
            text=text
        )

        with open(output_path, "wb") as file:
            for chunk in audio:
                file.write(chunk)

        print(f"Generated: {output_path}")

    

