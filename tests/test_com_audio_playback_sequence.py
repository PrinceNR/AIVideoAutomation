from pathlib import Path

from presentation.automation.powerpoint_controller import (
    PowerPointController
)


PPTX = Path(
    "output/test_builder.pptx"
).resolve()

AUDIO_FOLDER = Path(
    r"output\farming\audio\cultivate"
).resolve()

OUTPUT = Path(
    "research/com_audio_playback_sequence_test.pptx"
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


def configure_audio(effect, audio_shape, delay):

    # Tell PowerPoint this media should actually play
    # when its animation is triggered.
    audio_shape.AnimationSettings.PlaySettings.PlayOnEntry = True

    # Do not hide the media while testing.
    audio_shape.AnimationSettings.PlaySettings.HideWhileNotPlaying = False

    # The effect itself should happen automatically
    # after the previous effect.
    effect.Timing.TriggerType = 3

    # Delay after the previous effect.
    effect.Timing.TriggerDelayTime = delay


def main():

    print("=" * 70)
    print("COM AUDIO PLAYBACK SEQUENCE TEST")
    print("=" * 70)

    pronunciation = (
        AUDIO_FOLDER / "pronunciation.mp3"
    )

    meaning = (
        AUDIO_FOLDER / "meaning.mp3"
    )

    if not pronunciation.exists():
        raise FileNotFoundError(pronunciation)

    if not meaning.exists():
        raise FileNotFoundError(meaning)

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

        sequence = slide.TimeLine.MainSequence

        print(
            "Initial animation count:",
            sequence.Count
        )

        effect1 = sequence.AddEffect(
            audio1,
            83,   # msoAnimEffectMediaPlay
            0,
            1     # msoAnimTriggerOnPageClick
        )

        effect2 = sequence.AddEffect(
            audio2,
            83,   # msoAnimEffectMediaPlay
            0,
            3     # msoAnimTriggerAfterPrevious
        )

        effect3 = sequence.AddEffect(
            audio3,
            83,   # msoAnimEffectMediaPlay
            0,
            3     # msoAnimTriggerAfterPrevious
        )

        # -------------------------------------------------
        # Configure automatic playback
        # -------------------------------------------------

        configure_audio(
            effect1,
            audio1,
            0.0
        )

        configure_audio(
            effect2,
            audio2,
            0.0
        )

        configure_audio(
            effect3,
            audio3,
            0.0
        )

        # -------------------------------------------------
        # Set durations only for the animation timeline.
        # -------------------------------------------------

        # effect1.Timing.Duration = 0.91
        # effect2.Timing.Duration = 0.91
        # effect3.Timing.Duration = 3.47

        effect1.Timing.Duration = 0.91
        effect1.Timing.TriggerType = 3
        effect1.Timing.TriggerDelayTime = 0.0

        effect2.Timing.Duration = 0.91
        effect2.Timing.TriggerType = 3
        effect2.Timing.TriggerDelayTime = 0.3

        effect3.Timing.Duration = 3.47
        effect3.Timing.TriggerType = 3
        effect3.Timing.TriggerDelayTime = 0.3

        print("Effect 1 delay:", effect1.Timing.TriggerDelayTime)
        print("Effect 2 delay:", effect2.Timing.TriggerDelayTime)
        print("Effect 3 delay:", effect3.Timing.TriggerDelayTime)

        # -------------------------------------------------
        # Inspect
        # -------------------------------------------------

        effects = [
            effect1,
            effect2,
            effect3
        ]

        print(
            "\nFinal animation count:",
            sequence.Count
        )

        for index, effect in enumerate(
            effects,
            start=1
        ):

            print(
                f"\nEffect {index}:"
            )

            # print(
            #     "  Shape:",
            #     effect.Shape.Name
            # )

            print("Effect", index)
            print("  EffectType:", effect.EffectType)
            print("  TriggerType:", effect.Timing.TriggerType)
            print("  Duration:", effect.Timing.Duration)
            print("  Delay:", effect.Timing.TriggerDelayTime)

            try:
                shape = effect.Shape

                if shape is not None:
                    print("  Shape:", shape.Name)
                else:
                    print("  Shape: None")

            except Exception as e:
                print("  Shape inspection failed:", e)

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

            try:

                print(
                    "  PlayOnEntry:",
                    effect.Shape
                    .AnimationSettings
                    .PlaySettings
                    .PlayOnEntry
                )

            except Exception as e:

                print(
                    "  PlayOnEntry unavailable:",
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
            "\nOpen the Animation Pane and start "
            "Slide Show from Slide 1. "
            "Listen carefully to the three sounds. "
            "Press Enter to close..."
        )


if __name__ == "__main__":
    main()