from dataclasses import dataclass


@dataclass
class VideoCandidate:

    source: str

    video_url: str

    duration: float

    width: int

    height: int

    source_id: str | None = None

    preview_url: str | None = None

    source_page: str | None = None

    local_path: str | None = None