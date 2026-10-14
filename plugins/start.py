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

# (button label, module NAME) - alphabetical, 6 per page -> 3 pages
HELP_MODULES = [
    ("Abuse", "abuse"), ("Approve", "approve"), ("Bio-Mode", "biomode"),
    ("Echo", "echo"), ("Edit", "edit"), ("F-Sub", "fsub"),
    ("Fonts", "nostylish"), ("Forward", "noforward"), ("Link-Filter", "linkfilter"),
    ("Media-Del", "mediadelete"), ("Msg-Del", "msgdelete"), ("No-Hash", "nohashtags"),
    ("NSFW", "nsfw"), ("Phone", "nophone"), ("Promo", "nopromo"), ("Purge", "purge"),
]
PAGES = (len(HELP_MODULES) + PER_PAGE - 1) // PER_PAGE


def btn(label, **kw):
    return InlineKeyboardButton(btn_style(label), **kw)


def start_text(name):
    greet = style(config.START_GREETING).format(name=style(html.escape(name)))
    body = style(config.START_BODY).format(bot_name=style(html.escape(config.BOT_NAME)))
    return f"<blockquote>{greet}</blockquote>\n<blockquote expandable>{body}</blockquote>"


def start_kb(bot_username):
    return InlineKeyboardMarkup([
        [btn("ADD ME TO YOUR GROUP",
             url=f"https://t.me/{bot_username}?startgroup=true&admin=delete_messages+restrict_members")],
        [btn("OWNER", url=config.OWNER_URL), btn("UPDATES", url=config.UPDATE_CHANNEL_URL)],
        [btn("SUPPORT", url=config.SUPPORT_URL), btn("SOURCE", url=config.SOURCE_URL)],
        [btn("HELP COMMAND", callback_data="hp:0")],
    ])


def help_kb(page=0):
    page = max(0, min(page, PAGES - 1))
    items = HELP_MODULES[page * PER_PAGE:(page + 1) * PER_PAGE]
    btns = [btn(label, callback_data=f"h:{name}:{page}") for label, name in items]
    rows = [btns[i:i + 2] for i in range(0, len(btns), 2)]
    nav = []
    if page > 0:
        nav.append(btn("◀️ Back", callback_data=f"hp:{page - 1}"))
    nav.append(btn("Home🏡", callback_data="start"))
    if page < PAGES - 1:
        nav.append(btn("Next ▶️", callback_data=f"hp:{page + 1}"))
    rows.append(nav)
    return InlineKeyboardMarkup(rows)


async def send_panel(message, text, kb):
    """Send text with the bot photo on top (if one is set)."""
    img = get_image()
    if img:
        try:
            return await message.reply_photo(img, caption=text, parse_mode=HTML, reply_markup=kb)
        except Exception as e:
            log.warning("photo failed, sending text only: %s", e)
    return await message.reply_text(text, parse_mode=HTML, reply_markup=kb)


async def show(q, text, kb):
    """Edit the panel in place (caption if it has a photo, text otherwise)."""
    try:
        if q.message.photo:
            await q.edit_message_caption(caption=text, parse_mode=HTML, reply_markup=kb)
        else:
            await q.edit_message_text(text, parse_mode=HTML, reply_markup=kb)
    except Exception as e:
        log.warning("edit failed: %s", e)


async def start(update, context):
    if update.effective_chat.type != "private":
        return
    if db.add_user(update.effective_user.id):   # remember user for /broadcast
        await logs.new_user(context.bot, update.effective_user)   # first time -> log group
    await send_panel(update.message, start_text(update.effective_user.first_name), start_kb(context.bot.username))


async def help_cmd(update, context):
    await send_panel(update.message, style(config.HELP_TEXT), help_kb(0))


async def buttons(update, context):
    import plugins
    q = update.callback_query
    await q.answer()
    d = q.data
    if d == "start":
        await show(q, start_text(q.from_user.first_name), start_kb(context.bot.username))
    elif d.startswith("hp:"):
        await show(q, style(config.HELP_TEXT), help_kb(int(d[3:])))
    elif d.startswith("h:"):
        _, name, page = d.split(":")
        mod = plugins.ALL.get(name)
        if mod:
            await show(q, style(mod.HELP), InlineKeyboardMarkup([[btn("◀️ Back", callback_data=f"hp:{page}")]]))


def register(app):
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CallbackQueryHandler(buttons))
