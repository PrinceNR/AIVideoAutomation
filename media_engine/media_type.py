from enum import Enum


class MediaType(
    str,
    Enum
):

    PHOTO = "photo"

    ILLUSTRATION = (
        "illustration"
    )

    VIDEO = "video"