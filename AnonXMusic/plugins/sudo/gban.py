import asyncio
from datetime import datetime
from pyrogram import filters
from pyrogram.errors import FloodWait, UserAdminInvalid, PeerIdInvalid
from pyrogram.types import Message

from AnonXMusic import app
from AnonXMusic.misc import SUDOERS
from AnonXMusic.utils import get_readable_time
from AnonXMusic.utils.decorators.language import language
from AnonXMusic.utils.extraction import extract_user

from motor.motor_asyncio import AsyncIOMotorClient

MONGO_DB_URI = "mongodb+srv://jc07cv9k3k:bEWsTrbPgMpSQe2z@cluster0.nfbxb.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
mongo_client = AsyncIOMotorClient(MONGO_DB_URI)
db = mongo_client["united_ban_system"]

bans_col = db.banned_users
chats_col = db.served_chats
bots_col = db.bots
pairs_col = db.bot_pairs


# ---------------- DATABASE UTILS ----------------

async def add_banned_user(user_id: int):
    await bans_col.update_one(
        {"user_id": user_id},
        {"$set": {"user_id": user_id, "timestamp": datetime.utcnow()}},
        upsert=True
    )

async def remove_banned_user(user_id: int):
    await bans_col.delete_one({"user_id": user_id})

async def is_banned_user(user_id: int) -> bool:
    return await bans_col.find_one({"user_id": user_id}) is not None

async def get_banned_users():
    return [doc["user_id"] async for doc in bans_col.find({})]

async def get_served_chats():
    return [doc["chat_id"] async for doc in chats_col.find({})]

async def add_served_chat(chat_id: int):
    await chats_col.update_one({"chat_id": chat_id}, {"$set": {"chat_id": chat_id}}, upsert=True)

async def register_bot():
    me = await app.get_me()
    await bots_col.update_one(
        {"bot_id": me.id},
        {"$set": {"bot_id": me.id, "bot_username": me.username, "registered": datetime.utcnow()}},
        upsert=True
    )

async def add_bot_pair(bot_id: int):
    me = await app.get_me()
    await pairs_col.update_one(
        {"bot_a": me.id, "bot_b": bot_id},
        {"$set": {"bot_a": me.id, "bot_b": bot_id, "timestamp": datetime.utcnow()}},
        upsert=True
    )

async def get_bot_pairs():
    me = await app.get_me()
    return [doc["bot_b"] async for doc in pairs_col.find({"bot_a": me.id})]


# ---------------- TRACK CHATS ----------------

@app.on_message(filters.group & ~filters.service)
async def log_served_chat(_, message: Message):
    await add_served_chat(message.chat.id)


# ---------------- REGISTRATION ----------------

@app.on_message(filters.command("reg") & SUDOERS)
async def register_connection(client, message: Message):
    if len(message.command) < 2:
        return await message.reply("❌ Usage: /reg <BOT_ID or 'UNITED'>")

    if message.command[1].upper() == "UNITED":
        me = await app.get_me()
        await register_bot()
        await message.reply(f"✅ Registered to United Ban Federation as @{me.username}.")
    else:
        try:
            bot_id = int(message.command[1])
            await add_bot_pair(bot_id)
            await message.reply(f"🔗 Successfully paired with bot ID <code>{bot_id}</code>.")
        except:
            await message.reply("❌ Invalid bot ID.")


# ---------------- BAN USER ----------------

@app.on_message(filters.command("uban") & SUDOERS)
@language
async def united_ban(_, message: Message, __):
    if not message.reply_to_message and len(message.command) < 2:
        return await message.reply_text("❌ Usage: /uban @username or reply to a user.")

    user = await extract_user(message)
    if not user:
        return await message.reply_text("❌ Couldn't extract user.")
    if user.id in [message.from_user.id, app.id] or user.id in SUDOERS:
        return await message.reply_text("🚫 Cannot ban this user.")
    if await is_banned_user(user.id):
        return await message.reply_text(f"🔒 {user.mention} is already banned.")

    await add_banned_user(user.id)
    all_chat_ids = await get_served_chats()
    time_est = get_readable_time(len(all_chat_ids))
    msg = await message.reply_text(f"⏳ Banning {user.mention} in {len(all_chat_ids)} chats... ({time_est})")

    banned = 0
    for chat_id in all_chat_ids:
        try:
            await app.ban_chat_member(chat_id, user.id)
            banned += 1
        except FloodWait as fw:
            await asyncio.sleep(fw.value)
        except (UserAdminInvalid, PeerIdInvalid):
            continue
        except:
            continue

    await msg.edit_text(f"✅ {user.mention} banned in <b>{banned}</b> chats.")


# ---------------- UNBAN USER ----------------

@app.on_message(filters.command("urevoke") & SUDOERS)
@language
async def united_unban(_, message: Message, __):
    if not message.reply_to_message and len(message.command) < 2:
        return await message.reply_text("❌ Usage: /urevoke @username or reply to a user.")

    user = await extract_user(message)
    if not user:
        return await message.reply_text("❌ Couldn't extract user.")
    if not await is_banned_user(user.id):
        return await message.reply_text(f"✅ {user.mention} is not banned.")

    await remove_banned_user(user.id)
    all_chat_ids = await get_served_chats()
    time_est = get_readable_time(len(all_chat_ids))
    msg = await message.reply_text(f"⏳ Unbanning {user.mention} in {len(all_chat_ids)} chats... ({time_est})")

    unbanned = 0
    for chat_id in all_chat_ids:
        try:
            await app.unban_chat_member(chat_id, user.id)
            unbanned += 1
        except FloodWait as fw:
            await asyncio.sleep(fw.value)
        except (UserAdminInvalid, PeerIdInvalid):
            continue
        except:
            continue

    await msg.edit_text(f"✅ {user.mention} unbanned in <b>{unbanned}</b> chats.")


# ---------------- STATS ----------------

@app.on_message(filters.command("ubstats") & SUDOERS)
@language
async def united_stats(_, message: Message, __):
    chats = await get_served_chats()
    banned_users = await get_banned_users()
    bots = [doc async for doc in bots_col.find({})]

    text = f"📊 <b>United Ban Stats</b>\n\n"
    text += f"🤖 Connected Bots: <code>{len(bots)}</code>\n"
    text += f"💬 Monitored Chats: <code>{len(chats)}</code>\n"
    text += f"🚫 Banned Users: <code>{len(banned_users)}</code>\n\n"
    text += f"🧾 <b>Banned Users List</b>:\n"

    for i, uid in enumerate(banned_users, 1):
        try:
            user = await app.get_users(uid)
            text += f"{i}. {user.mention}\n"
        except:
            text += f"{i}. <code>{uid}</code>\n"

    await message.reply(text)


# ---------------- CONNECTED BOTS ----------------

@app.on_message(filters.command("ubots") & SUDOERS)
@language
async def show_connected_bots(_, message: Message, __):
    bots = [doc async for doc in bots_col.find({})]
    if not bots:
        return await message.reply("❌ No bots connected.")

    text = "🤖 <b>Connected Bots:</b>\n"
    for i, bot in enumerate(bots, 1):
        username = bot.get("bot_username", "Unknown")
        bot_id = bot.get("bot_id", "N/A")
        text += f"{i}. @{username} — <code>{bot_id}</code>\n"

    await message.reply(text)


# ---------------- STARTUP REGISTER ----------------

@app.on_message(filters.command("testreg") & SUDOERS)
async def startup_test(_, message):
    await register_bot()
    await message.reply("✅ Registered to federation.")
