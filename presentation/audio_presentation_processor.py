from pathlib import Path

from presentation.automation.powerpoint_controller import PowerPointController
from presentation.embedders.audio_embedder import AudioEmbedder
from presentation.audio_duration_calculator import AudioDurationCalculator
from presentation.slide_timing.slide_timing_controller import SlideTimingController
from presentation.timeline.slide_timeline import SlideTimeline
from config import NO_AUDIO_SLIDE_DURATION


class AudioPresentationProcessor:

    def __init__(self):

        self.audio_embedder = AudioEmbedder()
        self.duration_calculator = AudioDurationCalculator()
        self.slide_timing_controller = SlideTimingController()

    def process(
        self,
        pptx_path,
        lesson,
        template_definition
    ):

        pptx_path = Path(pptx_path).resolve()

        print("=" * 70)
        print("COM AUDIO EMBEDDING")
        print("=" * 70)

        with PowerPointController(visible=True) as ppt:

            ppt.open_presentation(
                pptx_path
            )

            presentation = ppt.presentation

            slide_index = 1

            for word in lesson.words:

                print(
                    f"\nWord {word.word}"
                )

                for slide_definition in template_definition.slides:

                    slide = presentation.Slides(
                        slide_index
                    )

                    print(
                        f"  Slide {slide_index}: "
                        f"{slide_definition.type}"
                    )

                    # -------------------------------------------------
                    # Create timeline for this slide
                    # -------------------------------------------------

                    audio_config = slide_definition.audio

                    timeline = SlideTimeline(
                        initial_delay=audio_config.initial_delay,
                        audio_gap=audio_config.gap
                    )

                    audio_sequence = audio_config.sequence

                    for audio_name in audio_sequence:

                        audio_path = word.get_audio(
                            audio_name
                        )

                        if audio_path is None:

                            print(
                                f"    Audio not found: "
                                f"{audio_name}"
                            )

                            continue

                        duration = (
                            self.duration_calculator.get_duration(
                                audio_path
                            )
                        )

                        # -------------------------------------------------
                        # Add audio to timeline
                        # -------------------------------------------------

                        event = timeline.add_audio(
                            file=audio_path,
                            duration=duration
                        )

                        delay = (
                            timeline.initial_delay
                            if len(timeline.audio_events) == 1
                            else timeline.audio_gap
                        )

                        print(
                            f"    Embedding: "
                            f"{audio_name}.mp3"
                        )

                        print(
                            f"      Start: "
                            f"{event.start_time:.2f}s"
                        )

                        print(
                            f"      Duration: "
                            f"{event.duration:.2f}s"
                        )

                        
                        self.audio_embedder.embed(
                            slide,
                            audio_path,
                            start_time=event.start_time,
                            duration=duration,
                            delay=delay
                        )

                        # self.audio_embedder.embed(
                        #     slide,
                        #     audio_path,
                        #     start_time=event.start_time,
                        #     duration=event.duration
                        # )

                    # -------------------------------------------------
                    # Set PowerPoint slide duration
                    # -------------------------------------------------

                    if timeline.audio_events:

                        slide_duration = (
                            timeline.duration
                        )

                    else:

                        slide_duration = (
                            NO_AUDIO_SLIDE_DURATION
                        )
                    self.slide_timing_controller.set_slide_duration(
                        slide,
                        slide_duration
                    )

                    print(
                        f"      Slide Duration: "
                        f"{slide_duration:.2f}s"
                    )

                    slide_index += 1

            ppt.save()

        print(
            "\nCOM audio embedding completed."
        )