import re

NAME = "linkfilter"
HELP = """<u>⊙ LINK FILTER :</u>

<blockquote>🔗 Blocks messages containing links.</blockquote>

<blockquote>↣ /linkfilter on : Block links...!
↣ /linkfilter off : Allow links..!</blockquote>

<blockquote>⚠️ <b>Action :</b>
— Detects http/https links, www links, t.me links and plain domains.
— Messages with links will be deleted.</blockquote>

<blockquote>⚠️ <b>Note :</b>
— 👮 Only group admins can configure this setting.</blockquote>"""
REASON = "links"
URL_RE = re.compile(r"(https?://|www\.|t\.me/|telegram\.me/|\b[\w-]+\.(com|net|org|in|io|me|xyz|info|co|link|site|online|app|ly)\b)", re.I)


async def check(context, msg, user, text, etypes):
    return REASON if (etypes & {"url", "text_link"} or URL_RE.search(text)) else None
