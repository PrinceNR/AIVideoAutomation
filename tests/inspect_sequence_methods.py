from presentation.automation.powerpoint_controller import PowerPointController


def inspect_object(name, obj):
    print("=" * 80)
    print(name)
    print("=" * 80)

    methods = []

    for attr in dir(obj):
        if attr.startswith("_"):
            continue

        try:
            value = getattr(obj, attr)

            if callable(value):
                methods.append(attr)

        except:
            pass

    methods.sort()

    for m in methods:
        print(m)


def main():

    with PowerPointController(True) as ppt:

        ppt.open_presentation("research/manual_audio.pptx")

        slide = ppt.audio.slide(1)

        inspect_object(
            "MainSequence",
            slide.TimeLine.MainSequence
        )

        if slide.TimeLine.InteractiveSequences.Count > 0:

            inspect_object(
                "InteractiveSequence",
                slide.TimeLine.InteractiveSequences.Item(1)
            )

        input("\nPress Enter...")


if __name__ == "__main__":
    main()