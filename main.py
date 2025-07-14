import json
import os
import random
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

# Load ENV
from dotenv import load_dotenv
load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

DB_FILE = "data.json"

ANIMALS = {
    "ဆင်": "🐘",
    "ကျား": "🐯",
    "လိပ်": "🐢",
    "ငါး": "🐟",
    "ပုဇွန်": "🦐",
    "ကြက်": "🐓"
}

def load_db():
    if not os.path.exists(DB_FILE):
        return {"users": {}, "pending": [], "admins": [ADMIN_ID]}
    with open(DB_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_db(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

db = load_db()
game_open = True
current_bets = {}
current_round = 1

def is_admin(user_id):
    return user_id in db["admins"]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    keyboard = [
        [InlineKeyboardButton("👤 အကောင့်ဖွင့်ရန်", callback_data="register")],
        [InlineKeyboardButton("💰 ငွေလက်ကျန်", callback_data="balance")],
        [InlineKeyboardButton("📥 ငွေဖြည့်", callback_data="topup"), InlineKeyboardButton("📤 ငွေထုတ်", callback_data="withdraw")],
        [InlineKeyboardButton("📖 အကူအညီ", callback_data="help"), InlineKeyboardButton("🎲 ဂိမ်းလမ်းညွှန်", callback_data="gamehelp")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    welcome_text = """
🎮 **ကြိုဆိုပါသည် - Animal Six Game သို့!** 🎲

🌟 **မြန်မာ့အကောင်းဆုံး သတ္တဝါ ၆ ကောင် ဂိမ်း!** 🌟

🐘🐯🐢🐟🦐🐓 **ရွေးချယ်နိုင်သော သတ္တဝါများ:**
🐘 ဆင် | 🐯 ကျား | 🐢 လိပ် | 🐟 ငါး | 🦐 ပုဇွန် | 🐓 ကြက်

✨ **ဂိမ်း၏ အင်္ဂါရပ်များ:**
💎 လွယ်ကူသော အကောင့်ဖွင့်ခြင်း
🔒 လုံခြုံသော ငွေလဲလှယ်မှု
⚡ Real-time တိုက်ရိုက်ထိုးထွင်းမှု
🎯 မြင့်မားသော အနိုင်ရနိုင်မှု
💰 လျင်မြန်သော ငွေပေးချေမှု

🚀 **အနိုင်ရရန် အဆင်သင့်ပါသလား? အောက်ပါခလုတ်များကို နှိပ်ပါ!**
    """

    await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "register":
        await register_callback(update, context)
    elif query.data == "balance":
        await balance_callback(update, context)
    elif query.data == "topup":
        await topup_callback(update, context)
    elif query.data == "withdraw":
        await withdraw_callback(update, context)
    elif query.data == "wave_pay":
        await wave_pay_callback(update, context)
    elif query.data == "kpay":
        await kpay_callback(update, context)
    elif query.data == "help":
        help_text = """
📖 **Animal Six Game - လျင်မြန်သော လမ်းညွှန်:**

🎮 **ဂိမ်းစည်းမျဥ်းများ:**
• ၆ မျိုးသတ္တဝါများကို ရွေးချယ်နိုင်ပါသည်
• တစ်ခုထိုးရင် = ၂ ဆပြန်ရ
• သုံးခုလုံးမှန်ရင် = ၆ ဆပြန်ရ
• အများထိုးရင် = မှန်တဲ့အကောင်တိုင်း ၂ ဆစီပြန်ရ

📝 **ထိုးသွင်းနည်း:**
• တစ်ခုထိုး: 'ဆင် 100'
• အများထိုး: 'ကျား 50 လိပ် 30 ငါး 20'

🎯 **ရရှိနိုင်သော သတ္တဝါများ:**
🐘 ဆင် | 🐯 ကျား | 🐢 လိပ်
🐟 ငါး | 🦐 ပုဇွန် | 🐓 ကြက်

💡 **နောက်ထပ် Commands များ:** /userhelp
        """
        await query.edit_message_text(help_text)
    elif query.data == "gamehelp":
        game_help_text = """
🎲 **ANIMAL SIX GAME - ပြည့်စုံသော လမ်းညွှန်:**

🎯 **ဘယ်လိုကစားရမလဲ:**
1️⃣ အကောင့်ဖွင့်ပါ (/register)
2️⃣ ငွေထည့်ပါ (admin ကို ဆက်သွယ်ပါ)
3️⃣ ထိုးသွင်းချိန် စောင့်ပါ
4️⃣ သင့်ရွေးချယ်မှုများ ထိုးပါ
5️⃣ ရလဒ်ကြည့်ပြီး အနိုင်ရငွေ ခံယူပါ!

🏆 **အနိုင်ရပုံစံများ:**
🥇 တစ်ခုအနိုင် = သင့်ထိုးငွေ ၂ ဆ
🥈 အများအနိုင် = မှန်တဲ့အကောင်တိုင်း ၂ ဆစီ
🥉 ပြီးပြည့်စုံ သုံးခုလုံးမှန် = သင့်ထိုးငွေ ၆ ဆ

💰 **ထိုးသွင်းနမူနာများ:**
• 'ဆင် 1000' = ဆင်ပေါ် 1000 ထိုး
• 'ကျား 500 ငါး 300' = ကျားနဲ့ ငါးပေါ် ထိုး

📱 **Commands:** /userhelp ကိုကြည့်ပါ
        """
        await query.edit_message_text(game_help_text)

async def topup_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    keyboard = [
        [InlineKeyboardButton("💙 Wave Pay", callback_data="wave_pay")],
        [InlineKeyboardButton("💚 KPay", callback_data="kpay")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        "📥 **ငွေဖြည့်သွင်းရန်:**\n\n💳 ငွေဖြည့်နည်းကို ရွေးချယ်ပါ:\n\n💰 အနည်းဆုံး: 1,000 ကျပ်\n⚡ လွှဲပြီး 5 မိနစ်အတွင်း လက်ခံရရှိပါမည်။",
        reply_markup=reply_markup
    )

async def wave_pay_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.edit_message_text(
        "💙 **Wave Pay ငွေဖြည့်သွင်းရန်:**\n\n"
        "📱 Wave ဖုန်းနံပါတ်: `09673585480`\n"
        "👤 အမည်: Nine Nine\n\n"
        "📝 **လုပ်ဆောင်ရမည့်အဆင့်များ:**\n"
        "1️⃣ အထက်ပါ ဖုန်းနံပါတ်သို့ Wave Money လွှဲပါ\n"
        "2️⃣ လွှဲပြီးပါက Screenshot ရိုက်ပါ\n"
        "3️⃣ Screenshot ကို Bot သို့ပေးပို့ပါ\n"
        "4️⃣ Admin မှ 5 မိနစ်အတွင်း အတည်ပြုပါမည်\n\n"
        "💡 **သတိပေးချက်:** ဖုန်းနံပါတ်ကို နှိပ်ပြီး copy လုပ်ပါ!",
        parse_mode='Markdown'
    )

async def kpay_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.edit_message_text(
        "💚 **KPay ငွေဖြည့်သွင်းရန်:**\n\n"
        "📱 KPay ဖုန်းနံပါတ်: `09678786528`\n"
        "👤 အမည်: Ma May Phoo Wai\n\n"
        "📝 **လုပ်ဆောင်ရမည့်အဆင့်များ:**\n"
        "1️⃣ အထက်ပါ ဖုန်းနံပါတ်သို့ KPay Money လွှဲပါ\n"
        "2️⃣ Note မှာ သင့် KPay အမည်ကို ရေးထည့်ပါ\n"
        "3️⃣ လွှဲပြီးပါက Screenshot ရိုက်ပါ\n"
        "4️⃣ Screenshot ကို Bot သို့ပေးပို့ပါ\n"
        "5️⃣ Admin မှ 5 မိနစ်အတွင်း အတည်ပြုပါမည်\n\n"
        "🚨 **အရေးကြီးသော သတိပေးချက်:**\n"
        "- KPay ငွေလွှဲသူ၏ အမည်နဲ့ Note မှာ တွဲရေးရပါမည်\n"
        "- ဖုန်းနံပါတ်ကို နှိပ်ပြီး copy လုပ်ပါ!",
        parse_mode='Markdown'
    )

async def withdraw_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = str(update.effective_user.id)
    if user_id not in db["users"]:
        await query.edit_message_text("❗ အကောင့်ဖွင့်ပြီးမှသာ အသုံးပြုနိုင်ပါသည်။")
        return

    await query.edit_message_text(
        "📤 **ငွေထုတ်ယူရန်:**\n\n"
        "💸 ငွေထုတ်လိုပါက အောက်ပါ အချက်အလက်များကို Bot သို့ ပေးပို့ပါ:\n\n"
        "📝 **လိုအပ်သော အချက်အလက်များ:**\n"
        "• Wave Pay ဖုန်းနံပါတ် (သို့)\n"
        "• KPay ဖုန်းနံပါတ်\n"
        "• ထုတ်လိုသော ငွေပမာဏ\n\n"
        "💰 အနည်းဆုံး: 10,000 ကျပ်\n"
        "⚡ အတည်ပြုပြီး 10 မိနစ်အတွင်း လွှဲပေးပါမည်။\n\n"
        "📱 **နမူနာ:** \n"
        "'ငွေထုတ် Wave 09123456789 10000'\n"
        "'ငွေထုတ် KPay 09123456789 15000'"
    )

async def register_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    user_id = str(user.id)

    if user_id in db["users"]:
        await query.edit_message_text("✅ အကောင့်ဖွင့်ပြီးသားပါ။")
        return

    if int(user_id) in db["pending"]:
        await query.edit_message_text("⏳ Admin မှ ခွင့်ပြုမှု စောင့်ဆဲဖြစ်ပါသည်။")
        return

    db["pending"].append(int(user_id))
    save_db(db)

    await context.bot.send_message(chat_id=ADMIN_ID, text=f"👤 အသစ် Register တောင်းခံမှု:\nID: {user_id}\nအမည်: {user.full_name}\nUserName: @{user.username}\nခွင့်ပြုရန် /approve {user_id}")
    await query.edit_message_text("✅ Register တောင်းခံမှုကို Admin ဆီ ပေးပို့လိုက်ပါပြီ။ ခဏစောင့်ပါ။")

async def balance_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = str(query.from_user.id)

    if user_id not in db["users"]:
        await query.edit_message_text("❗ အကောင့်ဖွင့်ပြီးမှသာ အသုံးပြုနိုင်ပါသည်။")
        return

    balance = db["users"][user_id]["balance"]
    await query.edit_message_text(f"💰 လက်ကျန်ငွေ: {balance:,} ကျပ်")

async def register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = str(user.id)

    if user_id in db["users"]:
        await update.message.reply_text("✅ အကောင့်ဖွင့်ပြီးသားပါ။")
        return

    if int(user_id) in db["pending"]:
        await update.message.reply_text("⏳ Admin မှ ခွင့်ပြုမှု စောင့်ဆဲဖြစ်ပါသည်။")
        return

    db["pending"].append(int(user_id))
    save_db(db)

    await context.bot.send_message(chat_id=ADMIN_ID, text=f"👤 အသစ် Register တောင်းခံမှု:\nID: {user_id}\nအမည်: {user.full_name}\nUserName: @{user.username}\nခွင့်ပြုရန် /approve {user_id}")
    await update.message.reply_text("✅ Register တောင်းခံမှုကို Admin ဆီ ပေးပို့လိုက်ပါပြီ။ ခဏစောင့်ပါ။")

async def topup_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id not in db["users"]:
        await update.message.reply_text("❗ အကောင့်ဖွင့်ပြီးမှသာ အသုံးပြုနိုင်ပါသည်။")
        return

    keyboard = [
        [InlineKeyboardButton("💙 Wave Pay", callback_data="wave_pay")],
        [InlineKeyboardButton("💚 KPay", callback_data="kpay")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "📥 **ငွေဖြည့်သွင်းရန်:**\n\n💳 ငွေဖြည့်နည်းကို ရွေးချယ်ပါ:\n\n💰 အနည်းဆုံး: 1,000 ကျပ်\n⚡ လွှဲပြီး 5 မိနစ်အတွင်း လက်ခံရရှိပါမည်။",
        reply_markup=reply_markup
    )

async def withdraw_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id not in db["users"]:
        await update.message.reply_text("❗ အကောင့်ဖွင့်ပြီးမှသာ အသုံးပြုနိုင်ပါသည်။")
        return

    await update.message.reply_text(
        "📤 **ငွေထုတ်ယူရန်:**\n\n"
        "💸 ငွေထုတ်လိုပါက အောက်ပါ အချက်အလက်များကို Bot သို့ ပေးပို့ပါ:\n\n"
        "📝 **လိုအပ်သော အချက်အလက်များ:**\n"
        "• Wave Pay ဖုန်းနံပါတ် (သို့)\n"
        "• KPay ဖုန်းနံပါတ်\n"
        "• ထုတ်လိုသော ငွေပမာဏ\n\n"
        "💰 အနည်းဆုံး: 10,000 ကျပ်\n"
        "⚡ အတည်ပြုပြီး 10 မိနစ်အတွင်း လွှဲပေးပါမည်။\n\n"
        "📱 **နမူနာ:** \n"
        "'ငွေထုတ် Wave 09123456789 10000'\n"
        "'ငွေထုတ် KPay 09123456789 15000'"
    )

async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    if len(context.args) != 1:
        await update.message.reply_text("Usage: /approve <user_id>")
        return

    user_id = int(context.args[0])
    if user_id in db["pending"]:
        db["pending"].remove(user_id)
        db["users"][str(user_id)] = {
            "balance": 1000,
            "history": []
        }
        save_db(db)
        await context.bot.send_message(chat_id=user_id, text="🎉 Admin မှ ခွင့်ပြုပါပြီ။ 1000 ကျပ် အဖွင့်လက်ဆောင်ရရှိပါသည်။\n\n🎮 ဂိမ်းကစားရန် အဆင်သင့်ပါပြီ!")
        await update.message.reply_text("✅ ခွင့်ပြုပြီး အကောင့်ဖွင့်ပေးပါပြီ။")
    else:
        await update.message.reply_text("❌ Pending list မှာ မတွေ့ပါ။")

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id not in db["users"]:
        await update.message.reply_text("❗ အကောင့်ဖွင့်ပြီးမှသာ အသုံးပြုနိုင်ပါသည်။")
        return

    balance = db["users"][user_id]["balance"]
    await update.message.reply_text(f"💰 လက်ကျန်ငွေ: {balance:,} ကျပ်")

async def handle_bet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global current_bets, game_open

    if not game_open:
        return

    user_id = str(update.effective_user.id)
    if user_id not in db["users"]:
        return

    text = update.message.text
    matches = re.findall(r"(ဆင်|ကျား|လိပ်|ငါး|ပုဇွန်|ကြက်)\s*(\d+)", text)
    if not matches:
        return

    if user_id not in current_bets:
        current_bets[user_id] = []

    total_bet = 0
    bet_details = []
    for animal, amount in matches:
        amount = int(amount)
        total_bet += amount
        current_bets[user_id].append((animal, amount))
        bet_details.append(f"{ANIMALS[animal]} {animal} - {amount:,} ကျပ်")

    if db["users"][user_id]["balance"] < total_bet:
        await update.message.reply_text("❌ လက်ကျန်ငွေ မလုံလောက်ပါ။")
        return

    db["users"][user_id]["balance"] -= total_bet
    save_db(db)

    # Show betting confirmation with details
    bet_summary = "\n".join(bet_details)
    new_balance = db["users"][user_id]["balance"]

    confirmation_text = f"""
✅ **ထိုးသွင်းမှု အတည်ပြုပါပြီ!**

🎯 **သင်ထိုးထားသော သတ္တဝါများ:**
{bet_summary}

💰 **စုစုပေါင်းထိုးငွေ:** {total_bet:,} ကျပ်
💳 **လက်ကျန်ငွေ:** {new_balance:,} ကျပ်

🍀 **Good Luck! ရလဒ်ကိုစောင့်ပါ။**
    """

    await update.message.reply_text(confirmation_text)

async def handle_deposit_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.photo:
        user = update.effective_user
        user_id = str(user.id)

        # Forward screenshot to admin
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"💰 **ငွေဖြည့်သွင်းတောင်းခံမှု:**\n\nမှ: {user.full_name}\nID: {user_id}\nUsername: @{user.username}\n\nငွေထည့်ပေးရန် /addmoney {user_id} <amount>"
        )
        await context.bot.forward_message(chat_id=ADMIN_ID, from_chat_id=update.effective_chat.id, message_id=update.message.message_id)

        await update.message.reply_text("✅ Screenshot လက်ခံရရှိပါပြီ။ Admin မှ စစ်ဆေးပြီး 5 မိနစ်အတွင်း ငွေထည့်ပေးပါမည်။")

async def handle_withdraw_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = str(update.effective_user.id)

    if user_id not in db["users"]:
        return

    # Check for withdraw request pattern
    withdraw_pattern = r"ငွေထုတ်\s+(Wave|KPay)\s+(\d+)\s+(\d+)"
    match = re.match(withdraw_pattern, text)

    if match:
        method = match.group(1)
        phone = match.group(2)
        amount = int(match.group(3))

        if amount > db["users"][user_id]["balance"]:
            await update.message.reply_text("❌ လက်ကျန်ငွေ မလုံလောက်ပါ။")
            return

        if amount < 10000:
            await update.message.reply_text("❌ အနည်းဆုံး 10,000 ကျပ် ထုတ်ယူနိုင်ပါသည်။")
            return

        user = update.effective_user
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"📤 **ငွေထုတ်ယူတောင်းခံမှု:**\n\nမှ: {user.full_name}\nID: {user_id}\nUsername: @{user.username}\n\nနည်းလမ်း: {method}\nဖုန်း: {phone}\nပမာဏ: {amount:,} ကျပ်\n\nလက်ကျန်: {db['users'][user_id]['balance']:,} ကျပ်\n\nလွှဲပေးပြီးရင် /deduct {user_id} {amount}"
        )
        await update.message.reply_text(f"✅ ငွေထုတ်ယူတောင်းခံမှုကို Admin ဆီ ပေးပို့ပါပြီ။\n\n📱 {method}: {phone}\n💰 ပမာဏ: {amount:,} ကျပ်\n\n⏰ 10 မိနစ်အတွင်း လွှဲပေးပါမည်။")

async def startround(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global current_round, current_bets, game_open

    if not is_admin(update.effective_user.id):
        return

    if not game_open:
        await update.message.reply_text("⛔ ဂိမ်း ပိတ်ထားပါသည်။")
        return

    # Send start round notification to all users and groups
    start_message = f"🎮 **Round {current_round} စတင်ပါပြီ!**\n\n🎯 ထိုးသွင်းကြပါ!\n\n📝 **ထိုးနည်း:** 'သတ္တဝါအမည် ငွေပမာဏ'\n💡 **ဥပမာ:** 'ဆင် 1000' သို့ 'ကျား 500 လိပ် 300'"
    for user_id in db["users"].keys():
        try:
            await context.bot.send_message(chat_id=int(user_id), text=start_message)
        except:
            pass  # User might have blocked the bot

    # Notify in groups the bot is in (if applicable)
    for chat_id in context.bot.get_updates(): # This line needs more work
        try:
            await context.bot.send_message(chat_id=update.effective_chat.id, text=start_message)
        except:
            pass

    game_open = True
    current_bets = {}

async def endround(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global current_round, current_bets, game_open

    if not is_admin(update.effective_user.id):
        return

    game_open = False
    winners = random.sample(list(ANIMALS.keys()), 3)
    winner_emojis = [f"{ANIMALS[a]} {a}" for a in winners]

    # Send results to main chat
    end_message = f"🏁 **Round {current_round} ပြီးဆုံးပါပြီ!**\n\n🥇 **အနိုင်ရသူများ:** {', '.join(winner_emojis)}"
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=end_message
    )

    # Process individual results
    group_winners = []

    for user_id, bets in current_bets.items():
        user = db["users"].get(user_id)
        if not user:
            continue

        win_animals = [animal for animal, amount in bets if animal in winners]
        total_payout = 0

        # Calculate payout
        if len(bets) == 1 and len(set([b[0] for b in bets])) == 3 and set([b[0] for b in bets]) == set(winners):
            # Perfect triple match
            total_payout = bets[0][1] * 6
        else:
            # Regular wins - 2x for each correct bet
            for animal, amount in bets:
                if animal in winners:
                    total_payout += amount * 2

        if total_payout > 0:
            db["users"][user_id]["balance"] += total_payout
            group_winners.append({
                "user_id": user_id,
                "bets": bets,
                "payout": total_payout,
                "winners": win_animals
            })

        # Add to history
        db["users"][user_id]["history"].append({
            "round": current_round,
            "bet": bets,
            "winners": winners,
            "payout": total_payout
        })

        # Send private message to user
        bet_details = "\n".join([f"{ANIMALS[animal]} {animal} - {amount:,} ကျပ်" for animal, amount in bets])
        win_details = "\n".join([f"✅ {ANIMALS[animal]} {animal}" for animal in win_animals]) if win_animals else "❌ ဘာမှ မမှန်ပါ"

        try:
            if total_payout > 0:
                private_msg = f"""
🎉 **Round {current_round} - သင်အနိုင်ရပါပြီ!**

🎯 **သင်ထိုးထားသော သတ္တဝါများ:**
{bet_details}

🏆 **အနိုင်ရသူများ:**
{', '.join(winner_emojis)}

✅ **သင်မှန်ကန်စွာ ထိုးထားသော သတ္တဝါများ:**
{win_details}

💰 **အနိုင်ရငွေ:** {total_payout:,} ကျပ်
💳 **လက်ကျန်ငွေ:** {db['users'][user_id]['balance']:,} ကျပ်

🎊 **ဂုဏ်ယူပါသည်!**
                """
            else:
                private_msg = f"""
😔 **Round {current_round} - ဒီတစ်ကြိမ် မအနိုင်ရပါ**

🎯 **သင်ထိုးထားသော သတ္တဝါများ:**
{bet_details}

🏆 **အနိုင်ရသူများ:**
{', '.join(winner_emojis)}

❌ **သင်မှန်ကန်စွာ ထိုးထားသော သတ္တဝါများ:**
ဘာမှ မမှန်ပါ

💳 **လက်ကျန်ငွေ:** {db['users'][user_id]['balance']:,} ကျပ်

🍀 **နောက်တစ်ကြိမ် ကံကောင်းပါစေ!**
                """
            await context.bot.send_message(chat_id=int(user_id), text=private_msg)
        except:
            pass  # User might have blocked the bot

    # Send group winners list if this is a group
    if update.effective_chat.type in ['group', 'supergroup'] and group_winners:
        winners_text = "🏆 **ဒီ Round မှာ အနိုင်ရသူများ:**\n\n"
        for winner in group_winners:
            bet_summary = ", ".join([f"{ANIMALS[animal]} {animal} ({amount:,})" for animal, amount in winner["bets"]])
            winners_text += f"👤 User {winner['user_id']}\n"
            winners_text += f"🎯 ထိုးထားမှု: {bet_summary}\n"
            winners_text += f"💰 အနိုင်ရငွေ: {winner['payout']:,} ကျပ်\n\n"

        if len(winners_text) < 4000:
            await update.message.reply_text(winners_text)

    save_db(db)
    current_round += 1
    current_bets = {}

async def toggle_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global game_open
    if not is_admin(update.effective_user.id):
        return

    game_open = not game_open
    status = "ဖွင့်" if game_open else "ပိတ်"

    # added game paused message
    paused_message = "⛔ ဂိမ်း ခေတ္တ ရပ်နားထားပါသည်။\nပွဲစသည့်အချိန်မှ ပြန်လည်ကစားနိုင်ပါမည်။"
    if not game_open:
        for user_id in db["users"].keys():
            try:
                await context.bot.send_message(chat_id=int(user_id), text=paused_message)
            except:
                pass  # User might have blocked the bot

    await update.message.reply_text(f"🎮 ဂိမ်းကို {status} ထားပြီးပါပြီ။")

async def admhelp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Admin ခွင့်ပြုချက် လိုအပ်ပါသည်!")
        return

    help_text = """
🔧 **Admin Control Panel - Animal Six Game:**

📊 **ဂိမ်း စီမံခန့်ခွဲမှု:**
/startround - ထိုးသွင်းချိန် စတင်ရန်
/endround - Round ပြီးဆုံးရန်နဲ့ အနိုင်ရသူများ ကြေညာရန်
/toggle - ထိုးသွင်းစနစ် ဖွင့်/ပိတ် လုပ်ရန်

👥 **User စီမံခန့်ခွဲမှု:**
/approve <user_id> - User အသစ် ခွင့်ပြုရန်
/addmoney <user_id> <amount> - User အကောင့်သို့ ငွေထည့်ရန်
/deduct <user_id> <amount> - User အကောင့်မှ ငွေနုတ်ရန်
/checkmoney <user_id> - User လက်ကျန်ငွေ စစ်ရန်
/allusers - Register ပြုလုပ်ထားသော User အားလုံး ကြည့်ရန်

👑 **Admin စီမံခန့်ခွဲမှု:**
/makeadmin <user_id> - Admin အသစ် ခန့်အပ်ရန်
/removeadmin <user_id> - Admin ဖြုတ်ရန်
/broadcast <message> - User အားလုံးသို့ စာပို့ရန်
/sendmsg <user_id> <message> - User တစ်ယောက်သို့ စာပို့ရန်

📖 **အကူအညီ Commands:**
/admhelp - Admin commands များ ပြရန်
/userhelp - User commands များ ပြရန် (အများပြည်သူ)
    """
    await update.message.reply_text(help_text)

async def add_money(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    if len(context.args) != 2:
        await update.message.reply_text("Usage: /addmoney <user_id> <amount>")
        return

    try:
        user_id = str(context.args[0])
        amount = int(context.args[1])

        if user_id not in db["users"]:
            await update.message.reply_text("❌ User မတွေ့ပါ။")
            return

        db["users"][user_id]["balance"] += amount
        save_db(db)
        
        # added money deposit advertise
        money_deposit_advertise = f"🎉 **ငွေဖြည့်သွင်းမှု အောင်မြင်ပါပြီ!**\nAdmin မှ {amount:,} ကျပ် ထည့်ပေးပါပြီ"
        for group_id in context.bot.get_updates():
            try:
                await context.bot.send_message(chat_id=update.effective_chat.id, text=money_deposit_advertise)
            except:
                pass


        await context.bot.send_message(chat_id=int(user_id), text=f"💰 **ငွေဖြည့်သွင်းမှု အောင်မြင်ပါပြီ!**\n\nAdmin မှ {amount:,} ကျပ် ထည့်ပေးပါပြီ။\n💳 လက်ကျန်ငွေ: {db['users'][user_id]['balance']:,} ကျပ်")
        await update.message.reply_text(f"✅ {amount:,} ကျပ် ထည့်ပေးပါပြီ။")
    except ValueError:
        await update.message.reply_text("❌ ရေဂုဏ်းများ မှန်ကန်စွာ ထည့်ပါ။")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")

async def deduct_money(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    if len(context.args) != 2:
        await update.message.reply_text("Usage: /deduct <user_id> <amount>")
        return

    try:
        user_id = str(context.args[0])
        amount = int(context.args[1])

        if user_id not in db["users"]:
            await update.message.reply_text("❌ User မတွေ့ပါ။")
            return

        if db["users"][user_id]["balance"] < amount:
            await update.message.reply_text("❌ User လက်ကျန်ငွေ မလုံလောက်ပါ။")
            return

        db["users"][user_id]["balance"] -= amount
        save_db(db)

        await context.bot.send_message(chat_id=int(user_id), text=f"📤 **ငွေထုတ်ယူမှု အောင်မြင်ပါပြီ!**\n\n{amount:,} ကျပ် သင့်အကောင့်သို့ လွှဲပေးပြီးပါပြီ။\n💳 လက်ကျန်ငွေ: {db['users'][user_id]['balance']:,} ကျပ်")
        await update.message.reply_text(f"✅ {amount:,} ကျပ် နုတ်ယူပြီး User သို့ လွှဲပေးပါပြီ။")
    except ValueError:
        await update.message.reply_text("❌ ရေဂုဏ်းများ မှန်ကန်စွာ ထည့်ပါ။")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")

async def check_money(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    if len(context.args) != 1:```python
        await update.message.reply_text("Usage: /checkmoney <user_id>")
        return

    user_id = str(context.args[0])
    if user_id not in db["users"]:
        await update.message.reply_text("❌ User မတွေ့ပါ။")
        return

    balance = db["users"][user_id]["balance"]
    await update.message.reply_text(f"💰 User {user_id} ရဲ့ လက်ကျန်ငွေ: {balance:,} ကျပ်")

async def all_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    users_text = "👥 **Register ပြုလုပ်ထားသော User များ:**\n\n"
    for i, (user_id, user_data) in enumerate(db["users"].items(), 1):
        users_text += f"{i}. ID: {user_id}\n   💰 လက်ကျန်: {user_data['balance']:,} ကျပ်\n\n"

    if len(users_text) > 4000:
        users_text = users_text[:4000] + "..."

    await update.message.reply_text(users_text)

async def make_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:  # Only main admin can make other admins
        return

    if len(context.args) != 1:
        await update.message.reply_text("Usage: /makeadmin <user_id>")
        return

    try:
        new_admin_id = int(context.args[0])
        if new_admin_id not in db["admins"]:
            db["admins"].append(new_admin_id)
            save_db(db)
            await context.bot.send_message(chat_id=new_admin_id, text="🎉 သင်သည် Admin အဖြစ် ခန့်အပ်ခြင်း ခံရပါပြီ!\n\n/admhelp ကိုသုံးပြီး Admin commands များကို ကြည့်ပါ။")
            await update.message.reply_text(f"✅ User {new_admin_id} ကို Admin အဖြစ် ခန့်အပ်ပါပြီ။")
        else:
            await update.message.reply_text("❌ သူသည် Admin ဖြစ်နေပြီးပါပြီ။")
    except ValueError:
        await update.message.reply_text("❌ မှန်ကန်သော User ID ထည့်ပါ။")

async def remove_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:  # Only main admin can remove admins
        return

    if len(context.args) != 1:
        await update.message.reply_text("Usage: /removeadmin <user_id>")
        return

    try:
        admin_id = int(context.args[0])
        if admin_id == ADMIN_ID:
            await update.message.reply_text("❌ Main Admin ကို မဖြုတ်နိုင်ပါ။")
            return

        if admin_id in db["admins"]:
            db["admins"].remove(admin_id)
            save_db(db)
            await context.bot.send_message(chat_id=admin_id, text="📢 သင့်ကို Admin ရာထူးမှ ဖြုတ်ခွင့် ခံရပါပြီ။")
            await update.message.reply_text(f"✅ User {admin_id} ကို Admin မှ ဖြုတ်ပါပြီ။")
        else:
            await update.message.reply_text("❌ သူသည် Admin မဟုတ်ပါ။")
    except ValueError:
        await update.message.reply_text("❌ မှန်ကန်သော User ID ထည့်ပါ။")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    if len(context.args) == 0:
        await update.message.reply_text("Usage: /broadcast <message>")
        return

    message = " ".join(context.args)
    sent_count = 0
    failed_count = 0

    for user_id in db["users"].keys():
        try:
            await context.bot.send_message(chat_id=int(user_id), text=f"📢 **Broadcast Message:**\n\n{message}")
            sent_count += 1
        except:
            failed_count += 1

    await update.message.reply_text(f"📊 **Broadcast Results:**\n✅ ပို့ပြီး: {sent_count}\n❌ မပို့နိုင်: {failed_count}")

async def send_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    if len(context.args) < 2:
        await update.message.reply_text("Usage: /sendmsg <user_id> <message>")
        return

    try:
        user_id = context.args[0]
        message = " ".join(context.args[1:])

        # Get chat info where the command was sent from
        chat_info = ""
        if update.effective_chat.type == "private":
            chat_info = f"Private Chat မှ Admin ထံမှ"
        elif update.effective_chat.type in ["group", "supergroup"]:
            chat_title = update.effective_chat.title or "Group"
            chat_info = f"Group: {chat_title} မှ Admin ထံမှ"

        await context.bot.send_message(
            chat_id=int(user_id), 
            text=f"💌 **Message from Admin:**\n📍 ပေးပို့သည့်နေရာ: {chat_info}\n\n{message}"
        )
        await update.message.reply_text(f"✅ User {user_id} သို့ စာပို့ပြီးပါပြီ။")
    except ValueError:
        await update.message.reply_text("❌ မှန်ကန်သော User ID ထည့်ပါ။")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")

async def userhelp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
🎮 **Animal Six Game - User Commands:**

🎯 **အခြေခံ Commands:**
/start - Bot စတင်ရန်နဲ့ main menu ကြည့်ရန်
/register - အကောင့်အသစ် ဖွင့်ရန်
/balance - လက်ကျန်ငွေ စစ်ရန်
/topup - ငွေဖြည့်သွင်းရန်
/withdraw - ငွေထုတ်ယူရန်

🎲 **ဂိမ်း Commands:**
/userhelp - ဒီ အကူအညီ menu ပြရန်

📝 **ထိုးနည်းများ:**
• တစ်ခုထိုး: "ဆင် 100" (ဆင်ပေါ် 100 ထိုး)
• အများထိုး: "ကျား 50 လိပ် 30" (ကျားပေါ် 50, လိပ်ပေါ် 30 ထိုး)

🎖️ **ငွေပြန်ရနည်းများ:**
• တစ်ခုမှန်ရင် = သင့်ထိုးငွေ x2
• သုံးခုလုံးမှန်ရင် = သင့်ထိုးငွေ x6
• အများထိုးပြီး မှန်ရင် = မှန်တဲ့အကောင်တိုင်း x2

🐘🐯🐢🐟🦐🐓 **ရရှိနိုင်သော သတ္တဝါများ:**
🐘 ဆင် (Elephant) | 🐯 ကျား (Tiger) | 🐢 လိပ် (Turtle)
🐟 ငါး (Fish) | 🦐 ပုဇွန် (Shrimp) | 🐓 ကြက် (Chicken)

💰 **ငွေသွင်း/ထုတ် အတွက်:**
• /topup - ငွေဖြည့်သွင်းရန်
• /withdraw - ငွေထုတ်ယူရန်
• Screenshot များ ပေးပို့ပါ Admin မှ စစ်ဆေးပါမည်

📞 **ပြဿနာများ အတွက် Admin ထံ ဆက်သွယ်ပါ**
    """
    await update.message.reply_text(help_text)

def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("register", register))
    app.add_handler(CommandHandler("approve", approve))
    app.add_handler(CommandHandler("balance", balance))
    app.add_handler(CommandHandler("topup", topup_command))
    app.add_handler(CommandHandler("withdraw", withdraw_command))
    app.add_handler(CommandHandler("startround", startround))
    app.add_handler(CommandHandler("endround", endround))
    app.add_handler(CommandHandler("toggle", toggle_game))
    app.add_handler(CommandHandler("admhelp", admhelp))
    app.add_handler(CommandHandler("userhelp", userhelp))
    app.add_handler(CommandHandler("addmoney", add_money))
    app.add_handler(CommandHandler("deduct", deduct_money))
    app.add_handler(CommandHandler("checkmoney", check_money))
    app.add_handler(CommandHandler("allusers", all_users))
    app.add_handler(CommandHandler("makeadmin", make_admin))
    app.add_handler(CommandHandler("removeadmin", remove_admin))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CommandHandler("sendmsg", send_message))

    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.PHOTO, handle_deposit_screenshot))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), lambda update, context: 
        handle_withdraw_request(update, context) if update.message.text.startswith("ငွေထုတ်") 
        else handle_bet(update, context)))

    app.run_polling()

if __name__ == "__main__":
    main()
