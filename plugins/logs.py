
"""Logger: sends bot events to the log group (LOG_GROUP_ID).

Events: bot started / stopped, bot added to / removed from a chat, new user started the bot.
Does nothing if LOG_GROUP_ID is not set.
"""

import html
import pkgutil
import platform
from datetime import datetime, timezone

import telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, LinkPreviewOptions
from telegram.constants import ParseMode
from telegram.error import ChatMigrated, TelegramError
from telegram.ext import ChatMemberHandler, CommandHandler, filters

import config
import plugins
from fonts import btn_style, style
from helpers import get_image, log

NAME = "logs"
_IN = ("member", "administrator", "creator", "restricted")
_NO_PREVIEW = LinkPreviewOptions(is_disabled=True)

last_error = ""
_resolved = None


def _now():
    return datetime.now(timezone.utc).strftime("%d %b %Y, %H:%M:%S UTC")


def _user_link(user):
    name = html.escape(user.full_name or "User")
    return f'<a href="tg://user?id={user.id}">{name}</a>'


def _targets():
    """Return the configured logger chat ID and common ID alternatives."""
    cid = config.LOG_GROUP_ID

    if not isinstance(cid, int) or not cid:
        return [cid] if cid else []

    if _resolved is not None:
        return [_resolved]

    out = [cid]

    if cid > 0:
        out.extend([-cid, int(f"-100{cid}")])
    elif not str(cid).startswith("-100"):
        out.append(int(f"-100{-cid}"))

    return out


def _hint(err):
    low = str(err).lower()

    if (
        isinstance(err, ChatMigrated)
        or "upgraded to a supergroup" in low
        or "migrated" in low
    ):
        return "Group supergroup ban gaya hai. Nayi ID LOG_GROUP_ID mein daalein."

    if any(x in low for x in (
        "not enough rights",
        "have no rights",
        "need administrator",
        "can't send",
    )):
        return "Bot ko message bhejne ki permission nahi hai. Bot ko admin banayein."

    if "chat not found" in low:
        return "Chat nahi mila. ID check karein aur bot ko group/channel mein add karein."

    if any(x in low for x in ("forbidden", "not a member", "kicked")):
        return "Bot group mein nahi hai ya kick/ban hai. Bot ko dobara add karein."

    if "thread" in low or "topic" in low:
        return "Group topic access check karein."

    return "Telegram error."


async def send_log(bot, text, photo=None, markup=None):
    """Send an HTML log message. Returns True if successful."""
    global last_error, _resolved

    if not config.LOG_GROUP_ID:
        last_error = (
            "LOG_GROUP_ID set nahi hai ya galat hai. "
            "Format: -1001234567890"
        )
        return False

    queue = list(_targets())
    tried = []

    while queue:
        target = queue.pop(0)

        if target in tried:
            continue

        tried.append(target)

        try:
            sent = False

            if photo:
                try:
                    await bot.send_photo(
                        chat_id=target,
                        photo=photo,
                        caption=text,
                        parse_mode=ParseMode.HTML,
                        reply_markup=markup,
                    )
                    sent = True

                except TelegramError as exc:
                    if (
                        isinstance(exc, ChatMigrated)
                        or "chat not found" in str(exc).lower()
                    ):
                        raise

                    log.warning(
                        "Logger photo failed; trying text: %s", exc
                    )

            if not sent:
                await bot.send_message(
                    chat_id=target,
                    text=text,
                    parse_mode=ParseMode.HTML,
                    link_preview_options=_NO_PREVIEW,
                    reply_markup=markup,
                )

            _resolved = target
            last_error = ""

            if target != config.LOG_GROUP_ID:
                log.warning(
                    "Logger works with chat ID %s. Set LOG_GROUP_ID=%s",
                    target,
                    target,
                )

            return True

        except ChatMigrated as exc:
            last_error = f"{exc} -> {_hint(exc)}"
            queue.insert(0, exc.new_chat_id)

        except TelegramError as exc:
            last_error = f"{exc} -> {_hint(exc)}"

            if "chat not found" not in str(exc).lower():
                break

        except Exception as exc:
            last_error = f"{type(exc).__name__}: {exc}"
            break

    log.warning(
        "Logger failed for LOG_GROUP_ID=%s | %s",
        config.LOG_GROUP_ID,
        last_error,
    )
    return False


