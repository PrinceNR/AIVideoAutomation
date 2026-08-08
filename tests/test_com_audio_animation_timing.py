from pathlib import Path

from presentation.automation.powerpoint_controller import PowerPointController


PPTX = Path(
    "output/test_builder.pptx"
).resolve()

AUDIO_FOLDER = Path(
    r"output\farming\audio\cultivate"
).resolve()

OUTPUT = Path(
    "research/com_audio_animation_timing_test.pptx"
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
    print("COM AUDIO ANIMATION TIMING TEST")
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
        # Add three audio objects
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

        print("\nAudio objects created.")

        # -------------------------------------------------
        # Animation sequence
        # -------------------------------------------------

        sequence = (
            slide.TimeLine.MainSequence
        )

        print(
            "Initial animation count:",
            sequence.Count
        )

        effects = []

        for audio in [
            audio1,
            audio2,
            audio3
        ]:

            effect = sequence.AddEffect(
                Shape=audio,
                effectId=1
            )

            effects.append(effect)

        print(
            "Final animation count:",
            sequence.Count
        )

        # -------------------------------------------------
        # Inspect timing
        # -------------------------------------------------

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
                "  EffectType:",
                effect.EffectType
            )

            timing = effect.Timing

            print(
                "  TriggerType:",
                timing.TriggerType
            )

            try:

                print(
                    "  Duration:",
                    timing.Duration
                )

            except Exception as e:

                print(
                    "  Duration unavailable:",
                    e
                )

            try:

                print(
                    "  TriggerDelayTime:",
                    timing.TriggerDelayTime
                )

            except Exception as e:

                print(
                    "  TriggerDelayTime unavailable:",
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
            "Saved:",
            OUTPUT
        )

        print("\n" + "=" * 70)
        print("TEST COMPLETE")
        print("=" * 70)

        input(
            "\nOpen the output PPTX and inspect "
            "the Animation Pane. "
            "Press Enter to close..."
        )


if __name__ == "__main__":
    main()