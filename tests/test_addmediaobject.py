from pathlib import Path
from presentation.automation.powerpoint_controller import PowerPointController

audio = Path(
    r"output\farming\audio\cultivate\pronunciation.mp3"
).resolve()

with PowerPointController(True) as ppt:

    ppt.open_presentation("output/test_builder.pptx")

    slide = ppt.audio.slide(1)

    media = slide.Shapes.AddMediaObject(
        str(audio),
        0,
        0,
        32,
        32
    )

    print(media.Name)
    print(media.Type)

    input("Press Enter...")

    ppt.save_as("research/addmediaobject_test.pptx")