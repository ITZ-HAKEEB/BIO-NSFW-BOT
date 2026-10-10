"""All settings live here. Values come from environment variables (Heroku Config Vars / .env)."""

import os

# ---- ʀᴇǫᴜɪʀᴇᴅ ----
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

# ---- ᴅᴀᴛᴀʙᴀsᴇ ----
MONGO_URI = os.getenv("MONGO_URI", "")
DB_NAME = os.getenv("DB_NAME", "meowguard")

# ---- ғᴏɴᴛ / ᴘʜᴏᴛᴏ ----
FONT_STYLE = os.getenv("FONT_STYLE", "smallcaps")
OWNER_ID = int(os.getenv("OWNER_ID", "0") or 0)
START_IMAGE = os.getenv("START_IMAGE", "")

# ---- ʙᴏᴛ ɪᴅᴇɴᴛɪᴛʏ ----
BOT_NAME = os.getenv("BOT_NAME", "˹ᴍᴇᴏᴡ x ʀᴏʙᴏᴛ˼ ♡")

# ---- /sᴛᴀʀᴛ ʙᴜᴛᴛᴏɴs ----
OWNER_URL = os.getenv(
    "OWNER_URL",
    "https://t.me/System_xd_lll"
)

UPDATE_CHANNEL_URL = os.getenv(
    "UPDATE_CHANNEL_URL",
    "https://t.me/kirti_bots_support"
)

SUPPORT_URL = os.getenv(
    "SUPPORT_URL",
    os.getenv("UPDATE_GROUP_URL", "https://t.me/kirti_bots")
)

SOURCE_URL = os.getenv(
    "SOURCE_URL",
    "https://github.com/TEAM-KRITI/pro"
)

# ---- ʙᴇʜᴀᴠɪᴏᴜʀ sᴇᴛᴛɪɴɢs ----
WARN_DELETE_AFTER = int(
    os.getenv("WARN_DELETE_AFTER", "5")
)

ADMIN_CACHE_TTL = int(
    os.getenv("ADMIN_CACHE_TTL", "60")
)

BIO_CACHE_TTL = int(
    os.getenv("BIO_CACHE_TTL", "600")
)

FSUB_CACHE_TTL = int(
    os.getenv("FSUB_CACHE_TTL", "60")
)

STYLISH_MIN_CHARS = int(
    os.getenv("STYLISH_MIN_CHARS", "3")
)

DEFAULT_BAD_WORDS = [
    word
    for word in os.getenv(
        "DEFAULT_BAD_WORDS",
        "fuck,bitch,bastard,slut,asshole"
    ).split(",")
    if word
]

# ---- sᴛᴀʀᴛ ᴍᴇssᴀɢᴇ ----
START_GREETING = "🛡 ʜᴇʟʟᴏ {name}! 👋"

START_BODY = (
    "ɪ'ᴍ {bot_name}, ʏᴏᴜʀ ɢʀᴏᴜᴘ's sᴇᴄᴜʀɪᴛʏ ʙᴏᴛ "
    "ᴋᴇᴇᴘɪɴɢ ᴄʜᴀᴛs ᴄʟᴇᴀɴ ᴀɴᴅ sᴀғᴇ.\n\n"

    "⊙ ᴡʜᴀᴛ ɪ ᴄᴀɴ ᴅᴏ :\n"
    "➻ ʙʟᴏᴄᴋ ʟɪɴᴋs, ʜᴀsʜᴛᴀɢs, ᴘʜᴏɴᴇ ɴᴜᴍʙᴇʀs "
    "ᴀɴᴅ ᴘʀᴏᴍᴏs\n"

    "➻ ᴅᴇʟᴇᴛᴇ ᴇᴅɪᴛᴇᴅ ᴍᴇssᴀɢᴇs, ғᴏʀᴡᴀʀᴅs "
    "ᴀɴᴅ sᴛʏʟɪsʜ ғᴏɴᴛs\n"

    "➻ ᴀᴜᴛᴏ-ᴅᴇʟᴇᴛᴇ ᴍᴇssᴀɢᴇs ᴀɴᴅ ᴍᴇᴅɪᴀ "
    "ᴀғᴛᴇʀ ᴀ sᴇᴛ ᴛɪᴍᴇ\n"

    "➻ ғᴏʀᴄᴇ sᴜʙsᴄʀɪʙᴇ, ʙɪᴏ ʟɪɴᴋ ғɪʟᴛᴇʀ "
    "ᴀɴᴅ ᴀʙᴜsᴇ ғɪʟᴛᴇʀ\n"

    "•——•••——————•—•——————•••——•\n\n"

    "⚠️ ɢᴇᴛ sᴛᴀʀᴛᴇᴅ :\n"
    "— ᴀᴅᴅ ᴍᴇ ᴛᴏ ʏᴏᴜʀ ɢʀᴏᴜᴘ\n"
    "— ᴍᴀᴋᴇ ᴍᴇ ᴀɴ ᴀᴅᴍɪɴ ᴡɪᴛʜ ᴅᴇʟᴇᴛᴇ "
    "ᴍᴇssᴀɢᴇs ᴘᴇʀᴍɪssɪᴏɴ\n"
    "— ᴛᴀᴘ ʜᴇʟᴘ ᴀɴᴅ ᴄᴏᴍᴍᴀɴᴅs ᴛᴏ sᴇᴇ "
    "ᴇᴠᴇʀʏ ғᴇᴀᴛᴜʀᴇ"
)

# ---- ʜᴇʟᴘ ᴍᴇɴᴜ ----
HELP_TEXT = (
    "<u>⊙ ʙᴏᴛ ᴄᴏᴍᴍᴀɴᴅ ʜᴇʟᴘ :</u>\n\n"

    "<blockquote>🏵 ʜᴇʀᴇ ʏᴏᴜ'ʟʟ ғɪɴᴅ "
    "ᴅᴇᴛᴀɪʟs ғᴏʀ ᴀʟʟ ᴀᴠᴀɪʟᴀʙʟᴇ "
    "ᴘʟᴜɢɪɴs ᴀɴᴅ ғᴇᴀᴛᴜʀᴇs.</blockquote>\n\n"

    "<blockquote>👇 ᴛᴀᴘ ᴛʜᴇ ʙᴜᴛᴛᴏɴs ʙᴇʟᴏᴡ "
    "ᴛᴏ ᴠɪᴇᴡ ʜᴇʟᴘ ғᴏʀ ᴇᴀᴄʜ ᴍᴏᴅᴜʟᴇ :</blockquote>"
)
