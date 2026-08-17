from pathlib import Path

from image_engine.pixabay_client import (
    PixabayClient
)

from image_engine.image_candidate_type import (
    ImageCandidateType
)


def main():

    client = PixabayClient()

    query = (
        "person thinking decision"
    )

    urls = client.search(
        query=query,
        per_page=3,
        image_type=(
            ImageCandidateType
            .ILLUSTRATION
        )
    )

    print(
        f"\nIllustrations found: "
        f"{len(urls)}"
    )

    output_folder = Path(
        "output/"
        "test_pixabay_illustrations"
    )

    output_folder.mkdir(
        parents=True,
        exist_ok=True
    )

    for index, url in enumerate(
        urls,
        start=1
    ):

        path = (
            output_folder
            / f"illustration_{index:03d}.jpg"
        )

        client.download_image(
            url,
            path
        )

        print(
            f"Saved: {path}"
        )


if __name__ == "__main__":
    main()