def start_text(bot):
    plugins_loaded = sum(
        1 for _ in pkgutil.iter_modules(plugins.__path__)
    )

    return (
        f"❖ <b>{style('𝐁ᴏᴛ 𝐒ᴛᴀʀᴛᴇᴅ 𝐒ᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ')}</b> ✅\n\n"
        f"• <b>{style('𝐁ᴏᴛ')}</b> :- "
        f"{html.escape(config.BOT_NAME)}\n"
        f"• <b>{style('𝐏ʟᴜɢɪɴꜱ')}</b> :- "
        f"{plugins_loaded} {style('𝐋ᴏᴀᴅᴇᴅ')}\n"
        f"• <b>{style('𝐏𝐓𝐁')}</b> :- "
        f"<code>{telegram.__version__}</code>\n"
        f"• <b>{style('𝐏ʏᴛʜᴏɴ')}</b> :- "
        f"<code>{platform.python_version()}</code>\n\n"
        f"» <b>{style('𝐏ᴏᴡᴇʀᴇᴅ 𝐁ʏ')}</b> :- "
        f'<a href="{html.escape(config.UPDATE_CHANNEL_URL, quote=True)}">'
        f"{html.escape(config.BOT_NAME)}</a>"
    )


def start_kb(bot):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                btn_style("𝐀ᴅᴅ 𝐌ᴇ 𝐓ᴏ 𝐘ᴏᴜʀ 𝐆ʀᴏᴜᴘ"),
                url=(
                    f"https://t.me/{bot.username}"
                    "?startgroup=true&admin=delete_messages+restrict_members"
                ),
            )
        ]
    ])


async def started(bot):
    """Send startup logs without interrupting bot startup."""
    try:
        if not config.LOG_GROUP_ID:
            log.info(
                "Logger OFF: LOG_GROUP_ID not set or invalid: %r",
                config.LOG_GROUP_RAW,
            )

            if config.LOG_GROUP_RAW and config.OWNER_ID:
                await bot.send_message(
                    config.OWNER_ID,
                    style(
                        "⚠️ 𝐋ᴏɢɢᴇʀ 𝐎ꜰꜰ 𝐇ᴀɪ\n"
                        "𝐒ᴀʜɪ 𝐅ᴏʀᴍᴀᴛ: -1001234567890\n\n"
                        "𝐂ᴜʀʀᴇɴᴛ 𝐕ᴀʟᴜᴇ: "
                    ) + html.escape(config.LOG_GROUP_RAW),
                    parse_mode=ParseMode.HTML,
                )
            return

        ok = await send_log(
            bot,
            start_text(bot),
            photo=config.LOG_IMAGE or get_image(),
            markup=start_kb(bot),
        )

        if ok:
            log.info("Startup message sent to logger")
        elif config.OWNER_ID:
            await bot.send_message(
                config.OWNER_ID,
                style("⚠️ 𝐋ᴏɢɢᴇʀ 𝐅ᴀɪʟᴇᴅ:\n")
                + html.escape(last_error)
                + "\n\nLOG_GROUP_ID = "
                + html.escape(str(config.LOG_GROUP_RAW)),
                parse_mode=ParseMode.HTML,
            )

    except Exception as exc:
        log.warning("Logger startup failed: %s", exc)


async def logtest(update, context):
    """Owner-only logger test in private chat."""
    message = update.effective_message

    if not config.OWNER_ID:
        await message.reply_text(
            style("⚠️ 𝐎ᴡɴᴇʀ_𝐈𝐃 𝐂ᴏɴꜰɪɢ 𝐕ᴀʀ ꜱᴇᴛ 𝐊ᴀʀᴏ.")
        )
        return

    if update.effective_user.id != config.OWNER_ID:
        return

    bot = context.bot

    ok = await send_log(
        bot,
        start_text(bot),
        photo=config.LOG_IMAGE or get_image(),
        markup=start_kb(bot),
    )

    if ok:
        await message.reply_text(
            style("✅ 𝐋ᴏɢ 𝐌ᴇꜱꜱᴀɢᴇ 𝐒ᴇɴᴛ.\n")
            + f"Chat ID: {_resolved}"
        )

        if _resolved != config.LOG_GROUP_ID:
            await message.reply_text(
                style("💡 𝐂ᴏɴꜰɪɢ 𝐕ᴀʀ 𝐔ᴘᴅᴀᴛᴇ 𝐊ᴀʀᴏ:\n")
                + f"LOG_GROUP_ID = {_resolved}"
            )

    else:
        await message.reply_text(
            style("❌ 𝐌ᴇꜱꜱᴀɢᴇ 𝐅ᴀɪʟᴇᴅ.\n")
            + html.escape(last_error)
            + "\n\nLOG_GROUP_ID = "
            + html.escape(str(config.LOG_GROUP_RAW) or "empty"),
            parse_mode=ParseMode.HTML,
        )


