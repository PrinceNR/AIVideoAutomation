from pathlib import Path
import shutil
import subprocess


class AudioFileValidator:

    @staticmethod
    def is_valid_mp3(audio_path: Path) -> bool:

        audio_path = Path(audio_path)

        try:
            if (
                not audio_path.is_file()
                or audio_path.stat().st_size == 0
            ):
                return False
        except OSError:
            return False

        ffprobe = shutil.which("ffprobe")

        if not ffprobe:
            return False

        result = subprocess.run(
            [
                ffprobe,
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                str(audio_path)
            ],
            capture_output=True,
            text=True,
            check=False
        )

        if result.returncode != 0:
            return False

        try:
            return float(result.stdout.strip()) > 0
        except (TypeError, ValueError):
            return False
