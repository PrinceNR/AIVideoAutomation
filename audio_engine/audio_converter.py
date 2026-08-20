from pathlib import Path
import shutil
import subprocess


class AudioConverter:

    def __init__(self):

        if not shutil.which("ffmpeg"):
            raise RuntimeError(
                "FFmpeg was not found in PATH"
            )

    def wav_to_mp3(
        self,
        input_path: Path,
        output_path: Path
    ):

        input_path = Path(input_path)
        output_path = Path(output_path)

        if not input_path.exists():
            raise FileNotFoundError(
                f"Input audio not found: "
                f"{input_path}"
            )

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        command = [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",

            "-i",
            str(input_path),

            "-codec:a",
            "libmp3lame",

            "-b:a",
            "128k",

            str(output_path)
        ]

        try:

            subprocess.run(
                command,
                check=True
            )

        except subprocess.CalledProcessError as e:

            raise RuntimeError(
                f"Audio conversion failed: {e}"
            ) from e

        if not output_path.exists():
            raise RuntimeError(
                "FFmpeg completed but output "
                "file was not created"
            )

        print(
            f"Audio converted: "
            f"{input_path.name} "
            f"-> {output_path.name}"
        )