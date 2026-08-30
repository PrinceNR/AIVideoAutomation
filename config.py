# =========================================================
# PROJECT
# =========================================================

OUTPUT_FOLDER = "output"

# =========================================================
# CONTENT VERIFICATION
# =========================================================
# Ai models

# CONTENT_VERIFIER_MODEL = "openrouter/free"
CONTENT_VERIFIER_MODEL = "deepseek-v4-flash"

GEMINI_CONTENT_MODEL = "gemini-3.5-flash-lite"
CONTENT_GENERATION_VERBOSE_LOGGING = False
GEMINI_FALLBACK_MODEL = "gemini-3.6-flash"


# =========================================================
# IMAGE & IMAGE VERIFICATION
# =========================================================

IMAGE_COUNT = 3
IMAGE_FORMAT = "jpg"
IMAGE_VERIFICATION_MAX_CANDIDATES = 8


GEMINI_IMAGE_VERIFIER_MODEL = "gemini-3.6-flash"
GEMINI_IMAGE_VERIFIER_FALLBACK_MODEL = (
    "gemini-3.5-flash-lite"
)

IMAGE_MIN_SCORE = 80


# =========================================================
# VIDEO
# =========================================================

VIDEO_MAX_DURATION = 7.0
VIDEO_MIN_DURATION = 2.0
VIDEO_SEARCH_COUNT = 10
VIDEO_VERIFY_COUNT = 3
VIDEO_VERIFICATION_MAX_CANDIDATES = 4

VIDEO_MIN_SCORE = 80

GEMINI_VIDEO_VERIFIER_MODEL = (
    GEMINI_IMAGE_VERIFIER_MODEL
)

GEMINI_VIDEO_VERIFIER_FALLBACK_MODEL = (
    GEMINI_IMAGE_VERIFIER_FALLBACK_MODEL
)

NO_AUDIO_SLIDE_DURATION = 5.0


# =========================================================
# AUDIO
# =========================================================

AZURE_PRONUNCIATION_VOICE = "en-IN-AartiNeural"

PRONUNCIATION_RATE = "0.75"

PRONUNCIATION_MIN_SCORE = 85

TTS_PROVIDER = "azure"

AZURE_NARRATION_VOICE = "en-IN-AartiNeural"

AZURE_NARRATION_RATE = "0.80"

# =========================================================
# PRESENTATION
# =========================================================

PRESENTATION_TEMPLATE_PATH = (
    "templates/vocabulary_template_v3.pptx"
)

PRESENTATION_VERBOSE_LOGGING = False
PRESENTATION_SLIDE_END_PADDING = 0.0


# =========================================================
# PRESENTATION / VISUAL ANIMATION
# =========================================================

ANIMATION_NEW_WORD_TRANSITION = "fade"
ANIMATION_CONTINUATION_TRANSITION = "none"
ANIMATION_TRANSITION_SPEED = "fast"

ANIMATION_WORD_EFFECT = "wipe"
ANIMATION_WORD_DURATION = 0.25
ANIMATION_WORD_DIRECTION = "left"

ANIMATION_PRONUNCIATION_EFFECT = "fade"
ANIMATION_PRONUNCIATION_DURATION = 0.20

ANIMATION_MEANING_EFFECT = "fade"
ANIMATION_MEANING_DURATION = 0.20

ANIMATION_TRANSLATION_EFFECT = "fade"
ANIMATION_TRANSLATION_DURATION = 0.20

ANIMATION_VERB_FORM_EFFECT = "fade"
ANIMATION_VERB_FORM_DURATION = 0.20

ANIMATION_IMAGE_EFFECT = "fade"
ANIMATION_IMAGE_DURATION = 0.25

ANIMATION_SENTENCE_EFFECT = "handwriting_pen"
ANIMATION_SENTENCE_DURATION = 1.20
ANIMATION_SENTENCE_DIRECTION = "left_to_right"
ANIMATION_SENTENCE_DELAY = 0.0
ANIMATION_SENTENCE_MASK_COLOR = "#FFFFFF"

ANIMATION_HANDWRITING_PEN_ENABLED = True
ANIMATION_HANDWRITING_PEN_IMAGE = (
    "presentation/assets/handwriting/hand_pen.png"
)
ANIMATION_HANDWRITING_PEN_WIDTH = 72.0
ANIMATION_HANDWRITING_PEN_OFFSET_X = -4.0
ANIMATION_HANDWRITING_PEN_OFFSET_Y = 0.0
ANIMATION_HANDWRITING_HIDE_PEN_AFTER_REVEAL = True
ANIMATION_HANDWRITING_PEN_HIDE_DURATION = 0.05
ANIMATION_HANDWRITING_FALLBACK_EFFECT = "text_only"
ANIMATION_HANDWRITING_LETTER_DELAY = 0.030
ANIMATION_HANDWRITING_LINE_RETURN_DURATION = 0.12
ANIMATION_HANDWRITING_AUDIO_GAP = 0.10
ANIMATION_HANDWRITING_PEN_ALPHA_THRESHOLD = 8
ANIMATION_HANDWRITING_PEN_BACKGROUND_TOLERANCE = 2

ANIMATION_VISUAL_DELAY = 0.0


# =========================================================
# THUMBNAIL
# =========================================================

THUMBNAIL_TEMPLATE_PATH = (
    "templates/thumbnail/thumbnail_template.pptx"
)

THUMBNAIL_MAX_WORDS = 8

THUMBNAIL_WIDTH = 1280
THUMBNAIL_HEIGHT = 720


# =========================================================
# AUDIO / TIMELINE
# =========================================================

AUDIO_INITIAL_DELAY = 0.7
AUDIO_GAP = 0.5


# =========================================================
# YOUTUBE
# =========================================================

YOUTUBE_METADATA_MODEL = "gemini-flash-latest"

YOUTUBE_METADATA_FALLBACK_MODEL = GEMINI_FALLBACK_MODEL

YOUTUBE_PRIVACY_STATUS = "private"

YOUTUBE_MADE_FOR_KIDS = False

YOUTUBE_CATEGORY_ID = "27"

YOUTUBE_NOTIFY_SUBSCRIBERS = False


# =========================================================
# YOUTUBE AUTH
# =========================================================

YOUTUBE_CLIENT_SECRET_PATH = (
    "credentials/youtube_client_secret.json"
)

YOUTUBE_TOKEN_PATH = (
    "credentials/youtube_token.json"
)
