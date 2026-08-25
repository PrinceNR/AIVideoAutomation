import json
from pathlib import Path
import shutil
import subprocess
from uuid import uuid4

from presentation.presentation_logger import (
    presentation_logger as log,
)


class PresentationVideoError(RuntimeError):
    """Raised when a visual video cannot be made safe for PowerPoint."""


class SilentVideoNormalizer:
    """Creates cached H.264 MP4 visuals with no audio stream."""

    def __init__(
        self,
        runner=None,
        executable_finder=None,
    ):
        self.runner = runner or subprocess.run
        self.executable_finder = (
            executable_finder or shutil.which
        )
        self._prepared = {}

    def prepare(self, source_path: str | Path) -> Path:
        source = Path(source_path).resolve()

        if not source.is_file():
            raise PresentationVideoError(
                f"Presentation video not found: {source}"
            )

        cached = self._prepared.get(source)

        if cached is not None and cached.is_file():
            return cached

        ffmpeg = self.executable_finder("ffmpeg")
        ffprobe = self.executable_finder("ffprobe")

        if not ffmpeg or not ffprobe:
            raise PresentationVideoError(
                "FFmpeg and ffprobe are required to prepare "
                "silent PowerPoint video visuals."
            )

        source_stat = source.stat()
        fingerprint = (
            f"{source_stat.st_mtime_ns}-{source_stat.st_size}"
        )
        output = source.with_name(
            f"{source.stem}.powerpoint-silent-"
            f"{fingerprint}.mp4"
        )

        if self._is_silent_video(output, ffprobe):
            self._prepared[source] = output
            log.detail(
                f"Reusing silent presentation video: {output.name}"
            )
            return output

        temporary = output.with_name(
            f"{output.stem}.{uuid4().hex}.partial.mp4"
        )
        command = [
            ffmpeg,
            "-nostdin",
            "-y",
            "-loglevel",
            "error",
            "-i",
            str(source),
            "-map",
            "0:v:0",
            "-an",
            "-c:v",
            "libx264",
            "-preset",
            "fast",
            "-crf",
            "18",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            str(temporary),
        ]

        try:
            result = self.runner(
                command,
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode != 0:
                detail = (result.stderr or "").strip()[-300:]
                raise PresentationVideoError(
                    "FFmpeg could not create a silent PowerPoint "
                    f"video from '{source.name}': {detail}"
                )

            if not self._is_silent_video(
                temporary,
                ffprobe,
            ):
                raise PresentationVideoError(
                    "Prepared PowerPoint video is missing its "
                    "visual stream or still contains audio."
                )

            temporary.replace(output)
            self._prepared[source] = output
            log.detail(
                f"Prepared silent presentation video: {output.name}"
            )
            return output

        except OSError as error:
            raise PresentationVideoError(
                f"Could not prepare presentation video "
                f"'{source.name}': {error}"
            ) from error
        finally:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass

    def _is_silent_video(self, path, ffprobe):
        path = Path(path)

        if not path.is_file() or path.stat().st_size <= 0:
            return False

        result = self.runner(
            [
                ffprobe,
                "-v",
                "error",
                "-show_entries",
                "stream=codec_type",
                "-of",
                "json",
                str(path),
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode != 0:
            return False

        try:
            stream_types = {
                stream.get("codec_type")
                for stream in json.loads(
                    result.stdout or "{}"
                ).get("streams", [])
            }
        except (json.JSONDecodeError, AttributeError):
            return False

        return "video" in stream_types and "audio" not in stream_types
