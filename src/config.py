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
DEFAULT_CATEGORY = os.environ.get("VIDEO_CATEGORY", "22")
DEFAULT_LANGUAGE = "en"
DEFAULT_TAGS     = ["sleep", "relaxing", "meditation"]
TITLE_PREFIX     = os.environ.get("TITLE_PREFIX", "")
TITLE_SUFFIX     = os.environ.get("TITLE_SUFFIX", "")

MAX_VIDEO_DURATION_MINUTES = 1440
MIN_VIDEO_DURATION_MINUTES = 60

VIDEO_QUALITY = (
    "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]"
    "/bestvideo[height<=1080]+bestaudio"
    "/best[height<=1080]"
    "/best"
)

BASE_DIR            = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)
DOWNLOADS_DIR       = os.path.join(BASE_DIR, "downloads")
THUMBNAILS_DIR      = os.path.join(BASE_DIR, "thumbnails")
PROCESSED_DIR       = os.path.join(BASE_DIR, "processed")
DATABASE_FILE       = os.path.join(BASE_DIR, "database.json")
AUTH_TOKEN_FILE     = os.path.join(BASE_DIR, "token.json")
CLIENT_SECRETS_FILE = os.path.join(BASE_DIR, "client_secrets.json")

# Background image for thumbnails
BACKGROUND_IMAGE    = os.path.join(BASE_DIR, "assets", "background.jpg")

for d in [DOWNLOADS_DIR, THUMBNAILS_DIR, PROCESSED_DIR]:
    os.makedirs(d, exist_ok=True)
