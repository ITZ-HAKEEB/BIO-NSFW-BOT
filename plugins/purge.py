from telegram.ext import CommandHandler, filters

from fonts import style
from helpers import admin_only, delete_later, log

NAME = "purge"
HELP = """<u>⊙ PURGE :</u>

<blockquote>🧹 Deletes many messages at once.</blockquote>

<blockquote>↣ Reply to a message with /purge : Deletes everything from that message to your command</blockquote>

<blockquote>⚠️ <b>Action :</b>
— All messages between the replied message and /purge are deleted.</blockquote>

<blockquote>⚠️ <b>Note :</b>
— 👮 Only group admins can configure this setting.</blockquote>"""


async def purge(update, context):
    if not await admin_only(update, context):
        return
    m = update.message
    if not m.reply_to_message:
        await m.reply_text(style("Jis message se delete karna hai uspe reply karke /purge likho."))
        return
    ids = list(range(m.reply_to_message.message_id, m.message_id + 1))
    for i in range(0, len(ids), 100):
        try:
            await context.bot.delete_messages(m.chat_id, ids[i:i + 100])
        except Exception as e:
            log.warning("purge: %s", e)
    note = await context.bot.send_message(m.chat_id, style(f"🧹 Purged {len(ids)} messages."))
    delete_later(context, note.chat_id, note.message_id, 5)


def register(app):
    app.add_handler(CommandHandler(NAME, purge, filters=filters.ChatType.GROUPS))
