from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters

from database import db
from helpers import is_admin, notice, warn
from plugins import FILTERS, edit, fsub, mediadelete, msgdelete


async def guard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg, chat, user = update.effective_message, update.effective_chat, update.effective_user
    if not msg or not user or chat.type not in ("group", "supergroup"):
        return
    db.add_group(chat.id)                   # remember group for /broadcast
    if msg.sender_chat or msg.is_automatic_forward or user.is_bot:
        return
    if await is_admin(chat.id, user.id, context):
        return

    s = db.get(chat.id)
    if user.id in s["approved"]:
        return
    text = msg.text or msg.caption or ""
    ents = msg.entities or msg.caption_entities or []
    etypes = {e.type for e in ents}

    if update.edited_message:
        if s["mods"].get(edit.NAME):
            reason = await edit.check(context, msg, user, text, etypes)
            if reason:
                await warn(context, msg, user, reason)
        return

    if not update.edited_message and await fsub.enforce(context, msg, user, s):
        return

    for mod in FILTERS:
        if s["mods"].get(mod.NAME):
            res = await mod.check(context, msg, user, text, etypes)
            if not res:
                continue
            if isinstance(res, tuple):          # (reason, "warn") -> warning only
                await notice(context, msg, user, res[0])
                continue
            return await warn(context, msg, user, res, getattr(mod, "DELETE_DELAY", 0))

    if mediadelete.apply(context, msg, s):
        return
    msgdelete.apply(context, msg, s)


def register(app):
    app.add_handler(MessageHandler(filters.ChatType.GROUPS & ~filters.COMMAND, guard))
