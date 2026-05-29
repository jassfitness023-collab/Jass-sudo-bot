from pyrogram import Client, filters
from pyrogram.types import Message, ChatPermissions
from pyrogram.errors import ChatAdminRequired
import json
import os
import time

# ================= CONFIG =================
API_ID = 33124839
API_HASH = "3931d05edcb8b1a0a3a121efe9516f95"
BOT_TOKEN = "8805865814:AAGo-BDq5D3_z3zB9wtT_8KuOrNpR3TxAm8"   # Your latest token
OWNER_ID = 8349746023

SUDO_FILE = "sudo_users.json"

# Load Sudo Users
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
        return await message.reply("**⚠️ Already a sudo user.**")
    
    SUDO_USERS.add(user_id)
    save_sudo_users()
    user = await app.get_users(user_id)
    await message.reply(f"**✅ Added {user.mention} to Sudo Users.**")


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
    
    text = "**🔰 Sudo Users List:**\n\n"
    for uid in SUDO_USERS:
        try:
            user = await app.get_users(uid)
            text += f"• {user.mention} (`{uid}`)\n"
        except:
            text += f"• `{uid}`\n"
    await message.reply(text)


# ================= MODERATION COMMANDS =================

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
        return await message.reply("**❌ Cannot ban Sudo User / Owner.**")

    reason = " ".join(message.command[2:]) or "No reason given"
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


@app.on_message(filters.command(["mute", "dmute"]) & sudo_filter)
async def mute_user(client, message):
    if not message.reply_to_message and len(message.command) < 2:
        return await message.reply("**Usage:** `/mute <id/@user> [minutes]`")
    
    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
    else:
        target = message.command[1]
        user_id = (await app.get_users(target)).id if target.startswith("@") else int(target)

    minutes = int(message.command[2]) if len(message.command) > 2 else None
    until_date = int(time.time()) + minutes * 60 if minutes else None

    await app.restrict_chat_member(message.chat.id, user_id, ChatPermissions(can_send_messages=False), until_date=until_date)
    user = await app.get_users(user_id)
    text = f"**✅ Muted {user.mention}**"
    if minutes:
        text += f"\n**Duration:** {minutes} minutes"
    await message.reply(text)


@app.on_message(filters.command("unmute") & sudo_filter)
async def unmute_user(client, message):
    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
    else:
        user_id = int(message.command[1])
    await app.restrict_chat_member(message.chat.id, user_id, ChatPermissions(can_send_messages=True))
    user = await app.get_users(user_id)
    await message.reply(f"**✅ Unmuted {user.mention}**")


@app.on_message(filters.command(["kick", "dkick"]) & sudo_filter)
async def kick_user(client, message):
    if not message.reply_to_message and len(message.command) < 2:
        return await message.reply("**Usage:** `/kick <id/@user>`")
    
    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
    else:
        target = message.command[1]
        user_id = (await app.get_users(target)).id if target.startswith("@") else int(target)

    if user_id in SUDO_USERS or user_id == OWNER_ID:
        return await message.reply("**❌ Cannot kick Sudo/Owner.**")

    await app.ban_chat_member(message.chat.id, user_id)
    await app.unban_chat_member(message.chat.id, user_id)
    user = await app.get_users(user_id)
    await message.reply(f"**✅ Kicked {user.mention}**")


# Run Bot
if __name__ == "__main__":
    print("🚀 Jass SudoBot Started Successfully!")
    app.run()
