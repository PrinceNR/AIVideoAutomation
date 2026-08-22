from dataclasses import dataclass

import config


class AnimationConfigurationError(ValueError):
    """Raised when a visual-animation setting is invalid."""


@dataclass(frozen=True)
class VisualAnimationSettings:

    EFFECT_IDS = {
        "fade": 10,
        "wipe": 22,
    }

    TRANSITION_IDS = {
        "none": 0,
        "fade": 1793,
    }

    TRANSITION_SPEED_IDS = {
        "slow": 1,
        "medium": 2,
        "fast": 3,
    }

    DIRECTION_IDS = {
        None: None,
        "none": None,
        "left": 4,
    }

    SENTENCE_EFFECT_IDS = {
        "reveal_mask": 0,
    }

    SENTENCE_DIRECTIONS = {
        "left_to_right",
    }

    new_word_transition: str
    continuation_transition: str
    transition_speed: str

    word_effect: str
    word_duration: float
    word_direction: str | None

    pronunciation_effect: str
    pronunciation_duration: float

    meaning_effect: str
    meaning_duration: float

    translation_effect: str
    translation_duration: float

    verb_form_effect: str
    verb_form_duration: float

    image_effect: str
    image_duration: float

    sentence_effect: str
    sentence_duration: float
    sentence_direction: str
    sentence_delay: float
    sentence_mask_color: str

    visual_delay: float

    def __post_init__(self):
        self._validate_name(
            "ANIMATION_NEW_WORD_TRANSITION",
            self.new_word_transition,
            self.TRANSITION_IDS,
        )
        self._validate_name(
            "ANIMATION_CONTINUATION_TRANSITION",
            self.continuation_transition,
            self.TRANSITION_IDS,
        )
        self._validate_name(
            "ANIMATION_TRANSITION_SPEED",
            self.transition_speed,
            self.TRANSITION_SPEED_IDS,
        )

        for setting_name, value in (
            ("ANIMATION_WORD_EFFECT", self.word_effect),
            (
                "ANIMATION_PRONUNCIATION_EFFECT",
                self.pronunciation_effect,
            ),
            ("ANIMATION_MEANING_EFFECT", self.meaning_effect),
            (
                "ANIMATION_TRANSLATION_EFFECT",
                self.translation_effect,
            ),
            (
                "ANIMATION_VERB_FORM_EFFECT",
                self.verb_form_effect,
            ),
            ("ANIMATION_IMAGE_EFFECT", self.image_effect),
        ):
            self._validate_name(
                setting_name,
                value,
                self.EFFECT_IDS,
            )

        self._validate_name(
            "ANIMATION_WORD_DIRECTION",
            self.word_direction,
            self.DIRECTION_IDS,
        )
        self._validate_name(
            "ANIMATION_SENTENCE_EFFECT",
            self.sentence_effect,
            self.SENTENCE_EFFECT_IDS,
        )
        self._validate_name(
            "ANIMATION_SENTENCE_DIRECTION",
            self.sentence_direction,
            self.SENTENCE_DIRECTIONS,
        )
        self._parse_mask_color(
            self.sentence_mask_color
        )
        for setting_name, value in (
            ("ANIMATION_WORD_DURATION", self.word_duration),
            (
                "ANIMATION_PRONUNCIATION_DURATION",
                self.pronunciation_duration,
            ),
            ("ANIMATION_MEANING_DURATION", self.meaning_duration),
            (
                "ANIMATION_TRANSLATION_DURATION",
                self.translation_duration,
            ),
            (
                "ANIMATION_VERB_FORM_DURATION",
                self.verb_form_duration,
            ),
            ("ANIMATION_IMAGE_DURATION", self.image_duration),
            (
                "ANIMATION_SENTENCE_DURATION",
                self.sentence_duration,
            ),
            (
                "ANIMATION_SENTENCE_DELAY",
                self.sentence_delay,
            ),
            ("ANIMATION_VISUAL_DELAY", self.visual_delay),
        ):
            self._validate_non_negative(
                setting_name,
                value,
            )

    @classmethod
    def from_project_config(cls):
        return cls(
            new_word_transition=(
                config.ANIMATION_NEW_WORD_TRANSITION
            ),
            continuation_transition=(
                config.ANIMATION_CONTINUATION_TRANSITION
            ),
            transition_speed=(
                config.ANIMATION_TRANSITION_SPEED
            ),
            word_effect=config.ANIMATION_WORD_EFFECT,
            word_duration=config.ANIMATION_WORD_DURATION,
            word_direction=config.ANIMATION_WORD_DIRECTION,
            pronunciation_effect=(
                config.ANIMATION_PRONUNCIATION_EFFECT
            ),
            pronunciation_duration=(
                config.ANIMATION_PRONUNCIATION_DURATION
            ),
            meaning_effect=config.ANIMATION_MEANING_EFFECT,
            meaning_duration=config.ANIMATION_MEANING_DURATION,
            translation_effect=(
                config.ANIMATION_TRANSLATION_EFFECT
            ),
            translation_duration=(
                config.ANIMATION_TRANSLATION_DURATION
            ),
            verb_form_effect=(
                config.ANIMATION_VERB_FORM_EFFECT
            ),
            verb_form_duration=(
                config.ANIMATION_VERB_FORM_DURATION
            ),
            image_effect=config.ANIMATION_IMAGE_EFFECT,
            image_duration=config.ANIMATION_IMAGE_DURATION,
            sentence_effect=config.ANIMATION_SENTENCE_EFFECT,
            sentence_duration=(
                config.ANIMATION_SENTENCE_DURATION
            ),
            sentence_direction=(
                config.ANIMATION_SENTENCE_DIRECTION
            ),
            sentence_delay=config.ANIMATION_SENTENCE_DELAY,
            sentence_mask_color=(
                config.ANIMATION_SENTENCE_MASK_COLOR
            ),
            visual_delay=config.ANIMATION_VISUAL_DELAY,
        )

    def effect_id(self, effect_name):
        return self.EFFECT_IDS[effect_name]

    def transition_id(self, transition_name):
        return self.TRANSITION_IDS[transition_name]

    def transition_speed_id(self):
        return self.TRANSITION_SPEED_IDS[
            self.transition_speed
        ]

    def direction_id(self, direction_name):
        return self.DIRECTION_IDS[direction_name]

    def sentence_effect_id(self):
        return self.SENTENCE_EFFECT_IDS[
            self.sentence_effect
        ]

    def sentence_mask_rgb(self):
        return self._parse_mask_color(
            self.sentence_mask_color
        )

    @staticmethod
    def _parse_mask_color(value):
        if not isinstance(value, str):
            raise AnimationConfigurationError(
                "ANIMATION_SENTENCE_MASK_COLOR must be a "
                "hex color such as '#FFFFFF'."
            )

        hexadecimal = value.strip().lstrip("#")

        if len(hexadecimal) != 6:
            raise AnimationConfigurationError(
                "ANIMATION_SENTENCE_MASK_COLOR must contain "
                "exactly six hexadecimal digits."
            )

        try:
            red = int(hexadecimal[0:2], 16)
            green = int(hexadecimal[2:4], 16)
            blue = int(hexadecimal[4:6], 16)
        except ValueError as error:
            raise AnimationConfigurationError(
                "ANIMATION_SENTENCE_MASK_COLOR must be a "
                "valid hexadecimal color."
            ) from error

        return red | (green << 8) | (blue << 16)

    @staticmethod
    def _validate_name(
        setting_name,
        value,
        allowed_values,
    ):
        if value not in allowed_values:
            allowed = ", ".join(
                repr(option)
                for option in allowed_values
            )
            raise AnimationConfigurationError(
                f"{setting_name} has invalid value "
                f"{value!r}; expected one of: {allowed}."
            )

    @staticmethod
    def _validate_non_negative(
        setting_name,
        value,
    ):
        if not isinstance(value, (int, float)):
            raise AnimationConfigurationError(
                f"{setting_name} must be numeric; "
                f"received {value!r}."
            )

        if value < 0:
            raise AnimationConfigurationError(
                f"{setting_name} cannot be negative; "
                f"received {value}."
            )
