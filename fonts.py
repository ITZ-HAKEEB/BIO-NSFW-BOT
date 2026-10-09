"""Small-caps font (like: ꜱᴛᴀʏ). Applied to every bot text via style()."""
import re

import config

_LOWER = "ᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘǫʀꜱᴛᴜᴠᴡxʏᴢ"
_MAP = {}
for i, ch in enumerate(_LOWER):
    _MAP[ord("a") + i] = ch
    _MAP[ord("A") + i] = ch

# parts that must stay untouched: user links, html tags, /commands, urls, @names, {placeholders}, &entities;
_KEEP = re.compile(r"(<a [^>]*>.*?</a>|<[^>]+>|/\w+|https?://\S+|@\w+|\{\w+\}|&\w+;)", re.S)


def style(text: str) -> str:
    if config.FONT_STYLE != "smallcaps" or not text:
        return text
    parts = _KEEP.split(text)
    return "".join(p if i % 2 else p.translate(_MAP) for i, p in enumerate(parts))


# ---- button font: Title Case with small-caps body, o/r/e swapped for the "Meow" look ----
_BTN_LOWER = {ord("ᴏ"): "σ", ord("ʀ"): "ᖇ", ord("ᴇ"): "є"}
_BTN_UPPER = str.maketrans({"E": "Є", "O": "σ", "R": "ᖇ"})


def btn_style(text: str) -> str:
    """Inline-button label font. ALL CAPS labels -> caps with swapped letters, others -> Title Case small-caps."""
    if config.FONT_STYLE != "smallcaps" or not text:
        return text
    letters = [c for c in text if c.isascii() and c.isalpha()]
    if letters and all(c.isupper() for c in letters):
        return text.translate(_BTN_UPPER)
    return re.sub(r"[A-Za-z]+",
                  lambda m: m.group()[0].upper() + m.group()[1:].lower().translate(_MAP).translate(_BTN_LOWER),
                  text)
