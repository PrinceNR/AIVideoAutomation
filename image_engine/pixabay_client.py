import os
import requests

from dotenv import load_dotenv
from image_engine.image_candidate_type import ImageCandidateType


load_dotenv()


class PixabayClient:

    BASE_URL = "https://pixabay.com/api/"

    def __init__(self):

        self.api_key = os.getenv("PIXABAY_API_KEY")

        if not self.api_key:
            raise ValueError(
                "PIXABAY_API_KEY not found in .env"
            )

    def search(
        self,
        query: str,
        per_page: int,
        image_type:
            ImageCandidateType
            = ImageCandidateType.PHOTO
    ):

        params = {
            "key": self.api_key,
            "q": query,
            "per_page": per_page,
            "image_type": image_type.value,
            "safesearch": "true"
        }

        response = requests.get(
            self.BASE_URL,
            params=params
        )

        response.raise_for_status()

        data = response.json()

        image_urls = []

        for hit in data.get("hits", []):

            image_url = (
                hit.get("largeImageURL")
                or hit.get("webformatURL")
            )

            if image_url:
                image_urls.append(image_url)

        return image_urls

    def download_image(
        self,
        image_url: str,
        save_path
    ):

        response = requests.get(image_url)

        response.raise_for_status()

        with open(save_path, "wb") as file:
            file.write(response.content)

        print(f"Downloaded: {save_path}")