from presentation.automation.powerpoint_controller import PowerPointController

with PowerPointController(True) as ppt:

    # ppt.open_presentation("research/manual_audio.pptx")
    ppt.open_presentation("research/manual_after_com.pptx")

    slide = ppt.audio.slide(1)

    shape = None
    for s in slide.Shapes:
        if s.Name == "pronunciation":
            shape = s
            break

    print("=" * 60)

    candidates = [
        "MediaFormat",
        "AnimationSettings",
        "ActionSettings",
        "PlaySettings",
        "SoundFormat",
        "LinkFormat",
        "OLEFormat",
        "PictureFormat",
        "Tags",
    ]

    for name in candidates:

        print(name)

        try:
            obj = getattr(shape, name)

            action = shape.ActionSettings

            print("Count:", action.Count)

            for i in range(1, action.Count + 1):

                a = action.Item(i)

                print("=" * 40)
                print("Action", i)

                for attr in [
                    "Action",
                    "AnimateAction",
                    "Hyperlink",
                    "Run",
                    "ShowAndReturn",
                    "SlideShowName",
                ]:
                    try:
                        print(attr, "=", getattr(a, attr))
                    except Exception:
                        pass

            # enumerate child properties

            try:
                for x in dir(obj):

                    if x.startswith("_"):
                        continue

                    try:
                        value = getattr(obj, x)

                        if callable(value):
                            continue

                        print("   ", x, "=", value)

                    except:
                        pass

            except:
                pass

        except Exception as e:

            print("ERROR:", e)

        print("-" * 40)

    input()