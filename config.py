"""All settings live here. Values come from environment variables (Heroku Config Vars / .env)."""
import os

# ---- required ----
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

# ---- database (optional; without it a local data.json is used) ----
MONGO_URI = os.getenv("MONGO_URI", "")
DB_NAME = os.getenv("DB_NAME", "kirti")

# ---- logger: group/channel where the bot sends start/stop, new group and new user logs ----
# Add the bot to that group, then set its id (looks like -1003979103138). Empty = logger off.
_lg = os.getenv("LOG_GROUP_ID", os.getenv("LOGGER_ID", "-1003979103138")).strip()
LOG_GROUP_ID = int(_lg) if _lg.lstrip("-").isdigit() else 0

# ---- font / photo ----
FONT_STYLE = os.getenv("FONT_STYLE", "smallcaps")                # "smallcaps" or "off"
OWNER_ID = int(os.getenv("OWNER_ID", "0") or 0)                  # your Telegram user id (for /setimage)
START_IMAGE = os.getenv("START_IMAGE", "https://anya-file-host.vercel.app/r4vffnlszc")                       # image URL or file_id (optional, /setimage overrides)

# ---- bot identity ----
BOT_NAME = os.getenv("BOT_NAME", "˹kirti x Robot˼ ♡")

# ---- /start buttons (OWNER / UPDATES / SUPPORT / SOURCE) ----
OWNER_URL = os.getenv("OWNER_URL", "https://t.me/System_xd_lll")
UPDATE_CHANNEL_URL = os.getenv("UPDATE_CHANNEL_URL", "https://t.me/kirti_bots")
SUPPORT_URL = os.getenv("SUPPORT_URL", os.getenv("UPDATE_GROUP_URL", "https://t.me/kirti_bots_support"))
SOURCE_URL = os.getenv("SOURCE_URL", "https://github.com/TEAM-KRITI/pro")

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
