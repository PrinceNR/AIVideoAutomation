# # from presentation.audio_duration_calculator import (
# #     AudioDurationCalculator
# # )


# # class AudioProcessor:

# #     def __init__(self):

# #         self.duration_calculator = (
# #             AudioDurationCalculator()
# #         )

# #     def process(
# #         self,
# #         slide,
# #         slide_definition,
# #         word,
# #         word_number,
# #         total_words,
# #         timeline
# #     ):

# #         if slide_definition.audio is None:
# #             return

# #         sequence = slide_definition.audio.sequence


# #         for audio_name in sequence:

# #             audio_path = word.get_audio(
# #                 audio_name
# #             )

# #             if audio_path is None:

# #                 print(
# #                     f"Audio not found: "
# #                     f"{audio_name}"
# #                 )

# #                 continue

# #             duration = (
# #                 self.duration_calculator.get_duration(
# #                     audio_path
# #                 )
# #             )

# #             event = timeline.add_audio(
# #                 audio_path,
# #                 duration
# #             )

# #             print(
# #                 f"Audio scheduled: "
# #                 f"{audio_name}.mp3 "
# #                 f"({duration:.2f}s)"
# #             )

# #             print(
# #                 f"  Start: "
# #                 f"{event.start_time:.2f}s"
# #             )

# #             print(
# #                 f"  Duration: "
# #                 f"{event.duration:.2f}s"
# #             )



# from presentation.audio_duration_calculator import (
#     AudioDurationCalculator
# )
# from presentation.embedders.audio_embedder import (
#     AudioEmbedder
# )
# from presentation.slide_timing.slide_timing_controller import (
#     SlideTimingController
# )


# class AudioProcessor:

#     def __init__(self):

#         self.duration_calculator = (
#             AudioDurationCalculator()
#         )

#         self.audio_embedder = AudioEmbedder()

#         self.slide_timing_controller = (
#             SlideTimingController()
#         )

#     def process(
#         self,
#         slide,
#         slide_definition,
#         word,
#         word_number,
#         total_words,
#         timeline
#     ):

#         if slide_definition.audio is None:
#             return

#         sequence = slide_definition.audio.sequence

#         for audio_name in sequence:

#             audio_path = word.get_audio(
#                 audio_name
#             )

#             if audio_path is None:

#                 print(
#                     f"Audio not found: "
#                     f"{audio_name}"
#                 )

#                 continue

#             duration = (
#                 self.duration_calculator.get_duration(
#                     audio_path
#                 )
#             )

#             # ---------------------------------------------
#             # Add event to timeline
#             # ---------------------------------------------

#             event = timeline.add_audio(
#                 audio_path,
#                 duration
#             )

#             print(
#                 f"Audio scheduled: "
#                 f"{audio_name}.mp3 "
#                 f"({duration:.2f}s)"
#             )

#             print(
#                 f"  Start: "
#                 f"{event.start_time:.2f}s"
#             )

#             print(
#                 f"  Duration: "
#                 f"{event.duration:.2f}s"
#             )

#             # ---------------------------------------------
#             # Calculate delay
#             # ---------------------------------------------

#             delay = (
#                 0.5
#                 if len(timeline.audio_events) == 1
#                 else timeline.audio_gap
#             )

#             # ---------------------------------------------
#             # Embed audio into PowerPoint
#             # ---------------------------------------------

#             self.audio_embedder.embed(
#                 slide,
#                 audio_path,
#                 start_time=event.start_time,
#                 duration=event.duration,
#                 delay=delay
#             )

#         # ---------------------------------------------
#         # Set slide duration
#         # ---------------------------------------------

#         if timeline.duration > 0:

#             self.slide_timing_controller.set_slide_duration(
#                 slide,
#                 timeline.duration
#             )

from presentation.audio_duration_calculator import (
    AudioDurationCalculator
)
from presentation.presentation_logger import (
    presentation_logger as log,
)


class AudioProcessor:

    def __init__(self):

        self.duration_calculator = (
            AudioDurationCalculator()
        )

    def process(
        self,
        slide,
        slide_definition,
        word,
        word_number,
        total_words,
        timeline
    ):

        if slide_definition.audio is None:
            return

        sequence = slide_definition.audio.sequence

        for audio_name in sequence:

            audio_path = word.get_audio(
                audio_name
            )

            if audio_path is None:

                log.warning(
                    f"Audio not found: "
                    f"{audio_name}"
                )

                continue

            duration = (
                self.duration_calculator.get_duration(
                    audio_path
                )
            )

            # ---------------------------------------------
            # Add audio to timeline
            # ---------------------------------------------

            event = timeline.add_audio(
                audio_path,
                duration
            )

            log.detail(
                f"Audio scheduled: "
                f"{audio_name}.mp3 "
                f"({duration:.2f}s)"
            )

            log.detail(
                f"  Start: "
                f"{event.start_time:.2f}s"
            )

            log.detail(
                f"  Duration: "
                f"{event.duration:.2f}s"
            )
