import config

NAME = "nostylish"
HELP = """<u>⊙ STYLISH FONT FILTER :</u>

<blockquote>🔤 Automatically detects and removes messages sent with stylish or decorative fonts.</blockquote>

<blockquote>↣ /nostylish on : Enable stylish font filter...!
↣ /nostylish off : Disable stylish font filter..!</blockquote>

<blockquote>⚠️ <b>Action :</b>
— Messages with stylish text will be deleted after 5 seconds.
— A warning will be sent and also deleted after 5 seconds.</blockquote>

<blockquote>⚠️ <b>Note :</b>
— 👮 Only group admins can configure this setting.</blockquote>"""
REASON = "stylish text"
DELETE_DELAY = 5  # message is deleted after 5 seconds
RANGES = [(0x1D00, 0x1DBF), (0x1D400, 0x1D7FF), (0x2100, 0x214F), (0x249C, 0x24E9),
          (0xFF21, 0xFF5A), (0x1F130, 0x1F189), (0x0250, 0x02AF), (0xA720, 0xA7FF), (0x0300, 0x036F)]


async def check(context, msg, user, text, etypes):
    n = sum(1 for ch in text if any(a <= ord(ch) <= b for a, b in RANGES))
    return REASON if n >= config.STYLISH_MIN_CHARS else None
