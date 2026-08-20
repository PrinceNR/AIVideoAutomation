import os
import time

import requests

from dotenv import load_dotenv
from image_engine.image_candidate_type import ImageCandidateType


load_dotenv()


class PixabayCooldownError(RuntimeError):

    def __init__(self, retry_after_seconds: float):

        self.retry_after_seconds = max(
            0.0,
            retry_after_seconds
        )

        super().__init__(
            "Pixabay is cooling down for "
            f"{self.retry_after_seconds:.0f} second(s)"
        )


class PixabayClient:

    BASE_URL = "https://pixabay.com/api/"
    COOLDOWN_SECONDS = 60.0

    def __init__(self):

        self.api_key = os.getenv("PIXABAY_API_KEY")

        if not self.api_key:
            raise ValueError(
                "PIXABAY_API_KEY not found in .env"
            )

        self._cooldown_until = 0.0

    def search(
        self,
        query: str,
        per_page: int,
        image_type:
            ImageCandidateType
            = ImageCandidateType.PHOTO
    ):

        self._raise_if_cooling_down()

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

        self._handle_rate_limit(response)
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

        self._raise_if_cooling_down()

        response = requests.get(image_url)

        self._handle_rate_limit(response)
        response.raise_for_status()

        with open(save_path, "wb") as file:
            file.write(response.content)

        print(f"Downloaded: {save_path}")

    def _raise_if_cooling_down(self):

        remaining = (
            self._cooldown_until
            - time.monotonic()
        )

        if remaining > 0:
            raise PixabayCooldownError(remaining)

    def _handle_rate_limit(self, response):

        if response.status_code != 429:
            return

        self._cooldown_until = (
            time.monotonic()
            + self.COOLDOWN_SECONDS
        )

        raise PixabayCooldownError(
            self.COOLDOWN_SECONDS
        )
