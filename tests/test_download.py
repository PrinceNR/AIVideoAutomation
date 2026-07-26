from pathlib import Path

from image_engine.pexels_client import PexelsClient

client = PexelsClient()

images = client.search("church", per_page=5)

folder = Path("output/test")

folder.mkdir(parents=True, exist_ok=True)

# client.download_image(
#     images[0],
#     folder / "000.jpg"
# )

for index, image_url in enumerate(images, start=1):

    filename = f"{index:03}.jpg"

    client.download_image(
        image_url,
        folder / filename
    )


print("Finished!")
