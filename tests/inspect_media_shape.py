from pathlib import Path
from presentation.automation.powerpoint_controller import PowerPointController


def inspect(obj):

    print("=" * 80)

    for name in dir(obj):

        if name.startswith("_"):
            continue

        try:
            value = getattr(obj, name)

            if callable(value):
                continue

            print(f"\n{name}")
            print("-" * 40)
            print(type(value))
            print(value)

        except Exception as e:
            print(f"{name} -> ERROR: {e}")

    print("=" * 80)


def main():

    audio_file = Path(
        r"output\farming\audio\cultivate\pronunciation.mp3"
    ).resolve()

    with PowerPointController(True) as ppt:

        ppt.open_presentation("output/test_builder.pptx")

        media = ppt.audio.add_audio(
            slide_index=1,
            audio_path=str(audio_file)
        )
        print(type(media.MediaFormat))
        print(media.MediaFormat)

        print(type(media.AnimationSettings))
        print(media.AnimationSettings)

        print(type(media.ActionSettings))
        print(media.ActionSettings)

        inspect(media)

        print("\n=== MediaFormat ===")
        inspect(media.MediaFormat)

        print("\n=== AnimationSettings ===")
        inspect(media.AnimationSettings)

        input("Press Enter...")


if __name__ == "__main__":
    main()