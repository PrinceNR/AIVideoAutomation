
from presentation.audio_duration_calculator import AudioDurationCalculator


class AudioProcessor:

    def __init__(self):

        self.duration_calculator = AudioDurationCalculator()

    def process(
        self,
        slide,
        slide_definition,
        word,
        word_number,
        total_words,
        timeline
    ):

        sequence = slide_definition.audio_sequence

        for audio_name in sequence:

            audio_path = word.get_audio(audio_name)

            if audio_path is None:

                print(
                    f"Audio not found: {audio_name}"
                )

                continue

            duration = self.duration_calculator.get_duration(
                audio_path
            )

            timeline.add_audio(
                audio_path,
                duration
            )

            print(
                f"Audio scheduled: "
                f"{audio_name}.mp3 "
                f"({duration:.2f}s)"
            )


