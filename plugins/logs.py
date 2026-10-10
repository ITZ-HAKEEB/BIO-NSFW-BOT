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
from telegram.ext import ChatMemberHandler, CommandHandler, filters

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


last_error = ""        # why the last log message failed (shown by /logtest and sent to OWNER_ID)
_resolved = None       # chat id that worked


def _targets():
    """The configured id first, then common mistakes (missing -100 prefix / missing minus sign)."""
    cid = config.LOG_GROUP_ID
    if not isinstance(cid, int) or not cid:
        return [cid] if cid else []
    if _resolved is not None:
        return [_resolved]
    out = [cid]
    if cid > 0:
        out += [-cid, int(f"-100{cid}")]
    elif not str(cid).startswith("-100"):
        out.append(int(f"-100{-cid}"))
    return out


def _hint(err):
    low = str(err).lower()
    if "chat not found" in low:
        return "Chat nahi mila: ID galat hai ya bot us group/channel me add nahi hai."
    if "forbidden" in low or "not a member" in low or "kicked" in low:
        return "Bot us group me nahi hai (ya kick/ban hai). Bot ko group me add karo."
    if "not enough rights" in low or "administrator" in low:
        return "Bot ke paas yaha message bhejne ka right nahi hai. Channel ho to bot ko admin banao."
    return "Telegram error."


async def send_log(bot, text, photo=None, markup=None):
    """Send an HTML message (optionally with photo + buttons) to the log group. Never raises; True if sent."""
    global last_error, _resolved
    if not config.LOG_GROUP_ID:
        last_error = "LOG_GROUP_ID set nahi hai (ya galat format me hai). Sahi format: -1001234567890"
        return False
    for target in _targets():
        try:
            sent = False
            if photo:
                try:
                    await bot.send_photo(target, photo, caption=text, parse_mode=ParseMode.HTML, reply_markup=markup)
                    sent = True
                except TelegramError as e:
                    if "chat not found" in str(e).lower():
                        raise
                    log.warning("Logger: photo failed, sending text only: %s", e)
            if not sent:
                await bot.send_message(target, text, parse_mode=ParseMode.HTML,
                                       link_preview_options=_NO_PREVIEW, reply_markup=markup)
            _resolved, last_error = target, ""
            return True
        except TelegramError as e:
            last_error = f"{e} -> {_hint(e)}"
            if "chat not found" not in str(e).lower():
                break
        except Exception as e:
            last_error = f"{type(e).__name__}: {e}"
            break
    log.warning("Logger: message not sent to LOG_GROUP_ID=%s | %s", config.LOG_GROUP_ID, last_error)
    return False


async def started(bot):
    """Never raises: a logger problem must not stop the bot."""
    try:
        if not config.LOG_GROUP_ID:
            log.info("Logger is OFF (LOG_GROUP_ID not set or invalid: %r)", config.LOG_GROUP_RAW)
            return
        ok = await send_log(bot, start_text(bot), photo=config.LOG_IMAGE or get_image(), markup=start_kb(bot))
        if ok:
            log.info("Start message sent to log group")
        elif config.OWNER_ID:   # tell the owner in PM why it failed (Heroku logs are hard to read on a phone)
            await bot.send_message(config.OWNER_ID, style("⚠️ Logger fail ho gaya:\n") + html.escape(last_error)
                                   + f"\n\nLOG_GROUP_ID = {html.escape(str(config.LOG_GROUP_RAW))}", parse_mode=ParseMode.HTML)
    except Exception as e:
        log.warning("Logger startup message failed: %s", e)


def start_text(bot):
    plugins_loaded = sum(1 for _ in pkgutil.iter_modules(plugins.__path__))
    return (f"❖ <b>{style('BOT STARTED SUCCESSFULLY')}</b> ✅\n\n"
            f"• <b>{style('BOT')}</b> :- {html.escape(config.BOT_NAME)}\n"
            f"• <b>{style('PLUGINS')}</b> :- {plugins_loaded} {style('LOADED')}\n"
            f"• <b>{style('PTB')}</b> :- <code>{telegram.__version__}</code>\n"
            f"• <b>{style('PYTHON')}</b> :- <code>{platform.python_version()}</code>\n\n"
            f"» <b>{style('POWERED BY')}</b> :- "
            f'<a href="{html.escape(config.UPDATE_CHANNEL_URL)}">{style(html.escape(config.BOT_NAME))}</a>')


def start_kb(bot):
    return InlineKeyboardMarkup([[InlineKeyboardButton(
        btn_style("ADD ME IN YOUR GROUP"),
        url=f"https://t.me/{bot.username}?startgroup=true&admin=delete_messages+restrict_members")]])


async def logtest(update, context):
    """Owner only, in bot PM: sends the start message to the log group and shows the exact result."""
    m = update.effective_message
    if not config.OWNER_ID:
        return await m.reply_text(style("OWNER_ID config var set nahi hai."))
    if update.effective_user.id != config.OWNER_ID:
        return
    bot = context.bot
    ok = await send_log(bot, start_text(bot), photo=config.LOG_IMAGE or get_image(), markup=start_kb(bot))
    if ok:
        await m.reply_text(style(f"✅ Log group me message chala gaya.\nChat id: {_resolved}"))
        if _resolved != config.LOG_GROUP_ID:
            await m.reply_text(style(f"💡 Config Var me LOG_GROUP_ID = {_resolved} kar do (abhi galat format hai)."))
    else:
        await m.reply_text(style("❌ Message nahi gaya.\n") + html.escape(last_error)
                           + f"\n\nLOG_GROUP_ID = {html.escape(str(config.LOG_GROUP_RAW) or 'empty')}", parse_mode=ParseMode.HTML)


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
    if not cm or cm.chat.type == "private" or cm.chat.id in _targets():
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
    app.add_handler(CommandHandler("logtest", logtest, filters=filters.ChatType.PRIVATE))
