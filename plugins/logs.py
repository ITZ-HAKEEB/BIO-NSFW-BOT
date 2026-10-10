"""Logger: sends bot events to the log group (LOG_GROUP_ID).

Events: bot started / stopped, bot added to / removed from a chat, new user started the bot.
Does nothing if LOG_GROUP_ID is not set.
"""
import html, pkgutil, platform
from datetime import datetime, timezone

import telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, LinkPreviewOptions
from telegram.constants import ParseMode
from telegram.error import TelegramError
from telegram.ext import ChatMemberHandler

import config
import plugins
from fonts import btn_style, style
from helpers import get_image, log

NAME = "logs"
_IN = ("member", "administrator", "creator", "restricted")
_NO_PREVIEW = LinkPreviewOptions(is_disabled=True)


def _now():
    return datetime.now(timezone.utc).strftime("%d %b %Y, %H:%M:%S UTC")


def _user_link(user):
    return f'<a href="tg://user?id={user.id}">{html.escape(user.full_name)}</a>'


async def send_log(bot, text, photo=None, markup=None):
    """Send an HTML message (optionally with photo + buttons) to the log group. Never raises."""
    if not config.LOG_GROUP_ID:
        return False
    try:
        if photo:
            try:
                await bot.send_photo(config.LOG_GROUP_ID, photo, caption=text, parse_mode=ParseMode.HTML,
                                     reply_markup=markup)
                return True
            except TelegramError as e:   # bad photo url / file_id -> still send the text
                log.warning("Logger: photo failed, sending text only: %s", e)
        await bot.send_message(config.LOG_GROUP_ID, text, parse_mode=ParseMode.HTML,
                               link_preview_options=_NO_PREVIEW, reply_markup=markup)
        return True
    except TelegramError as e:
        log.warning("Logger: message not sent to LOG_GROUP_ID=%s (%s). Bot ko log group me add karo "
                    "(channel ho to admin banao) aur check karo ki ID -100... wali ho.",
                    config.LOG_GROUP_ID, e)
        return False


async def started(bot):
    plugins_loaded = sum(1 for _ in pkgutil.iter_modules(plugins.__path__))
    text = (f"❖ <b>{style('BOT STARTED SUCCESSFULLY')}</b> ✅\n\n"
            f"• <b>{style('BOT')}</b> :- {html.escape(config.BOT_NAME)}\n"
            f"• <b>{style('PLUGINS')}</b> :- {plugins_loaded} {style('LOADED')}\n"
            f"• <b>{style('PTB')}</b> :- <code>{telegram.__version__}</code>\n"
            f"• <b>{style('PYTHON')}</b> :- <code>{platform.python_version()}</code>\n\n"
            f"» <b>{style('POWERED BY')}</b> :- "
            f'<a href="{html.escape(config.UPDATE_CHANNEL_URL)}">{style(html.escape(config.BOT_NAME))}</a>')
    kb = InlineKeyboardMarkup([[InlineKeyboardButton(
        btn_style("ADD ME IN YOUR GROUP"),
        url=f"https://t.me/{bot.username}?startgroup=true&admin=delete_messages+restrict_members")]])
    if await send_log(bot, text, photo=config.LOG_IMAGE or get_image(), markup=kb):
        log.info("Start message sent to log group")


async def stopped(bot):
    await send_log(bot, f"🔴 <b>{style('Bot Stopped')}</b>\n\n{style('Time')} : {_now()}")


async def new_user(bot, user):
    """Called from /start when a user is seen for the first time."""
    uname = f"@{user.username}" if user.username else style("none")
    await send_log(bot, f"👤 <b>{style('New User')}</b>\n\n"
                        f"{style('Name')} : {_user_link(user)}\n"
                        f"{style('ID')} : <code>{user.id}</code>\n"
                        f"{style('Username')} : {uname}\n"
                        f"{style('Time')} : {_now()}")


async def on_my_member(update, context):
    """Bot added to / removed from a group or channel."""
    cm = update.my_chat_member
    if not cm or cm.chat.type == "private" or cm.chat.id == config.LOG_GROUP_ID:
        return
    was_in, is_in = cm.old_chat_member.status in _IN, cm.new_chat_member.status in _IN
    if was_in == is_in:
        return
    chat = cm.chat
    title = html.escape(chat.title or "?")
    uname = f"@{chat.username}" if chat.username else style("private")
    by = _user_link(cm.from_user) if cm.from_user else "?"
    if is_in:
        try:
            members = await context.bot.get_chat_member_count(chat.id)
        except TelegramError:
            members = "?"
        head, who = f"➕ <b>{style('Added To New Chat')}</b>", style("Added by")
        extra = f"{style('Members')} : {members}\n"
    else:
        head, who, extra = f"➖ <b>{style('Removed From Chat')}</b>", style("Removed by"), ""
    await send_log(context.bot, f"{head}\n\n"
                                f"{style('Chat')} : {title}\n"
                                f"{style('ID')} : <code>{chat.id}</code>\n"
                                f"{style('Username')} : {uname}\n"
                                f"{extra}"
                                f"{who} : {by}\n"
                                f"{style('Time')} : {_now()}")


def register(app):
    # group=1 so it runs in addition to the tracker in broadcast.py (one handler per group only)
    app.add_handler(ChatMemberHandler(on_my_member, ChatMemberHandler.MY_CHAT_MEMBER), group=1)
