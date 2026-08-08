# from dataclasses import dataclass, field
# from pathlib import Path


# @dataclass
# class AudioEvent:

#     file: Path

#     start_time: float

#     duration: float


# @dataclass
# class SlideTimeline:

#     audio_events: list[AudioEvent] = field(default_factory=list)

#     current_time: float = 0.0

#     @property
#     def duration(self):

#         return self.current_time

#     def add_audio(
#         self,
#         file: Path,
#         duration: float
#     ):

#         start_time = self.current_time

#         event = AudioEvent(
#             file=file,
#             start_time=start_time,
#             duration=duration
#         )

#         self.audio_events.append(event)

#         self.current_time += duration

#         return event




from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class AudioEvent:
    file: Path
    start_time: float
    duration: float


@dataclass
class SlideTimeline:
    audio_events: list[AudioEvent] = field(default_factory=list)

    current_time: float = 0.5

    audio_gap: float = 0.3

    @property
    def duration(self):
        return self.current_time

    def add_audio(
        self,
        file: Path,
        duration: float
    ):

        # Add the gap before every audio except the first.
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
