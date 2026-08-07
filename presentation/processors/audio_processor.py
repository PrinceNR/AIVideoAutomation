from presentation.audio_duration_calculator import AudioDurationCalculator
from presentation.embedders.audio_embedder import AudioEmbedder

class AudioProcessor:

    def __init__(self):

        self.duration_calculator = AudioDurationCalculator()
        # self.audio_embedder = AudioEmbedder()

    def process(
        self,
        slide,
        slide_definition,
        word,
        word_number,
        total_words,
        timeline
    ):

        # audio_name = slide_definition.audio
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


            # print(f"embed this audio into the PowerPoint slide. {audio_path}")
            # self.audio_embedder.embed(
            #     slide,
            #     event.file,
            #     event.start_time
            # )

        # if audio_name is None:
        #     return

        # audio_path = word.get_audio(audio_name)
