import os
import requests

from dotenv import load_dotenv

from video_engine.video_candidate import (
    VideoCandidate
)


load_dotenv()


class PixabayVideoClient:

    BASE_URL = (
        "https://pixabay.com/api/videos/"
    )

    def __init__(
        self,
        api_key: str | None = None
    ):

        self.api_key = (
            api_key
            or os.getenv(
                "PIXABAY_API_KEY"
            )
        )

        if not self.api_key:

            raise ValueError(
                "PIXABAY_API_KEY "
                "not found in .env"
            )

    def search(
        self,
        query: str,
        per_page: int = 3
    ) -> list[VideoCandidate]:

        params = {
            "key": self.api_key,
            "q": query,
            "per_page": per_page,
            "video_type": "all",
            "safesearch": "true",
            "min_width": 1280,
            "min_height": 720
        }

        response = requests.get(
            self.BASE_URL,
            params=params,
            timeout=30
        )

        response.raise_for_status()

        data = response.json()

        candidates = []

        for hit in data.get(
            "hits",
            []
        ):

            video_file = (
                self._select_video_file(
                    hit.get(
                        "videos",
                        {}
                    )
                )
            )

            if video_file is None:
                continue

            candidate = (
                VideoCandidate(
                    source="pixabay",

                    source_id=str(
                        hit.get(
                            "id",
                            ""
                        )
                    ),

                    video_url=(
                        video_file[
                            "url"
                        ]
                    ),

                    duration=float(
                        hit.get(
                            "duration",
                            0
                        )
                    ),

                    width=int(
                        video_file.get(
                            "width",
                            0
                        )
                    ),

                    height=int(
                        video_file.get(
                            "height",
                            0
                        )
                    ),

                    preview_url=(
                        video_file.get(
                            "thumbnail"
                        )
                    ),

                    source_page=(
                        hit.get(
                            "pageURL"
                        )
                    )
                )
            )

            candidates.append(
                candidate
            )

        return candidates

    def _select_video_file(
        self,
        videos: dict
    ) -> dict | None:

        available = []

        for video in videos.values():

            if not isinstance(
                video,
                dict
            ):
                continue

            if not video.get("url"):
                continue

            available.append(
                video
            )

        if not available:
            return None

        # Prefer the smallest version
        # that is at least 1280x720.
        hd_files = [
            video
            for video in available
            if (
                video.get(
                    "width",
                    0
                ) >= 1280
                and
                video.get(
                    "height",
                    0
                ) >= 720
            )
        ]

        if hd_files:

            return min(
                hd_files,
                key=lambda video: (
                    video.get(
                        "width",
                        0
                    )
                    *
                    video.get(
                        "height",
                        0
                    )
                )
            )

        # Fallback to the best
        # available rendition.
        return max(
            available,
            key=lambda video: (
                video.get(
                    "width",
                    0
                )
                *
                video.get(
                    "height",
                    0
                )
            )
        )