import os


def load_channels():
    channels = []
    if os.path.exists("channels.txt"):
        with open("channels.txt", "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    channels.append(line)
    return channels


SOURCE_CHANNELS  = load_channels()
DEFAULT_PRIVACY  = os.environ.get("VIDEO_PRIVACY",  "public")
DEFAULT_CATEGORY = os.environ.get("VIDEO_CATEGORY", "10")  # 10 = Music
DEFAULT_LANGUAGE = "en"
DEFAULT_TAGS     = [
    "sleep music",
    "relaxing music",
    "deep sleep",
    "meditation",
    "stress relief",
    "calm music",
    "sleep sounds",
    "relaxation",
    "peaceful music",
    "ambient music",
]

TITLE_PREFIX = os.environ.get("TITLE_PREFIX", "")
TITLE_SUFFIX = os.environ.get("TITLE_SUFFIX", "")

# ── Video Settings ─────────────────────────────
MIN_VIDEO_DURATION_MINUTES = 60    # Skip if less than 60 min
MAX_VIDEO_DURATION_MINUTES = 1440  # Max 24 hours
PART_DURATION_HOURS        = 4     # Split into 4 hour parts

# ── Video Quality ──────────────────────────────
VIDEO_QUALITY = (
    "bestaudio[ext=m4a]"
    "/bestaudio[ext=mp3]"
    "/bestaudio"
    "/best"
)

# ── Paths ──────────────────────────────────────
BASE_DIR            = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)
DOWNLOADS_DIR       = os.path.join(BASE_DIR, "downloads")
THUMBNAILS_DIR      = os.path.join(BASE_DIR, "thumbnails")
PROCESSED_DIR       = os.path.join(BASE_DIR, "processed")
ASSETS_DIR          = os.path.join(BASE_DIR, "assets")
DATABASE_FILE       = os.path.join(BASE_DIR, "database.json")
AUTH_TOKEN_FILE     = os.path.join(BASE_DIR, "token.json")
CLIENT_SECRETS_FILE = os.path.join(BASE_DIR, "client_secrets.json")
BACKGROUND_IMAGE    = os.path.join(ASSETS_DIR, "background.jpg")

for d in [DOWNLOADS_DIR, THUMBNAILS_DIR, PROCESSED_DIR, ASSETS_DIR]:
    os.makedirs(d, exist_ok=True)
