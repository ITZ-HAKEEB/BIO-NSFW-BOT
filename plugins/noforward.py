NAME = "noforward"
HELP = """<u>⊙ FORWARD FILTER :</u>

<blockquote>📤 Blocks forwarded messages in the group.</blockquote>

<blockquote>↣ /noforward on : Block forwarded messages...!
↣ /noforward off : Allow forwarded messages..!</blockquote>

<blockquote>⚠️ <b>Action :</b>
— Forwarded messages will be deleted automatically.</blockquote>

<blockquote>⚠️ <b>Note :</b>
— 👮 Only group admins can configure this setting.</blockquote>"""
REASON = "forwarded messages"


async def check(context, msg, user, text, etypes):
    return REASON if msg.forward_origin else None
