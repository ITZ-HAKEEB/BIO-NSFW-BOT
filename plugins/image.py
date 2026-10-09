from telegram.ext import CommandHandler, MessageHandler, filters

import config
from database import db
from fonts import style

NAME = "image"
HELP = "Owner only: reply to a photo with /setimage (or send a photo with caption /setimage). /delimage removes it."


def _owner(update):
    return config.OWNER_ID and update.effective_user.id == config.OWNER_ID


async def set_image(update, context):
    m = update.effective_message
    if not config.OWNER_ID:
        return await m.reply_text(style("OWNER_ID config var set nahi hai."))
    if not _owner(update):
        return
    photo = m.photo or (m.reply_to_message.photo if m.reply_to_message else None)
    if not photo:
        return await m.reply_text(style("Photo pe reply karke /setimage likho."))
    g = db.get(0)
    g["image"] = photo[-1].file_id
    db.save(0)
    await m.reply_text(style("✅ Photo set ho gayi. /start check karo."))


async def del_image(update, context):
    if not _owner(update):
        return
    g = db.get(0)
    g["image"] = None
    db.save(0)
    await update.effective_message.reply_text(style("🗑 Photo hata di."))


def register(app):
    pm = filters.ChatType.PRIVATE
    app.add_handler(CommandHandler("setimage", set_image, filters=pm))
    app.add_handler(MessageHandler(pm & filters.PHOTO & filters.CaptionRegex(r"^/setimage"), set_image))
    app.add_handler(CommandHandler("delimage", del_image, filters=pm))
