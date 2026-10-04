import os
import json
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
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
        # اضافه کردن اطلاعات جدید به بازیکنان قدیمی
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

        save_players(players)

    return players[user_id]


# =========================
# TRANSACTIONS
# =========================

def add_transaction(player, transaction_type, amount, description):
    player["transactions"].append({
        "type": transaction_type,
        "amount": amount,
        "description": description
    })

    # فقط 50 تراکنش آخر نگه داشته شود
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
        f"💰 کل دارایی نقدی: ${player['cash'] + player['bank_balance']:,}\n\n"
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
        "از این بخش می‌تونی مدیریت مالی شخصیتت رو انجام بدی."
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
        f"💵 موجودی حساب:\n"
        f"${player['bank_balance']:,}\n\n"
        f"🎖️ امتیاز اعتباری: {player['credit_score']}\n\n"
        "امکانات بانکی بیشتر در مراحل بعدی اضافه می‌شوند."
    )

    keyboard = [
        [InlineKeyboardButton("📥 واریز", callback_data="deposit")],
        [InlineKeyboardButton("📤 برداشت", callback_data="withdraw")],
        [InlineKeyboardButton("📜 تراکنش‌ها", callback_data="transactions")],
        [InlineKeyboardButton("🔙 کیف پول", callback_data="wallet")]
    ]

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================
# DEPOSIT / WITHDRAW
# =========================

async def deposit_info(query, user):
    player = get_player(user)

    text = (
        "📥 واریز به بانک\n\n"
        f"💵 پول نقد شما: ${player['cash']:,}\n\n"
        "برای واریز فعلاً از مبالغ آماده استفاده کن:"
    )

    keyboard = [
        [
            InlineKeyboardButton("💵 $1,000", callback_data="deposit_1000"),
            InlineKeyboardButton("💵 $5,000", callback_data="deposit_5000")
        ],
        [
            InlineKeyboardButton("💵 $10,000", callback_data="deposit_10000")
        ],
        [
            InlineKeyboardButton("🔙 بانک", callback_data="bank")
        ]
    ]

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def withdraw_info(query, user):
    player = get_player(user)

    text = (
        "📤 برداشت از بانک\n\n"
        f"🏦 موجودی بانک: ${player['bank_balance']:,}\n\n"
        "مبلغ موردنظر را انتخاب کن:"
    )

    keyboard = [
        [
            InlineKeyboardButton("💵 $1,000", callback_data="withdraw_1000"),
            InlineKeyboardButton("💵 $5,000", callback_data="withdraw_5000")
        ],
        [
            InlineKeyboardButton("💵 $10,000", callback_data="withdraw_10000")
        ],
        [
            InlineKeyboardButton("🔙 بانک", callback_data="bank")
        ]
    ]

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================
# TRANSACTION ACTION
# =========================

async def deposit_money(query, user, amount):
    players = load_players()
    player = players[str(user.id)]

    if player["cash"] < amount:
        await query.answer("❌ پول نقد کافی نداری.", show_alert=True)
        return

    player["cash"] -= amount
    player["bank_balance"] += amount

    add_transaction(
        player,
        "deposit",
        amount,
        f"واریز ${amount:,} به بانک"
    )

    save_players(players)

    await query.answer("✅ واریز با موفقیت انجام شد.")

    await show_wallet(query, user)


async def withdraw_money(query, user, amount):
    players = load_players()
    player = players[str(user.id)]

    if player["bank_balance"] < amount:
        await query.answer("❌ موجودی بانک کافی نیست.", show_alert=True)
        return

    player["bank_balance"] -= amount
    player["cash"] += amount

    add_transaction(
        player,
        "withdraw",
        amount,
        f"برداشت ${amount:,} از بانک"
    )

    save_players(players)

    await query.answer("✅ برداشت با موفقیت انجام شد.")

    await show_wallet(query, user)


# =========================
# TRANSACTIONS
# =========================

