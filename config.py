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

PRONUNCIATION_RATE = "0.65"

PRONUNCIATION_MIN_SCORE = 85

TTS_PROVIDER = "azure"

AZURE_NARRATION_VOICE = "en-IN-AartiNeural"

AZURE_NARRATION_RATE = "0.85"

# =========================================================
# PRESENTATION
# =========================================================

PRESENTATION_TEMPLATE_PATH = (
    "templates/vocabulary_template_v3.pptx"
)


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
