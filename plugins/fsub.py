import html, time

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
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
— Add the bot as admin in the channel first.
— Group admins and approved users are exempt.
— 👮 Only group admins can configure this setting.</blockquote>"""

_cache = {}


async def is_joined(context, channel_id, user_id):
    key, now = (channel_id, user_id), time.time()
    hit = _cache.get(key)
    if hit and now - hit < config.FSUB_CACHE_TTL:
        return True
    try:
        m = await context.bot.get_chat_member(channel_id, user_id)
        ok = m.status not in ("left", "kicked") and not (m.status == "restricted" and not getattr(m, "is_member", True))
    except Exception as e:                       # bot not admin in channel etc. -> never block users
        log.warning("fsub check failed: %s", e)
        return True
    if ok:
        _cache[key] = now
    return ok


async def enforce(context, msg, user, s):
    """Returns True if the message was removed because the user has not joined."""
    cfg = s.get("fsub")
    if not cfg or await is_joined(context, cfg["id"], user.id):
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
            f'⚠️ <a href="tg://user?id={user.id}">{style(html.escape(user.first_name))}</a>, ' + style("join the channel first to chat here."),
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
        cur = s["fsub"]["link"] or s["fsub"]["id"] if s["fsub"] else "off"
        return await update.message.reply_text(style(f"Force subscribe: {cur}\nUsage: /fsub @channel | off"))
    if arg.lower() == "off":
        s["fsub"] = None
        db.save(cid)
        return await update.message.reply_text(style("✅ fsub disabled."))
    try:
        ch = await context.bot.get_chat(int(arg) if arg.lstrip("-").isdigit() else arg)
        link = f"https://t.me/{ch.username}" if ch.username else (ch.invite_link or await context.bot.export_chat_invite_link(ch.id))
    except Exception as e:
        log.warning("fsub set failed: %s", e)
        return await update.message.reply_text(style("Channel not found. Add me as admin in the channel and try again."))
    s["fsub"] = {"id": ch.id, "link": link}
    db.save(cid)
    await update.message.reply_text(style(f"✅ fsub enabled for {ch.title}."))


def register(app):
    app.add_handler(CommandHandler(NAME, fsub, filters=filters.ChatType.GROUPS))
