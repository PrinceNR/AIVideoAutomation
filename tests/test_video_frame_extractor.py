from pathlib import Path

from video_engine.video_frame_extractor import (
    VideoFrameExtractor
)


def main():

    video_folder = Path(
        "output/test_video_download"
    )

    videos = list(
        video_folder.glob(
            "*.mp4"
        )
    )

    if not videos:

        print(
            "No downloaded MP4 "
            "found for testing."
        )

        return

    video_path = videos[0]

    print(
        f"Testing video: "
        f"{video_path}"
    )

    extractor = (
        VideoFrameExtractor(
            frame_count=4
        )
    )

    frames = extractor.extract(
        video_path=video_path,

        output_folder=(
            video_folder
            / "frames"
        )
    )

    print(
        f"\nFrames extracted: "
        f"{len(frames)}"
    )

    for frame in frames:

        print(
            frame
        )


if __name__ == "__main__":
    main()