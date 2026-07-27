from pathlib import Path
from audio_engine.elevenlabs_client import ElevenLabsClient


client = ElevenLabsClient()

client.generate_audio(
    text = "Hello World",
    output_path = Path("hello.mp3")
)

