import html, time

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.error import TelegramError
from telegram.ext import CommandHandler, filters

import config
from database import db
from fonts import btn_style, style
from helpers import admin_only, delete_later, log

NAME = "fsub"
HELP = """<u>⊙ FORCE SUBSCRIBE :</u>

<blockquote>📢 Users must join your channel before they can chat in the group.</blockquote>

<blockquote>↣ /fsub @channel : Set the channel (or channel id)
↣ /fsub off : Disable force subscribe
↣ /fsub : Show current status</blockquote>

<blockquote>⚠️ <b>Action :</b>
— Messages from users who have not joined are deleted and a join button is sent.</blockquote>

<blockquote>⚠️ <b>Note :</b>
— Add the bot as <b>admin</b> in the channel first (it must be able to see the member list).
— Group admins and approved users are exempt.
— 👮 Only group admins can configure this setting.</blockquote>"""

_cache = {}          # (channel_id, user_id) -> time the user was last seen joined
_broken = {}         # channel_id -> time of last failed member lookup (bot not admin etc.)
_notified = {}       # group chat_id -> time we last told the group that fsub is broken
BROKEN_RETRY = 300   # seconds to wait before retrying a channel that failed
NOTIFY_EVERY = 1800  # seconds between "fsub is broken" notices per group


async def check_member(context, channel_id, user_id):
    """True = joined, False = not joined, None = cannot check (bot is not admin in the channel etc.)."""
    key, now = (channel_id, user_id), time.time()
    hit = _cache.get(key)
    if hit and now - hit < config.FSUB_CACHE_TTL:
        return True
    if now - _broken.get(channel_id, 0) < BROKEN_RETRY:
        return None                          # do not hammer Telegram while the channel is misconfigured
    try:
        m = await context.bot.get_chat_member(channel_id, user_id)
    except TelegramError as e:
        _broken[channel_id] = now
        log.warning("fsub check failed for channel %s: %s (make the bot ADMIN in that channel)", channel_id, e)
        return None
    _broken.pop(channel_id, None)
    ok = m.status not in ("left", "kicked") and not (m.status == "restricted" and not getattr(m, "is_member", True))
    if ok:
        _cache[key] = now
    return ok


async def _tell_group_broken(context, chat_id):
    now = time.time()
    if now - _notified.get(chat_id, 0) < NOTIFY_EVERY:
        return
    _notified[chat_id] = now
    try:
        w = await context.bot.send_message(
            chat_id,
            "⚠️ " + style("Force subscribe is not working: I cannot see the channel's member list. "
                          "Admins: make me ADMIN in the channel, then send /fsub again."))
        delete_later(context, w.chat_id, w.message_id, 60)
    except Exception:
        pass


async def enforce(context, msg, user, s):
    """Returns True if the message was removed because the user has not joined."""
    cfg = s.get("fsub")
    if not cfg:
        return False
    joined = await check_member(context, cfg["id"], user.id)
    if joined is None:                           # cannot verify -> never block users, but tell the admins
        await _tell_group_broken(context, msg.chat_id)
        return False
    if joined:
        return False
    try:
        await msg.delete()
    except Exception as e:
        log.warning("fsub: cannot delete: %s", e)
        return True
    kb = InlineKeyboardMarkup([[InlineKeyboardButton(btn_style("JOIN CHANNEL"), url=cfg["link"])]]) if cfg.get("link") else None
    try:
        w = await context.bot.send_message(
            msg.chat_id,
            f'⚠️ <a href="tg://user?id={user.id}">{html.escape(user.first_name)}</a>, ' + style("join the channel first to chat here."),
            parse_mode=ParseMode.HTML, reply_markup=kb)
        delete_later(context, w.chat_id, w.message_id, max(config.WARN_DELETE_AFTER, 10))
    except Exception:
        pass
    return True


async def fsub(update, context):
    if not await admin_only(update, context):
        return
    cid = update.effective_chat.id
    s = db.get(cid)
    arg = context.args[0] if context.args else ""
    if not arg:
        cfg = s["fsub"]
        cur = (cfg.get("link") or cfg["id"]) if cfg else "off"
        return await update.message.reply_text(style(f"Force subscribe: {cur}\nUsage: /fsub @channel | off"))
    if arg.lower() == "off":
        s["fsub"] = None
        db.save(cid)
        return await update.message.reply_text(style("✅ fsub disabled."))
    try:
        ch = await context.bot.get_chat(int(arg) if arg.lstrip("-").isdigit() else arg)
    except TelegramError as e:
        log.warning("fsub set failed: %s", e)
        return await update.message.reply_text(style("Channel not found. Check the @username / id, add me as admin in the channel and try again."))
    # the bot must be ADMIN there, otherwise Telegram answers "Member list is inaccessible"
    try:
        me = await context.bot.get_chat_member(ch.id, context.bot.id)
        is_admin_there = me.status in ("administrator", "creator")
    except TelegramError:
        is_admin_there = False
    if not is_admin_there:
        return await update.message.reply_text(style(
            f"❌ I am not an admin in {ch.title}. Add me to the channel as ADMIN "
            "(so I can see its members) and send /fsub again."))
    link = f"https://t.me/{ch.username}" if ch.username else ch.invite_link
    if not link:
        try:
            link = await context.bot.export_chat_invite_link(ch.id)
        except TelegramError as e:
            log.warning("fsub: no invite link: %s", e)   # still works, just without a join button
    _broken.pop(ch.id, None)
    s["fsub"] = {"id": ch.id, "link": link}
    db.save(cid)
    await update.message.reply_text(style(f"✅ fsub enabled for {ch.title}." + ("" if link else
                                          "\n⚠️ No invite link available, the join button will be missing.")))


def register(app):
    app.add_handler(CommandHandler(NAME, fsub, filters=filters.ChatType.GROUPS))
