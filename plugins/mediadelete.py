from telegram.ext import CommandHandler, filters

from helpers import delete_later, make_timer

NAME = "mediadelete"
HELP = """<u>⊙ MEDIA DELETE :</u>

<blockquote>🖼 Auto-deletes media (photo, video, file, sticker...) sent by regular users.</blockquote>

<blockquote>↣ /mediadelete seconds : Delete media after the given seconds (0 = instantly)
↣ /mediadelete off : Disable media delete</blockquote>

<blockquote>⚠️ <b>Action :</b>
— Media from regular users is deleted after the set time.</blockquote>

<blockquote>⚠️ <b>Note :</b>
— Group admins are always exempt.
— 👮 Only group admins can configure this setting.</blockquote>"""


def apply(context, msg, s):
    """Schedule deletion. Returns True if msg was media and handled."""
    m = msg
    is_media = bool(m.photo or m.video or m.document or m.audio or m.voice
                    or m.sticker or m.animation or m.video_note)
    if s.get("mediadelete") is not None and is_media:
        delete_later(context, m.chat_id, m.message_id, s["mediadelete"])
        return True
    return False


def register(app):
    app.add_handler(CommandHandler(NAME, make_timer(NAME), filters=filters.ChatType.GROUPS))
