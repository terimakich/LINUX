import asyncio
from pyrogram import filters
from pyrogram.errors import FloodWait
from pyrogram.types import Message
from AnonXMusic import app
from AnonXMusic.misc import SUDOERS
from AnonXMusic.utils import get_readable_time
from AnonXMusic.utils.database import (
    add_banned_user,
    get_banned_count,
    get_banned_users,
    get_served_chats,
    is_banned_user,
    remove_banned_user,
)
from AnonXMusic.utils.decorators.language import language
from AnonXMusic.utils.extraction import extract_user
from config import BANNED_USERS

LOG_CHANNEL = -1002693521679  # 👈 Log channel for combo ban system


@app.on_message(filters.command(["gban", "globalban"]) & SUDOERS)
@language
async def global_ban(client, message: Message, _):
    if not message.reply_to_message:
        if len(message.command) != 2:
            return await message.reply_text(_["general_1"])
    user = await extract_user(message)
    if user.id == message.from_user.id:
        return await message.reply_text(_["gban_1"])
    elif user.id == app.id:
        return await message.reply_text(_["gban_2"])
    elif user.id in SUDOERS:
        return await message.reply_text(_["gban_3"])

    is_gbanned = await is_banned_user(user.id)
    if is_gbanned:
        return await message.reply_text(_["gban_4"].format(user.mention))

    if user.id not in BANNED_USERS:
        BANNED_USERS.add(user.id)

    served_chats = [int(chat["chat_id"]) for chat in await get_served_chats()]
    time_expected = get_readable_time(len(served_chats))

    mystic = await message.reply_text(_["gban_5"].format(user.mention, time_expected))

    number_of_chats = 0
    for chat_id in served_chats:
        try:
            await app.ban_chat_member(chat_id, user.id)
            number_of_chats += 1
        except FloodWait as fw:
            await asyncio.sleep(int(fw.value))
        except:
            continue

    await add_banned_user(user.id)

    # ✅ Send Log
    ban_code = f"#banit-{str(user.id)[-2:]}"
    try:
        await app.send_message(
            LOG_CHANNEL,
            f"🚫 **Global Ban Issued**\n"
            f"👤 User: {user.mention}\n"
            f"🆔 ID: `{user.id}`\n"
            f"🔐 Code: `{user.id} {ban_code}`\n"
            f"📊 Total Chats Banned: `{number_of_chats}`"
        )
    except Exception as e:
        print(f"Failed to log gban: {e}")

    await message.reply_text(
        _["gban_6"].format(
            app.mention,
            message.chat.title,
            message.chat.id,
            user.mention,
            user.id,
            message.from_user.mention,
            number_of_chats,
        )
    )
    await mystic.delete()


@app.on_message(filters.command(["ungban", "urevoke"]) & SUDOERS)
@language
async def global_un(client, message: Message, _):
    if not message.reply_to_message:
        if len(message.command) != 2:
            return await message.reply_text(_["general_1"])
    user = await extract_user(message)

    is_gbanned = await is_banned_user(user.id)
    if not is_gbanned:
        return await message.reply_text(_["gban_7"].format(user.mention))

    if user.id in BANNED_USERS:
        BANNED_USERS.remove(user.id)

    served_chats = [int(chat["chat_id"]) for chat in await get_served_chats()]
    time_expected = get_readable_time(len(served_chats))

    mystic = await message.reply_text(_["gban_8"].format(user.mention, time_expected))

    number_of_chats = 0
    for chat_id in served_chats:
        try:
            await app.unban_chat_member(chat_id, user.id)
            number_of_chats += 1
        except FloodWait as fw:
            await asyncio.sleep(int(fw.value))
        except:
            continue

    await remove_banned_user(user.id)

    try:
        await app.send_message(
            LOG_CHANNEL,
            f"✅ **Global Unban Issued**\n"
            f"👤 User: {user.mention}\n"
            f"🆔 ID: `{user.id}`\n"
            f"📊 Total Chats Unbanned: `{number_of_chats}`"
        )
    except Exception as e:
        print(f"Failed to log ungban: {e}")

    await message.reply_text(_["gban_9"].format(user.mention, number_of_chats))
    await mystic.delete()


@app.on_message(filters.command(["gbannedusers", "gbanlist", "ubstats"]) & SUDOERS)
@language
async def gbanned_list(client, message: Message, _):
    counts = await get_banned_count()
    if counts == 0:
        return await message.reply_text(_["gban_10"])

    mystic = await message.reply_text(_["gban_11"])
    msg = _["gban_12"]
    count = 0
    users = await get_banned_users()
    for user_id in users:
        count += 1
        try:
            user = await app.get_users(user_id)
            user_mention = user.first_name if not user.mention else user.mention
            msg += f"{count}➤ {user_mention}\n"
        except Exception:
            msg += f"{count}➤ `{user_id}`\n"
            continue

    if count == 0:
        return await mystic.edit_text(_["gban_10"])
    else:
        return await mystic.edit_text(msg)
