from pathlib import Path

from image_engine.pexels_client import (
    PexelsClient
)

from image_engine.pixabay_client import (
    PixabayClient
)
from image_engine.image_candidate_type import (
    ImageCandidateType
)

from config import (
    IMAGE_COUNT,
    IMAGE_FORMAT
)


class ImageCandidateCollector:

    def __init__(
        self,
        pexels_client=None,
        pixabay_client=None
    ):

        self.pexels_client = (
            pexels_client
            or PexelsClient()
        )

        self.pixabay_client = (
            pixabay_client
            or PixabayClient()
        )

    def collect(
        self,
        query: str,
        image_folder: Path,
        attempt: int,
        per_source: int = IMAGE_COUNT,
        candidate_type: ImageCandidateType = (
            ImageCandidateType.PHOTO
        )
    ) -> list[Path]:

        image_folder = Path(
            image_folder
        )

        image_folder.mkdir(
            parents=True,
            exist_ok=True
        )

        candidates = []

        # -----------------------------------------
        # Pexels supports stock photos
        # -----------------------------------------

        if candidate_type == ImageCandidateType.PHOTO:

            candidates.extend(
                self._collect_from_source(
                    source_name="pexels",
                    client=self.pexels_client,
                    query=query,
                    image_folder=image_folder,
                    attempt=attempt,
                    per_source=per_source,
                    candidate_type=candidate_type
                )
            )


        # -----------------------------------------
        # Pixabay supports photos,
        # illustrations and vectors
        # -----------------------------------------

        candidates.extend(
            self._collect_from_source(
                source_name="pixabay",
                client=self.pixabay_client,
                query=query,
                image_folder=image_folder,
                attempt=attempt,
                per_source=per_source,
                candidate_type=candidate_type,
                search_kwargs={
                    "image_type": candidate_type
                }
            )
        )

        return candidates

    def _collect_from_source(
        self,
        source_name,
        client,
        query,
        image_folder,
        attempt,
        per_source,
        candidate_type,
        search_kwargs=None
    ) -> list[Path]:

        search_kwargs = (
            search_kwargs or {}
        )

        downloaded = []

        try:

            print(
                f"Searching {source_name.title()}: "
                f"{query}"
            )

            image_urls = client.search(
                query,
                per_source,
                **search_kwargs
            )

            for index, image_url in enumerate(
                image_urls,
                start=1
            ):

                filename = (
                    f"attempt_{attempt:02d}_"
                    f"{candidate_type.value}_"
                    f"{source_name}_"
                    f"{index:03d}."
                    f"{IMAGE_FORMAT}"
                )

                save_path = (
                    image_folder /
                    filename
                )

                try:

                    client.download_image(
                        image_url,
                        save_path
                    )

                    downloaded.append(
                        save_path
                    )

                except Exception as error:

                    print(
                        f"Failed to download "
                        f"{source_name} candidate "
                        f"{index}: {error}"
                    )

                    continue

        except Exception as error:

            print(
                f"{source_name.title()} search "
                f"failed: {error}"
            )

        return downloaded