from dataclasses import dataclass, field

from media_engine.media_type import (
    MediaType
)


@dataclass
class MediaRecoveryPlan:

    media_type: MediaType

    reason: str

    search_queries: list[str] = field(
        default_factory=list
    )
