from video_engine.video_candidate import (
    VideoCandidate
)

from video_engine.video_candidate_filter import (
    VideoCandidateFilter
)


def main():

    candidates = [

        VideoCandidate(
            source="pexels",
            video_url="https://example.com/1.mp4",
            duration=6,
            width=1280,
            height=720,
            source_id="1"
        ),

        VideoCandidate(
            source="pexels",
            video_url="https://example.com/2.mp4",
            duration=34,
            width=1366,
            height=720,
            source_id="2"
        ),

        VideoCandidate(
            source="pexels",
            video_url="https://example.com/3.mp4",
            duration=5,
            width=640,
            height=360,
            source_id="3"
        ),

        VideoCandidate(
            source="pexels",
            video_url="https://example.com/4.mp4",
            duration=4,
            width=720,
            height=1280,
            source_id="4"
        )
    ]

    candidate_filter = (
        VideoCandidateFilter()
    )

    filtered = (
        candidate_filter.filter(
            candidates
        )
    )

    print(
        f"Original candidates: "
        f"{len(candidates)}"
    )

    print(
        f"Accepted candidates: "
        f"{len(filtered)}"
    )

    for candidate in filtered:

        print(
            f"\nAccepted ID: "
            f"{candidate.source_id}"
        )

        print(
            f"Duration: "
            f"{candidate.duration}s"
        )

        print(
            f"Resolution: "
            f"{candidate.width}x"
            f"{candidate.height}"
        )


if __name__ == "__main__":
    main()