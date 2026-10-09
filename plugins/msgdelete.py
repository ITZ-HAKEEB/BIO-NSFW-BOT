from telegram.ext import CommandHandler, filters

from helpers import delete_later, make_timer

NAME = "msgdelete"
HELP = """<u>⊙ MESSAGE DELETE :</u>

<blockquote>⏱ Auto-deletes every message sent by regular users after a delay.</blockquote>

<blockquote>↣ /msgdelete seconds : Delete messages after the given seconds
↣ /msgdelete off : Disable message delete</blockquote>

<blockquote>⚠️ <b>Action :</b>
— Messages from regular users are deleted after the set time.</blockquote>

<blockquote>⚠️ <b>Note :</b>
— Group admins are always exempt.
— 👮 Only group admins can configure this setting.</blockquote>"""


def apply(context, msg, s):
    if s.get("msgdelete") is not None:
        delete_later(context, msg.chat_id, msg.message_id, s["msgdelete"])
        return True
    return False


def register(app):
    app.add_handler(CommandHandler(NAME, make_timer(NAME), filters=filters.ChatType.GROUPS))
