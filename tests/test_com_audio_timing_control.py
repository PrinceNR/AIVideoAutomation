from pathlib import Path

from presentation.automation.powerpoint_controller import PowerPointController


PPTX = Path(
    "output/test_builder.pptx"
).resolve()

AUDIO_FOLDER = Path(
    r"output\farming\audio\cultivate"
).resolve()

OUTPUT = Path(
    "research/com_audio_timing_control_test.pptx"
).resolve()


def add_audio(slide, audio_path, left):

    return slide.Shapes.AddMediaObject2(
        FileName=str(audio_path),
        LinkToFile=False,
        SaveWithDocument=True,
        Left=left,
        Top=0,
        Width=32,
        Height=32
    )


def main():

    print("=" * 70)
    print("COM AUDIO TIMING CONTROL TEST")
    print("=" * 70)

    pronunciation = (
        AUDIO_FOLDER / "pronunciation.mp3"
    )

    meaning = (
        AUDIO_FOLDER / "meaning.mp3"
    )

    with PowerPointController(visible=True) as ppt:

        ppt.open_presentation(PPTX)

        presentation = ppt.presentation
        slide = presentation.Slides(1)

        print("\nPowerPoint opened.")
        print("Slide 1 obtained.")

        # -------------------------------------------------
        # Add audio
        # -------------------------------------------------

        audio1 = add_audio(
            slide,
            pronunciation,
            0
        )

        audio2 = add_audio(
            slide,
            pronunciation,
            40
        )

        audio3 = add_audio(
            slide,
            meaning,
            80
        )

        # -------------------------------------------------
        # Animation sequence
        # -------------------------------------------------

        sequence = slide.TimeLine.MainSequence

        effect1 = sequence.AddEffect(
            Shape=audio1,
            effectId=1
        )

        effect2 = sequence.AddEffect(
            Shape=audio2,
            effectId=1
        )

        effect3 = sequence.AddEffect(
            Shape=audio3,
            effectId=1
        )

        # -------------------------------------------------
        # Apply timing
        # -------------------------------------------------

        print("\nSetting timing...")

        effect1.Timing.Duration = 0.91
        effect1.Timing.TriggerDelayTime = 0.0

        effect2.Timing.Duration = 0.91
        effect2.Timing.TriggerDelayTime = 0.91

        effect3.Timing.Duration = 3.47
        effect3.Timing.TriggerDelayTime = 1.82

        # -------------------------------------------------
        # Inspect
        # -------------------------------------------------

        effects = [
            effect1,
            effect2,
            effect3
        ]

        for index, effect in enumerate(
            effects,
            start=1
        ):

            print(
                f"\nEffect {index}:"
            )

            print(
                "  Shape:",
                effect.Shape.Name
            )

            print(
                "  TriggerType:",
                effect.Timing.TriggerType
            )

            print(
                "  Duration:",
                effect.Timing.Duration
            )

            print(
                "  TriggerDelayTime:",
                effect.Timing.TriggerDelayTime
            )

        # -------------------------------------------------
        # Save
        # -------------------------------------------------

        print("\nSaving...")

        ppt.save_as(
            str(OUTPUT)
        )

        print(
            "Saved:",
            OUTPUT
        )

        print("\n" + "=" * 70)
        print("TEST COMPLETE")
        print("=" * 70)

        input(
            "\nOpen the output PPTX. "
            "Check the Animation Pane and play Slide Show. "
            "Press Enter to close..."
        )


if __name__ == "__main__":
    main()