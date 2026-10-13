"""All settings live here. Values come from environment variables (Heroku Config Vars / .env)."""
import os

# ---- required ----
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

# ---- database (optional; without it a local data.json is used) ----
MONGO_URI = os.getenv("MONGO_URI", "")
DB_NAME = os.getenv("DB_NAME", "meowguard")

# ---- logger: group/channel where the bot sends start/stop, new group and new user logs ----
# Add the bot to that group, then set its id (looks like -1001234567890). Empty = logger off.
def _first_env(*names):
    for n in names:
        v = os.getenv(n, "")
        if v.strip():
            return v
    return ""


DEFAULT_LOG_GROUP_ID = "-1003979103138"   # used when no Config Var is set (a Heroku Config Var overrides it)
LOG_GROUP_RAW = _first_env("LOG_GROUP_ID", "LOGGER_ID", "LOGGER_GROUP_ID", "LOG_CHANNEL_ID", "LOG_CHANNEL", "LOG_CHAT_ID") or DEFAULT_LOG_GROUP_ID
LOG_GROUP_RAW = LOG_GROUP_RAW.strip().strip("'\"").strip()
# phones/docs often turn "-" into a fancy minus/dash -> normalise, and drop spaces
_CLEAN = LOG_GROUP_RAW.translate({ord(c): "-" for c in "\u2212\u2012\u2013\u2014\u2010\u2011"}).replace(" ", "")
if _CLEAN.lstrip("-").isdigit():
    LOG_GROUP_ID = int(_CLEAN)
elif _CLEAN.startswith("@"):
    LOG_GROUP_ID = _CLEAN                   # public group/channel username also works
else:
    LOG_GROUP_ID = 0                        # empty / invalid -> logger off

# photo for the "Bot Started" log message (empty = same photo as /start, set with /setimage or START_IMAGE)
LOG_IMAGE = os.getenv("LOG_IMAGE", "https://anya-file-host.vercel.app/r4vffnlszc")

# ---- font / photo ----
FONT_STYLE = os.getenv("FONT_STYLE", "smallcaps")                # "smallcaps" or "off"
OWNER_ID = int(os.getenv("OWNER_ID", "8957532324") or 0)                  # your Telegram user id (for /setimage)
START_IMAGE = os.getenv("START_IMAGE", "https://anya-file-host.vercel.app/r4vffnlszc")                       # image URL or file_id (optional, /setimage overrides)

# ---- bot identity ----
BOT_NAME = os.getenv("BOT_NAME", "˹Meow x Robot˼ ♡")

# ---- /start buttons (OWNER / UPDATES / SUPPORT / SOURCE) ----
OWNER_URL = os.getenv("OWNER_URL", "https://t.me/telegram")
UPDATE_CHANNEL_URL = os.getenv("UPDATE_CHANNEL_URL", "https://t.me/kirti_bots")
SUPPORT_URL = os.getenv("SUPPORT_URL", os.getenv("UPDATE_GROUP_URL", "https://t.me/kirti_bots_support"))
SOURCE_URL = os.getenv("SOURCE_URL", "https://github.com")

# ---- behaviour tuning ----
WARN_DELETE_AFTER = int(os.getenv("WARN_DELETE_AFTER", "5"))     # seconds before warning msg disappears
ADMIN_CACHE_TTL = int(os.getenv("ADMIN_CACHE_TTL", "60"))        # seconds to cache admin check
BIO_CACHE_TTL = int(os.getenv("BIO_CACHE_TTL", "600"))           # seconds to cache user bio
FSUB_CACHE_TTL = int(os.getenv("FSUB_CACHE_TTL", "60"))          # seconds to cache "user joined channel"
STYLISH_MIN_CHARS = int(os.getenv("STYLISH_MIN_CHARS", "3"))     # fancy chars needed to trigger nostylish
DEFAULT_BAD_WORDS = [w for w in os.getenv("DEFAULT_BAD_WORDS", "fuck,bitch,bastard,slut,asshole").split(",") if w]

# ---- texts ----
START_GREETING = "🛡 Hello {name}! 👋"
START_BODY = (
    "I'm {bot_name}, your group's security bot keeping chats clean and safe.\n"
    "⊙ What I can do :\n"
    "➻ Block links, hashtags, phone numbers and promos\n"
    "➻ Delete edited messages, forwards and stylish fonts\n"
    "➻ Auto-delete messages and media after a set time\n"
    "➻ Force subscribe, bio link filter and abuse filter\n"
    "•——•••——————•—•——————•••——•\n\n"
    "⚠️ Get started :\n"
    "— Add me to your group\n"
    "— Make me admin with delete messages permission\n"
    "— Tap Help and commands to see every feature"
)
HELP_TEXT = (
    "<u>⊙ BOT COMMAND HELP :</u>\n\n"
    "<blockquote>🏵 Here you'll find details for all available plugins and features.</blockquote>\n\n"
    "<blockquote>👇 Tap the buttons below to view help for each module :</blockquote>"
)
