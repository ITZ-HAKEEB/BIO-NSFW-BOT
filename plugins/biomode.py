import re
import time
import html

import config

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode

NAME = "biomode"

HELP = """<u>⊙ ʙɪᴏ ᴍᴏᴅᴇ :</u>

<blockquote>👤 ᴅᴇʟᴇᴛᴇs ᴍᴇssᴀɢᴇs ғʀᴏᴍ ᴜsᴇʀs ᴡʜᴏ ʜᴀᴠᴇ ᴀ ʟɪɴᴋ ᴏʀ @ᴜsᴇʀɴᴀᴍᴇ ɪɴ ᴛʜᴇɪʀ ʙɪᴏ.</blockquote>

<blockquote>↣ /biomode on : ᴇɴᴀʙʟᴇ ʙɪᴏ ᴍᴏᴅᴇ
↣ /biomode off : ᴅɪsᴀʙʟᴇ ʙɪᴏ ᴍᴏᴅᴇ</blockquote>

<blockquote>⚠️ <b>ᴀᴄᴛɪᴏɴ :</b>
— ᴜsᴇʀs ᴡɪᴛʜ ʟɪɴᴋs ɪɴ ᴛʜᴇɪʀ ʙɪᴏ ᴡɪʟʟ ʙᴇ ᴡᴀʀɴᴇᴅ ᴀɴᴅ ᴛʜᴇɪʀ ᴍᴇssᴀɢᴇs ᴅᴇʟᴇᴛᴇᴅ.</blockquote>

<blockquote>⚠️ <b>ɴᴏᴛᴇ :</b>
— ɢʀᴏᴜᴘ ᴀᴅᴍɪɴs ᴀʀᴇ ᴇxᴇᴍᴘᴛ.
— 👮 ᴏɴʟʏ ɢʀᴏᴜᴘ ᴀᴅᴍɪɴs ᴄᴀɴ ᴄᴏɴғɪɢᴜʀᴇ ᴛʜɪs sᴇᴛᴛɪɴɢ.</blockquote>"""

REASON = "ʟɪɴᴋs ɪɴ ʏᴏᴜʀ ʙɪᴏ"

BIO_RE = re.compile(
    r"(https?://|www\.|t\.me/|@\w{4,})",
    re.I
)

BIO_WARNING = (
    "⚠️ <b>ʙɪᴏ ᴡᴀʀɴɪɴɢ!</b>\n\n"
    "{mention}, ʀᴇᴍᴏᴠᴇ ʟɪɴᴋ ғʀᴏᴍ ʙɪᴏ!"
)

BIO_WARNING_BUTTONS = InlineKeyboardMarkup([
    [
        InlineKeyboardButton(
            "sᴜᴘᴘᴏʀᴛ",
            url=config.SUPPORT_URL
        ),
        InlineKeyboardButton(
            "ᴜᴘᴅᴀᴛᴇs",
            url=config.UPDATE_CHANNEL_URL
        ),
    ]
])

_cache = {}


async def check(context, msg, user, text, etypes):
    hit = _cache.get(user.id)

    if hit and time.time() - hit[0] < config.BIO_CACHE_TTL:
        bad = hit[1]
    else:
        try:
            bio = (await context.bot.get_chat(user.id)).bio or ""
        except Exception:
            bio = ""

        bad = bool(BIO_RE.search(bio))
        _cache[user.id] = (time.time(), bad)

    return REASON if bad else None


async def send_bio_warning(context, msg, user):
    """Send the short BioMode warning with Support and Updates buttons."""

    mention = (
        f'<a href="tg://user?id={user.id}">'
        f'{html.escape(user.first_name)}</a>'
    )

    try:
        warning = await context.bot.send_message(
            chat_id=msg.chat_id,
            text=BIO_WARNING.format(mention=mention),
            parse_mode=ParseMode.HTML,
            reply_markup=BIO_WARNING_BUTTONS,
        )
        return warning

    except Exception:
        return None
