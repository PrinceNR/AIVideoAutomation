from video_engine.pexels_video_client import (
    PexelsVideoClient
)


def main():

    client = (
        PexelsVideoClient()
    )

    candidates = client.search(
        query="person nodding head",
        per_page=3
    )

    print(
        f"\nVideo candidates: "
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
            f"Duration: "
            f"{candidate.duration}s"
        )

        print(
            f"Resolution: "
            f"{candidate.width}x"
            f"{candidate.height}"
        )

        print(
            f"Video URL: "
            f"{candidate.video_url}"
        )


if __name__ == "__main__":
    main()