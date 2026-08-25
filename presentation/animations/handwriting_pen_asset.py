import hashlib
from collections import Counter
from pathlib import Path

from PIL import Image, UnidentifiedImageError


class HandwritingPenAssetError(RuntimeError):
    """Raised when the handwriting pen PNG cannot be normalized."""


class HandwritingPenAssetNormalizer:
    """Prepare a deterministic transparent PNG without changing its source."""

    CACHE_VERSION = "v1"
    PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
    MIN_BACKGROUND_FRACTION = 0.05
    MAX_BACKGROUND_COLORS = 4

    def prepare(
        self,
        source_path,
        alpha_threshold=8,
        background_tolerance=2,
    ):
        source_path = Path(source_path).resolve()
        self._validate_settings(
            alpha_threshold,
            background_tolerance,
        )

        if not source_path.is_file():
            raise HandwritingPenAssetError(
                f"Handwriting pen PNG does not exist: {source_path}"
            )

        try:
            source_bytes = source_path.read_bytes()
        except OSError as error:
            raise HandwritingPenAssetError(
                f"Could not read handwriting pen PNG '{source_path}': "
                f"{error}"
            ) from error

        if not source_bytes.startswith(self.PNG_SIGNATURE):
            raise HandwritingPenAssetError(
                f"Handwriting pen asset is not a valid PNG: {source_path}"
            )

        cache_key = hashlib.sha256(
            source_bytes
            + (
                f"|{self.CACHE_VERSION}|{alpha_threshold}|"
                f"{background_tolerance}"
            ).encode("ascii")
        ).hexdigest()[:16]
        cache_dir = source_path.parent / ".normalized"
        normalized_path = cache_dir / (
            f"{source_path.stem}.normalized-{cache_key}.png"
        )

        if normalized_path.is_file():
            return normalized_path

        try:
            with Image.open(source_path) as source_image:
                source_image.load()
                image = source_image.convert("RGBA")

            palette = self._background_palette(image)
            normalized = self._normalize_pixels(
                image,
                palette,
                alpha_threshold,
                background_tolerance,
            )
            bounds = normalized.getchannel("A").getbbox()

            if bounds is None:
                raise HandwritingPenAssetError(
                    "Handwriting pen normalization removed every pixel."
                )

            normalized = normalized.crop(bounds)
            cache_dir.mkdir(parents=True, exist_ok=True)
            temporary_path = normalized_path.with_suffix(".tmp.png")
            normalized.save(temporary_path, format="PNG")
            temporary_path.replace(normalized_path)
            return normalized_path

        except HandwritingPenAssetError:
            raise
        except (
            OSError,
            UnidentifiedImageError,
            ValueError,
        ) as error:
            raise HandwritingPenAssetError(
                f"Could not normalize handwriting pen PNG "
                f"'{source_path}': {error}"
            ) from error

    def _background_palette(self, image):
        width, height = image.size
        pixels = image.load()
        border = []

        for x in range(width):
            border.append(pixels[x, 0])
            border.append(pixels[x, height - 1])

        for y in range(1, height - 1):
            border.append(pixels[0, y])
            border.append(pixels[width - 1, y])

        minimum_count = max(
            4,
            int(len(border) * self.MIN_BACKGROUND_FRACTION),
        )
        palette = []

        for color, count in Counter(border).most_common():
            red, green, blue, alpha = color

            if count < minimum_count:
                break

            if alpha < 250:
                continue

            if max(red, green, blue) - min(red, green, blue) > 3:
                continue

            palette.append((red, green, blue))

            if len(palette) >= self.MAX_BACKGROUND_COLORS:
                break

        return tuple(palette)

    @staticmethod
    def _normalize_pixels(
        image,
        palette,
        alpha_threshold,
        background_tolerance,
    ):
        normalized = Image.new("RGBA", image.size)
        output = []

        for red, green, blue, alpha in image.getdata():
            clear_low_alpha = alpha <= alpha_threshold
            clear_background = any(
                max(
                    abs(red - background_red),
                    abs(green - background_green),
                    abs(blue - background_blue),
                )
                <= background_tolerance
                for (
                    background_red,
                    background_green,
                    background_blue,
                ) in palette
            )

            if clear_low_alpha or clear_background:
                output.append((red, green, blue, 0))
            else:
                output.append((red, green, blue, alpha))

        normalized.putdata(output)
        return normalized

    @staticmethod
    def _validate_settings(
        alpha_threshold,
        background_tolerance,
    ):
        for setting_name, value in (
            ("alpha threshold", alpha_threshold),
            ("background tolerance", background_tolerance),
        ):
            if not isinstance(value, int) or not 0 <= value <= 255:
                raise HandwritingPenAssetError(
                    f"Handwriting pen {setting_name} must be an integer "
                    f"from 0 to 255; received {value!r}."
                )
