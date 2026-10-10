import html
import time

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.error import TelegramError
from telegram.ext import CommandHandler, filters

import config
from database import db
from fonts import btn_style, style
from helpers import admin_only, delete_later, log


NAME = "fsub"

HELP = """<u>⊙ ғᴏʀᴄᴇ sᴜʙsᴄʀɪʙᴇ :</u>

<blockquote>📢 ᴜsᴇʀs ᴍᴜsᴛ ᴊᴏɪɴ ʏᴏᴜʀ ᴄʜᴀɴɴᴇʟ ʙᴇғᴏʀᴇ ᴛʜᴇʏ ᴄᴀɴ ᴄʜᴀᴛ ɪɴ ᴛʜᴇ ɢʀᴏᴜᴘ.</blockquote>

<blockquote>↣ /fsub @channel : sᴇᴛ ᴛʜᴇ ᴄʜᴀɴɴᴇʟ
↣ /fsub off : ᴅɪsᴀʙʟᴇ ғᴏʀᴄᴇ sᴜʙsᴄʀɪʙᴇ
↣ /fsub : sʜᴏᴡ ᴄᴜʀʀᴇɴᴛ sᴛᴀᴛᴜs</blockquote>

<blockquote>⚠️ <b>ᴀᴄᴛɪᴏɴ :</b>
— ᴍᴇssᴀɢᴇs ғʀᴏᴍ ᴜsᴇʀs ᴡʜᴏ ʜᴀᴠᴇ ɴᴏᴛ ᴊᴏɪɴᴇᴅ ᴀʀᴇ ᴅᴇʟᴇᴛᴇᴅ ᴀɴᴅ ᴀ ᴊᴏɪɴ ʙᴜᴛᴛᴏɴ ɪs sᴇɴᴛ.</blockquote>

<blockquote>⚠️ <b>ɴᴏᴛᴇ :</b>
— ᴀᴅᴅ ᴛʜᴇ ʙᴏᴛ ᴀs ᴀɴ ᴀᴅᴍɪɴ ɪɴ ᴛʜᴇ ᴄʜᴀɴɴᴇʟ.
— ɢʀᴏᴜᴘ ᴀᴅᴍɪɴs ᴀɴᴅ ᴀᴘᴘʀᴏᴠᴇᴅ ᴜsᴇʀs ᴀʀᴇ ᴇxᴇᴍᴘᴛ.
— 👮 ᴏɴʟʏ ɢʀᴏᴜᴘ ᴀᴅᴍɪɴs ᴄᴀɴ ᴄᴏɴғɪɢᴜʀᴇ ᴛʜɪs sᴇᴛᴛɪɴɢ.</blockquote>"""


_cache = {}
_broken = {}
_notified = {}

BROKEN_RETRY = 300
NOTIFY_EVERY = 1800


async def check_member(context, channel_id, user_id):
    """True = joined, False = not joined, None = cannot check."""

    key = (channel_id, user_id)
    now = time.time()

    hit = _cache.get(key)

    if hit and now - hit < config.FSUB_CACHE_TTL:
        return True

    if now - _broken.get(channel_id, 0) < BROKEN_RETRY:
        return None

    try:
        member = await context.bot.get_chat_member(
            channel_id,
            user_id
        )

    except TelegramError as e:
        _broken[channel_id] = now

        log.warning(
            "ғsᴜʙ ᴄʜᴇᴄᴋ ғᴀɪʟᴇᴅ ғᴏʀ ᴄʜᴀɴɴᴇʟ %s: %s",
            channel_id,
            e
        )

        return None

    _broken.pop(channel_id, None)

    joined = (
        member.status not in ("left", "kicked")
        and not (
            member.status == "restricted"
            and not getattr(member, "is_member", True)
        )
    )

    if joined:
        _cache[key] = now

    return joined


async def _tell_group_broken(context, chat_id):
    now = time.time()

    if now - _notified.get(chat_id, 0) < NOTIFY_EVERY:
        return

    _notified[chat_id] = now

    try:
        message = await context.bot.send_message(
            chat_id,
            "⚠️ " + style(
                "ғᴏʀᴄᴇ sᴜʙsᴄʀɪʙᴇ ɪs ɴᴏᴛ ᴡᴏʀᴋɪɴɢ!\n\n"
                "ᴀᴅᴍɪɴs: ᴍᴀᴋᴇ ᴍᴇ ᴀᴅᴍɪɴ ɪɴ ᴛʜᴇ ᴄʜᴀɴɴᴇʟ, "
                "ᴛʜᴇɴ sᴇɴᴅ /fsub ᴀɢᴀɪɴ."
            )
        )

        delete_later(
            context,
            message.chat_id,
            message.message_id,
            60
        )

    except Exception:
        pass


