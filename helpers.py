import html, logging, time

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

import config
from database import db
from fonts import style

log = logging.getLogger("meowguard")
_admin_cache = {}


async def is_admin(chat_id, user_id, context):
    key, now = (chat_id, user_id), time.time()
    hit = _admin_cache.get(key)
    if hit and now - hit[0] < config.ADMIN_CACHE_TTL:
        return hit[1]
    try:
        m = await context.bot.get_chat_member(chat_id, user_id)
        ok = m.status in ("administrator", "creator")
    except Exception:
        ok = False
    _admin_cache[key] = (now, ok)
    return ok


async def _del_job(context: ContextTypes.DEFAULT_TYPE):
    chat_id, msg_id = context.job.data
    try:
        await context.bot.delete_message(chat_id, msg_id)
    except Exception:
        pass


def delete_later(context, chat_id, msg_id, delay):
    context.job_queue.run_once(_del_job, max(delay, 0.1), data=(chat_id, msg_id))


async def _send_notice(context, msg, user, text):
    try:
        w = await context.bot.send_message(
            msg.chat_id,
            f'⚠️ <a href="tg://user?id={user.id}">{style(html.escape(user.first_name))}</a>, {style(text)}',
            parse_mode=ParseMode.HTML)
        delete_later(context, w.chat_id, w.message_id, config.WARN_DELETE_AFTER)
    except Exception:
        pass


async def warn(context, msg, user, reason, delay=0):
    """Delete msg (now, or after `delay` seconds) and send a self-deleting warning."""
    try:
        if delay:
            delete_later(context, msg.chat_id, msg.message_id, delay)
        else:
            await msg.delete()
    except Exception as e:
        log.warning("cannot delete (need 'Delete messages' right): %s", e)
        return
    await _send_notice(context, msg, user, f"{reason} is not allowed here.")


async def notice(context, msg, user, reason):
    """Warning only, message is kept."""
    await _send_notice(context, msg, user, f"{reason} is not allowed here. Next time it will be deleted.")


async def admin_only(update: Update, context):
    chat, user = update.effective_chat, update.effective_user
    if chat.type not in ("group", "supergroup"):
        await update.message.reply_text(style("Ye command group me use karo."))
        return False
    return await is_admin(chat.id, user.id, context)


def make_toggle(name):
    async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await admin_only(update, context):
            return
        cid = update.effective_chat.id
        s = db.get(cid)
        arg = context.args[0].lower() if context.args else ""
        if arg in ("on", "off"):
            s["mods"][name] = arg == "on"
            db.save(cid)
            await update.message.reply_text(style(f"✅ {name} {'enabled' if arg == 'on' else 'disabled'}."))
        else:
            st = "ON" if s["mods"].get(name) else "OFF"
            await update.message.reply_text(style(f"{name} is {st}.\nUsage: /{name} on|off"))
    return handler


def make_timer(name):
    async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await admin_only(update, context):
            return
        cid = update.effective_chat.id
        s = db.get(cid)
        arg = context.args[0].lower() if context.args else ""
        if arg == "off":
            s[name] = None
        elif arg.isdigit():
            s[name] = int(arg)
        else:
            cur = s[name] if s[name] is not None else "off"
            await update.message.reply_text(style(f"Usage: /{name} <seconds> | off\nNow: {cur}"))
            return
        db.save(cid)
        await update.message.reply_text(style(f"✅ {name}: {'off' if s[name] is None else str(s[name]) + 's'}"))
    return handler


def get_image():
    """Photo shown on /start and help: set with /setimage, or START_IMAGE env."""
    return db.get(0).get("image") or config.START_IMAGE or None
