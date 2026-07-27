from elevenlabs.client import ElevenLabs
from dotenv import load_dotenv
import os

load_dotenv()

client = ElevenLabs(
    api_key=os.getenv("ELEVENLABS_API_KEY")
)

voices = client.voices.get_all()

for voice in voices.voices:
    print(f"{voice.name} -> {voice.voice_id}")