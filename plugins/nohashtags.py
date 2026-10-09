import re

NAME = "nohashtags"
HELP = """<u>⊙ HASHTAG FILTER :</u>

<blockquote># Blocks messages containing hashtags.</blockquote>

<blockquote>↣ /nohashtags on : Block hashtags...!
↣ /nohashtags off : Allow hashtags..!</blockquote>

<blockquote>⚠️ <b>Action :</b>
— Any word starting with the # symbol is detected.
— Example: #join, #promotion, #trending</blockquote>

<blockquote>⚠️ <b>Note :</b>
— Messages with hashtags will be deleted.
— 👮 Only group admins can configure this setting.</blockquote>"""
REASON = "hashtags"
HASH_RE = re.compile(r"(?<!\w)#\w+")


async def check(context, msg, user, text, etypes):
    return REASON if ("hashtag" in etypes or HASH_RE.search(text)) else None
