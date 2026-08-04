from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class AudioEvent:

    file: Path

    start_time: float


@dataclass
class SlideTimeline:

    audio_events: list[AudioEvent] = field(default_factory=list)

    current_time: float = 0.0

    @property
    def duration(self):

        return self.current_time

    def add_audio(
        self,
        file: Path,
        duration: float
    ):

        self.audio_events.append(

            AudioEvent(
                file=file,
                start_time=self.current_time
            )

        )
        self.current_time += duration