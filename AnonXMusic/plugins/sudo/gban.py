import asyncio
from pyrogram import filters
from pyrogram.errors import FloodWait, UserAdminInvalid, PeerIdInvalid
from pyrogram.types import Message

from saptasree import app
from saptasree.misc import SUDOERS
from saptasree.utils import get_readable_time
from saptasree.utils.decorators.language import language
from saptasree.utils.extraction import extract_user

# -------------------- 🔗 MONGO CONFIG --------------------
from motor.motor_asyncio import AsyncIOMotorClient

MONGO_DB_URI = "mongodb+srv://jc07cv9k3k:bEWsTrbPgMpSQe2z@cluster0.nfbxb.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
mongo_client = AsyncIOMotorClient(MONGO_DB_URI)
db = mongo_client["united_ban_system"]

bans_col = db.banned_users
chats_col = db.served_chats
# --------------------------------------------------------


# -------------------- 📦 DATABASE UTILS --------------------
async def add_banned_user(user_id: int):
    await bans_col.update_one({"user_id": user_id}, {"$set": {"user_id": user_id}}, upsert=True)

async def remove_banned_user(user_id: int):
    await bans_col.delete_one({"user_id": user_id})

async def is_banned_user(user_id: int) -> bool:
    return await bans_col.find_one({"user_id": user_id}) is not None

async def get_banned_users():
    return [doc["user_id"] async for doc in bans_col.find({})]

async def get_banned_count():
    return await bans_col.count_documents({})

async def add_served_chat(chat_id: int):
    await chats_col.update_one({"chat_id": chat_id}, {"$set": {"chat_id": chat_id}}, upsert=True)

async def get_served_chats():
    return [doc async for doc in chats_col.find({})]
# ------------------------------------------------------------


# ------------------ ✅ TRACK EVERY CHAT --------------------
@app.on_message(filters.group & ~filters.service)
async def log_served_chat(client, message: Message):
    await add_served_chat(message.chat.id)
# ------------------------------------------------------------


# -------------------- 🚫 UNIFIED BAN ------------------------
@app.on_message(filters.command("uban") & SUDOERS)
@language
async def united_ban(client, message: Message, _):
    if not message.reply_to_message and len(message.command) < 2:
        return await message.reply_text("❌ Usage: `/uban @username` or reply to a user.")

    user = await extract_user(message)
    if not user:
        return await message.reply_text("❌ Couldn't extract user.")
    if user.id in [message.from_user.id, app.id] or user.id in SUDOERS:
        return await message.reply_text("🚫 Cannot ban this user.")

    if await is_banned_user(user.id):
        return await message.reply_text(f"🔒 {user.mention} is already banned.")

    await add_banned_user(user.id)
    served_chats = [int(chat["chat_id"]) for chat in await get_served_chats()]
    time_est = get_readable_time(len(served_chats))
    processing = await message.reply_text(f"⏳ Banning {user.mention} in {len(served_chats)} chats... ({time_est})")

    banned = 0
    for chat_id in served_chats:
        try:
            await app.ban_chat_member(chat_id, user.id)
            banned += 1
        except FloodWait as fw:
            await asyncio.sleep(fw.value)
        except (UserAdminInvalid, PeerIdInvalid):
            continue
        except Exception:
            continue

    await processing.edit_text(
        f"✅ {user.mention} was banned from <b>{banned}</b> chats.\n"
        f"👮 Banned by: {message.from_user.mention}"
    )
# ------------------------------------------------------------


# ------------------ ♻️ UNBAN FUNCTION -----------------------
@app.on_message(filters.command("urevoke") & SUDOERS)
@language
async def united_unban(client, message: Message, _):
    if not message.reply_to_message and len(message.command) < 2:
        return await message.reply_text("❌ Usage: `/urevoke @username` or reply to a user.")

    user = await extract_user(message)
    if not user:
        return await message.reply_text("❌ Couldn't extract user.")
    if not await is_banned_user(user.id):
        return await message.reply_text(f"✅ {user.mention} is not banned.")

    await remove_banned_user(user.id)
    served_chats = [int(chat["chat_id"]) for chat in await get_served_chats()]
    time_est = get_readable_time(len(served_chats))
    processing = await message.reply_text(f"⏳ Unbanning {user.mention} from {len(served_chats)} chats... ({time_est})")

    unbanned = 0
    for chat_id in served_chats:
        try:
            await app.unban_chat_member(chat_id, user.id)
            unbanned += 1
        except FloodWait as fw:
            await asyncio.sleep(fw.value)
        except (UserAdminInvalid, PeerIdInvalid):
            continue
        except Exception:
            continue

    await processing.edit_text(
        f"✅ {user.mention} was unbanned in <b>{unbanned}</b> chats.\n"
        f"👮 Action by: {message.from_user.mention}"
    )
# ------------------------------------------------------------


# ------------------- 📊 STATS COMMAND ------------------------
@app.on_message(filters.command("ubstats") & SUDOERS)
@language
async def united_ban_stats(client, message: Message, _):
    chats = await get_served_chats()
    banned_users = await get_banned_users()
    banned_count = len(banned_users)

    text = (
        f"📊 <b>United Ban System Stats</b>\n\n"
        f"🤖 Total Bots Connected: <code>1</code>\n"
        f"💬 Monitored Chats: <code>{len(chats)}</code>\n"
        f"🚫 Banned Users: <code>{banned_count}</code>\n\n"
        f"🧾 <b>List of Banned Users:</b>\n"
    )

    for idx, uid in enumerate(banned_users, start=1):
        try:
            user = await app.get_users(uid)
            name = user.mention
        except:
            name = f"<code>{uid}</code>"
        text += f"{idx}. {name}\n"

    await message.reply_text(text)
# ------------------------------------------------------------
