from pathlib import Path

import cv2


class VideoFrameExtractor:

    def __init__(
        self,
        frame_count: int = 4,
        start_ratio: float = 0.15,
        end_ratio: float = 0.85
    ):

        self.frame_count = frame_count
        self.start_ratio = start_ratio
        self.end_ratio = end_ratio

    def extract(
        self,
        video_path: Path,
        output_folder: Path
    ) -> list[Path]:

        video_path = Path(
            video_path
        )

        output_folder = Path(
            output_folder
        )

        if not video_path.exists():

            raise FileNotFoundError(
                f"Video not found: "
                f"{video_path}"
            )

        output_folder.mkdir(
            parents=True,
            exist_ok=True
        )

        capture = cv2.VideoCapture(
            str(video_path)
        )

        if not capture.isOpened():

            raise ValueError(
                f"Could not open video: "
                f"{video_path}"
            )

        try:

            duration_ms = self._get_duration_ms(
                capture
            )

            if duration_ms <= 0:

                raise ValueError(
                    "Could not determine "
                    "video duration."
                )

            timestamps = (
                self._build_timestamps(
                    duration_ms
                )
            )

            frames = []

            for index, timestamp in enumerate(
                timestamps,
                start=1
            ):

                frame_path = (
                    output_folder
                    / f"frame_{index:02d}.jpg"
                )

                success = (
                    self._save_frame(
                        capture=capture,
                        timestamp_ms=timestamp,
                        frame_path=frame_path
                    )
                )

                if success:

                    frames.append(
                        frame_path
                    )

            if not frames:

                raise ValueError(
                    "No frames could be "
                    "extracted from video."
                )

            return frames

        finally:

            capture.release()

    def _get_duration_ms(
        self,
        capture
    ) -> float:

        frame_count = capture.get(
            cv2.CAP_PROP_FRAME_COUNT
        )

        fps = capture.get(
            cv2.CAP_PROP_FPS
        )

        if fps <= 0:
            return 0

        duration_seconds = (
            frame_count / fps
        )

        return (
            duration_seconds * 1000
        )

    def _build_timestamps(
        self,
        duration_ms: float
    ) -> list[float]:

        if self.frame_count == 1:

            return [
                duration_ms * 0.5
            ]

        step = (
            self.end_ratio
            - self.start_ratio
        ) / (
            self.frame_count - 1
        )

        return [
            duration_ms
            * (
                self.start_ratio
                + step * index
            )
            for index in range(
                self.frame_count
            )
        ]

    def _save_frame(
        self,
        capture,
        timestamp_ms: float,
        frame_path: Path
    ) -> bool:

        capture.set(
            cv2.CAP_PROP_POS_MSEC,
            timestamp_ms
        )

        success, frame = (
            capture.read()
        )

        if not success:
            return False

        return bool(
            cv2.imwrite(
                str(frame_path),
                frame
            )
        )