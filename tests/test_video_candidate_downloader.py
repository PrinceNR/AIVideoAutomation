from pathlib import Path

from models.word import Word

from video_engine.video_search_service import (
    VideoSearchService
)

from video_engine.video_candidate_downloader import (
    VideoCandidateDownloader
)


def main():

    word = Word(
        word="nod",

        meaning=(
            "to move the head "
            "up and down"
        ),

        pronunciation="",
        part_of_speech="verb",
        difficulty="",

        translations={},

        present_sentence=(
            "He nods his head "
            "in agreement."
        ),

        past_sentence="",
        future_sentence="",

        base_form="nod",
        present_form="nods",
        past_form="nodded",

        synonyms=[],
        antonyms=[],

        image_keywords=[
            "person nodding head",
            "head nod agreement",
            "person saying yes gesture"
        ],

        search_query=(
            "person nodding head"
        )
    )

    search_service = (
        VideoSearchService()
    )

    search_result = (
        search_service.search(
            word
        )
    )

    candidates = (
        search_result.get(
            "candidates",
            []
        )
    )

    if not candidates:

        print(
            "\nNo short videos "
            "available to download."
        )

        return

    downloader = (
        VideoCandidateDownloader()
    )

    downloaded = (
        downloader.download(
            candidates=candidates,

            output_folder=Path(
                "output/"
                "test_video_download"
            ),

            max_downloads=3
        )
    )

    print(
        f"\nDownloaded candidates: "
        f"{len(downloaded)}"
    )

    for candidate in downloaded:

        print(
            f"\nSource: "
            f"{candidate.source}"
        )

        print(
            f"Duration: "
            f"{candidate.duration}s"
        )

        print(
            f"Local path: "
            f"{candidate.local_path}"
        )


if __name__ == "__main__":
    main()