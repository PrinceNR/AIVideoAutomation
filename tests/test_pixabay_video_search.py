from video_engine.pixabay_video_client import (
    PixabayVideoClient
)


def main():

    client = (
        PixabayVideoClient()
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

        print(
            f"Video URL: "
            f"{candidate.video_url}"
        )


if __name__ == "__main__":
    main()