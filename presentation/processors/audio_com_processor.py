from presentation.embedders.audio_embedder import (
    AudioEmbedder
)

from presentation.slide_timing.slide_timing_controller import (
    SlideTimingController
)


class AudioComProcessor:

    def __init__(self):

        self.audio_embedder = AudioEmbedder()

        self.slide_timing_controller = (
            SlideTimingController()
        )

    def process(
        self,
        slide,
        timeline
    ):

        for event in timeline.audio_events:

            print(
                f"Embedding: "
                f"{event.file.name}"
            )

            self.audio_embedder.embed(
                slide,
                event.file,
                start_time=event.start_time,
                duration=event.duration
            )

        if timeline.duration > 0:

            self.slide_timing_controller.set_slide_duration(
                slide,
                timeline.duration
            )