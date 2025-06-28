import logging
import json
import os
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, ContextTypes
)

# --- Configuration ---
BOT_TOKEN = "8130755365:AAEafiinjqk-ppKyp1cfUi7yM8xwAxHI01Y"
ADMIN_USER_ID = 7802484685
WELCOME_IMAGE = "https://i.ibb.co/zH0ZjZCm/CAD0120.png"

DATA_FILE = "users.json"
HACK_FILE = "hack.json"
CHANNELS = [
    {"username": "rockypredictionai", "display_name": "📢 @rockypredictionai"},
    {"username": "rockycodes0offical", "display_name": "💎 @rockycodes0offical"}
]

# --- JSON Storage ---
def load_users():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return set(json.load(f))
    return set()

def save_users(user_ids):
    with open(DATA_FILE, "w") as f:
        json.dump(list(user_ids), f)

def load_hack_url():
    if os.path.exists(HACK_FILE):
        with open(HACK_FILE, "r") as f:
            return json.load(f).get("hack_url", "")
    return "https://rockydev.netlify.app"

def save_hack_url(url):
    with open(HACK_FILE, "w") as f:
        json.dump({"hack_url": url}, f)

# --- In-Memory Storage ---
user_ids = load_users()
hack_url = load_hack_url()

# --- Logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Admin Check ---
def admin_only(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id != ADMIN_USER_ID:
            await update.message.reply_text("🚫 Access Denied: Admin only.")
            return
        return await func(update, context)
    return wrapper

# --- /start Command ---
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_ids.add(user.id)
    save_users(user_ids)

    # Progress bar
    loading = await update.message.reply_text("⏳ Please wait... 0%")
    for i in range(10, 101, 10):
        await asyncio.sleep(0.1)
        try:
            await loading.edit_text(f"⏳ Please wait... {i}%")
        except:
            break

    # Show channel join message
    buttons = [[InlineKeyboardButton(ch['display_name'], url=f"https://t.me/{ch['username']}")] for ch in CHANNELS]
    buttons.append([InlineKeyboardButton("✅ Joined", callback_data="joined_pressed")])
    
    caption = (
        f"👋 Hello {user.first_name}!\n\n"
        "Please join the channels below and tap ✅ Joined to continue."
    )

    try:
        await context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=WELCOME_IMAGE,
            caption=caption,
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    except:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=caption,
            reply_markup=InlineKeyboardMarkup(buttons)
        )

# --- Joined Button ---
async def joined_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_caption(
        caption="✅ You're in! Tap below to continue:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔗 Open Hack", url=hack_url)]
        ])
    )

# --- Admin Panel ---
@admin_only
async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global hack_url
    args = context.args

    if not args:
        await update.message.reply_text(
            "🛠️ Admin Commands:\n"
            "/admin sethack <url>\n"
            "/admin addchannel <@username> <name>\n"
            "/admin editchannel <index> <@username> <name>\n"
            "/admin removechannel <index>\n"
            "/admin broadcast <message>\n"
            "/admin broadcastphoto <url> <caption>\n"
            "/admin broadcastbutton <text> | <button text> | <button url>\n"
            "/admin status\n"
            "/admin users\n"
            "/admin resetusers"
        )
        return

    sub = args[0].lower()

    if sub == "sethack" and len(args) == 2:
        hack_url = args[1]
        save_hack_url(hack_url)
        await update.message.reply_text("✅ Hack link updated.")

    elif sub == "addchannel" and len(args) >= 3:
        username = args[1].lstrip("@")
        name = " ".join(args[2:])
        CHANNELS.append({"username": username, "display_name": name})
        await update.message.reply_text("➕ Channel added.")

    elif sub == "editchannel" and len(args) >= 4:
        try:
            idx = int(args[1]) - 1
            username = args[2].lstrip("@")
            name = " ".join(args[3:])
            if 0 <= idx < len(CHANNELS):
                CHANNELS[idx] = {"username": username, "display_name": name}
                await update.message.reply_text("✏️ Channel updated.")
            else:
                await update.message.reply_text("❌ Invalid index.")
        except:
            await update.message.reply_text("⚠️ Format: /admin editchannel <index> <@username> <name>")

    elif sub == "removechannel" and len(args) == 2:
        try:
            idx = int(args[1]) - 1
            ch = CHANNELS.pop(idx)
            await update.message.reply_text(f"🗑️ Removed {ch['display_name']}")
        except:
            await update.message.reply_text("❌ Error removing. Check index.")

    elif sub == "broadcast" and len(args) >= 2:
        message = " ".join(args[1:])
        count = 0
        for uid in list(user_ids):
            try:
                await context.bot.send_message(chat_id=uid, text=message)
                count += 1
            except:
                continue
        await update.message.reply_text(f"📢 Sent to {count} users.")

    elif sub == "broadcastphoto" and len(args) >= 3:
        url = args[1]
        caption = " ".join(args[2:])
        count = 0
        for uid in list(user_ids):
            try:
                await context.bot.send_photo(chat_id=uid, photo=url, caption=caption)
                count += 1
            except:
                continue
        await update.message.reply_text(f"🖼️ Sent image to {count} users.")

    elif sub == "broadcastbutton":
        parts = " ".join(args[1:]).split("|")
        if len(parts) != 3:
            await update.message.reply_text("⚠️ Format:\n/admin broadcastbutton <text> | <btn text> | <btn url>")
            return
        text, btn_text, btn_url = map(str.strip, parts)
        markup = InlineKeyboardMarkup([[InlineKeyboardButton(btn_text, url=btn_url)]])
        count = 0
        for uid in list(user_ids):
            try:
                await context.bot.send_message(chat_id=uid, text=text, reply_markup=markup)
                count += 1
            except:
                continue
        await update.message.reply_text(f"📎 Button broadcast sent to {count} users.")

    elif sub == "status":
        await update.message.reply_text(
            f"📊 Bot Status:\n• Users: {len(user_ids)}\n• Channels: {len(CHANNELS)}\n• Hack URL: {hack_url}"
        )

    elif sub == "users":
        await update.message.reply_text(
            "👥 First 20 Users:\n" + ", ".join(str(uid) for uid in list(user_ids)[:20])
        )

    elif sub == "resetusers":
        user_ids.clear()
        save_users(user_ids)
        await update.message.reply_text("♻️ User list cleared.")

    else:
        await update.message.reply_text("❓ Unknown admin sub-command. Use /admin")

# --- /help ---
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("ℹ️ Use /start to begin.\nAdmins: /admin")

# --- Main Bot ---
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("admin", admin_command))
    app.add_handler(CallbackQueryHandler(joined_button_handler, pattern="^joined_pressed$"))
    logger.info("✅ Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()