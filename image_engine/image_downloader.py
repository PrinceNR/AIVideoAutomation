from pathlib import Path

from image_engine.pexels_client import PexelsClient


class ImageDownloader:

    def __init__(self):

        self.client = PexelsClient()

    def download_word_images(
        self,
        word: str,
        lesson_folder: Path,
        per_page: int = 3
    ):

        images = self.client.search(word, per_page)

        image_folder = lesson_folder / "images" / word.lower()

        image_folder.mkdir(
            parents=True,
            exist_ok=True
        )

        for index, image_url in enumerate(images, start=1):

            filename = f"{index:03}.jpg"

            self.client.download_image(
                image_url,
                image_folder / filename
            )

        print(f"Finished downloading images for {word}")