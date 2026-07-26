from pathlib import Path

from image_engine.image_downloader import ImageDownloader

lesson_folder = Path("output/test")

lesson_folder.mkdir(
    parents=True,
    exist_ok=True
)

downloader = ImageDownloader()

downloader.download_word_images(
    "church",
    lesson_folder
)