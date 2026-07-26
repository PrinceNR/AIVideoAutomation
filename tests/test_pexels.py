from image_engine.pexels_client import PexelsClient

client = PexelsClient()

images = client.search("whisk")

print("\nImages found:\n")

for image in images:
    print(image)