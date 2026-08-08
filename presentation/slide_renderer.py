from pathlib import Path
from presentation.processor_manager import ProcessorManager
from presentation.timeline.slide_timeline import SlideTimeline

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
        timeline = SlideTimeline()

        print(f"Rendering {slide_definition.type}")

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

        print("Timeline")

        for event in timeline.audio_events:

            print(
                event.start_time,
                event.file
            )
        print(
            "Slide Duration:",
            round(
                timeline.duration,
                2
            ),
            "seconds"
        )