async def enforce(context, msg, user, s):
    """Returns True if the message was removed because the user has not joined."""

    cfg = s.get("fsub")

    if not cfg:
        return False

    joined = await check_member(
        context,
        cfg["id"],
        user.id
    )

    if joined is None:
        await _tell_group_broken(
            context,
            msg.chat_id
        )
        return False

    if joined:
        return False

    try:
        await msg.delete()

    except Exception as e:
        log.warning("ғsᴜʙ: ᴄᴀɴɴᴏᴛ ᴅᴇʟᴇᴛᴇ: %s", e)
        return True

    keyboard = None

    if cfg.get("link"):
        keyboard = InlineKeyboardMarkup(
            [[
                InlineKeyboardButton(
                    btn_style("✦ ᴊᴏɪɴ ᴄʜᴀɴɴᴇʟ ✦"),
                    url=cfg["link"]
                )
            ]]
        )

    try:
        message = await context.bot.send_message(
            msg.chat_id,
            (
                f'⚠️ <a href="tg://user?id={user.id}">'
                f'{html.escape(user.first_name)}</a>, '
                + style(
                    "ᴘʟᴇᴀsᴇ ᴊᴏɪɴ ᴛʜᴇ ᴄʜᴀɴɴᴇʟ "
                    "ғɪʀsᴛ ᴛᴏ ᴄʜᴀᴛ ʜᴇʀᴇ."
                )
            ),
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard
        )

        delete_later(
            context,
            message.chat_id,
            message.message_id,
            max(config.WARN_DELETE_AFTER, 10)
        )

    except Exception:
        pass

    return True


async def fsub(update, context):
    if not await admin_only(update, context):
        return

    chat_id = update.effective_chat.id
    settings = db.get(chat_id)

    arg = context.args[0] if context.args else ""

    if not arg:
        cfg = settings.get("fsub")

        current = (
            cfg.get("link") or cfg["id"]
            if cfg else "ᴏғғ"
        )

        return await update.message.reply_text(
            style(
                f"⊙ ғᴏʀᴄᴇ sᴜʙsᴄʀɪʙᴇ\n\n"
                f"✦ sᴛᴀᴛᴜs : {current}\n\n"
                f"✦ ᴜsᴀɢᴇ : /fsub @channel | off"
            )
        )

    if arg.lower() == "off":
        settings["fsub"] = None
        db.save(chat_id)

        return await update.message.reply_text(
            style("✅ ғᴏʀᴄᴇ sᴜʙsᴄʀɪʙᴇ ᴅɪsᴀʙʟᴇᴅ!")
        )

    try:
        channel = await context.bot.get_chat(
            int(arg) if arg.lstrip("-").isdigit() else arg
        )

    except TelegramError as e:
        log.warning("ғsᴜʙ sᴇᴛ ғᴀɪʟᴇᴅ: %s", e)

        return await update.message.reply_text(
            style(
                "❌ ᴄʜᴀɴɴᴇʟ ɴᴏᴛ ғᴏᴜɴᴅ!\n\n"
                "ᴄʜᴇᴄᴋ ᴛʜᴇ @username / ɪᴅ, ᴀᴅᴅ ᴍᴇ ᴀs "
                "ᴀɴ ᴀᴅᴍɪɴ ɪɴ ᴛʜᴇ ᴄʜᴀɴɴᴇʟ ᴀɴᴅ ᴛʀʏ ᴀɢᴀɪɴ."
            )
        )

    try:
        me = await context.bot.get_chat_member(
            channel.id,
            context.bot.id
        )

        is_admin = me.status in (
            "administrator",
            "creator"
        )

    except TelegramError:
        is_admin = False

    if not is_admin:
        return await update.message.reply_text(
            style(
                f"❌ ɪ ᴀᴍ ɴᴏᴛ ᴀɴ ᴀᴅᴍɪɴ ɪɴ {channel.title}!\n\n"
                "ᴀᴅᴅ ᴍᴇ ᴀs ᴀɴ ᴀᴅᴍɪɴ ɪɴ ᴛʜᴇ ᴄʜᴀɴɴᴇʟ "
                "ᴀɴᴅ sᴇɴᴅ /fsub ᴀɢᴀɪɴ."
            )
        )

    link = (
        f"https://t.me/{channel.username}"
        if channel.username
        else channel.invite_link
    )

    if not link:
        try:
            link = await context.bot.export_chat_invite_link(
                channel.id
            )

        except TelegramError as e:
            log.warning("ғsᴜʙ: ɴᴏ ɪɴᴠɪᴛᴇ ʟɪɴᴋ: %s", e)

    _broken.pop(channel.id, None)

    settings["fsub"] = {
        "id": channel.id,
        "link": link
    }

    db.save(chat_id)

    await update.message.reply_text(
        style(
            f"✅ ғᴏʀᴄᴇ sᴜʙsᴄʀɪʙᴇ ᴇɴᴀʙʟᴇᴅ!\n\n"
            f"📢 ᴄʜᴀɴɴᴇʟ : {channel.title}"
            + (
                ""
                if link
                else "\n⚠️ ɴᴏ ɪɴᴠɪᴛᴇ ʟɪɴᴋ ᴀᴠᴀɪʟᴀʙʟᴇ."
            )
        )
    )


def register(app):
    app.add_handler(
        CommandHandler(
            NAME,
            fsub,
            filters=filters.ChatType.GROUPS
        )
    )
