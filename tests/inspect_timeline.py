from pathlib import Path
from presentation.automation.powerpoint_controller import PowerPointController


def main():

    audio_file = Path(
        r"output\farming\audio\cultivate\pronunciation.mp3"
    ).resolve()

    with PowerPointController(True) as ppt:

        ppt.open_presentation("research/manual_audio.pptx")

        # ppt.audio.add_audio(
        #     slide_index=1,
        #     audio_path=str(audio_file)
        # )

        slide = ppt.audio.slide(1)

        print("=" * 80)

        for shape in slide.Shapes:

            print(
                shape.Id,
                shape.Name,
                shape.Type
            )

        timeline = slide.TimeLine

        print("="*60)
        print("=" * 80)
        print("MainSequence:", timeline.MainSequence.Count)

        for i in range(1, timeline.MainSequence.Count + 1):

            effect = timeline.MainSequence.Item(i)

            print("-" * 50)

            print("Effect", i)

            print("Shape:", effect.Shape.Name)

            print("EffectType:", effect.EffectType)

            print("DisplayName:", effect.DisplayName)

            timing = effect.Timing

            print()

            print("Timing")

            print("Duration:", timing.Duration)

            print("TriggerType:", timing.TriggerType)

            print("RepeatCount:", timing.RepeatCount)

            print("Restart:", timing.Restart)


        print("="*60)
        print("InteractiveSequences:", timeline.InteractiveSequences.Count)

        for i in range(1, timeline.InteractiveSequences.Count + 1):

            seq = timeline.InteractiveSequences.Item(i)

            print("=" * 80)
            print("Sequence", i)
            print("Effects:", seq.Count)

            for j in range(1, seq.Count + 1):

                effect = seq.Item(j)

                print("-" * 40)
                print("Effect", j)

                try:
                    print("Shape:", effect.Shape.Name)
                except:
                    pass

                try:
                    print("EffectType:", effect.EffectType)
                except:
                    pass

                try:
                    print("DisplayName:", effect.DisplayName)
                except:
                    pass

                try:
                    timing = effect.Timing

                    print("=" * 80)
                    print("Timing Properties")
                    print("=" * 80)

                    for attr in dir(timing):

                        if attr.startswith("_"):
                            continue

                        try:
                            value = getattr(timing, attr)

                            if callable(value):
                                continue

                            print(attr)
                            print("-" * 30)
                            print(type(value))
                            print(value)

                        except Exception as e:
                            print(attr, "-> ERROR:", e)
                except:
                    pass

                try:
                    print("Paragraph:", effect.Paragraph)
                except:
                    pass

                print("=" * 80)
                print("Behaviors:", effect.Behaviors.Count)

                for k in range(1, effect.Behaviors.Count + 1):

                    behavior = effect.Behaviors.Item(k)

                    print("Behavior", k)
                    print("Type:", behavior.Type)

        input("Press Enter...")


if __name__ == "__main__":
    main()