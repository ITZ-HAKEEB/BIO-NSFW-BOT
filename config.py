
"""All settings live here. Values come from environment variables (Heroku Config Vars / .env)."""
import os


# ---- required ----
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")


# ---- database ----
MONGO_URI = os.getenv("MONGO_URI", "")
DB_NAME = os.getenv("DB_NAME", "meowguard")


# ---- logger ----
def _first_env(*names):
    for n in names:
        v = os.getenv(n, "")
        if v.strip():
            return v
    return ""


DEFAULT_LOG_GROUP_ID = "-1004357107295"

LOG_GROUP_RAW = (
    _first_env(
        "LOG_GROUP_ID",
        "LOGGER_ID",
        "LOGGER_GROUP_ID",
        "LOG_CHANNEL_ID",
        "LOG_CHANNEL",
        "LOG_CHAT_ID",
    )
    or DEFAULT_LOG_GROUP_ID
)

LOG_GROUP_RAW = LOG_GROUP_RAW.strip().strip("'\"").strip()

_CLEAN = (
    LOG_GROUP_RAW.translate({
        ord(c): "-"
        for c in "\u2212\u2012\u2013\u2014\u2010\u2011"
    }).replace(" ", "")
)

if _CLEAN.lstrip("-").isdigit():
    LOG_GROUP_ID = int(_CLEAN)
elif _CLEAN.startswith("@"):
    LOG_GROUP_ID = _CLEAN
else:
    LOG_GROUP_ID = 0


LOG_IMAGE = os.getenv("LOG_IMAGE", "")


# ---- font / photo ----
FONT_STYLE = os.getenv("FONT_STYLE", "smallcaps")
OWNER_ID = int(os.getenv("OWNER_ID", "0") or 0)

START_IMAGE = os.getenv(
    "START_IMAGE",
    "https://i.ibb.co/39myJ3bw/28c52384-97e9-4a70-9152-59bede124a1c.jpg",
)


# ---- bot identity ----
BOT_NAME = os.getenv("BOT_NAME", "𝗡𝗦𝗙𝗪 𝗣𝗥𝗢𝗧𝗘𝗖𝗧𝗜𝗢𝗡 𝗕𝗢𝗧⚡️ ")


# ---- /start buttons ----
OWNER_URL = os.getenv("OWNER_URL", "https://t.me/telegram")
UPDATE_CHANNEL_URL = os.getenv(
    "UPDATE_CHANNEL_URL",
    "https://t.me/lVAMPIRE_WORLDl",
)
SUPPORT_URL = os.getenv(
    "SUPPORT_URL",
    os.getenv("UPDATE_GROUP_URL", "https://t.me/lVAMPIRE_WORLDl"),
)
SOURCE_URL = os.getenv("SOURCE_URL", "https://github.com")


# ---- behaviour tuning ----
WARN_DELETE_AFTER = int(os.getenv("WARN_DELETE_AFTER", "5"))
ADMIN_CACHE_TTL = int(os.getenv("ADMIN_CACHE_TTL", "60"))
BIO_CACHE_TTL = int(os.getenv("BIO_CACHE_TTL", "600"))
FSUB_CACHE_TTL = int(os.getenv("FSUB_CACHE_TTL", "60"))
STYLISH_MIN_CHARS = int(os.getenv("STYLISH_MIN_CHARS", "3"))

DEFAULT_BAD_WORDS = [
    w.strip()
    for w in os.getenv(
        "DEFAULT_BAD_WORDS",
        "fuck,bitch,bastard,slut,asshole",
    ).split(",")
    if w.strip()
]


# ---- NSFW filter ----
NSFW_THRESHOLD = float(os.getenv("NSFW_THRESHOLD", "0.5"))

NSFW_LABELS = [
    x.strip()
    for x in os.getenv(
        "NSFW_LABELS",
        "FEMALE_GENITALIA_EXPOSED,MALE_GENITALIA_EXPOSED,"
        "FEMALE_BREAST_EXPOSED,BUTTOCKS_EXPOSED,ANUS_EXPOSED",
    ).split(",")
    if x.strip()
]

