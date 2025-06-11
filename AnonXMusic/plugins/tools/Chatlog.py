import random
from pyrogram import Client, filters
from pyrogram.types import (
    Message,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    CallbackQuery,
)
from config import LOGGER_ID as LOG_GROUP_ID
from AnonXMusic import app

# Images
ADDED_IMAGE = "https://files.catbox.moe/ro0pv8.jpg"
REMOVED_IMAGE = "https://files.catbox.moe/rsvbcs.jpg"

# Store messages for editing later
group_logs = {}

@app.on_message(filters.new_chat_members, group=2)
async def join_watcher(_, message):    
    chat = message.chat
    link = await app.export_chat_invite_link(chat.id)
    for member in message.new_chat_members:
        if member.id == app.id:
            count = await app.get_chat_members_count(chat.id)
            msg = (
                "◆━━━━━━━━━━━━━◆\n\n"
                "❖ #ᴀᴅᴅᴇᴅ_ɪɴ_ɢʀᴏᴜᴘ ❖\n\n"
                f"❖ ᴄʜᴀᴛ ɴᴀᴍᴇ : {chat.title}\n"
                f"❖ ᴄʜᴀᴛ ɪᴅ : `{chat.id}`\n"
                f"❖ ᴄʜᴀᴛ ᴜsᴇʀɴᴀᴍᴇ : @{chat.username if chat.username else 'None'}\n"
                f"❖ ᴄʜᴀᴛ ʟɪɴᴋ : {link}\n"
                f"❖ ᴛᴏᴛᴀʟ ᴍᴇᴍʙᴇʀs : {count}\n"
                f"❖ ᴀᴅᴅᴇᴅ ʙʏ : {message.from_user.mention}\n\n"
                "◆━━━━━━━━━━━━━◆"
            )
            sent = await app.send_photo(
                LOG_GROUP_ID,
                photo=ADDED_IMAGE,
                caption=msg,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("➜ ɢᴇᴛ ʟɪɴᴋ", callback_data=f"getlink|{link}")]
                ])
            )
            group_logs[sent.message_id] = msg

@app.on_callback_query(filters.regex(r"getlink\|(.*)"))
async def send_link_message(_, query: CallbackQuery):
    link = query.data.split("|")[1]
    await query.message.edit_caption(
        caption=f"🔗 ʜᴇʀᴇ ɪs ᴛʜᴇ ɢʀᴏᴜᴘ ʟɪɴᴋ:\n{link}",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("ʙᴀᴄᴋ", callback_data=f"back|{query.message.message_id}")]
        ])
    )

@app.on_callback_query(filters.regex(r"back\|(\d+)"))
async def back_to_main(_, query: CallbackQuery):
    msg_id = int(query.data.split("|")[1])
    original = group_logs.get(msg_id)
    if original:
        await query.message.edit_caption(
            caption=original,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("➜ ɢᴇᴛ ʟɪɴᴋ", callback_data=f"getlink|{await app.export_chat_invite_link(query.message.chat.id)}")]
            ])
        )

@app.on_message(filters.left_chat_member)
async def on_left_chat_member(_, message: Message):
    if (await app.get_me()).id == message.left_chat_member.id:
        remove_by = message.from_user.mention if message.from_user else "ᴜɴᴋɴᴏᴡɴ ᴜsᴇʀ"
        title = message.chat.title
        username = f"@{message.chat.username}" if message.chat.username else "𝐏ʀɪᴠᴀᴛᴇ 𝐂ʜᴀᴛ"
        chat_id = message.chat.id

        left_msg = (
            "◆━━━━━━━━━━━━━◆\n\n"
            "❖ #ʀᴇᴍᴏᴠᴇᴅ_ғʀᴏᴍ_ɢʀᴏᴜᴘ ❖\n\n"
            f"❖ ᴄʜᴀᴛ ɴᴀᴍᴇ : {title}\n"
            f"❖ ᴄʜᴀᴛ ɪᴅ : `{chat_id}`\n"
            f"❖ ʀᴇᴍᴏᴠᴇᴅ ʙʏ : {remove_by}\n\n"
            "◆━━━━━━━━━━━━━◆"
        )

        await app.send_photo(LOG_GROUP_ID, photo=REMOVED_IMAGE, caption=left_msg)
