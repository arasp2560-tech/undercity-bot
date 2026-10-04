import os
import json
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

PORT = int(os.environ.get("PORT", 10000))
PLAYERS_FILE = "players.json"


# =========================
# HTTP SERVER FOR RENDER
# =========================

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"UNDERCITY is alive")

    def log_message(self, format, *args):
        return


def run_server():
    server = HTTPServer(("0.0.0.0", PORT), HealthHandler)
    server.serve_forever()


# =========================
# PLAYER DATA
# =========================

def load_players():
    try:
        with open(PLAYERS_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_players(players):
    with open(PLAYERS_FILE, "w", encoding="utf-8") as file:
        json.dump(players, file, ensure_ascii=False, indent=2)


def get_player(user):
    players = load_players()
    user_id = str(user.id)

    if user_id not in players:
        players[user_id] = {
            "name": user.first_name or "Player",
            "username": user.username or "",

            "level": 1,
            "xp": 0,

            "money": 10000,

            "cash": 10000,
            "bank_balance": 0,

            "credit_score": 500,

            "loan": {
                "active": False,
                "principal": 0,
                "remaining": 0,
                "interest_rate": 0,
                "installment": 0,
                "next_payment": None
            },

            "transactions": [],

            "reputation": 0,
            "location": "پایین‌شهر",

            "home": {
                "type": "اتاق اجاره‌ای",
                "name": "اتاق کوچک پایین‌شهر",
                "rent": 200
            },

            "properties": [],
            "vehicles": [],
            "businesses": []
        }

        save_players(players)

    else:
        player = players[user_id]

        if "cash" not in player:
            player["cash"] = player.get("money", 10000)

        if "bank_balance" not in player:
            player["bank_balance"] = 0

        if "credit_score" not in player:
            player["credit_score"] = 500

        if "loan" not in player:
            player["loan"] = {
                "active": False,
                "principal": 0,
                "remaining": 0,
                "interest_rate": 0,
                "installment": 0,
                "next_payment": None
            }

        if "transactions" not in player:
            player["transactions"] = []

        if "username" not in player:
            player["username"] = user.username or ""

        save_players(players)

    return players[user_id]


# =========================
# TRANSACTIONS
# =========================

def add_transaction(player, transaction_type, amount, description):
    if "transactions" not in player:
        player["transactions"] = []

    player["transactions"].append({
        "type": transaction_type,
        "amount": amount,
        "description": description
    })

    player["transactions"] = player["transactions"][-50:]


# =========================
# MAIN MENU
# =========================

def main_menu():
    keyboard = [
        [
            InlineKeyboardButton("👤 پروفایل", callback_data="profile"),
            InlineKeyboardButton("💰 کیف پول", callback_data="wallet")
        ],
        [
            InlineKeyboardButton("🏙️ شهر", callback_data="city"),
            InlineKeyboardButton("🏠 املاک", callback_data="properties")
        ],
        [
            InlineKeyboardButton("🚗 وسایل نقلیه", callback_data="vehicles"),
            InlineKeyboardButton("🏢 کسب‌وکارها", callback_data="businesses")
        ],
        [
            InlineKeyboardButton("📈 بازار", callback_data="market"),
            InlineKeyboardButton("🕶️ دنیای زیرزمینی", callback_data="underground")
        ],
        [
            InlineKeyboardButton("🤝 باند و اتحاد", callback_data="gang"),
            InlineKeyboardButton("🏥 درمانگاه", callback_data="clinic")
        ],
        [
            InlineKeyboardButton("💊 داروخانه", callback_data="pharmacy"),
            InlineKeyboardButton("⚙️ تنظیمات", callback_data="settings")
        ]
    ]

    return InlineKeyboardMarkup(keyboard)


# =========================
# WALLET MENU
# =========================

def wallet_menu():
    keyboard = [
        [
            InlineKeyboardButton("💵 پول نقد", callback_data="cash"),
            InlineKeyboardButton("🏦 بانک", callback_data="bank")
        ],
        [
            InlineKeyboardButton("📥 واریز به بانک", callback_data="deposit"),
            InlineKeyboardButton("📤 برداشت از بانک", callback_data="withdraw")
        ],
        [
            InlineKeyboardButton("💸 انتقال وجه", callback_data="transfer")
        ],
        [
            InlineKeyboardButton("📜 تراکنش‌ها", callback_data="transactions")
        ],
        [
            InlineKeyboardButton("🔙 برگشت", callback_data="main")
        ]
    ]

    return InlineKeyboardMarkup(keyboard)


# =========================
# START
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    context.user_data.clear()

    player = get_player(user)

    text = (
        f"🏙️ به UNDERCITY خوش آمدی، {player['name']}!\n\n"
        "اینجا شهریه که از پایین‌ترین نقطه می‌تونی شروع کنی "
        "و قدم‌به‌قدم به یک امپراتوری بزرگ برسی.\n\n"
        "💵 سرمایه اولیه: 10,000$\n"
        "📍 محل شروع: پایین‌شهر\n"
        "🏠 خانه: اتاق کوچک پایین‌شهر\n\n"
        "انتخاب با توئه..."
    )

    await update.message.reply_text(
        text,
        reply_markup=main_menu()
    )


# =========================
# PROFILE
# =========================

async def show_profile(query, user):
    player = get_player(user)

    text = (
        "👤 پروفایل بازیکن\n\n"
        f"نام: {player['name']}\n"
        f"🆔 ID: {user.id}\n"
        f"⭐ سطح: {player['level']}\n"
        f"✨ XP: {player['xp']}\n\n"
        f"💵 پول نقد: ${player['cash']:,}\n"
        f"🏦 موجودی بانک: ${player['bank_balance']:,}\n"
        f"💰 کل دارایی نقدی: "
        f"${player['cash'] + player['bank_balance']:,}\n\n"
        f"🎖️ اعتبار: {player['credit_score']}\n"
        f"🏙️ منطقه: {player['location']}\n"
        f"🏠 خانه: {player['home']['name']}\n"
        f"💸 اجاره: ${player['home']['rent']:,}\n\n"
        f"🏘️ املاک: {len(player['properties'])}\n"
        f"🚗 وسایل نقلیه: {len(player['vehicles'])}\n"
        f"🏢 کسب‌وکارها: {len(player['businesses'])}"
    )

    keyboard = [
        [InlineKeyboardButton("🔙 برگشت", callback_data="main")]
    ]

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================
# WALLET
# =========================

async def show_wallet(query, user):
    player = get_player(user)

    total = player["cash"] + player["bank_balance"]

    text = (
        "💰 کیف پول\n\n"
        f"💵 پول نقد: ${player['cash']:,}\n"
        f"🏦 موجودی بانک: ${player['bank_balance']:,}\n"
        "━━━━━━━━━━━━━━\n"
        f"💰 مجموع پول: ${total:,}\n\n"
        "💸 انتقال وجه از حساب بانکی انجام می‌شود."
    )

    await query.edit_message_text(
        text,
        reply_markup=wallet_menu()
    )


# =========================
# CASH
# =========================

async def show_cash(query, user):
    player = get_player(user)

    text = (
        "💵 پول نقد\n\n"
        f"موجودی نقدی شما:\n"
        f"${player['cash']:,}\n\n"
        "پول نقد برای خریدها و معاملات مستقیم استفاده می‌شود."
    )

    keyboard = [
        [InlineKeyboardButton("📥 واریز به بانک", callback_data="deposit")],
        [InlineKeyboardButton("🔙 کیف پول", callback_data="wallet")]
    ]

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================
# BANK
# =========================

async def show_bank(query, user):
    player = get_player(user)

    text = (
        "🏦 بانک\n\n"
        f"موجودی حساب شما:\n"
        f"${player['bank_balance']:,}\n\n"
        "🏦 بانک برای نگهداری امن پول و انجام تراکنش‌ها استفاده می‌شود."
    )

    keyboard = [
        [InlineKeyboardButton("📥 واریز به بانک", callback_data="deposit")],
        [InlineKeyboardButton("📤 برداشت از بانک", callback_data="withdraw")],
        [InlineKeyboardButton("🔙 کیف پول", callback_data="wallet")]
    ]

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================
# MONEY TRANSFER
# =========================

async def transfer_money(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    message = update.message

    if not message:
        return

    parts = message.text.strip().split()

    # انتقال با Reply
    if message.reply_to_message:
        target_user = message.reply_to_message.from_user

        if not target_user:
            await message.reply_text("❌ مقصد انتقال پیدا نشد.")
            return

        if target_user.id == user.id:
            await message.reply_text("❌ نمی‌توانی به خودت پول انتقال بدهی.")
            return

        if len(parts) != 2:
            await message.reply_text(
                "❌ فرمت صحیح:\n\n"
                "انتقال پول 5000\n\n"
                "این پیام را به پیام شخص موردنظر Reply کن."
            )
            return

        try:
            amount = int(parts[1])
        except ValueError:
            await message.reply_text("❌ مبلغ باید عدد باشد.")
            return

    # انتقال با ID
    else:
        if len(parts) != 4 or parts[2] != "به":
            await message.reply_text(
                "❌ فرمت صحیح:\n\n"
                "انتقال پول 5000 به 123456789"
            )
            return

        try:
            amount = int(parts[1])
            target_id = int(parts[3])
        except ValueError:
            await message.reply_text("❌ مبلغ و ID باید عدد باشند.")
            return

        if target_id == user.id:
            await message.reply_text("❌ نمی‌توانی به خودت پول انتقال بدهی.")
            return

        target_user = None
        players = load_players()

        if str(target_id) not in players:
            await message.reply_text(
                "❌ این بازیکن هنوز ربات را فعال نکرده است.\n"
                "ابتدا باید با /start وارد UNDERCITY شود."
            )
            return

        target_player_data = players[str(target_id)]

    # بررسی مبلغ
    if amount <= 0:
        await message.reply_text("❌ مبلغ انتقال باید بیشتر از صفر باشد.")
        return

    # دریافت اطلاعات فرستنده
    players = load_players()
    sender_id = str(user.id)

    if sender_id not in players:
        get_player(user)
        players = load_players()

    sender = players[sender_id]

    # اطمینان از وجود موجودی بانک
    if "bank_balance" not in sender:
        sender["bank_balance"] = sender.get("money", 10000)

    # بررسی موجودی
    if sender["bank_balance"] < amount:
        await message.reply_text(
            "❌ موجودی حساب بانکی کافی نیست.\n\n"
            f"🏦 موجودی: ${sender['bank_balance']:,}\n"
            f"💸 مبلغ انتقال: ${amount:,}"
        )
        return

    # اطلاعات مقصد در حالت Reply
    if message.reply_to_message:
        target_id = target_user.id

        if str(target_id) not in players:
            get_player(target_user)
            players = load_players()

        target = players[str(target_id)]

    # اطلاعات مقصد در حالت ID
    else:
        target = players[str(target_id)]

    if "bank_balance" not in target:
        target["bank_balance"] = target.get("money", 10000)

    # انجام انتقال
    sender["bank_balance"] -= amount
    target["bank_balance"] += amount

    # ثبت تراکنش فرستنده
    add_transaction(
        sender,
        "transfer_sent",
        amount,
        f"انتقال به {target.get('name', 'Player')}"
    )

    # ثبت تراکنش گیرنده
    add_transaction(
        target,
        "transfer_received",
        amount,
        f"دریافت از {sender.get('name', 'Player')}"
    )

    save_players(players)

    await message.reply_text(
        "✅ انتقال با موفقیت انجام شد.\n\n"
        f"👤 فرستنده: {sender.get('name', 'Player')}\n"
        f"👤 گیرنده: {target.get('name', 'Player')}\n"
        f"💸 مبلغ: ${amount:,}\n\n"
        f"🏦 موجودی جدید شما: ${sender['bank_balance']:,}"
    )


# =========================
# BUTTON HANDLER
# =========================

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user = update.effective_user

    if query.data == "profile":
        await show_profile(query, user)

    elif query.data == "wallet":
        await show_wallet(query, user)

    elif query.data == "cash":
        await show_cash(query, user)

    elif query.data == "bank":
        await show_bank(query, user)

    elif query.data == "transfer":
        await query.edit_message_text(
            "💸 انتقال وجه\n\n"
            "برای انتقال پول یکی از روش‌های زیر را استفاده کن:\n\n"
            "1️⃣ روی پیام بازیکن Reply کن و بنویس:\n"
            "انتقال پول 5000\n\n"
            "2️⃣ با ID بنویس:\n"
            "انتقال پول 5000 به 123456789",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 کیف پول", callback_data="wallet")]
            ])
        )

    elif query.data == "main":
        await query.edit_message_text(
            "🏙️ منوی اصلی UNDERCITY",
            reply_markup=main_menu()
        )


# =========================
# RUN BOT
# =========================

def main():
    token = os.environ.get("BOT_TOKEN")

    if not token:
        raise RuntimeError("BOT_TOKEN is not set")

    threading.Thread(
        target=run_server,
        daemon=True
    ).start()

    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", start))

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            transfer_money
        )
    )

    app.add_handler(
        CallbackQueryHandler(button_handler)
    )

    print("UNDERCITY bot is running...")

    app.run_polling()


if __name__ == "__main__":
    main()
