from telegram.ext import CommandHandler, filters
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from database import db
from fonts import style
from helpers import admin_only

NAME = "approve"

HELP = """<u>⊙ APPROVE :</u>

<blockquote>✅ Approved users are never filtered by the bot.</blockquote>

<blockquote>↣ /approve : Reply to a user to approve
↣ /approve user_id : Approve by user ID
↣ /approve @username : Approve by username
↣ /approve Full Name : Approve by full name
↣ /unapprove : Reply to a user or use ID/username/name
↣ /approved : Show all approved users</blockquote>

<blockquote>⚠️ <b>Action :</b>
— Approved users can send links, hashtags, forwards etc. without being deleted.</blockquote>

<blockquote>⚠️ <b>Note :</b>
— 👮 Only group admins can configure this setting.</blockquote>"""


def _find_target(update, context):
    message = update.message

    # 1. Reply to a user's message
    if message.reply_to_message:
        target_message = message.reply_to_message

        # Ignore anonymous admin / channel messages
        if target_message.from_user:
            return target_message.from_user

    args = context.args

    # No target provided
    if not args:
        return None

    target = " ".join(args).strip()

    # 2. Numeric Telegram user ID
    if target.lstrip("-").isdigit():
        return int(target)

    # 3. Username
    if target.startswith("@"):
        username = target[1:].lower()

        # Check users visible in the current group's chat history
        chat_members = getattr(context, "chat_data", {})
        cached_users = chat_members.get("known_users", {})

        for user in cached_users.values():
            if user.username and user.username.lower() == username:
                return user

        # Telegram Bot API cannot resolve arbitrary usernames
        # to user IDs automatically. Ask the user to reply instead.
        return {"error": "username", "value": target}

    # 4. Full name
    full_name = target.casefold()

    chat_members = getattr(context, "chat_data", {})
    cached_users = chat_members.get("known_users", {})

    matches = [
        user for user in cached_users.values()
        if user.full_name.casefold() == full_name
    ]

    if len(matches) == 1:
        return matches[0]

    if len(matches) > 1:
        return {"error": "ambiguous", "value": target}

    return {"error": "not_found", "value": target}


def _uid(target):
    return target if isinstance(target, int) else target.id


def _label(target):
    if isinstance(target, int):
        return f'<a href="tg://user?id={target}">{target}</a>'

    return target.mention_html()


async def approve(update, context):
    if not await admin_only(update, context):
        return

    target = _find_target(update, context)

    if target is None:
        return await update.message.reply_text(
            style(
                "Reply to a user's message or use:\n"
                "/approve USER_ID\n"
                "/approve @username\n"
                "/approve Full Name"
            )
        )

    if isinstance(target, dict):
        error = target["error"]
        value = target["value"]

        if error == "username":
            message = (
                f"❌ I cannot resolve {value} automatically.\n\n"
                "Ask that user to send a message in this group, "
                "then reply to their message with /approve."
            )
        elif error == "ambiguous":
            message = (
                f"❌ Multiple users have the name '{value}'.\n"
                "Please reply to the correct user's message "
                "or use their numeric user ID."
            )
        else:
            message = (
                f"❌ No matching user found for '{value}'.\n"
                "Reply to their message or use their numeric user ID."
            )

        return await update.message.reply_text(style(message))

    chat_id = update.effective_chat.id
    user_id = _uid(target)

    data = db.get(chat_id)

    if user_id not in data["approved"]:
        data["approved"].append(user_id)
        db.save(chat_id)

    await update.message.reply_html(
        f"✅ {_label(target)} {style('is approved now.')}"
    )


async def unapprove(update, context):
    if not await admin_only(update, context):
        return

    target = _find_target(update, context)

    if target is None:
        return await update.message.reply_text(
            style(
                "Reply to a user's message or use:\n"
                "/unapprove USER_ID\n"
                "/unapprove @username\n"
                "/unapprove Full Name"
            )
        )

    if isinstance(target, dict):
        return await update.message.reply_text(
            style(
                "❌ Could not identify that user. "
                "Reply to their message or use their numeric user ID."
            )
        )

    chat_id = update.effective_chat.id
    user_id = _uid(target)

    data = db.get(chat_id)

    if user_id in data["approved"]:
        data["approved"].remove(user_id)
        db.save(chat_id)

    await update.message.reply_html(
        f"🗑 {_label(target)} {style('is no longer approved.')}"
    )


async def approved(update, context):
    if not await admin_only(update, context):
        return

    ids = db.get(update.effective_chat.id)["approved"]

    if not ids:
        return await update.message.reply_text(
            style("No approved users.")
        )

    lines = [
        f'• <a href="tg://user?id={user_id}">{user_id}</a>'
        for user_id in ids
    ]

    await update.message.reply_html(
        style("✅ Approved users :") + "\n" + "\n".join(lines)
    )


def register(app):
    group_filter = filters.ChatType.GROUPS

    app.add_handler(
        CommandHandler("approve", approve, filters=group_filter)
    )
    app.add_handler(
        CommandHandler("unapprove", unapprove, filters=group_filter)
    )
    app.add_handler(
        CommandHandler("approved", approved, filters=group_filter)
    )
