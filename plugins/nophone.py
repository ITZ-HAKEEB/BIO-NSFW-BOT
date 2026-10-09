import re

NAME = "nophone"
HELP = """<u>⊙ PHONE NUMBER FILTER :</u>

<blockquote>📞 Blocks messages containing phone numbers.</blockquote>

<blockquote>↣ /nophone on : Block phone numbers...!
↣ /nophone off : Allow phone numbers..!</blockquote>

<blockquote>⚠️ <b>Action :</b>
— International format: +91 9876543210
— With spaces or dashes: +1-234-567-8900
— Without plus: 919876543210</blockquote>

<blockquote>⚠️ <b>Note :</b>
— Messages with phone numbers will be deleted.
— 👮 Only group admins can configure this setting.</blockquote>"""
REASON = "phone numbers"
PHONE_RE = re.compile(r"(?<!\d)(?:\+?\d[\s\-().]?){9,14}\d(?!\d)")


async def check(context, msg, user, text, etypes):
    return REASON if ("phone_number" in etypes or PHONE_RE.search(text)) else None
