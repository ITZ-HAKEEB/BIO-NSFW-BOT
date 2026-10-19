
import asyncio
import logging

from telegram import BotCommand, Update
from telegram.ext import Application

import config
import plugins
from fonts import style
from plugins import logs, nsfw


# ---- logging configuration ----
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

# Hide HTTP request URLs that could contain the bot token.
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)


# ---- bot commands ----
COMMANDS = [
    ("start", "𝐒ᴛᴀʀᴛ ᴛʜᴇ ʙᴏᴛ"),
    ("help", "𝐇ᴇʟᴘ ᴀɴᴅ ᴄᴏᴍᴍᴀɴᴅꜱ"),
    ("settings", "𝐒ʜᴏᴡ ɢʀᴏᴜᴘ ꜱᴇᴛᴛɪɴɢꜱ"),
    ("approve", "𝐀ᴘᴘʀᴏᴠᴇ ᴀ ᴜꜱᴇʀ"),
    ("unapprove", "𝐑ᴇᴍᴏᴠᴇ ᴀᴘᴘʀᴏᴠᴀʟ"),
    ("approved", "𝐋ɪꜱᴛ ᴀᴘᴘʀᴏᴠᴇᴅ ᴜꜱᴇʀꜱ"),
    ("fsub", "𝐅ᴏʀᴄᴇ ꜱᴜʙꜱᴄʀɪʙᴇ ᴀ ᴄʜᴀɴɴᴇʟ"),
    ("abuse", "𝐀ʙᴜꜱᴇ ꜰɪʟᴛᴇʀ ᴏɴ/ᴏꜰꜰ"),
    ("linkfilter", "𝐋ɪɴᴋ ꜰɪʟᴛᴇʀ ᴏɴ/ᴏꜰꜰ"),
    ("nopromo", "𝐏ʀᴏᴍᴏ ꜰɪʟᴛᴇʀ ᴏɴ/ᴏꜰꜰ"),
    ("nophone", "𝐏ʜᴏɴᴇ ꜰɪʟᴛᴇʀ ᴏɴ/ᴏꜰꜰ"),
    ("nohashtags", "𝐇ᴀꜱʜᴛᴀɢ ꜰɪʟᴛᴇʀ ᴏɴ/ᴏꜰꜰ"),
    ("noforward", "𝐅ᴏʀᴡᴀʀᴅ ꜰɪʟᴛᴇʀ ᴏɴ/ᴏꜰꜰ"),
    ("nostylish", "𝐒ᴛʏʟɪꜱʜ ꜰᴏɴᴛ ꜰɪʟᴛᴇʀ ᴏɴ/ᴏꜰꜰ"),
    ("biomode", "𝐁ɪᴏ ʟɪɴᴋ ꜰɪʟᴛᴇʀ ᴏɴ/ᴏꜰꜰ"),
    ("nsfw", "𝐍𝐒𝐅𝐖 ᴘʜᴏᴛᴏ ꜰɪʟᴛᴇʀ ᴏɴ/ᴏꜰꜰ"),
    ("edit", "𝐃ᴇʟᴇᴛᴇ ᴇᴅɪᴛᴇᴅ ᴍᴇꜱꜱᴀɢᴇꜱ"),
    ("mediadelete", "𝐀ᴜᴛᴏ-ᴅᴇʟᴇᴛᴇ ᴍᴇᴅɪᴀ"),
    ("msgdelete", "𝐀ᴜᴛᴏ-ᴅᴇʟᴇᴛᴇ ᴍᴇꜱꜱᴀɢᴇꜱ"),
    ("echo", "𝐌ᴀᴋᴇ ᴛʜᴇ ʙᴏᴛ ʀᴇᴘᴇᴀᴛ ᴛᴇxᴛ"),
    ("purge", "𝐃ᴇʟᴇᴛᴇ ᴍᴜʟᴛɪᴘʟᴇ ᴍᴇꜱꜱᴀɢᴇꜱ"),
]


async def post_init(app):
    """Set commands and initialize services after application startup."""
    try:
        await app.bot.set_my_commands([
            BotCommand(command, style(description))
            for command, description in COMMANDS
        ])
        logging.info("Bot commands registered successfully")

    except Exception as exc:
        logging.warning("Setting bot commands failed: %s", exc)

    try:
        # Load the offline NSFW model in a worker thread.
        await asyncio.to_thread(nsfw.load_model)
    except Exception:
        logging.exception("NSFW model initialization failed")

    # Send startup event to the logger.
    await logs.started(app.bot)


async def post_stop(app):
    """Send shutdown event when the application stops."""
    try:
        await logs.stopped(app.bot)
    except Exception:
        logging.exception("Bot shutdown logging failed")


def main():
    if not config.BOT_TOKEN:
        raise SystemExit(
            "BOT_TOKEN is not set (Heroku Config Vars or .env)"
        )

    app = (
        Application.builder()
        .token(config.BOT_TOKEN)
        .post_init(post_init)
        .post_stop(post_stop)
        .build()
    )

    plugins.register_all(app)

    logging.info("𝐁ᴏᴛ ɪꜱ ꜱᴛᴀʀᴛɪɴɢ...")
    app.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True,
    )


if __name__ == "__main__":
    main()
