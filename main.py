from pyrogram import Client, filters
from pyrogram.types import Message, ChatPermissions
from pyrogram.errors import ChatAdminRequired
import time
import json
import os

# ================= CONFIG =================
API_ID = 33124839
API_HASH = "3931d05edcb8b1a0a3a121efe9516f95"
BOT_TOKEN = "8859104219:AAHnty9uZicQW9osVTp0ZUdm5u54YkRpVSE"
OWNER_ID = 8349746023

SUDO_FILE = "sudo_users.json"

def load_sudo_users():
    if os.path.exists(SUDO_FILE):
        try:
            with open(SUDO_FILE, "r") as f:
                return set(json.load(f))
        except:
            return {OWNER_ID}
    return {OWNER_ID}

def save_sudo_users():
    with open(SUDO_FILE, "w") as f:
        json.dump(list(SUDO_USERS), f, indent=4)

SUDO_USERS = load_sudo_users()

app = Client("JassSudoBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

def is_sudo(_, __, message: Message):
    return message.from_user.id in SUDO_USERS

sudo_filter = filters.create(is_sudo)

# ================= HELPERS =================
async def is_admin(chat_id, user_id):
    try:
        member = await app.get_chat_member(chat_id, user_id)
        return member.status in ["administrator", "creator"]
    except:
        return False

# ================= SUDO MANAGEMENT =================
@app.on_message(filters.command(["addsudo", "sudo2"]) & sudo_filter)
async def add_sudo(client, message):
    if len(message.command) < 2:
        return await message.reply("**Usage:** `/addsudo <user_id or @username>`")
    
    target = message.command[1]
    try:
        if target.startswith("@"):
            user = await app.get_users(target)
            user_id = user.id
        else:
            user_id = int(target)
    except:
        return await message.reply("**❌ Invalid user.**")

    if user_id in SUDO_USERS:
        return await message.reply("**⚠️ Already sudo.**")
    
    SUDO_USERS.add(user_id)
    save_sudo_users()
    user = await app.get_users(user_id)
    await message.reply(f"**✅ Added {user.mention} to Sudo.**")


@app.on_message(filters.command(["rmsudo", "removesudo"]) & sudo_filter)
async def remove_sudo(client, message):
    if len(message.command) < 2:
        return await message.reply("**Usage:** `/rmsudo <user_id or @username>`")
    
    target = message.command[1]
    try:
        if target.startswith("@"):
            user = await app.get_users(target)
            user_id = user.id
        else:
            user_id = int(target)
    except:
        return await message.reply("**❌ Invalid user.**")

    if user_id == OWNER_ID:
        return await message.reply("**❌ Cannot remove Owner!**")
    if user_id not in SUDO_USERS:
        return await message.reply("**⚠️ Not a sudo user.**")

    SUDO_USERS.remove(user_id)
    save_sudo_users()
    user = await app.get_users(user_id)
    await message.reply(f"**✅ Removed {user.mention} from Sudo.**")


@app.on_message(filters.command("sudolist") & sudo_filter)
async def sudo_list(client, message):
    if not SUDO_USERS:
        return await message.reply("**No sudo users.**")
    
    text = "**🔰 Sudo Users:**\n\n"
    for uid in SUDO_USERS:
        try:
            user = await app.get_users(uid)
            text += f"• {user.mention} (`{uid}`)\n"
        except:
            text += f"• `{uid}`\n"
    await message.reply(text)


# ================= MODERATION =================
@app.on_message(filters.command(["ban", "dban"]) & sudo_filter)
async def ban_user(client, message):
    if not message.reply_to_message and len(message.command) < 2:
        return await message.reply("**Usage:** `/ban <id/@user> [reason]`")
    
    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
    else:
        target = message.command[1]
        user_id = (await app.get_users(target)).id if target.startswith("@") else int(target)

    if user_id in SUDO_USERS or user_id == OWNER_ID:
        return await message.reply("**❌ Cannot ban Sudo/Owner.**")

    reason = " ".join(message.command[2:]) or "No reason"
    await app.ban_chat_member(message.chat.id, user_id)
    user = await app.get_users(user_id)
    await message.reply(f"**✅ Banned {user.mention}**\n**Reason:** {reason}")


@app.on_message(filters.command("unban") & sudo_filter)
async def unban_user(client, message):
    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
    else:
        user_id = int(message.command[1])
    await app.unban_chat_member(message.chat.id, user_id)
    user = await app.get_users(user_id)
    await message.reply(f"**✅ Unbanned {user.mention}**")


# Run the bot
if __name__ == "__main__":
    print("🚀 Jass SudoBot Started...")
    app.run()
