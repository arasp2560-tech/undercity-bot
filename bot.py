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
# MASTER
# =========================

MASTER_USER_ID = int(os.environ.get("MASTER_USER_ID", "0"))


# =========================
# HTTP SERVER FOR RENDER
# =========================

class HealthHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
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
        json.dump(
            players,
            file,
            ensure_ascii=False,
            indent=2
        )


def default_player(user):
    return {
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


def get_player(user):
    players = load_players()
    user_id = str(user.id)

    if user_id not in players:
        players[user_id] = default_player(user)
        save_players(players)

    else:
        player = players[user_id]

        # اطلاعات پایه
        player["name"] = user.first_name or player.get("name", "Player")
        player["username"] = user.username or ""

        # سازگاری با نسخه‌های قبلی
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

        if "properties" not in player:
            player["properties"] = []

        if "vehicles" not in player:
            player["vehicles"] = []

        if "businesses" not in player:
            player["businesses"] = []

        if "home" not in player:
            player["home"] = {
                "type": "اتاق اجاره‌ای",
                "name": "اتاق کوچک پایین‌شهر",
                "rent": 200
            }

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

    if user.id == MASTER_USER_ID:
        title = "👑 MASTER"
    else:
        title = "🏙️ UNDERCITY"

    text = (
        f"{title}\n\n"
        f"خوش آمدی، {player['name']}!\n\n"
        "اینجا شهریه که از پایین‌ترین نقطه می‌تونی شروع کنی "
        "و قدم‌به‌قدم به یک امپراتوری بزرگ برسی.\n\n"
        f"💵 پول نقد: ${player['cash']:,}\n"
        f"🏦 بانک: ${player['bank_balance']:,}\n"
        f"📍 محل شروع: {player['location']}\n"
        f"🏠 خانه: {player['home']['name']}\n\n"
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
        "انتخاب کن:"
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
        [
            InlineKeyboardButton(
                "📥 واریز به بانک",
                callback_data="deposit"
            )
        ],
        [
            InlineKeyboardButton(
                "🔙 کیف پول",
                callback_data="wallet"
            )
        ]
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
        "بانک برای نگهداری پول و انجام تراکنش‌ها استفاده می‌شود."
    )

    keyboard = [
        [
            InlineKeyboardButton(
                "📥 واریز به بانک",
                callback_data="deposit"
            ),
            InlineKeyboardButton(
                "📤 برداشت از بانک",
                callback_data="withdraw"
            )
        ],
        [
            InlineKeyboardButton(
                "💸 انتقال وجه",
                callback_data="transfer"
            )
        ],
        [
            InlineKeyboardButton(
                "📜 تراکنش‌ها",
                callback_data="transactions"
            )
        ],
        [
            InlineKeyboardButton(
                "🔙 کیف پول",
                callback_data="wallet"
            )
        ]
    ]

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================
# DEPOSIT
# =========================

async def deposit_money(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    player = get_player(user)

    parts = update.message.text.strip().split()

    if len(parts) != 2:
        await update.message.reply_text(
            "❌ فرمت صحیح:\n\n"
            "واریز 5000"
        )
        return

    try:
        amount = int(parts[1])
    except ValueError:
        await update.message.reply_text(
            "❌ مبلغ باید عدد باشد."
        )
        return

    if amount <= 0:
        await update.message.reply_text(
            "❌ مبلغ باید بیشتر از صفر باشد."
        )
        return

    if player["cash"] < amount:
        await update.message.reply_text(
            "❌ پول نقد کافی نیست."
        )
        return

    player["cash"] -= amount
    player["bank_balance"] += amount

    add_transaction(
        player,
        "deposit",
        amount,
        "واریز پول نقد به بانک"
    )

    players = load_players()
    players[str(user.id)] = player
    save_players(players)

    await update.message.reply_text(
        "✅ واریز انجام شد.\n\n"
        f"📥 مبلغ: ${amount:,}\n"
        f"💵 نقد: ${player['cash']:,}\n"
        f"🏦 بانک: ${player['bank_balance']:,}"
    )


# =========================
# WITHDRAW
# =========================

async def withdraw_money(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    player = get_player(user)

    parts = update.message.text.strip().split()

    if len(parts) != 2:
        await update.message.reply_text(
            "❌ فرمت صحیح:\n\n"
            "برداشت 5000"
        )
        return

    try:
        amount = int(parts[1])
    except ValueError:
        await update.message.reply_text(
            "❌ مبلغ باید عدد باشد."
        )
        return

    if amount <= 0:
        await update.message.reply_text(
            "❌ مبلغ باید بیشتر از صفر باشد."
        )
        return

    if player["bank_balance"] < amount:
        await update.message.reply_text(
            "❌ موجودی بانک کافی نیست."
        )
        return

    player["bank_balance"] -= amount
    player["cash"] += amount

    add_transaction(
        player,
        "withdraw",
        amount,
        "برداشت پول از بانک"
    )

    players = load_players()
    players[str(user.id)] = player
    save_players(players)

    await update.message.reply_text(
        "✅ برداشت انجام شد.\n\n"
        f"📤 مبلغ: ${amount:,}\n"
        f"💵 نقد: ${player['cash']:,}\n"
        f"🏦 بانک: ${player['bank_balance']:,}"
    )


# =========================
# FIND PLAYER
# =========================

def find_player_by_username(username):
    username = username.strip().lstrip("@").lower()

    players = load_players()

    for user_id, player in players.items():
        saved_username = str(
            player.get("username", "")
        ).lower()

        if saved_username == username:
            return user_id, player

    return None, None


# =========================
# MONEY TRANSFER
# =========================

async def transfer_money(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    sender_user = update.effective_user

    if not message:
        return

    text = message.text.strip()
    parts = text.split()

    # ---------------------------------
    # Reply transfer
    # انتقال پول 5000
    # ---------------------------------

    if message.reply_to_message:

        target_user = message.reply_to_message.from_user

        if not target_user:
            await message.reply_text(
                "❌ مقصد انتقال پیدا نشد."
            )
            return

        if target_user.id == sender_user.id:
            await message.reply_text(
                "❌ نمی‌توانی به خودت پول انتقال بدهی."
            )
            return

        if len(parts) != 3 or parts[0] != "انتقال" or parts[1] != "پول":
            await message.reply_text(
                "❌ فرمت صحیح:\n\n"
                "انتقال پول 5000\n\n"
                "این پیام را روی پیام بازیکن مقصد Reply کن."
            )
            return

        try:
            amount = int(parts[2])
        except ValueError:
            await message.reply_text(
                "❌ مبلغ باید عدد باشد."
            )
            return

        target_id = str(target_user.id)

    # ---------------------------------
    # ID transfer
    # انتقال پول 5000 به 123456789
    # ---------------------------------

    elif len(parts) == 4 and parts[0] == "انتقال" and parts[1] == "پول" and parts[2] == "به":

        try:
            amount = int(parts[3])
        except ValueError:
            await message.reply_text(
                "❌ مبلغ باید عدد باشد."
            )
            return

        await message.reply_text(
            "❌ برای انتقال با ID از این فرمت استفاده کن:\n\n"
            "انتقال پول 5000 به 123456789"
        )
        return

    # ---------------------------------
    # Username transfer
    # انتقال پول 5000 به @username
    # ---------------------------------

    elif len(parts) == 5 and parts[0] == "انتقال" and parts[1] == "پول" and parts[2] == "به":

        try:
            amount = int(parts[3])
        except ValueError:
            await message.reply_text(
                "❌ مبلغ باید عدد باشد."
            )
            return

        username = parts[4]

        target_id, target = find_player_by_username(username)

        if not target_id:
            await message.reply_text(
                "❌ این username در UNDERCITY پیدا نشد.\n\n"
                "بازیکن مقصد باید حداقل یک‌بار /start زده باشد."
            )
            return

    else:
        return

    # ---------------------------------
    # General validation
    # ---------------------------------

    if amount <= 0:
        await message.reply_text(
            "❌ مبلغ باید بیشتر از صفر باشد."
        )
        return

    players = load_players()

    sender_id = str(sender_user.id)

    if sender_id not in players:
        get_player(sender_user)
        players = load_players()

    if target_id not in players:
        await message.reply_text(
            "❌ بازیکن مقصد هنوز در UNDERCITY ثبت نشده است."
        )
        return

    if target_id == sender_id:
        await message.reply_text(
            "❌ نمی‌توانی به خودت پول انتقال بدهی."
        )
        return

    sender = players[sender_id]
    target = players[target_id]

    sender_balance = sender.get("bank_balance", 0)

    if sender_balance < amount:
        await message.reply_text(
            "❌ موجودی حساب بانکی کافی نیست.\n\n"
            f"🏦 موجودی: ${sender_balance:,}\n"
            f"💸 مبلغ: ${amount:,}"
        )
        return

    # ---------------------------------
    # Transfer
    # ---------------------------------

    sender["bank_balance"] -= amount
    target["bank_balance"] = target.get("bank_balance", 0) + amount

    add_transaction(
        sender,
        "transfer_sent",
        amount,
        f"انتقال به {target.get('name', 'Player')}"
    )

    add_transaction(
        target,
        "transfer_received",
        amount,
        f"دریافت از {sender.get('name', 'Player')}"
    )

    save_players(players)

    await message.reply_text(
        "✅ انتقال با موفقیت انجام شد.\n\n"
        f"👤 گیرنده: {target.get('name', 'Player')}\n"
        f"💸 مبلغ: ${amount:,}\n"
        f"🏦 موجودی جدید: ${sender['bank_balance']:,}"
    )


# =========================
# TRANSACTIONS
# =========================

async def show_transactions(query, user):
    player = get_player(user)

    transactions = player.get("transactions", [])

    if not transactions:
        text = (
            "📜 تراکنش‌ها\n\n"
            "هنوز هیچ تراکنشی ثبت نشده است."
        )

    else:
        recent = transactions[-10:][::-1]

        lines = ["📜 آخرین تراکنش‌ها\n"]

        for item in recent:
            transaction_type = item.get("type", "")
            amount = item.get("amount", 0)
            description = item.get("description", "")

            if transaction_type in (
                "transfer_received",
            ):
                sign = "+"
            elif transaction_type in (
                "transfer_sent",
                "withdraw"
            ):
                sign = "-"
            else:
                sign = "+"

            lines.append(
                f"{sign}${amount:,} — {description}"
            )

        text = "\n".join(lines)

    keyboard = [
        [
            InlineKeyboardButton(
                "🔙 کیف پول",
                callback_data="wallet"
            )
        ]
    ]

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================
# PLACEHOLDER MENUS
# =========================

async def coming_soon(query):
    await query.edit_message_text(
        "🚧 این بخش هنوز در حال ساخت است.\n\n"
        "به‌زودی امکانات بیشتری به UNDERCITY اضافه می‌شود.",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "🔙 منوی اصلی",
                    callback_data="main"
                )
            ]
        ])
    )


