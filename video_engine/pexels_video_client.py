import os
import requests

from dotenv import load_dotenv

from video_engine.video_candidate import (
    VideoCandidate
)


load_dotenv()


class PexelsVideoClient:

    BASE_URL = (
        "https://api.pexels.com/"
        "v1/videos/search"
    )

    def __init__(
        self,
        api_key: str | None = None
    ):

        self.api_key = (
            api_key
            or os.getenv("PEXELS_API_KEY")
        )

        if not self.api_key:

            raise ValueError(
                "PEXELS_API_KEY not found in .env"
            )

    def search(
        self,
        query: str,
        per_page: int = 3
    ) -> list[VideoCandidate]:

        response = requests.get(
            self.BASE_URL,
            headers={
                "Authorization":
                    self.api_key
            },
            params={
                "query": query,
                "per_page": per_page,
                "orientation":
                    "landscape"
            },
            timeout=30
        )

        response.raise_for_status()

        data = response.json()

        candidates = []

        for video in data.get(
            "videos",
            []
        ):

            video_file = (
                self._select_video_file(
                    video.get(
                        "video_files",
                        []
                    )
                )
            )

            if video_file is None:
                continue

            candidate = VideoCandidate(
                source="pexels",

                source_id=str(
                    video.get(
                        "id",
                        ""
                    )
                ),

                video_url=video_file[
                    "link"
                ],

                duration=float(
                    video.get(
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
                    video.get("image")
                ),

                source_page=(
                    video.get("url")
                )
            )

            candidates.append(
                candidate
            )

        return candidates

    def _select_video_file(
        self,
        video_files
    ) -> dict | None:

        mp4_files = [
            file
            for file in video_files
            if (
                file.get("file_type")
                == "video/mp4"
            )
        ]

        if not mp4_files:
            return None

        # Prefer HD-ish files without
        # unnecessarily downloading 4K.
        suitable_files = [
            file
            for file in mp4_files
            if (
                file.get("width", 0)
                >= 1280
                and file.get(
                    "height",
                    0
                ) >= 720
            )
        ]

        if suitable_files:

            return min(
                suitable_files,
                key=lambda file:
                    file.get(
                        "width",
                        0
                    )
                    * file.get(
                        "height",
                        0
                    )
            )

        return max(
            mp4_files,
            key=lambda file:
                file.get(
                    "width",
                    0
                )
                * file.get(
                    "height",
                    0
                )
        )