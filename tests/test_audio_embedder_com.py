from pathlib import Path

from presentation.automation.powerpoint_controller import PowerPointController
from presentation.embedders.audio_embedder import AudioEmbedder


PPTX = Path(
    "output/test_builder.pptx"
).resolve()

AUDIO = Path(
    r"output\farming\audio\cultivate\pronunciation.mp3"
).resolve()

OUTPUT = Path(
    "research/audio_embedder_com_test.pptx"
).resolve()


def main():

    print("=" * 70)
    print("AUDIO EMBEDDER COM TEST")
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

        embedder = AudioEmbedder()

        print("\nEmbedding audio...")

        media = embedder.embed(
            slide,
            AUDIO,
            0.0
        )

        print("\nAudio embedding successful!")

        print("Name:", media.Name)
        print("Type:", media.Type)
        print("ID:", media.Id)

        print("\nSaving presentation...")

        ppt.save_as(
            str(OUTPUT)
        )

        print("Saved:")
        print(OUTPUT)

        print("\n" + "=" * 70)
        print("TEST COMPLETE")
        print("=" * 70)

        input(
            "\nPowerPoint is still open. "
            "Open the slide and test the audio. "
            "Press Enter to close..."
        )


if __name__ == "__main__":
    main()