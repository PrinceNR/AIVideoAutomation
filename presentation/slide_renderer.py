from pathlib import Path
from presentation.processor_manager import ProcessorManager
from presentation.timeline.slide_timeline import SlideTimeline
from presentation.presentation_logger import (
    presentation_logger as log,
)

class SlideRenderer:

    def __init__(self):

        self.processor_manager = ProcessorManager()

    def render(
        self,
        slide,
        slide_definition,
        word,
        word_number,
        total_words
    ):
        timeline = SlideTimeline(
            initial_delay=(
                slide_definition.audio.initial_delay
                if slide_definition.audio
                else 0.5
            ),
            audio_gap=(
                slide_definition.audio.gap
                if slide_definition.audio
                else 0.3
            )
        )

        log.detail(
            f"Rendering {slide_definition.type}"
        )

        for processor_name in slide_definition.processors:

            processor = self.processor_manager.get(
                processor_name
            )

            processor.process(
                slide,
                slide_definition,
                word,
                word_number,
                total_words,
                timeline
            )

        log.detail("Timeline")

        for event in timeline.audio_events:

            log.detail(
                f"{event.start_time} {event.file}"
            )
        log.detail(
            f"Slide Duration: "
            f"{timeline.duration:.2f} seconds"
        )
        return timeline
