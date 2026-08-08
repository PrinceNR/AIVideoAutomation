from pathlib import Path

from presentation.automation.powerpoint_controller import PowerPointController
from presentation.embedders.audio_embedder import AudioEmbedder
from presentation.audio_duration_calculator import AudioDurationCalculator


class AudioPresentationProcessor:

    def __init__(self):

        self.audio_embedder = AudioEmbedder()
        self.duration_calculator = AudioDurationCalculator()

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

                    audio_sequence = (
                        slide_definition.audio_sequence
                    )

                    current_time = 0.0

                    for index, audio_name in enumerate(
                        audio_sequence
                    ):

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

                        # First audio gets 0.5s.
                        # All following audio gets 0.3s.
                        delay = (
                            0.5
                            if index == 0
                            else 0.3
                        )

                        actual_start_time = (
                            current_time + delay
                        )

                        print(
                            f"    Embedding: "
                            f"{audio_name}.mp3"
                        )

                        print(
                            f"      Timeline: "
                            f"{current_time:.2f}s"
                        )

                        print(
                            f"      Actual start: "
                            f"{actual_start_time:.2f}s"
                        )

                        print(
                            f"      Duration: "
                            f"{duration:.2f}s"
                        )

                        print(
                            f"      Delay: "
                            f"{delay:.2f}s"
                        )

                        self.audio_embedder.embed(
                            slide,
                            audio_path,
                            start_time=current_time,
                            duration=duration,
                            delay=delay
                        )

                        current_time += duration

                    slide_index += 1

            ppt.save()

        print(
            "\nCOM audio embedding completed."
        )