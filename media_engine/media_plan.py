from dataclasses import dataclass

from media_engine.media_type import (
    MediaType
)


@dataclass
class MediaPlan:

    preferred_type: MediaType

    reason: str

    requires_motion: bool = False