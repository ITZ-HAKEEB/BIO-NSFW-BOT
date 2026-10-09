from telegram.ext import CommandHandler, filters

from helpers import admin_only

NAME = "echo"
HELP = """<u>⊙ ECHO :</u>

<blockquote>🔊 Makes the bot repeat your text.</blockquote>

<blockquote>↣ /echo text : Bot sends your text
↣ Reply to a message with /echo text : Bot replies with your text</blockquote>

<blockquote>⚠️ <b>Action :</b>
— Your command message is deleted and the bot sends the text.</blockquote>

<blockquote>⚠️ <b>Note :</b>
— 👮 Only group admins can configure this setting.</blockquote>"""


async def echo(update, context):
    if not await admin_only(update, context) or not context.args:
        return
    text = update.message.text.split(None, 1)[1]
    try:
        await update.message.delete()
    except Exception:
        pass
    r = update.message.reply_to_message
    await context.bot.send_message(update.effective_chat.id, text,
                                   reply_to_message_id=r.message_id if r else None)


def register(app):
    app.add_handler(CommandHandler(NAME, echo, filters=filters.ChatType.GROUPS))
