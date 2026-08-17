from pathlib import Path

from models.word import Word

from media_engine.media_selection_service import (
    MediaSelectionService
)


class FakeVideoSelectionService:

    def select(
        self,
        word,
        output_folder
    ):

        if word.word == "wave":

            return {
                "status": "selected",
                "selected_video":
                    "output/test/wave.mp4",
                "preview_image":
                    "output/test/frame_02.jpg",
                "selected_score": 92,
                "selected_query":
                    "woman waving hand",
                "source": "pexels",
                "duration": 5.0,
                "loop_suitable": True,
                "attempts": []
            }

        return {
            "status":
                "no_suitable_video",
            "selected_video":
                None,
            "selected_score":
                35,
            "selected_query":
                None,
            "attempts":
                []
        }


class FakeImageDownloader:

    def download_word_images(
        self,
        word,
        lesson_folder
    ):

        word.default_image = (
            f"output/test/"
            f"{word.word}.jpg"
        )

        word.media_type = "photo"


def make_word(
    word_text,
    preferred_media
):

    return Word(
        word=word_text,
        meaning="test meaning",
        pronunciation="",
        part_of_speech="verb",
        difficulty="",
        translations={},

        present_sentence="Test sentence.",
        past_sentence="",
        future_sentence="",

        base_form=word_text,
        present_form=word_text,
        past_form=word_text,

        synonyms=[],
        antonyms=[],

        image_keywords=[],
        search_query="",

        preferred_media=preferred_media
    )


def main():

    service = MediaSelectionService(
        video_selection_service=(
            FakeVideoSelectionService()
        ),
        image_downloader=(
            FakeImageDownloader()
        )
    )

    lesson_folder = Path(
        "output/test_media_routing"
    )

    wave = make_word(
        "wave",
        "video"
    )

    nod = make_word(
        "nod",
        "video"
    )

    cup = make_word(
        "cup",
        "photo"
    )

    service.process_word(
        wave,
        lesson_folder
    )

    service.process_word(
        nod,
        lesson_folder
    )

    service.process_word(
        cup,
        lesson_folder
    )

    print("\n--- FINAL RESULTS ---")

    print(
        f"wave: "
        f"{wave.media_type}, "
        f"{wave.default_video}, "
        f"{wave.default_image}"
    )

    print(
        f"nod: "
        f"{nod.media_type}, "
        f"{nod.default_video}, "
        f"{nod.default_image}"
    )

    print(
        f"cup: "
        f"{cup.media_type}, "
        f"{cup.default_video}, "
        f"{cup.default_image}"
    )


if __name__ == "__main__":
    main()