# =========================
# BUTTON HANDLER
# =========================

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    await query.answer()

    user = update.effective_user

    # ---------------------------------
    # Security
    # ---------------------------------

    # در نسخه فعلی، Telegram خودش مشخص می‌کند
    # چه کسی روی دکمه کلیک کرده.
    # اطلاعات هر بازیکن نیز با user.id جداست.

    if query.data == "profile":
        await show_profile(query, user)

    elif query.data == "wallet":
        await show_wallet(query, user)

    elif query.data == "cash":
        await show_cash(query, user)

    elif query.data == "bank":
        await show_bank(query, user)

    elif query.data == "transactions":
        await show_transactions(query, user)

    elif query.data == "transfer":
        await query.edit_message_text(
            "💸 انتقال وجه\n\n"
            "دو روش داری:\n\n"
            "1️⃣ Reply:\n"
            "روی پیام بازیکن مقصد Reply کن و بنویس:\n"
            "انتقال پول 5000\n\n"
            "2️⃣ Username:\n"
            "انتقال پول 5000 به @username\n\n"
            "بازیکن مقصد باید قبلاً /start زده باشد.",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "🔙 کیف پول",
                        callback_data="wallet"
                    )
                ]
            ])
        )

    elif query.data == "deposit":
        await query.edit_message_text(
            "📥 واریز به بانک\n\n"
            "در یک پیام جدید بنویس:\n\n"
            "واریز 5000\n\n"
            "مثال:\n"
            "واریز 10000",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "🔙 بانک",
                        callback_data="bank"
                    )
                ]
            ])
        )

    elif query.data == "withdraw":
        await query.edit_message_text(
            "📤 برداشت از بانک\n\n"
            "در یک پیام جدید بنویس:\n\n"
            "برداشت 5000\n\n"
            "مثال:\n"
            "برداشت 10000",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "🔙 بانک",
                        callback_data="bank"
                    )
                ]
            ])
        )

    elif query.data == "main":
        await query.edit_message_text(
            "🏙️ منوی اصلی UNDERCITY",
            reply_markup=main_menu()
        )

    elif query.data in (
        "city",
        "properties",
        "vehicles",
        "businesses",
        "market",
        "underground",
        "gang",
        "clinic",
        "pharmacy",
        "settings"
    ):
        await coming_soon(query)


