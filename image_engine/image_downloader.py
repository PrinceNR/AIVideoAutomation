from pathlib import Path
from image_engine.pexels_client import PexelsClient
from models.word import Word
from config import IMAGE_COUNT
from config import IMAGE_FORMAT


class ImageDownloader:

    def __init__(self):

        self.client = PexelsClient()

    def download_word_images(
        self,
        word: Word,
        lesson_folder: Path,
        per_page: int = IMAGE_COUNT
    ):

        
        images = self.client.search(word, per_page)

        image_folder = lesson_folder / "images" / word.word.lower()

        image_folder.mkdir(
            parents=True,
            exist_ok=True
        )

        for index, image_url in enumerate(images, start=1):

            filename = f"{index:03}.{IMAGE_FORMAT}"

            self.client.download_image(
                image_url,
                image_folder / filename
            )
            # Save the folder location
            # word.image_folder = str(image_folder)
            # word.image_path = str(image_folder / "001.jpg")

        word.image_folder = str(image_folder)
        word.default_image = str(image_folder / "001.jpg")

        print(f"Finished downloading images for {word.word}")