from enum import Enum


class ImageCandidateType(
    str,
    Enum
):

    PHOTO = "photo"

    ILLUSTRATION = (
        "illustration"
    )

    VECTOR = "vector"