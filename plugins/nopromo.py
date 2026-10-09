import re

NAME = "nopromo"
HELP = """<u>⊙ PROMOTIONAL MESSAGE FILTER :</u>

<blockquote>🚫 Blocks spam and promotional content.</blockquote>

<blockquote>↣ /nopromo on : Enable promo blocking...!
↣ /nopromo off : Disable promo blocking..!</blockquote>

<blockquote>⚠️ <b>Detected patterns :</b>
— Multiple repeated links (3+ URLs)
— "Join now", "Click here" spam
— 24/7 active, VC, chat group promotions
— Excessive emojis (15+ unique emojis)
— All-caps spam messages
— Promotional text with multiple lines
— "Make new friends", "Safe for girls" patterns</blockquote>

<blockquote>⚠️ <b>Action :</b>
— Score 15-25 : A warning message is sent.
— Score 25+ : The message is deleted.</blockquote>

<blockquote>⚠️ <b>Note :</b>
— Spam messages will be deleted.
— 👮 Only group admins can configure this setting.</blockquote>"""
REASON = "promotional content"

WARN_SCORE = 15    # 15-25 -> warning only
DELETE_SCORE = 25  # 25+   -> message deleted

URL_RE = re.compile(r"(https?://\S+|www\.\S+|t\.me/\S+|telegram\.me/\S+)", re.I)
PHRASES = [  # (pattern, points)
    (re.compile(r"\b(join now|click here)\b", re.I), 15),
    (re.compile(r"(24\s*/\s*7\s*active|\bvc\b|chat group)", re.I), 15),
    (re.compile(r"(make new friends|safe for girls)", re.I), 15),
]


def _unique_emojis(text):
    return {ch for ch in text if ord(ch) >= 0x1F300 or 0x2600 <= ord(ch) <= 0x27BF}


def score(text):
    pts = 0
    if len(URL_RE.findall(text)) >= 3:
        pts += 25
    for rx, p in PHRASES:
        if rx.search(text):
            pts += p
    if len(_unique_emojis(text)) >= 15:
        pts += 15
    letters = [c for c in text if c.isalpha()]
    if len(letters) >= 10 and sum(c.isupper() for c in letters) / len(letters) > 0.7:
        pts += 10
    if pts and len([l for l in text.splitlines() if l.strip()]) >= 4:
        pts += 10  # promotional text spread over many lines
    return pts


async def check(context, msg, user, text, etypes):
    pts = score(text)
    if pts >= DELETE_SCORE:
        return REASON                 # str  -> delete message + warning
    if pts >= WARN_SCORE:
        return (REASON, "warn")       # tuple -> warning only
    return None
