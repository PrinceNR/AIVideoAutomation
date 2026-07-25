import os
import requests

from dotenv import load_dotenv

load_dotenv()


class PexelsClient:

    BASE_URL = "https://api.pexels.com/v1/search"

    def __init__(self):

        self.api_key = os.getenv("PEXELS_API_KEY")

        if not self.api_key:
            raise ValueError("PEXELS_API_KEY not found in .env")


    def download_image(self, image_url: str, save_path):

        response = requests.get(image_url)

        response.raise_for_status()

        with open(save_path, "wb") as file:
            file.write(response.content)

        print(f"Downloaded: {save_path}")

    def search(self, query: str, per_page: int = 3):

        headers = {
            "Authorization": self.api_key
        }

        params = {
            "query": query,
            "per_page": per_page
        }

        response = requests.get(
            self.BASE_URL,
            headers=headers,
            params=params
        )

        response.raise_for_status()

        data = response.json()

        image_urls = []

        for photo in data.get("photos", []):

            image_urls.append(photo["src"]["large"])

        return image_urls