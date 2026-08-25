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
        "handwriting_pen": 0,
    }

    SENTENCE_DIRECTIONS = {
        "left_to_right",
    }

    HANDWRITING_FALLBACK_EFFECTS = {
        "text_only",
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

    handwriting_pen_enabled: bool
    handwriting_pen_image: str
    handwriting_pen_width: float
    handwriting_pen_offset_x: float
    handwriting_pen_offset_y: float
    handwriting_hide_pen_after_reveal: bool
    handwriting_pen_hide_duration: float
    handwriting_fallback_effect: str
    handwriting_letter_delay: float
    handwriting_line_return_duration: float
    handwriting_audio_gap: float
    handwriting_pen_alpha_threshold: int
    handwriting_pen_background_tolerance: int

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
        self._validate_name(
            "ANIMATION_HANDWRITING_FALLBACK_EFFECT",
            self.handwriting_fallback_effect,
            self.HANDWRITING_FALLBACK_EFFECTS,
        )
        self._validate_boolean(
            "ANIMATION_HANDWRITING_PEN_ENABLED",
            self.handwriting_pen_enabled,
        )
        self._validate_boolean(
            "ANIMATION_HANDWRITING_HIDE_PEN_AFTER_REVEAL",
            self.handwriting_hide_pen_after_reveal,
        )
        self._validate_non_empty_string(
            "ANIMATION_HANDWRITING_PEN_IMAGE",
            self.handwriting_pen_image,
        )
        self._validate_positive(
            "ANIMATION_HANDWRITING_PEN_WIDTH",
            self.handwriting_pen_width,
        )
        self._validate_positive(
            "ANIMATION_HANDWRITING_LETTER_DELAY",
            self.handwriting_letter_delay,
        )
        self._validate_numeric(
            "ANIMATION_HANDWRITING_PEN_OFFSET_X",
            self.handwriting_pen_offset_x,
        )
        self._validate_numeric(
            "ANIMATION_HANDWRITING_PEN_OFFSET_Y",
            self.handwriting_pen_offset_y,
        )
        self._validate_byte(
            "ANIMATION_HANDWRITING_PEN_ALPHA_THRESHOLD",
            self.handwriting_pen_alpha_threshold,
        )
        self._validate_byte(
            "ANIMATION_HANDWRITING_PEN_BACKGROUND_TOLERANCE",
            self.handwriting_pen_background_tolerance,
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
            (
                "ANIMATION_HANDWRITING_PEN_HIDE_DURATION",
                self.handwriting_pen_hide_duration,
            ),
            (
                "ANIMATION_HANDWRITING_LINE_RETURN_DURATION",
                self.handwriting_line_return_duration,
            ),
            (
                "ANIMATION_HANDWRITING_AUDIO_GAP",
                self.handwriting_audio_gap,
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
            handwriting_pen_enabled=(
                config.ANIMATION_HANDWRITING_PEN_ENABLED
            ),
            handwriting_pen_image=(
                config.ANIMATION_HANDWRITING_PEN_IMAGE
            ),
            handwriting_pen_width=(
                config.ANIMATION_HANDWRITING_PEN_WIDTH
            ),
            handwriting_pen_offset_x=(
                config.ANIMATION_HANDWRITING_PEN_OFFSET_X
            ),
            handwriting_pen_offset_y=(
                config.ANIMATION_HANDWRITING_PEN_OFFSET_Y
            ),
            handwriting_hide_pen_after_reveal=(
                config.ANIMATION_HANDWRITING_HIDE_PEN_AFTER_REVEAL
            ),
            handwriting_pen_hide_duration=(
                config.ANIMATION_HANDWRITING_PEN_HIDE_DURATION
            ),
            handwriting_fallback_effect=(
                config.ANIMATION_HANDWRITING_FALLBACK_EFFECT
            ),
            handwriting_letter_delay=(
                config.ANIMATION_HANDWRITING_LETTER_DELAY
            ),
            handwriting_line_return_duration=(
                config.ANIMATION_HANDWRITING_LINE_RETURN_DURATION
            ),
            handwriting_audio_gap=(
                config.ANIMATION_HANDWRITING_AUDIO_GAP
            ),
            handwriting_pen_alpha_threshold=(
                config.ANIMATION_HANDWRITING_PEN_ALPHA_THRESHOLD
            ),
            handwriting_pen_background_tolerance=(
                config
                .ANIMATION_HANDWRITING_PEN_BACKGROUND_TOLERANCE
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

    @staticmethod
    def _validate_byte(
        setting_name,
        value,
    ):
        if not isinstance(value, int) or isinstance(value, bool):
            raise AnimationConfigurationError(
                f"{setting_name} must be an integer from 0 to 255; "
                f"received {value!r}."
            )

        if not 0 <= value <= 255:
            raise AnimationConfigurationError(
                f"{setting_name} must be from 0 to 255; "
                f"received {value}."
            )

    @staticmethod
    def _validate_positive(
        setting_name,
        value,
    ):
        VisualAnimationSettings._validate_numeric(
            setting_name,
            value,
        )

        if value <= 0:
            raise AnimationConfigurationError(
                f"{setting_name} must be greater than 0; "
                f"received {value}."
            )

    @staticmethod
    def _validate_numeric(
        setting_name,
        value,
    ):
        if (
            not isinstance(value, (int, float))
            or isinstance(value, bool)
        ):
            raise AnimationConfigurationError(
                f"{setting_name} must be numeric; "
                f"received {value!r}."
            )

    @staticmethod
    def _validate_boolean(
        setting_name,
        value,
    ):
        if not isinstance(value, bool):
            raise AnimationConfigurationError(
                f"{setting_name} must be True or False; "
                f"received {value!r}."
            )

    @staticmethod
    def _validate_non_empty_string(
        setting_name,
        value,
    ):
        if not isinstance(value, str) or not value.strip():
            raise AnimationConfigurationError(
                f"{setting_name} must be a non-empty path."
            )
