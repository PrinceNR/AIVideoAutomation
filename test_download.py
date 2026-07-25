from pathlib import Path

from image_engine.pexels_client import PexelsClient

client = PexelsClient()

images = client.search("whisk")

folder = Path("output/test")

folder.mkdir(parents=True, exist_ok=True)

client.download_image(
    images[0],
    folder / "000.jpg"
)
client.download_image(
    images[3],
    folder / "003.jpg"
)
client.download_image(
    images[6],
    folder / "006.jpg"
)

# for i, image in enumerate(images[:3], start=1):
#     client.download_image(image, folder / f"{i:03}.jpg")

print("Finished!")
