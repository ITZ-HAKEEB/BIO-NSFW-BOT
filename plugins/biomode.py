import re, time

import config

NAME = "biomode"
HELP = """<u>⊙ BIO MODE :</u>

<blockquote>👤 Deletes messages from users who have a link or @username in their bio.</blockquote>

<blockquote>↣ /biomode on : Enable bio mode...!
↣ /biomode off : Disable bio mode..!</blockquote>

<blockquote>⚠️ <b>Action :</b>
— Messages from users with links or @usernames in their bio will be deleted and a warning is sent.</blockquote>

<blockquote>⚠️ <b>Note :</b>
— Group admins are always exempt.
— 👮 Only group admins can configure this setting.</blockquote>"""
REASON = "links in your bio"
BIO_RE = re.compile(r"(https?://|www\.|t\.me/|@\w{4,})", re.I)
_cache = {}


async def check(context, msg, user, text, etypes):
    hit = _cache.get(user.id)
    if hit and time.time() - hit[0] < config.BIO_CACHE_TTL:
        bad = hit[1]
    else:
        try:
            bio = (await context.bot.get_chat(user.id)).bio or ""
        except Exception:
            bio = ""
        bad = bool(BIO_RE.search(bio))
        _cache[user.id] = (time.time(), bad)
    return REASON if bad else None
