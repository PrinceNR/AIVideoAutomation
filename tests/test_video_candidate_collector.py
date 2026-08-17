from video_engine.video_candidate_collector import (
    VideoCandidateCollector
)


def main():

    collector = (
        VideoCandidateCollector()
    )

    candidates = collector.collect(
        query="person nodding head"
    )

    print(
        f"\nAccepted short videos: "
        f"{len(candidates)}"
    )

    for index, candidate in enumerate(
        candidates,
        start=1
    ):

        print(
            f"\nCandidate {index}"
        )

        print(
            f"Source: "
            f"{candidate.source}"
        )

        print(
            f"ID: "
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