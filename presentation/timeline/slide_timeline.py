from dataclasses import dataclass, field
from pathlib import Path
from config import (
    AUDIO_INITIAL_DELAY,
    AUDIO_GAP,
)


@dataclass
class AudioEvent:
    file: Path
    start_time: float
    duration: float


@dataclass
class SlideTimeline:

    audio_events: list[AudioEvent] = field(
        default_factory=list
    )

    initial_delay: float = AUDIO_INITIAL_DELAY
    audio_gap: float = AUDIO_GAP

    current_time: float = field(init=False)

    def __post_init__(self):
        self.current_time = self.initial_delay

    @property
    def duration(self) -> float:
        return self.current_time

    def add_audio(
        self,
        file: Path,
        duration: float
    ):

        # Add gap before every audio except the first.
        if self.audio_events:
            self.current_time += self.audio_gap

        start_time = self.current_time

        event = AudioEvent(
            file=file,
            start_time=start_time,
            duration=duration
        )

        self.audio_events.append(event)

        self.current_time += duration

        return event