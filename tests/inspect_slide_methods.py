from presentation.automation.powerpoint_controller import PowerPointController

with PowerPointController(True) as ppt:

    ppt.open_presentation("research/manual_audio.pptx")

    slide = ppt.audio.slide(1)

    print("=" * 80)
    print("Slide methods")
    print("=" * 80)

    for name in dir(slide):

        if name.startswith("_"):
            continue

        try:
            obj = getattr(slide, name)

            if callable(obj):
                print(name)

        except:
            pass

    input("Press Enter...")