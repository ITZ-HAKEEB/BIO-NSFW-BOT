import re

from telegram.ext import CommandHandler, filters

import config
from database import db
from fonts import style
from helpers import admin_only

NAME = "abuse"
HELP = """<u>⊙ ABUSE FILTER :</u>

<blockquote>🤬 Deletes messages containing bad words.</blockquote>

<blockquote>↣ /abuse on : Enable abuse filter...!
↣ /abuse off : Disable abuse filter..!
↣ /addabuse word : Add a custom bad word
↣ /rmabuse word : Remove a custom bad word</blockquote>

<blockquote>⚠️ <b>Action :</b>
— Messages with abusive words will be deleted and a warning is sent.</blockquote>

<blockquote>⚠️ <b>Note :</b>
— Group admins are always exempt.
— 👮 Only group admins can configure this setting.</blockquote>"""
REASON = "abusive language"


async def check(context, msg, user, text, etypes):
    if not text:
        return None
    low = text.lower()
    words = config.DEFAULT_BAD_WORDS + db.get(msg.chat_id).get("words", [])
    for w in words:
        if re.search(rf"(?<!\w){re.escape(w)}(?!\w)", low):
            return REASON


async def add_word(update, context):
    if not await admin_only(update, context) or not context.args:
        return
    cid = update.effective_chat.id
    s, w = db.get(cid), " ".join(context.args).lower()
    if w not in s["words"]:
        s["words"].append(w)
        db.save(cid)
    await update.message.reply_text(f"{style('✅ Added:')} {w}")


async def remove_word(update, context):
    if not await admin_only(update, context) or not context.args:
        return
    cid = update.effective_chat.id
    s, w = db.get(cid), " ".join(context.args).lower()
    if w in s["words"]:
        s["words"].remove(w)
        db.save(cid)
    await update.message.reply_text(f"{style('🗑 Removed:')} {w}")


def register(app):
    g = filters.ChatType.GROUPS
    app.add_handler(CommandHandler("addabuse", add_word, filters=g))
    app.add_handler(CommandHandler("rmabuse", remove_word, filters=g))
