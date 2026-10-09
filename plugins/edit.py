NAME = "edit"
HELP = """<u>⊙ EDIT MODE :</u>

<blockquote>✍️ Deletes edited messages sent by regular users.</blockquote>

<blockquote>↣ /edit on : Enable edit mode...!
↣ /edit off : Disable edit mode..!</blockquote>

<blockquote>⚠️ <b>Action :</b>
— Edited messages from regular users will be deleted and a notice is sent.</blockquote>

<blockquote>⚠️ <b>Note :</b>
— Group admins are always exempt.
— 👮 Only group admins can configure this setting.</blockquote>"""
REASON = "editing messages"


async def check(context, msg, user, text, etypes):
    return REASON  # guard only calls this for edited messages
