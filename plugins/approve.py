from telegram.ext import CommandHandler, filters

from database import db
from fonts import style
from helpers import admin_only

NAME = "approve"
HELP = """<u>⊙ APPROVE :</u>

<blockquote>✅ Approved users are never filtered by the bot.</blockquote>

<blockquote>↣ /approve : Reply to a user (or /approve user_id) to approve
↣ /unapprove : Reply to a user (or /unapprove user_id) to remove approval
↣ /approved : Show all approved users</blockquote>

<blockquote>⚠️ <b>Action :</b>
— Approved users can send links, hashtags, forwards etc. without being deleted.</blockquote>

<blockquote>⚠️ <b>Note :</b>
— 👮 Only group admins can configure this setting.</blockquote>"""


def _target(update, context):
    m = update.message
    if m.reply_to_message and m.reply_to_message.from_user:
        return m.reply_to_message.from_user
    if context.args and context.args[0].lstrip("-").isdigit():
        return int(context.args[0])
    return None


def _uid(t):
    return t if isinstance(t, int) else t.id


def _label(t):
    return str(t) if isinstance(t, int) else (t.mention_html() if t else "")


async def approve(update, context):
    if not await admin_only(update, context):
        return
    t = _target(update, context)
    if t is None:
        return await update.message.reply_text(style("Reply to a user or send /approve user_id"))
    cid = update.effective_chat.id
    s = db.get(cid)
    if _uid(t) not in s["approved"]:
        s["approved"].append(_uid(t))
        db.save(cid)
    await update.message.reply_html(f"✅ {_label(t)} {style('is approved now.')}")


async def unapprove(update, context):
    if not await admin_only(update, context):
        return
    t = _target(update, context)
    if t is None:
        return await update.message.reply_text(style("Reply to a user or send /unapprove user_id"))
    cid = update.effective_chat.id
    s = db.get(cid)
    if _uid(t) in s["approved"]:
        s["approved"].remove(_uid(t))
        db.save(cid)
    await update.message.reply_html(f"🗑 {_label(t)} {style('is no longer approved.')}")


async def approved(update, context):
    if not await admin_only(update, context):
        return
    ids = db.get(update.effective_chat.id)["approved"]
    if not ids:
        return await update.message.reply_text(style("No approved users."))
    lines = [f'• <a href="tg://user?id={i}">{i}</a>' for i in ids]
    await update.message.reply_html(style("✅ Approved users :") + "\n" + "\n".join(lines))


def register(app):
    g = filters.ChatType.GROUPS
    app.add_handler(CommandHandler("approve", approve, filters=g))
    app.add_handler(CommandHandler("unapprove", unapprove, filters=g))
    app.add_handler(CommandHandler("approved", approved, filters=g))
