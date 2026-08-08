from pathlib import Path

from presentation.automation.powerpoint_controller import PowerPointController


PPTX = Path(
    "research/com_audio_sequence_test.pptx"
).resolve()

OUTPUT = Path(
    "research/com_audio_animation_test.pptx"
).resolve()


def main():

    print("=" * 70)
    print("COM AUDIO ANIMATION TEST")
    print("=" * 70)

    with PowerPointController(visible=True) as ppt:

        ppt.open_presentation(PPTX)

        presentation = ppt.presentation
        slide = presentation.Slides(1)

        print("\nPowerPoint opened.")
        print("Slide 1 obtained.")

        print("\nFinding audio objects...")

        audio_shapes = []

        for shape in slide.Shapes:

            try:

                if shape.Type == 16:

                    audio_shapes.append(shape)

                    print(
                        f"Audio found: "
                        f"{shape.Name} "
                        f"ID={shape.Id}"
                    )

            except Exception:

                continue

        print(
            f"\nTotal audio objects: "
            f"{len(audio_shapes)}"
        )

        # if len(audio_shapes) != 3:

        #     raise RuntimeError(
        #         "Expected 3 audio objects."
        #     )

        if len(audio_shapes) == 0:
            raise RuntimeError(
                "No audio objects found."
            )

        print(
            f"Found {len(audio_shapes)} audio objects."
        )

        # --------------------------------------------------
        # Access PowerPoint animation timeline
        # --------------------------------------------------

        print("\nAccessing animation timeline...")

        timeline = slide.TimeLine

        sequence = timeline.MainSequence

        print(
            "Existing animation count:",
            sequence.Count
        )

        # --------------------------------------------------
        # Add audio objects to animation sequence
        # --------------------------------------------------

        for index, audio in enumerate(
            audio_shapes,
            start=1
        ):
            print(
                f"\nTesting audio {index}: {audio.Name}"
            )

            print(
                f"\nAdding audio {index} "
                f"to animation sequence..."
            )

            try:

                effect = sequence.AddEffect(
                    Shape=audio,
                    effectId=1
                )

                print(
                    "Effect created."
                )

                print(
                    "Effect:",
                    effect
                )

            except Exception as e:

                print(
                    "AddEffect failed:"
                )

                print(e)

        # --------------------------------------------------
        # Inspect sequence
        # --------------------------------------------------

        print(
            "\nFinal animation count:",
            sequence.Count
        )

        for i in range(
            1,
            sequence.Count + 1
        ):

            try:

                effect = sequence.Item(i)

                print(
                    f"\nEffect {i}"
                )

                print(
                    "  Shape:",
                    effect.Shape.Name
                )

                print(
                    "  Effect ID:",
                    effect.EffectType
                )

                try:

                    print(
                        "  Trigger:",
                        effect.Timing.TriggerType
                    )

                except Exception as e:

                    print(
                        "  Trigger unavailable:",
                        e
                    )

            except Exception as e:

                print(
                    f"Could not inspect effect {i}:",
                    e
                )

        # --------------------------------------------------
        # Save
        # --------------------------------------------------

        # print("\nSaving...")

        # ppt.save_as(
        #     str(OUTPUT)
        # )

        # print(
        #     "Saved:",
        #     OUTPUT
        # )

        # print("\n" + "=" * 70)
        # print("TEST COMPLETE")
        # print("=" * 70)

        input(
            "\nPowerPoint is still open. "
            "Open Slide 1 and inspect the animation pane. "
            "Press Enter to close..."
        )


if __name__ == "__main__":
    main()