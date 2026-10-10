import html

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import CallbackQueryHandler, CommandHandler

import config
from database import db
from fonts import btn_style, style
from helpers import get_image, log

HTML = ParseMode.HTML
PER_PAGE = 6

# Small Caps Font: ʙᴀᴅɴᴀᴍ
HELP_MODULES = [
    ("ᴀʙᴜsᴇ", "abuse"),
    ("ᴀᴘᴘʀᴏᴠᴇ", "approve"),
    ("ʙɪᴏ-ᴍᴏᴅᴇ", "biomode"),
    ("ᴇᴄʜᴏ", "echo"),
    ("ᴇᴅɪᴛ", "edit"),
    ("ғ-sᴜʙ", "fsub"),
    ("ғᴏɴᴛs", "nostylish"),
    ("ғᴏʀᴡᴀʀᴅ", "noforward"),
    ("ʟɪɴᴋ-ғɪʟᴛᴇʀ", "linkfilter"),
    ("ᴍᴇᴅɪᴀ-ᴅᴇʟ", "mediadelete"),
    ("ᴍsɢ-ᴅᴇʟ", "msgdelete"),
    ("ɴᴏ-ʜᴀsʜ", "nohashtags"),
    ("ᴘʜᴏɴᴇ", "nophone"),
    ("ᴘʀᴏᴍᴏ", "nopromo"),
    ("ᴘᴜʀɢᴇ", "purge"),
]

PAGES = (len(HELP_MODULES) + PER_PAGE - 1) // PER_PAGE


def btn(label, **kw):
    return InlineKeyboardButton(btn_style(label), **kw)


def start_text(name):
    greet = style(config.START_GREETING).format(
        name=style(html.escape(name))
    )

    body = style(config.START_BODY).format(
        bot_name=style(html.escape(config.BOT_NAME))
    )

    return (
        f"<blockquote>{greet}</blockquote>\n"
        f"<blockquote expandable>{body}</blockquote>"
    )


def start_kb(bot_username):
    return InlineKeyboardMarkup([
        [
            btn(
                "✦ ᴀᴅᴅ ᴍᴇ ᴛᴏ ʏᴏᴜʀ ɢʀᴏᴜᴘ ✦",
                url=(
                    f"https://t.me/{bot_username}"
                    "?startgroup=true&admin=delete_messages+restrict_members"
                )
            )
        ],
        [
            btn("ᴏᴡɴᴇʀ", url=config.OWNER_URL),
            btn("ᴜᴘᴅᴀᴛᴇs", url=config.UPDATE_CHANNEL_URL),
        ],
        [
            btn("sᴜᴘᴘᴏʀᴛ", url=config.SUPPORT_URL),
            btn("sᴏᴜʀᴄᴇ", url=config.SOURCE_URL),
        ],
        [
            btn("✧ ʜᴇʟᴘ ᴍᴇɴᴜ ✧", callback_data="hp:0"),
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
            btn("◀️ ʙᴀᴄᴋ", callback_data=f"hp:{page - 1}")
        )

    nav.append(
        btn("ʜᴏᴍᴇ 🏡", callback_data="start")
    )

    if page < PAGES - 1:
        nav.append(
            btn("ɴᴇxᴛ ▶️", callback_data=f"hp:{page + 1}")
        )

    rows.append(nav)

    return InlineKeyboardMarkup(rows)


async def send_panel(message, text, kb):
    """Send text with the bot photo on top, if configured."""

    img = get_image()

    if img:
        try:
            return await message.reply_photo(
                img,
                caption=text,
                parse_mode=HTML,
                reply_markup=kb
            )

        except Exception as e:
            log.warning(
                "photo failed, sending text only: %s",
                e
            )

    return await message.reply_text(
        text,
        parse_mode=HTML,
        reply_markup=kb
    )


async def show(q, text, kb):
    """Edit the panel caption or text."""

    try:
        if q.message.photo:
            await q.edit_message_caption(
                caption=text,
                parse_mode=HTML,
                reply_markup=kb
            )
        else:
            await q.edit_message_text(
                text,
                parse_mode=HTML,
                reply_markup=kb
            )

    except Exception as e:
        log.warning("edit failed: %s", e)


async def start(update, context):
    if update.effective_chat.type != "private":
        return

    db.add_user(update.effective_user.id)

    await send_panel(
        update.message,
        start_text(update.effective_user.first_name),
        start_kb(context.bot.username)
    )


async def help_cmd(update, context):
    await send_panel(
        update.message,
        style(config.HELP_TEXT),
        help_kb(0)
    )


async def buttons(update, context):
    import plugins

    q = update.callback_query
    await q.answer()

    data = q.data

    if data == "start":
        await show(
            q,
            start_text(q.from_user.first_name),
            start_kb(context.bot.username)
        )

    elif data.startswith("hp:"):
        page = int(data[3:])

        await show(
            q,
            style(config.HELP_TEXT),
            help_kb(page)
        )

    elif data.startswith("h:"):
        _, name, page = data.split(":")

        mod = plugins.ALL.get(name)

        if mod:
            await show(
                q,
                style(mod.HELP),
                InlineKeyboardMarkup([
                    [
                        btn(
                            "◀️ ʙᴀᴄᴋ",
                            callback_data=f"hp:{page}"
                        )
                    ]
                ])
            )


def register(app):
    app.add_handler(
        CommandHandler("start", start)
    )

    app.add_handler(
        CommandHandler("help", help_cmd)
    )

    app.add_handler(
        CallbackQueryHandler(buttons)
    )
