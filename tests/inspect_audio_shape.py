from presentation.automation.powerpoint_controller import PowerPointController

with PowerPointController(True) as ppt:

    ppt.open_presentation("research/manual_audio.pptx")

    slide = ppt.audio.slide(1)

    # Find the audio icon
    audio_shape = None
    for shape in slide.Shapes:
        if shape.Name == "pronunciation":
            audio_shape = shape
            break

    print("=" * 80)
    print("Shape:", audio_shape.Name)
    print("=" * 80)

    for attr in dir(audio_shape):

        if attr.startswith("_"):
            continue

        try:
            value = getattr(audio_shape, attr)

            if callable(value):
                continue

            print(attr)
            print(type(value))
            print(value)
            print("-" * 40)

        except Exception:
            pass

    input("Press Enter...")