async def stopped(bot):
    await send_log(
        bot,
        f"🔴 <b>{style('𝐁ᴏᴛ 𝐒ᴛᴏᴘᴘᴇᴅ')}</b>\n\n"
        f"{style('𝐓ɪᴍᴇ')} : {_now()}",
    )


async def new_user(bot, user):
    """Log a user the first time they start the bot."""
    username = (
        f"@{html.escape(user.username)}"
        if user.username
        else style("𝐍ᴏɴᴇ")
    )

    await send_log(
        bot,
        f"👤 <b>{style('𝐍ᴇᴡ 𝐔ꜱᴇʀ')}</b>\n\n"
        f"{style('𝐍ᴀᴍᴇ')} : {_user_link(user)}\n"
        f"{style('𝐈𝐃')} : <code>{user.id}</code>\n"
        f"{style('𝐔ꜱᴇʀɴᴀᴍᴇ')} : {username}\n"
        f"{style('𝐓ɪᴍᴇ')} : {_now()}",
    )


async def on_my_member(update, context):
    """Log when the bot joins or leaves a group or channel."""
    chat_member = update.my_chat_member

    if (
        not chat_member
        or chat_member.chat.type == "private"
        or chat_member.chat.id in _targets()
    ):
        return

    was_in = chat_member.old_chat_member.status in _IN
    is_in = chat_member.new_chat_member.status in _IN

    if was_in == is_in:
        return

    chat = chat_member.chat
    title = html.escape(chat.title or "?")

    username = (
        f"@{html.escape(chat.username)}"
        if chat.username
        else style("𝐏ʀɪᴠᴀᴛᴇ")
    )

    by = (
        _user_link(chat_member.from_user)
        if chat_member.from_user
        else "?"
    )

    if is_in:
        try:
            members = await context.bot.get_chat_member_count(chat.id)
        except TelegramError:
            members = "?"

        heading = f"➕ <b>{style('𝐀ᴅᴅᴇᴅ 𝐓ᴏ 𝐍ᴇᴡ 𝐂ʜᴀᴛ')}</b>"
        who = style("𝐀ᴅᴅᴇᴅ 𝐁ʏ")
        extra = f"{style('𝐌ᴇᴍʙᴇʀꜱ')} : {members}\n"

    else:
        heading = f"➖ <b>{style('𝐑ᴇᴍᴏᴠᴇᴅ 𝐅ʀᴏᴍ 𝐂ʜᴀᴛ')}</b>"
        who = style("𝐑ᴇᴍᴏᴠᴇᴅ 𝐁ʏ")
        extra = ""

    await send_log(
        context.bot,
        f"{heading}\n\n"
        f"{style('𝐂ʜᴀᴛ')} : {title}\n"
        f"{style('𝐈𝐃')} : <code>{chat.id}</code>\n"
        f"{style('𝐔ꜱᴇʀɴᴀᴍᴇ')} : {username}\n"
        f"{extra}"
        f"{who} : {by}\n"
        f"{style('𝐓ɪᴍᴇ')} : {_now()}",
    )


def register(app):
    # group=1 allows this handler to run alongside other group-0 handlers.
    app.add_handler(
        ChatMemberHandler(
            on_my_member,
            ChatMemberHandler.MY_CHAT_MEMBER,
        ),
        group=1,
    )

    app.add_handler(
        CommandHandler(
            "logtest",
            logtest,
            filters=filters.ChatType.PRIVATE,
        )
    )
