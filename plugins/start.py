
import html

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import CallbackQueryHandler, CommandHandler

import config
from database import db
from fonts import btn_style, style
from helpers import get_image, log
from plugins import logs

HTML = ParseMode.HTML
PER_PAGE = 6

# ---- Stylish help modules ----
HELP_MODULES = [
    ("𝐀ʙᴜꜱᴇ", "abuse"),
    ("𝐀ᴘᴘʀᴏᴠᴇ", "approve"),
    ("𝐁ɪᴏ-𝐌ᴏᴅᴇ", "biomode"),
    ("𝐄ᴄʜᴏ", "echo"),
    ("𝐄ᴅɪᴛ", "edit"),
    ("𝐅-𝐒ᴜʙ", "fsub"),
    ("𝐅ᴏɴᴛꜱ", "nostylish"),
    ("𝐅ᴏʀᴡᴀʀᴅ", "noforward"),
    ("𝐋ɪɴᴋ-𝐅ɪʟᴛᴇʀ", "linkfilter"),
    ("𝐌ᴇᴅɪᴀ-𝐃ᴇʟ", "mediadelete"),
    ("𝐌ꜱɢ-𝐃ᴇʟ", "msgdelete"),
    ("𝐍ᴏ-𝐇ᴀꜱʜ", "nohashtags"),
    ("𝐍𝐒𝐅𝐖", "nsfw"),
    ("𝐏ʜᴏɴᴇ", "nophone"),
    ("𝐏ʀᴏᴍᴏ", "nopromo"),
    ("𝐏ᴜʀɢᴇ", "purge"),
]

PAGES = (len(HELP_MODULES) + PER_PAGE - 1) // PER_PAGE


def btn(label, **kwargs):
    return InlineKeyboardButton(btn_style(label), **kwargs)


def start_text(name):
    safe_name = html.escape(name or "User")
    safe_bot_name = html.escape(config.BOT_NAME)

    greet = style(config.START_GREETING).format(
        name=style(safe_name)
    )

    body = style(config.START_BODY).format(
        bot_name=style(safe_bot_name)
    )

    return (
        f"<blockquote>{greet}</blockquote>\n"
        f"<blockquote expandable>{body}</blockquote>"
    )


def start_kb(bot_username):
    return InlineKeyboardMarkup([
        [
            btn(
                "𝐀ᴅᴅ 𝐌ᴇ 𝐓ᴏ 𝐘ᴏᴜʀ 𝐆ʀᴏᴜᴘ",
                url=(
                    f"https://t.me/{bot_username}"
                    "?startgroup=true&admin=delete_messages+restrict_members"
                ),
            )
        ],
        [
            btn("𝐎ᴡɴᴇʀ", url=config.OWNER_URL),
            btn("𝐔ᴘᴅᴀᴛᴇs", url=config.UPDATE_CHANNEL_URL),
        ],
        [
            btn("𝐒ᴜᴘᴘᴏʀᴛ", url=config.SUPPORT_URL),
            btn("𝐒ᴏᴜʀᴄᴇ", url=config.SOURCE_URL),
        ],
        [
            btn("𝐇ᴇʟᴘ 𝐂ᴏᴍᴍᴀɴᴅ", callback_data="hp:0"),
        ],
    ])


def help_kb(page=0):
    page = max(0, min(page, PAGES - 1))

    items = HELP_MODULES[
        page * PER_PAGE:(page + 1) * PER_PAGE
    ]

    buttons = [
        btn(label, callback_data=f"h:{name}:{page}")
        for label, name in items
    ]

    rows = [
        buttons[i:i + 2]
        for i in range(0, len(buttons), 2)
    ]

    nav = []

    if page > 0:
        nav.append(
            btn("◀️ 𝐁ᴀᴄᴋ", callback_data=f"hp:{page - 1}")
        )

    nav.append(
        btn("𝐇ᴏᴍᴇ 🏡", callback_data="start")
    )

    if page < PAGES - 1:
        nav.append(
            btn("𝐍ᴇxᴛ ▶️", callback_data=f"hp:{page + 1}")
        )

    rows.append(nav)

    return InlineKeyboardMarkup(rows)


async def send_panel(message, text, keyboard):
    """Send a panel with the configured bot image, if available."""
    img = get_image()

    if img:
        try:
            return await message.reply_photo(
                photo=img,
                caption=text,
                parse_mode=HTML,
                reply_markup=keyboard,
            )
        except Exception as exc:
            log.warning(
                "Photo sending failed; sending text instead: %s",
                exc,
            )

    return await message.reply_text(
        text=text,
        parse_mode=HTML,
        reply_markup=keyboard,
    )


async def show(query, text, keyboard):
    """Edit the existing panel caption or text."""
    try:
        if query.message.photo:
            await query.edit_message_caption(
                caption=text,
                parse_mode=HTML,
                reply_markup=keyboard,
            )
        else:
            await query.edit_message_text(
                text=text,
                parse_mode=HTML,
                reply_markup=keyboard,
            )
    except Exception as exc:
        log.warning("Panel editing failed: %s", exc)


async def start(update, context):
    if update.effective_chat.type != "private":
        return

    user = update.effective_user

    if db.add_user(user.id):
        await logs.new_user(context.bot, user)

    await send_panel(
        update.message,
        start_text(user.first_name),
        start_kb(context.bot.username),
    )


async def help_cmd(update, context):
    await send_panel(
        update.message,
        style(config.HELP_TEXT),
        help_kb(0),
    )


async def buttons(update, context):
    import plugins

    query = update.callback_query
    await query.answer()

    data = query.data

    if data == "start":
        await show(
            query,
            start_text(query.from_user.first_name),
            start_kb(context.bot.username),
        )

    elif data.startswith("hp:"):
        try:
            page = int(data.split(":", 1)[1])
        except (ValueError, IndexError):
            page = 0

        await show(
            query,
            style(config.HELP_TEXT),
            help_kb(page),
        )

    elif data.startswith("h:"):
        try:
            _, name, page = data.split(":")
            page = int(page)
        except ValueError:
            return

        module = plugins.ALL.get(name)

        if module and hasattr(module, "HELP"):
            await show(
                query,
                style(module.HELP),
                InlineKeyboardMarkup([
                    [
                        btn(
                            "◀️ 𝐁ᴀᴄᴋ",
                            callback_data=f"hp:{page}",
                        )
                    ]
                ]),
            )


def register(app):
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CallbackQueryHandler(buttons))
