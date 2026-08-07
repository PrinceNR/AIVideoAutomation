from pathlib import Path

from presentation.automation.powerpoint_controller import PowerPointController


PPTX = Path("output/test_builder.pptx").resolve()

AUDIO = Path(
    r"output\farming\audio\cultivate\pronunciation.mp3"
).resolve()

OUTPUT = Path(
    "research/com_audio_test.pptx"
).resolve()


def main():

    print("=" * 70)
    print("COM AUDIO TEST")
    print("=" * 70)

    print("PPTX :", PPTX)
    print("Audio:", AUDIO)
    print("Output:", OUTPUT)

    if not PPTX.exists():
        raise FileNotFoundError(
            f"PPTX not found: {PPTX}"
        )

    if not AUDIO.exists():
        raise FileNotFoundError(
            f"Audio not found: {AUDIO}"
        )

    OUTPUT.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with PowerPointController(visible=True) as ppt:

        ppt.open_presentation(PPTX)

        print("\nPowerPoint opened.")

        slide = ppt.presentation.Slides(1)

        print("Slide 1 obtained.")

        print("\nAdding audio using AddMediaObject2...")

        media = slide.Shapes.AddMediaObject2(
            FileName=str(AUDIO),
            LinkToFile=False,
            SaveWithDocument=True,
            Left=0,
            Top=0,
            Width=32,
            Height=32
        )

        print("Audio added successfully!")

        print("Name:", media.Name)
        print("Type:", media.Type)
        print("ID:", media.Id)

        print("\nSaving presentation...")

        ppt.save_as(str(OUTPUT))

        print("Saved:")
        print(OUTPUT)

        print("\n" + "=" * 70)
        print("TEST COMPLETE")
        print("=" * 70)

        input(
            "\nPowerPoint is still open. "
            "Press Enter to close it..."
        )


if __name__ == "__main__":
    main()