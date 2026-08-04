from pathlib import Path
from mutagen.mp3 import MP3


class AudioDurationCalculator:

    def get_duration(
        self,
        audio_path: str | Path
    ) -> float:

        audio = MP3(str(audio_path))

        return audio.info.length