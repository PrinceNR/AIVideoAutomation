# from pathlib import Path

# audio = Path(r"output\farming\audio\cultivate\pronunciation.mp3")

# print(audio)
# print(audio.exists())
# print(audio.resolve())

# from presentation.automation.powerpoint_controller import PowerPointController

# with PowerPointController(True) as ppt:

#     ppt.open_presentation("research/manual_audio.pptx")

#     slide = ppt.audio.slide(1)

#     seq = slide.TimeLine.MainSequence

#     print(seq.AddEffect)

#     help(seq.AddEffect)

#     input("Press Enter...")


# from win32com.client import constants

# for name in dir(constants):

#     if "Media" in name:
#         print(name, getattr(constants, name))

#     if "Effect" in name:
#         if "Media" in name:
#             print(name, getattr(constants, name))


from presentation.automation.powerpoint_controller import PowerPointController

with PowerPointController(True) as ppt:

    ppt.open_presentation("research/manual_audio.pptx")

    slide = ppt.audio.slide(1)

    seq = slide.TimeLine.MainSequence

    print("=" * 60)
    print("AddEffect")
    help(seq.AddEffect)

    print("=" * 60)
    print("AddTriggerEffect")
    help(seq.AddTriggerEffect)

    input("Press Enter...")