async def show_transactions(query, user):
    player = get_player(user)

    transactions = player.get("transactions", [])

    if not transactions:
        text = (
            "📜 تاریخچه تراکنش‌ها\n\n"
            "هنوز هیچ تراکنشی ثبت نشده."
        )
    else:
        text = "📜 تاریخچه تراکنش‌ها\n\n"

        for transaction in reversed(transactions[-10:]):
            amount = transaction["amount"]
            description = transaction["description"]

            if transaction["type"] == "deposit":
                icon = "📥"
            elif transaction["type"] == "withdraw":
                icon = "📤"
            else:
                icon = "💰"

            text += f"{icon} {description}\n"

    keyboard = [
        [InlineKeyboardButton("🔙 کیف پول", callback_data="wallet")]
    ]

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================
# BUTTON HANDLER
# =========================

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user = query.from_user
    data = query.data

    # MAIN
    if data == "main":
        await query.edit_message_text(
            "🏙️ منوی اصلی UNDERCITY",
            reply_markup=main_menu()
        )

    # PROFILE
    elif data == "profile":
        await show_profile(query, user)

    # WALLET
    elif data == "wallet":
        await show_wallet(query, user)

    # CASH
    elif data == "cash":
        await show_cash(query, user)

    # BANK
    elif data == "bank":
        await show_bank(query, user)

    # DEPOSIT
    elif data == "deposit":
        await deposit_info(query, user)

    # WITHDRAW
    elif data == "withdraw":
        await withdraw_info(query, user)

    # DEPOSIT AMOUNTS
    elif data.startswith("deposit_"):
        amount = int(data.split("_")[1])
        await deposit_money(query, user, amount)

    # WITHDRAW AMOUNTS
    elif data.startswith("withdraw_"):
        amount = int(data.split("_")[1])
        await withdraw_money(query, user, amount)

    # TRANSACTIONS
    elif data == "transactions":
        await show_transactions(query, user)

    # OTHER SECTIONS
    elif data == "city":
        await query.edit_message_text(
            "🏙️ بخش شهر به‌زودی فعال می‌شود.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 برگشت", callback_data="main")]
            ])
        )

    elif data == "properties":
        await query.edit_message_text(
            "🏠 بخش املاک به‌زودی فعال می‌شود.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 برگشت", callback_data="main")]
            ])
        )

    elif data == "vehicles":
        await query.edit_message_text(
            "🚗 بخش وسایل نقلیه به‌زودی فعال می‌شود.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 برگشت", callback_data="main")]
            ])
        )

    elif data == "businesses":
        await query.edit_message_text(
            "🏢 بخش کسب‌وکارها به‌زودی فعال می‌شود.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 برگشت", callback_data="main")]
            ])
        )

    elif data == "market":
        await query.edit_message_text(
            "📈 بازار به‌زودی فعال می‌شود.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 برگشت", callback_data="main")]
            ])
        )

    elif data == "underground":
        await query.edit_message_text(
            "🕶️ دنیای زیرزمینی به‌زودی فعال می‌شود.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 برگشت", callback_data="main")]
            ])
        )

    elif data == "gang":
        await query.edit_message_text(
            "🤝 باند و اتحاد به‌زودی فعال می‌شود.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 برگشت", callback_data="main")]
            ])
        )

    elif data == "clinic":
        await query.edit_message_text(
            "🏥 درمانگاه به‌زودی فعال می‌شود.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 برگشت", callback_data="main")]
            ])
        )

    elif data == "pharmacy":
        await query.edit_message_text(
            "💊 داروخانه به‌زودی فعال می‌شود.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 برگشت", callback_data="main")]
            ])
        )

    elif data == "settings":
        await query.edit_message_text(
            "⚙️ تنظیمات به‌زودی فعال می‌شود.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 برگشت", callback_data="main")]
            ])
        )


# =========================
# MAIN
# =========================

def main():
    threading.Thread(
        target=run_server,
        daemon=True
    ).start()

    token = os.environ.get("BOT_TOKEN")

    if not token:
        raise ValueError("BOT_TOKEN is not set")

    app = Application.builder().token(token).build()

    app.add_handler(
        CommandHandler("start", start)
    )

    app.add_handler(
        CallbackQueryHandler(button_handler)
    )

    print("UNDERCITY BOT IS RUNNING...")

    app.run_polling()


if __name__ == "__main__":
    main()
