from presentation.automation.powerpoint_controller import PowerPointController


def dump_sequence(name, seq):

    print("=" * 80)
    print(name)
    print("=" * 80)

    for attr in dir(seq):

        if attr.startswith("_"):
            continue

        try:

            value = getattr(seq, attr)

            if callable(value):
                continue

            print(attr)
            print(type(value))
            print(value)

        except Exception:
            pass


with PowerPointController(True) as ppt:

    # ppt.open_presentation("research/manual_audio.pptx")
    ppt.open_presentation("output/test_builder.pptx")

    slide = ppt.audio.slide(1)

    # dump_sequence("MainSequence", slide.TimeLine.MainSequence)
    dump_sequence(
        "Interactive",
        slide.TimeLine.InteractiveSequences.Item(1)
    )

    input("Press Enter...")