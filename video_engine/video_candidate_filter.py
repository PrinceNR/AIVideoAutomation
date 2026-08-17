from video_engine.video_candidate import (
    VideoCandidate
)
from config import VIDEO_MAX_DURATION, VIDEO_MIN_DURATION



class VideoCandidateFilter:

    def __init__(
        self,
        min_width: int = 1280,
        min_height: int = 720,
        min_duration: float = VIDEO_MIN_DURATION,
        max_duration: float = VIDEO_MAX_DURATION
    ):
        self.min_width = min_width
        self.min_height = min_height
        self.min_duration = min_duration
        self.max_duration = max_duration

    def filter(
        self,
        candidates: list[VideoCandidate]
    ) -> list[VideoCandidate]:

        filtered = []

        for candidate in candidates:

            if not self._is_valid(
                candidate
            ):
                continue

            filtered.append(
                candidate
            )

        return filtered

    def _is_valid(
        self,
        candidate: VideoCandidate
    ) -> bool:

        # Must have a downloadable video
        if not candidate.video_url:
            return False

        # Invalid duration
        if candidate.duration <= 0:
            return False

        if (
            candidate.duration
            < self.min_duration
        ):
            return False

        # Avoid unnecessarily long downloads
        if (
            candidate.duration
            > self.max_duration
        ):
            return False

        # Minimum quality
        if (
            candidate.width
            < self.min_width
        ):
            return False

        if (
            candidate.height
            < self.min_height
        ):
            return False

        # Landscape video preferred
        if (
            candidate.width
            < candidate.height
        ):
            return False

        return True