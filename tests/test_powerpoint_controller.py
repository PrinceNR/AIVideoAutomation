from presentation.automation.powerpoint_controller import PowerPointController
from pathlib import Path


def main():

    with PowerPointController(visible=True) as ppt:

        ppt.open_presentation("research/manual_audio.pptx")

        # ppt.audio.add_audio(
        #     slide_index=1,
        #     audio_path=r"output\farming\audio\cultivate\pronunciation.mp3"
        # )

        audio = Path(
            r"output\farming\audio\cultivate\pronunciation.mp3"
        ).resolve()

        audio = ppt.audio.add_audio(
            slide_index=1,
            audio_path=str(audio.resolve())
        )


        ppt.save_as(str(Path("research/manual_after_com.pptx").resolve()))
        # print(audio)

        # ppt.save()

        # slide = ppt.audio.slide(1)

        # print(slide.Name)

        input("PowerPoint opened successfully. Press Enter to continue...")

        # ppt.save()


if __name__ == "__main__":
    main()