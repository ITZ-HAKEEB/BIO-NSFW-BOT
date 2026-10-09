from telegram.ext import CommandHandler, filters

from database import db
from fonts import style
from helpers import admin_only


async def settings(update, context):
    if not await admin_only(update, context):
        return
    import plugins
    s = db.get(update.effective_chat.id)
    names = [m.NAME for m in plugins.TOGGLE_MODULES]
    lines = [f"{'✅' if s['mods'].get(n) else '❌'} {n}" for n in names]
    for n in ("mediadelete", "msgdelete"):
        lines.append(f"⏱ {n}: {s[n] if s[n] is not None else 'off'}")
    lines.append(f"📢 fsub: {'on' if s['fsub'] else 'off'}")
    lines.append(f"✅ approved users: {len(s['approved'])}")
    await update.message.reply_text(style("⚙️ Settings\n" + "\n".join(lines)))


def register(app):
    app.add_handler(CommandHandler("settings", settings, filters=filters.ChatType.GROUPS))
