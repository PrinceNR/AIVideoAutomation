from presentation.automation.powerpoint_controller import PowerPointController

with PowerPointController(True) as ppt:

    ppt.open_presentation("research/manual_audio.pptx")

    slide = ppt.audio.slide(1)

    shapes = slide.Shapes

    print("="*60)
    print("AddMediaObject")
    help(shapes.AddMediaObject)

    print("="*60)
    print("AddMediaObject2")
    help(shapes.AddMediaObject2)

    print("="*60)
    print("AddMediaObjectFromEmbedTag")
    help(shapes.AddMediaObjectFromEmbedTag)

    input("Press Enter...")