# =========================
# TEXT HANDLER
# =========================

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    parts = text.split()

    if not parts:
        return

    # انتقال پول
    if len(parts) >= 2 and parts[0] == "انتقال" and parts[1] == "پول":
        await transfer_money(update, context)
        return

    # واریز
    if parts[0] == "واریز":
        await deposit_money(update, context)
        return

    # برداشت
    if parts[0] == "برداشت":
        await withdraw_money(update, context)
        return

    await update.message.reply_text(
        "🤔 دستور شناخته نشد.\n\n"
        "برای دیدن منوی بازی /start را بزن."
    )


# =========================
# MAIN
# =========================

def main():

    token = os.environ.get("BOT_TOKEN")

    if not token:
        raise RuntimeError(
            "BOT_TOKEN is not set in Render Environment Variables."
        )

    # HTTP server
    threading.Thread(
        target=run_server,
        daemon=True
    ).start()

    # Telegram application
    app = Application.builder().token(token).build()

    app.add_handler(
        CommandHandler("start", start)
    )

    app.add_handler(
        CallbackQueryHandler(button_handler)
    )

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            text_handler
        )
    )

    print("UNDERCITY bot is running...")
    print(f"MASTER USER ID: {MASTER_USER_ID}")

    app.run_polling()


# =========================
# START
# =========================

if __name__ == "__main__":
    main()
