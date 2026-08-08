from pathlib import Path

from presentation.automation.powerpoint_controller import PowerPointController


PPTX = Path("output/test_builder.pptx").resolve()

AUDIO_FOLDER = Path(
    r"output\farming\audio\cultivate"
).resolve()

OUTPUT = Path(
    "research/com_audio_sequence_test.pptx"
).resolve()


def main():

    print("=" * 70)
    print("COM AUDIO SEQUENCE TEST")
    print("=" * 70)

    pronunciation = AUDIO_FOLDER / "pronunciation.mp3"
    meaning = AUDIO_FOLDER / "meaning.mp3"

    for audio in [pronunciation, meaning]:

        if not audio.exists():

            raise FileNotFoundError(
                f"Audio not found: {audio}"
            )

    with PowerPointController(visible=True) as ppt:

        ppt.open_presentation(PPTX)

        presentation = ppt.presentation

        slide = presentation.Slides(1)

        print("\nPowerPoint opened.")
        print("Slide 1 obtained.")

        # -------------------------------------------------
        # Audio 1
        # -------------------------------------------------

        print("\nAdding pronunciation #1...")

        audio1 = slide.Shapes.AddMediaObject2(
            FileName=str(pronunciation),
            LinkToFile=False,
            SaveWithDocument=True,
            Left=0,
            Top=0,
            Width=32,
            Height=32
        )

        print(
            "Added:",
            audio1.Name,
            audio1.Type,
            audio1.Id
        )

        # -------------------------------------------------
        # Audio 2
        # -------------------------------------------------

        print("\nAdding pronunciation #2...")

        audio2 = slide.Shapes.AddMediaObject2(
            FileName=str(pronunciation),
            LinkToFile=False,
            SaveWithDocument=True,
            Left=40,
            Top=0,
            Width=32,
            Height=32
        )

        print(
            "Added:",
            audio2.Name,
            audio2.Type,
            audio2.Id
        )

        # -------------------------------------------------
        # Audio 3
        # -------------------------------------------------

        print("\nAdding meaning...")

        audio3 = slide.Shapes.AddMediaObject2(
            FileName=str(meaning),
            LinkToFile=False,
            SaveWithDocument=True,
            Left=80,
            Top=0,
            Width=32,
            Height=32
        )

        print(
            "Added:",
            audio3.Name,
            audio3.Type,
            audio3.Id
        )

        # -------------------------------------------------
        # Inspect animation settings
        # -------------------------------------------------

        print("\nInspecting animation settings...")

        for index, media in enumerate(
            [audio1, audio2, audio3],
            start=1
        ):

            print(
                f"\nAudio {index}: {media.Name}"
            )

            try:

                animation = media.AnimationSettings

                print(
                    "  Animate:",
                    animation.Animate
                )

                print(
                    "  EntryEffect:",
                    animation.EntryEffect
                )

                print(
                    "  AnimationOrder:",
                    animation.AnimationOrder
                )

            except Exception as e:

                print(
                    "  Animation inspection failed:",
                    e
                )

        # -------------------------------------------------
        # Save
        # -------------------------------------------------

        print("\nSaving...")

        ppt.save_as(
            str(OUTPUT)
        )

        print(
            "\nSaved:",
            OUTPUT
        )

        print("\n" + "=" * 70)
        print("TEST COMPLETE")
        print("=" * 70)

        input(
            "\nPowerPoint is still open. "
            "Open Slide 1 and test the audio. "
            "Press Enter to close..."
        )


if __name__ == "__main__":
    main()