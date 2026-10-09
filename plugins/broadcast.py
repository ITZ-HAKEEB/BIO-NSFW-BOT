import asyncio, re

from telegram.error import Forbidden, RetryAfter, TelegramError
from telegram.ext import ChatMemberHandler, CommandHandler, filters

import config
from database import db
from fonts import style
from helpers import log

NAME = "broadcast"
HELP = "Owner only: /broadcast (reply to a message or give text), /stats"
USAGE = ("Usage (owner only, in bot PM):\n"
         "• Reply to any message with /broadcast  (media/format kept, no forward tag)\n"
         "• /broadcast your text here\n"
         "Flags: -users  -groups  -pin   (default: users + groups)\n"
         "Example: /broadcast -groups -pin Server maintenance at 9 PM")
_running = False


def _is_owner(update):
    return bool(config.OWNER_ID) and update.effective_user.id == config.OWNER_ID


async def _send_one(context, target, src, text, pin):
    """Returns 'ok', 'dead' (blocked / kicked / chat gone) or 'fail'."""
    for _ in range(3):
        try:
            if src:
                r = await context.bot.copy_message(target, src.chat_id, src.message_id)
            else:
                r = await context.bot.send_message(target, text)
            if pin:
                try:
                    await context.bot.pin_chat_message(target, r.message_id, disable_notification=True)
                except TelegramError:
                    pass
            return "ok"
        except RetryAfter as e:
            wait = e.retry_after
            await asyncio.sleep((wait.total_seconds() if hasattr(wait, "total_seconds") else wait) + 1)
        except Forbidden:
            return "dead"
        except TelegramError as e:
            low = str(e).lower()
            return "dead" if ("chat not found" in low or "deactivated" in low) else "fail"
        except Exception as e:
            log.warning("broadcast error to %s: %s", target, e)
            return "fail"
    return "fail"


async def _run(context, status, src, text, targets, pin):
    global _running
    ok = fail = dead = done = 0
    total = sum(len(v) for _, v in targets)
    try:
        for kind, ids in targets:
            for i in ids:
                res = await _send_one(context, i, src, text, pin and kind == "groups")
                if res == "ok":
                    ok += 1
                elif res == "dead":
                    dead += 1
                    await asyncio.to_thread(db.remove, kind, i)
                else:
                    fail += 1
                done += 1
                if done % 100 == 0:
                    try:
                        await status.edit_text(style(f"📣 Broadcasting... {done}/{total}"))
                    except TelegramError:
                        pass
                await asyncio.sleep(0.05)   # stay under Telegram's ~30 msg/sec limit
        try:
            await status.edit_text(style(f"✅ Broadcast finished\n\nTotal: {total}\nSent: {ok}\n"
                                         f"Failed: {fail}\nRemoved (blocked or left): {dead}"))
        except TelegramError:
            pass
    finally:
        _running = False


async def broadcast(update, context):
    global _running
    m = update.effective_message
    if update.effective_chat.type != "private":
        return
    if not config.OWNER_ID:
        return await m.reply_text(style("OWNER_ID config var set nahi hai."))
    if not _is_owner(update):
        return
    parts = m.text.split(None, 1)
    body, flags = (parts[1] if len(parts) > 1 else ""), set()
    while True:
        f = re.match(r"-(users|groups|pin)\b\s*", body)
        if not f:
            break
        flags.add(f.group(1))
        body = body[f.end():]
    src = m.reply_to_message
    if not src and not body.strip():
        return await m.reply_text(style(USAGE))
    if _running:
        return await m.reply_text(style("Ek broadcast already chal raha hai, wait karo."))
    kinds = [k for k in ("users", "groups") if k in flags] or ["users", "groups"]
    targets = [(k, await asyncio.to_thread(db.ids, k)) for k in kinds]
    total = sum(len(v) for _, v in targets)
    if not total:
        return await m.reply_text(style("Koi user/group saved nahi hai abhi."))
    status = await m.reply_text(style(f"📣 Broadcasting to {total} chats..."))
    _running = True
    context.application.create_task(_run(context, status, src, body.strip(), targets, "pin" in flags))


async def stats(update, context):
    if update.effective_chat.type != "private" or not _is_owner(update):
        return
    mode = "MongoDB" if config.MONGO_URI else "local data.json (resets on Heroku restart)"
    u, g = await asyncio.gather(asyncio.to_thread(db.count, "users"), asyncio.to_thread(db.count, "groups"))
    await update.effective_message.reply_text(style(f"📊 Stats\n\nUsers: {u}\nGroups: {g}\nStorage: {mode}"))


async def on_my_member(update, context):
    """Track where the bot lives: added -> save, blocked/kicked/left -> remove."""
    cm = update.my_chat_member
    if not cm:
        return
    kind = "users" if cm.chat.type == "private" else "groups"
    if cm.new_chat_member.status in ("left", "kicked"):
        await asyncio.to_thread(db.remove, kind, cm.chat.id)
    elif cm.chat.type != "channel":
        await asyncio.to_thread(db.add, kind, cm.chat.id)


def register(app):
    pm = filters.ChatType.PRIVATE
    app.add_handler(CommandHandler("broadcast", broadcast, filters=pm))
    app.add_handler(CommandHandler("stats", stats, filters=pm))
    app.add_handler(ChatMemberHandler(on_my_member, ChatMemberHandler.MY_CHAT_MEMBER))