NSFW_PROFILE_CACHE_TTL = int(
    os.getenv("NSFW_PROFILE_CACHE_TTL", "3600")
)
NSFW_SCAN_VIDEO = os.getenv("NSFW_SCAN_VIDEO", "1") != "0"
NSFW_VIDEO_MAX_MB = int(os.getenv("NSFW_VIDEO_MAX_MB", "8"))
NSFW_MAX_IMAGE_MB = int(os.getenv("NSFW_MAX_IMAGE_MB", "8"))


# ---- stylish texts ----
START_GREETING = "🛡 𝐇ᴇʟʟᴏ {name}! 👋"

START_BODY = (
    "𝐈'ᴍ {bot_name}, ʏᴏᴜʀ ɢʀᴏᴜᴘ'ꜱ ꜱᴇᴄᴜʀɪᴛʏ ʙᴏᴛ, "
    "ᴋᴇᴇᴘɪɴɢ ᴄʜᴀᴛꜱ ᴄʟᴇᴀɴ ᴀɴᴅ ꜱᴀꜰᴇ.\n\n"

    "⊙ 𝐖ʜᴀᴛ 𝐈 𝐂ᴀɴ 𝐃ᴏ :\n"
    "➻ 𝐁ʟᴏᴄᴋ ʟɪɴᴋꜱ, ʜᴀꜱʜᴛᴀɢꜱ, ᴘʜᴏɴᴇ ɴᴜᴍʙᴇʀꜱ "
    "ᴀɴᴅ ᴘʀᴏᴍᴏꜱ\n"
    "➻ 𝐃ᴇʟᴇᴛᴇ ᴇᴅɪᴛᴇᴅ ᴍᴇꜱꜱᴀɢᴇꜱ, ꜰᴏʀᴡᴀʀᴅꜱ "
    "ᴀɴᴅ ꜱᴛʏʟɪꜱʜ ꜰᴏɴᴛꜱ\n"
    "➻ 𝐀ᴜᴛᴏ-ᴅᴇʟᴇᴛᴇ ᴍᴇꜱꜱᴀɢᴇꜱ ᴀɴᴅ ᴍᴇᴅɪᴀ\n"
    "➻ 𝐅ᴏʀᴄᴇ ꜱᴜʙꜱᴄʀɪʙᴇ, ʙɪᴏ ʟɪɴᴋ ꜰɪʟᴛᴇʀ "
    "ᴀɴᴅ ᴀʙᴜꜱᴇ ꜰɪʟᴛᴇʀ\n"

    "•——•••——————•—•——————•••——•\n\n"

    "⚠️ 𝐆ᴇᴛ 𝐒ᴛᴀʀᴛᴇᴅ :\n"
    "— 𝐀ᴅᴅ ᴍᴇ ᴛᴏ ʏᴏᴜʀ ɢʀᴏᴜᴘ\n"
    "— 𝐌ᴀᴋᴇ ᴍᴇ ᴀɴ ᴀᴅᴍɪɴ ᴡɪᴛʜ ᴅᴇʟᴇᴛᴇ "
    "ᴍᴇꜱꜱᴀɢᴇꜱ ᴘᴇʀᴍɪꜱꜱɪᴏɴ\n"
    "— 𝐓ᴀᴘ 𝐇ᴇʟᴘ ᴛᴏ ᴠɪᴇᴡ ᴀʟʟ ᴄᴏᴍᴍᴀɴᴅꜱ"
)


HELP_TEXT = (
    "<u>⊙ 𝐁ᴏᴛ 𝐂ᴏᴍᴍᴀɴᴅ 𝐇ᴇʟᴘ :</u>\n\n"
    "<blockquote>🏵 𝐇ᴇʀᴇ ʏᴏᴜ'ʟʟ ꜰɪɴᴅ ᴅᴇᴛᴀɪʟꜱ "
    "ꜰᴏʀ ᴀʟʟ ᴀᴠᴀɪʟᴀʙʟᴇ ᴘʟᴜɢɪɴꜱ "
    "ᴀɴᴅ ꜰᴇᴀᴛᴜʀᴇꜱ.</blockquote>\n\n"
    "<blockquote>👇 𝐓ᴀᴘ ᴛʜᴇ ʙᴜᴛᴛᴏɴꜱ ʙᴇʟᴏᴡ "
    "ᴛᴏ ᴠɪᴇᴡ ʜᴇʟᴘ ꜰᴏʀ ᴇᴀᴄʜ ᴍᴏᴅᴜʟᴇ :</blockquote>"
)
