from pathlib import Path

import requests

from video_engine.video_candidate import (
    VideoCandidate
)


class VideoCandidateDownloader:

    def __init__(
        self,
        session=None,
        chunk_size: int = 1024 * 1024
    ):

        self.session = (
            session
            or requests.Session()
        )

        self.chunk_size = chunk_size

    def download(
        self,
        candidates: list[VideoCandidate],
        output_folder: Path,
        max_downloads: int = 3
    ) -> list[VideoCandidate]:

        output_folder = Path(
            output_folder
        )

        output_folder.mkdir(
            parents=True,
            exist_ok=True
        )

        downloaded = []

        for index, candidate in enumerate(
            candidates[:max_downloads],
            start=1
        ):

            try:

                local_path = (
                    self._download_candidate(
                        candidate=candidate,
                        output_folder=output_folder,
                        index=index
                    )
                )

                candidate.local_path = str(
                    local_path
                )

                downloaded.append(
                    candidate
                )

                print(
                    f"Downloaded video: "
                    f"{local_path}"
                )

            except Exception as error:

                print(
                    f"Failed to download "
                    f"{candidate.source} video "
                    f"{candidate.source_id}: "
                    f"{error}"
                )

        return downloaded

    def _download_candidate(
        self,
        candidate: VideoCandidate,
        output_folder: Path,
        index: int
    ) -> Path:

        filename = (
            self._build_filename(
                candidate,
                index
            )
        )

        final_path = (
            output_folder
            / filename
        )

        temporary_path = (
            final_path.with_suffix(
                ".part"
            )
        )

        try:

            with self.session.get(
                candidate.video_url,
                stream=True,
                timeout=60
            ) as response:

                response.raise_for_status()

                with open(
                    temporary_path,
                    "wb"
                ) as file:

                    for chunk in (
                        response.iter_content(
                            chunk_size=self.chunk_size
                        )
                    ):

                        if chunk:
                            file.write(
                                chunk
                            )

            temporary_path.replace(
                final_path
            )

            return final_path

        except Exception:

            if temporary_path.exists():

                temporary_path.unlink()

            raise

    def _build_filename(
        self,
        candidate: VideoCandidate,
        index: int
    ) -> str:

        source_id = (
            candidate.source_id
            or str(index)
        )

        return (
            f"candidate_{index:02d}_"
            f"{candidate.source}_"
            f"{source_id}.mp4"
        )