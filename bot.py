import asyncio
import logging

from telegram import BotCommand, Update
from telegram.ext import Application

import config
import plugins
from fonts import style
from plugins import logs, nsfw

logging.basicConfig(level=logging.INFO)
# httpx logs every request URL, which contains the bot token -> keep it quiet
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)


COMMANDS = [
    ("start", "Start the bot"), ("help", "Help and commands"), ("settings", "Show group settings"),
    ("approve", "Approve a user"), ("unapprove", "Remove approval"), ("approved", "List approved users"),
    ("fsub", "Force subscribe a channel"), ("abuse", "Abuse filter on/off"), ("linkfilter", "Link filter on/off"),
    ("nopromo", "Promo filter on/off"), ("nophone", "Phone filter on/off"), ("nohashtags", "Hashtag filter on/off"),
    ("noforward", "Forward filter on/off"), ("nostylish", "Stylish font filter on/off"), ("biomode", "Bio link filter on/off"),
    ("nsfw", "NSFW photo filter on/off"), ("edit", "Delete edited messages on/off"), ("mediadelete", "Auto-delete media"), ("msgdelete", "Auto-delete messages"),
    ("echo", "Make the bot repeat text"), ("purge", "Delete many messages"),
]


async def post_init(app):
    try:  # command descriptions in the Menu button use the same font
        await app.bot.set_my_commands([BotCommand(c, style(d)) for c, d in COMMANDS])
    except Exception as e:
        logging.warning("set_my_commands failed: %s", e)
    await asyncio.to_thread(nsfw.load_model)   # load the offline NSFW model once at startup
    await logs.started(app.bot)   # "Bot Started" message in the log group


async def post_stop(app):
    await logs.stopped(app.bot)   # "Bot Stopped" (Heroku restart / deploy / shutdown)


def main():
    if not config.BOT_TOKEN:
        raise SystemExit("BOT_TOKEN is not set (Heroku Config Vars or .env)")
    app = Application.builder().token(config.BOT_TOKEN).post_init(post_init).post_stop(post_stop).build()
    plugins.register_all(app)
    logging.info("Bot started")
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)


if __name__ == "__main__":
    main()
