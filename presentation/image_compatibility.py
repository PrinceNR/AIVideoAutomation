from pathlib import Path

from PIL import Image, UnidentifiedImageError


class PresentationImageError(RuntimeError):
    """Raised when an image cannot be prepared for PowerPoint."""


class PresentationImageCompatibility:
    SUPPORTED_SUFFIXES = {
        ".bmp",
        ".gif",
        ".jpeg",
        ".jpg",
        ".png",
        ".tif",
        ".tiff",
        ".wmf",
    }

    def prepare(self, source_path: str | Path) -> Path:
        source = Path(source_path)

        if source.suffix.lower() in self.SUPPORTED_SUFFIXES:
            return source

        if source.suffix.lower() != ".webp":
            raise PresentationImageError(
                f"Unsupported presentation image format: {source}"
            )

        try:
            source_version = source.stat().st_mtime_ns
            converted = source.with_name(
                f"{source.stem}.powerpoint-{source_version}.png"
            )

            if converted.is_file():
                return converted

            with Image.open(source) as image:
                image.load()
                image.save(converted, format="PNG")

            return converted
        except (OSError, UnidentifiedImageError, ValueError) as error:
            raise PresentationImageError(
                f"Could not prepare presentation image '{source}': {error}"
            ) from error
