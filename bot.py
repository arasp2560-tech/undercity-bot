import os
import json
import re
import threading
import uuid
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


# =========================================================
# CONFIG
# =========================================================

PORT = int(os.environ.get("PORT", 10000))
PLAYERS_FILE = "players.json"

MASTER_USER_ID = int(
    os.environ.get(
        "MASTER_USER_ID",
        "5750241558"
    )
)

MASTER_CASH = 10_000_000_000_000
MASTER_BANK = 10_000_000_000_000


# =========================================================
# VEHICLE CATALOG
# =========================================================
# این فعلاً پایه سیستم خودرو است.
# بعداً می‌توانیم صدها/هزاران خودرو به آن اضافه کنیم.

VEHICLE_CATALOG = {
    "1": {
        "brand": "Saipa",
        "model": "Pride Saba",
        "year": 1386,
        "category": "اقتصادی",
        "price": 180_000_000,
        "mileage": 120_000,
        "condition": "کارکرده",
        "color": "سفید",
        "engine": "1.3L",
        "power": 63,
        "transmission": "دستی",
        "tuning": "فابریک"
    },

    "2": {
        "brand": "Peugeot",
        "model": "Pars",
        "year": 1400,
        "category": "اقتصادی",
        "price": 650_000_000,
        "mileage": 85_000,
        "condition": "کارکرده",
        "color": "سفید",
        "engine": "1.8L",
        "power": 100,
        "transmission": "دستی",
        "tuning": "فابریک"
    },

    "3": {
        "brand": "BMW",
        "model": "M5 F90",
        "year": 2022,
        "category": "اسپرت",
        "price": 12_000_000_000,
        "mileage": 35_000,
        "condition": "کارکرده",
        "color": "مشکی",
        "engine": "4.4L V8 Twin Turbo",
        "power": 600,
        "transmission": "8-Speed Automatic",
        "tuning": "فابریک"
    },

    "4": {
        "brand": "BMW",
        "model": "M5 CS",
        "year": 2022,
        "category": "سوپراسپرت",
        "price": 18_000_000_000,
        "mileage": 18_000,
        "condition": "کارکرده",
        "color": "مشکی",
        "engine": "4.4L V8 Twin Turbo",
        "power": 635,
        "transmission": "8-Speed Automatic",
        "tuning": "فابریک"
    },

    "5": {
        "brand": "Rolls-Royce",
        "model": "Phantom",
        "year": 2024,
        "category": "لوکس",
        "price": 45_000_000_000,
        "mileage": 8_000,
        "condition": "تقریباً نو",
        "color": "مشکی",
        "engine": "6.75L V12 Twin Turbo",
        "power": 563,
        "transmission": "Automatic",
        "tuning": "فابریک"
    },

    "6": {
        "brand": "Nissan",
        "model": "GT-R R35 Nismo",
        "year": 2024,
        "category": "هایپر اسپرت",
        "price": 35_000_000_000,
        "mileage": 5_000,
        "condition": "نو",
        "color": "مشکی",
        "engine": "3.8L V6 Twin Turbo",
        "power": 600,
        "transmission": "Dual-Clutch",
        "tuning": "Nismo"
    }
}


# =========================================================
# RENDER HEALTH SERVER
# =========================================================

class HealthHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)

        self.send_header(
            "Content-Type",
            "text/plain; charset=utf-8"
        )

        self.end_headers()

        self.wfile.write(
            b"UNDERCITY is alive"
        )

    def log_message(self, format, *args):
        return


def run_server():

    server = HTTPServer(
        ("0.0.0.0", PORT),
        HealthHandler
    )

    server.serve_forever()


# =========================================================
# DATABASE
# =========================================================

def load_players():

    try:

        with open(
            PLAYERS_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            return json.load(f)

    except (
        FileNotFoundError,
        json.JSONDecodeError
    ):

        return {}


def save_players(players):

    with open(
        PLAYERS_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            players,
            f,
            ensure_ascii=False,
            indent=2
        )


# =========================================================
# HELPERS
# =========================================================

def normalize_digits(text):

    if not text:
        return ""

    translation = str.maketrans(
        "۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩",
        "01234567890123456789"
    )

    return text.translate(translation)


def is_master(user_id):

    return int(user_id) == MASTER_USER_ID


def generate_vehicle_id():

    players = load_players()

    while True:

        vehicle_id = (
            "CAR-"
            + uuid.uuid4().hex[:8].upper()
        )

        exists = False

        for player in players.values():

            for vehicle in player.get(
                "vehicles",
                []
            ):

                if vehicle.get("id") == vehicle_id:

                    exists = True
                    break

            if exists:
                break

        if not exists:
            return vehicle_id


# =========================================================
# PLAYER CREATION
# =========================================================

def create_player(user):

    master = is_master(user.id)

    if master:

        cash = MASTER_CASH
        bank = MASTER_BANK

    else:

        cash = 10_000
        bank = 0

    return {

        "name": user.first_name or "Player",

        "username": user.username or "",

        "level": 1,

        "xp": 0,

        "cash": cash,

        "bank_balance": bank,

        "credit_score": 500,

        "reputation": 0,

        "banned": False,

        "ban_reason": "",

        "loan": {
            "active": False,
            "principal": 0,
            "remaining": 0,
            "interest_rate": 0,
            "installment": 0,
            "next_payment": None
        },

        "transactions": [],

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

    uid = str(user.id)

    if uid not in players:

        players[uid] = create_player(user)

    player = players[uid]

    # Telegram information
    player["name"] = (
        user.first_name
        or player.get(
            "name",
            "Player"
        )
    )

    player["username"] = (
        user.username
        or player.get(
            "username",
            ""
        )
    )

    # Compatibility
    player.setdefault(
        "cash",
        player.get(
            "money",
            10_000
        )
    )

    player.setdefault(
        "bank_balance",
        0
    )

    player.setdefault(
        "level",
        1
    )

    player.setdefault(
        "xp",
        0
    )

    player.setdefault(
        "credit_score",
        500
    )

    player.setdefault(
        "reputation",
        0
    )

    player.setdefault(
        "transactions",
        []
    )

    player.setdefault(
        "properties",
        []
    )

    player.setdefault(
        "vehicles",
        []
    )

    player.setdefault(
        "businesses",
        []
    )

    player.setdefault(
        "banned",
        False
    )

    player.setdefault(
        "ban_reason",
        ""
    )

    player.setdefault(
        "loan",
        {
            "active": False,
            "principal": 0,
            "remaining": 0,
            "interest_rate": 0,
            "installment": 0,
            "next_payment": None
        }
    )

    player.setdefault(
        "home",
        {
            "type": "اتاق اجاره‌ای",
            "name": "اتاق کوچک پایین‌شهر",
            "rent": 200
        }
    )

    # Master protection
    if is_master(user.id):

        player["is_master"] = True

        if player.get(
            "cash",
            0
        ) < MASTER_CASH:

            player["cash"] = MASTER_CASH

        if player.get(
            "bank_balance",
            0
        ) < MASTER_BANK:

            player["bank_balance"] = MASTER_BANK

    players[uid] = player

    save_players(players)

    return player


# =========================================================
# TRANSACTIONS
# =========================================================

def add_transaction(
    player,
    transaction_type,
    amount,
    description
):

    player.setdefault(
        "transactions",
        []
    )

    player["transactions"].append({

        "type": transaction_type,

        "amount": amount,

        "description": description
    })

    player["transactions"] = (
        player["transactions"][-100:]
    )


# =========================================================
# MAIN MENU
# =========================================================

def main_menu(user_id):

    uid = str(user_id)

    keyboard = [

        [
            InlineKeyboardButton(
                "👤 پروفایل",
                callback_data=f"profile|{uid}"
            ),

            InlineKeyboardButton(
                "💰 کیف پول",
                callback_data=f"wallet|{uid}"
            )
        ],

        [
            InlineKeyboardButton(
                "🏙️ شهر",
                callback_data=f"city|{uid}"
            ),

            InlineKeyboardButton(
                "🏠 املاک",
                callback_data=f"properties|{uid}"
            )
        ],

        [
            InlineKeyboardButton(
                "🚗 وسایل نقلیه",
                callback_data=f"vehicles|{uid}"
            ),

            InlineKeyboardButton(
                "🏢 کسب‌وکارها",
                callback_data=f"businesses|{uid}"
            )
        ],

        [
            InlineKeyboardButton(
                "📈 بازار",
                callback_data=f"market|{uid}"
            ),

            InlineKeyboardButton(
                "🕶️ دنیای زیرزمینی",
                callback_data=f"underground|{uid}"
            )
        ],

        [
            InlineKeyboardButton(
                "🤝 باند و اتحاد",
                callback_data=f"gang|{uid}"
            ),

            InlineKeyboardButton(
                "🏥 درمانگاه",
                callback_data=f"clinic|{uid}"
            )
        ],

        [
            InlineKeyboardButton(
                "💊 داروخانه",
                callback_data=f"pharmacy|{uid}"
            ),

            InlineKeyboardButton(
                "⚙️ تنظیمات",
                callback_data=f"settings|{uid}"
            )
        ]
    ]

    if is_master(user_id):

        keyboard.append([
            InlineKeyboardButton(
                "👑 پنل Master",
                callback_data=f"master|{uid}"
            )
        ])

    return InlineKeyboardMarkup(
        keyboard
    )


# =========================================================
# WALLET MENU
# =========================================================

def wallet_menu(user_id):

    uid = str(user_id)

    keyboard = [

        [
            InlineKeyboardButton(
                "💵 پول نقد",
                callback_data=f"cash|{uid}"
            ),

            InlineKeyboardButton(
                "🏦 بانک",
                callback_data=f"bank|{uid}"
            )
        ],

        [
            InlineKeyboardButton(
                "📥 واریز",
                callback_data=f"deposit|{uid}"
            ),

            InlineKeyboardButton(
                "📤 برداشت",
                callback_data=f"withdraw|{uid}"
            )
        ],

        [
            InlineKeyboardButton(
                "💸 انتقال وجه",
                callback_data=f"transfer|{uid}"
            )
        ],

        [
            InlineKeyboardButton(
                "📜 تراکنش‌ها",
                callback_data=f"transactions|{uid}"
            )
        ],

        [
            InlineKeyboardButton(
                "🔙 منوی اصلی",
                callback_data=f"main|{uid}"
            )
        ]
    ]

    return InlineKeyboardMarkup(
        keyboard
    )


# =========================================================
# VEHICLE MENU
# =========================================================

def vehicle_menu(user_id):

    uid = str(user_id)

    keyboard = [

        [
            InlineKeyboardButton(
                "🏪 نمایشگاه",
                callback_data=f"showroom|{uid}"
            )
        ],

        [
            InlineKeyboardButton(
                "🚘 گاراژ من",
                callback_data=f"garage|{uid}"
            )
        ],

        [
            InlineKeyboardButton(
                "🔙 منوی اصلی",
                callback_data=f"main|{uid}"
            )
        ]
    ]

    return InlineKeyboardMarkup(
        keyboard
    )


# =========================================================
# START
# =========================================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    user = update.effective_user
    chat = update.effective_chat

    if not user or not chat:
        return

    context.user_data.clear()

    player = get_player(user)

    if player.get(
        "banned",
        False
    ):

        await update.message.reply_text(

            "🚫 حساب شما در UNDERCITY مسدود شده است.\n\n"

            f"دلیل: {player.get('ban_reason', 'نامشخص')}"
        )

        return

    total = (
        player.get("cash", 0)
        +
        player.get("bank_balance", 0)
    )

    if is_master(user.id):

        title = "👑 UNDERCITY MASTER"

    else:

        title = "🏙️ UNDERCITY"

    text = (

        f"{title}\n\n"

        f"سلام {player['name']} 👋\n\n"

        "به UNDERCITY خوش آمدی.\n\n"

        f"💵 نقد: ${player['cash']:,}\n"

        f"🏦 بانک: ${player['bank_balance']:,}\n"

        f"💰 مجموع: ${total:,}\n"

        f"⭐ Level: {player['level']}\n"

        f"📍 منطقه: {player['location']}\n"

        f"🚗 خودرو: {len(player.get('vehicles', []))}\n\n"

        "از منوی زیر شروع کن:"
    )

    await update.message.reply_text(

        text,

        reply_markup=main_menu(
            user.id
        )
    )


# =========================================================
# PROFILE
# =========================================================

async def show_profile(
    query,
    user
):

    player = get_player(user)

    username = player.get(
        "username",
        ""
    )

    username_text = (
        f"@{username}"
        if username
        else "ندارد"
    )

    text = (

        "👤 پروفایل\n\n"

        f"نام: {player['name']}\n"

        f"Username: {username_text}\n"

        f"🆔 ID: {user.id}\n\n"

        f"⭐ Level: {player['level']}\n"

        f"✨ XP: {player['xp']}\n"

        f"🎖️ اعتبار: {player['credit_score']}\n"

        f"🏅 اعتبار اجتماعی: {player['reputation']}\n\n"

        f"💵 نقد: ${player['cash']:,}\n"

        f"🏦 بانک: ${player['bank_balance']:,}\n\n"

        f"🏠 خانه: {player['home']['name']}\n"

        f"🏘️ املاک: {len(player['properties'])}\n"

        f"🚗 خودرو: {len(player['vehicles'])}\n"

        f"🏢 کسب‌وکار: {len(player['businesses'])}"
    )

    keyboard = [

        [
            InlineKeyboardButton(
                "🔙 منوی اصلی",
                callback_data=f"main|{user.id}"
            )
        ]
    ]

    await query.edit_message_text(

        text,

        reply_markup=InlineKeyboardMarkup(
            keyboard
        )
    )


# =========================================================
# WALLET
# =========================================================

async def show_wallet(
    query,
    user
):

    player = get_player(user)

    total = (
        player["cash"]
        +
        player["bank_balance"]
    )

    text = (

        "💰 کیف پول\n\n"

        f"💵 پول نقد: ${player['cash']:,}\n"

        f"🏦 بانک: ${player['bank_balance']:,}\n"

        "━━━━━━━━━━━━━━\n"

        f"💰 مجموع: ${total:,}"
    )

    await query.edit_message_text(

        text,

        reply_markup=wallet_menu(
            user.id
        )
    )


# =========================================================
# CASH
# =========================================================

async def show_cash(
    query,
    user
):

    player = get_player(user)

    await query.edit_message_text(

        "💵 پول نقد\n\n"

        f"موجودی:\n"
        f"${player['cash']:,}",

        reply_markup=InlineKeyboardMarkup([

            [
                InlineKeyboardButton(
                    "📥 واریز به بانک",
                    callback_data=f"deposit|{user.id}"
                )
            ],

            [
                InlineKeyboardButton(
                    "🔙 کیف پول",
                    callback_data=f"wallet|{user.id}"
                )
            ]

        ])
    )


# =========================================================
# BANK
# =========================================================

async def show_bank(
    query,
    user
):

    player = get_player(user)

    await query.edit_message_text(

        "🏦 بانک\n\n"

        f"موجودی:\n"
        f"${player['bank_balance']:,}",

        reply_markup=InlineKeyboardMarkup([

            [

                InlineKeyboardButton(
                    "📥 واریز",
                    callback_data=f"deposit|{user.id}"
                ),

                InlineKeyboardButton(
                    "📤 برداشت",
                    callback_data=f"withdraw|{user.id}"
                )

            ],

            [

                InlineKeyboardButton(
                    "💸 انتقال وجه",
                    callback_data=f"transfer|{user.id}"
                )

            ],

            [

                InlineKeyboardButton(
                    "📜 تراکنش‌ها",
                    callback_data=f"transactions|{user.id}"
                )

            ],

            [

                InlineKeyboardButton(
                    "🔙 کیف پول",
                    callback_data=f"wallet|{user.id}"
                )

            ]

        ])
    )


# =========================================================
# TRANSACTIONS
# =========================================================

async def show_transactions(
    query,
    user
):

    player = get_player(user)

    transactions = player.get(
        "transactions",
        []
    )

    if not transactions:

        text = (
            "📜 تراکنش‌ها\n\n"
            "هنوز تراکنشی ثبت نشده."
        )

    else:

        lines = [
            "📜 آخرین تراکنش‌ها\n"
        ]

        for tx in reversed(
            transactions[-15:]
        ):

            amount = tx.get(
                "amount",
                0
            )

            description = tx.get(
                "description",
                ""
            )

            tx_type = tx.get(
                "type",
                ""
            )

            if tx_type in (
                "transfer_received",
                "deposit"
            ):

                sign = "+"

            else:

                sign = "-"

            lines.append(
            f"{sign}${amount:,} — "
                f"{description}"
            )

        text = "\n".join(lines)

    await query.edit_message_text(

        text,

        reply_markup=InlineKeyboardMarkup([

            [

                InlineKeyboardButton(
                    "🔙 کیف پول",
                    callback_data=f"wallet|{user.id}"
                )

            ]

        ])
    )


# =========================================================
# TRANSFER MENU
# =========================================================

async def show_transfer(
    query,
    user
):

    await query.edit_message_text(

        "💸 انتقال وجه\n\n"

        "روش اول — Reply:\n"

        "روی پیام بازیکن مقصد Reply کن و بنویس:\n\n"

        "انتقال پول 5000\n\n"

        "روش دوم — Username:\n"

        "انتقال پول 5000 به @username\n\n"

        "روش سوم — ID:\n"

        "انتقال پول 5000 به 123456789\n\n"

        "💡 انتقال از موجودی بانک انجام می‌شود.",

        reply_markup=InlineKeyboardMarkup([

            [

                InlineKeyboardButton(
                    "🔙 کیف پول",
                    callback_data=f"wallet|{user.id}"
                )

            ]

        ])
    )


# =========================================================
# FIND PLAYER
# =========================================================

def find_by_username(username):

    username = username.strip()

    username = username.lstrip("@").lower()

    players = load_players()

    for uid, player in players.items():

        saved = str(
            player.get(
                "username",
                ""
            )
        ).lower()

        if saved == username:

            return uid, player

    return None, None


# =========================================================
# TRANSFER MONEY
# =========================================================

async def transfer_money(
    update,
    context
):

    message = update.message

    sender_user = update.effective_user

    if not message:
        return

    text = normalize_digits(
        message.text.strip()
    )

    reply = message.reply_to_message

    if reply:

        match = re.match(
            r"^انتقال\s+پول\s+([0-9,]+)$",
            text
        )

        if not match:
            return

        amount = int(
            match.group(1).replace(
                ",",
                ""
            )
        )

        target_user = reply.from_user

        if not target_user:

            await message.reply_text(
                "❌ بازیکن مقصد پیدا نشد."
            )

            return

        if target_user.is_bot:

            await message.reply_text(
                "❌ نمی‌توان به ربات پول انتقال داد."
            )

            return

        target_id = str(
            target_user.id
        )

    else:

        match = re.match(
            r"^انتقال\s+پول\s+([0-9,]+)\s+به\s+(.+)$",
            text
        )

        if not match:
            return

        amount = int(
            match.group(1).replace(
                ",",
                ""
            )
        )

        target = match.group(2).strip()

        if target.isdigit():

            target_id = target

        else:

            target_id, _ = find_by_username(
                target
            )

            if not target_id:

                await message.reply_text(

                    "❌ این Username در بازی پیدا نشد.\n\n"

                    "بازیکن مقصد باید قبلاً /start زده باشد."
                )

                return

    if amount <= 0:

        await message.reply_text(
            "❌ مبلغ باید بیشتر از صفر باشد."
        )

        return

    sender_id = str(
        sender_user.id
    )

    if sender_id == target_id:

        await message.reply_text(
            "❌ نمی‌توانی به خودت پول انتقال بدهی."
        )

        return

    players = load_players()

    if sender_id not in players:

        get_player(
            sender_user
        )

        players = load_players()

    if target_id not in players:

        await message.reply_text(
            "❌ بازیکن مقصد در UNDERCITY ثبت نشده."
        )

        return

    sender = players[
        sender_id
    ]

    target = players[
        target_id
    ]

    if sender.get(
        "banned",
        False
    ):

        await message.reply_text(
            "🚫 حساب شما مسدود است."
        )

        return

    if target.get(
        "banned",
        False
    ):

        await message.reply_text(
            "❌ بازیکن مقصد مسدود است."
        )

        return

    if sender["bank_balance"] < amount:

        await message.reply_text(

            "❌ موجودی بانک کافی نیست.\n\n"

            f"🏦 موجودی: ${sender['bank_balance']:,}\n"

            f"💸 مبلغ: ${amount:,}"
        )

        return

    sender["bank_balance"] -= amount

    target["bank_balance"] += amount

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

    players[
        sender_id
    ] = sender

    players[
        target_id
    ] = target

    save_players(
        players
    )

    await message.reply_text(

        "✅ انتقال موفق بود.\n\n"

        f"👤 گیرنده: {target.get('name', 'Player')}\n"

        f"💸 مبلغ: ${amount:,}\n"
        f"🏦 موجودی جدید: ${sender['bank_balance']:,}"
    )


# =========================================================
# DEPOSIT
# =========================================================

async def deposit_command(
    update,
    context
):

    message = update.message

    user = update.effective_user

    text = normalize_digits(
        message.text.strip()
    )

    match = re.match(
        r"^واریز\s+([0-9,]+)$",
        text
    )

    if not match:
        return

    amount = int(
        match.group(1).replace(
            ",",
            ""
        )
    )

    if amount <= 0:

        await message.reply_text(
            "❌ مبلغ نامعتبر است."
        )

        return

    players = load_players()

    uid = str(
        user.id
    )

    player = players.get(
        uid
    )

    if not player:

        player = get_player(
            user
        )

        players = load_players()

    if player["cash"] < amount:

        await message.reply_text(
            "❌ پول نقد کافی نیست."
        )

        return

    player["cash"] -= amount

    player["bank_balance"] += amount

    add_transaction(
        player,
        "deposit",
        amount,
        "واریز به بانک"
    )

    players[uid] = player

    save_players(
        players
    )

    await message.reply_text(

        "✅ واریز انجام شد.\n\n"

        f"📥 مبلغ: ${amount:,}\n"

        f"💵 نقد: ${player['cash']:,}\n"

        f"🏦 بانک: ${player['bank_balance']:,}"
    )


# =========================================================
# WITHDRAW
# =========================================================

async def withdraw_command(
    update,
    context
):

    message = update.message

    user = update.effective_user

    text = normalize_digits(
        message.text.strip()
    )

    match = re.match(
        r"^برداشت\s+([0-9,]+)$",
        text
    )

    if not match:
        return

    amount = int(
        match.group(1).replace(
            ",",
            ""
        )
    )

    if amount <= 0:

        await message.reply_text(
            "❌ مبلغ نامعتبر است."
        )

        return

    players = load_players()

    uid = str(
        user.id
    )

    player = players.get(
        uid
    )

    if not player:

        player = get_player(
            user
        )

        players = load_players()

    if player["bank_balance"] < amount:

        await message.reply_text(
            "❌ موجودی بانک کافی نیست."
        )

        return

    player["bank_balance"] -= amount

    player["cash"] += amount

    add_transaction(
        player,
        "withdraw",
        amount,
        "برداشت از بانک"
    )

    players[uid] = player

    save_players(
        players
    )

    await message.reply_text(

        "✅ برداشت انجام شد.\n\n"

        f"📤 مبلغ: ${amount:,}\n"

        f"💵 نقد: ${player['cash']:,}\n"

        f"🏦 بانک: ${player['bank_balance']:,}"
    )


# =========================================================
# VEHICLE SYSTEM
# =========================================================

def create_vehicle(
    catalog_id,
    buyer_id
):

    data = VEHICLE_CATALOG[
        catalog_id
    ]

    vehicle_id = generate_vehicle_id()

    vehicle = {

        "id": vehicle_id,

        "catalog_id": catalog_id,

        "brand": data["brand"],

        "model": data["model"],

        "year": data["year"],

        "category": data["category"],

        "price": data["price"],

        "mileage": data["mileage"],

        "condition": data["condition"],

        "color": data["color"],

        "engine": data["engine"],

        "power": data["power"],

        "transmission": data["transmission"],

        "tuning": data["tuning"],

        "owner_id": str(buyer_id),

        "crashed": False,

        "repair_needed": False,

        "parts": [],

        "mods": [],

        "insurance": False
    }

    return vehicle


# =========================================================
# SHOWROOM
# =========================================================

async def show_showroom(
    query,
    user
):

    keyboard = []

    for catalog_id, vehicle in VEHICLE_CATALOG.items():

        keyboard.append([

            InlineKeyboardButton(

                f"🚗 {vehicle['brand']} "
                f"{vehicle['model']} — "
                f"${vehicle['price']:,}",

                callback_data=(
                    f"carview|"
                    f"{catalog_id}|"
                    f"{user.id}"
                )
            )

        ])

    keyboard.append([

        InlineKeyboardButton(
            "🔙 وسایل نقلیه",
            callback_data=f"vehicles|{user.id}"
        )

    ])

    await query.edit_message_text(

        "🏪 نمایشگاه UNDERCITY\n\n"

        "خودروی موردنظر را انتخاب کن:",

        reply_markup=InlineKeyboardMarkup(
            keyboard
        )
    )


# =========================================================
# VEHICLE CATALOG DETAIL
# =========================================================

async def show_catalog_vehicle(
    query,
    user,
    catalog_id
):

    vehicle = VEHICLE_CATALOG.get(
        catalog_id
    )

    if not vehicle:

        await query.answer(
            "❌ خودرو پیدا نشد.",
            show_alert=True
        )

        return

    text = (

        "🚗 مشخصات خودرو\n\n"

        f"🏷️ {vehicle['brand']} "
        f"{vehicle['model']}\n\n"

        f"📅 سال: {vehicle['year']}\n"

        f"🏷️ کلاس: {vehicle['category']}\n"

        f"💰 قیمت: ${vehicle['price']:,}\n"

        f"🛣️ کارکرد: {vehicle['mileage']:,} km\n"

        f"🔧 وضعیت: {vehicle['condition']}\n"

        f"🎨 رنگ: {vehicle['color']}\n"

        f"⚙️ موتور: {vehicle['engine']}\n"

        f"🐎 قدرت: {vehicle['power']} hp\n"

        f"⚙️ گیربکس: {vehicle['transmission']}\n"

        f"🔩 تیونینگ: {vehicle['tuning']}\n"
    )

    keyboard = [

        [

            InlineKeyboardButton(

                "💳 خرید خودرو",

                callback_data=(
                    f"buycar|"
                    f"{catalog_id}|"
                    f"{user.id}"
                )
            )

        ],

        [

            InlineKeyboardButton(

                "🔙 نمایشگاه",

                callback_data=f"showroom|{user.id}"
            )

        ]

    ]

    await query.edit_message_text(

        text,

        reply_markup=InlineKeyboardMarkup(
            keyboard
        )
    )


# =========================================================
# BUY VEHICLE
# =========================================================

async def buy_vehicle(
    query,
    user,
    catalog_id
):

    vehicle_data = VEHICLE_CATALOG.get(
        catalog_id
    )

    if not vehicle_data:

        await query.answer(
            "❌ خودرو پیدا نشد.",
            show_alert=True
        )

        return

    players = load_players()

    uid = str(
        user.id
    )

    if uid not in players:

        get_player(user)

        players = load_players()

    player = players[uid]

    if player.get(
        "banned",
        False
    ):

        await query.answer(
            "🚫 حساب شما مسدود است.",
            show_alert=True
        )

        return

    price = vehicle_data["price"]

    if player["bank_balance"] < price:

        await query.answer(
            "❌ موجودی بانک برای خرید این خودرو کافی نیست.",
            show_alert=True
        )

        return

    vehicle = create_vehicle(
        catalog_id,
        uid
    )

    player["bank_balance"] -= price

    player.setdefault(
        "vehicles",
        []
    )

    player["vehicles"].append(
        vehicle
    )

    add_transaction(
        player,
        "vehicle_purchase",
        price,
        (
            f"خرید خودرو "
            f"{vehicle['brand']} "
            f"{vehicle['model']} "
            f"({vehicle['id']})"
        )
    )

    players[uid] = player

    # -----------------------------------------------------
    # پول خودرو به Master می‌رسد
    # -----------------------------------------------------

    master_id = str(
        MASTER_USER_ID
    )

    if master_id in players:

        master = players[
            master_id
        ]

        master["bank_balance"] += price

        add_transaction(
            master,
            "vehicle_sale",
            price,
            (
                f"فروش خودرو "
                f"{vehicle['brand']} "
                f"{vehicle['model']} "
                f"به {player.get('name', 'Player')}"
            )
        )

        players[
            master_id
        ] = master

    save_players(
        players
    )

    await query.edit_message_text(

        "🎉 خرید خودرو موفق بود!\n\n"

        f"🚗 {vehicle['brand']} "
        f"{vehicle['model']}\n\n"

        f"🆔 شناسه خودرو:\n"
        f"{vehicle['id']}\n\n"

        f"💰 قیمت: ${price:,}\n"

        f"🏦 موجودی بانک:\n"
        f"${player['bank_balance']:,}\n\n"

        "🚘 خودرو به گاراژ شما اضافه شد.",

        reply_markup=InlineKeyboardMarkup([

            [

                InlineKeyboardButton(
                    "🚘 گاراژ من",
                    callback_data=f"garage|{user.id}"
                )

            ],

            [

                InlineKeyboardButton(
                    "🏪 نمایشگاه",
                    callback_data=f"showroom|{user.id}"
                )

            ],

            [

                InlineKeyboardButton(
                    "🔙 وسایل نقلیه",
                    callback_data=f"vehicles|{user.id}"
                )

            ]

        ])
    )


# =========================================================
# GARAGE
# =========================================================

async def show_garage(
    query,
    user
):

    player = get_player(user)

    vehicles = player.get(
        "vehicles",
        []
    )

    if not vehicles:

        await query.edit_message_text(

            "🚘 گاراژ من\n\n"

            "فعلاً هیچ خودرویی نداری.\n\n"

            "از نمایشگاه می‌توانی اولین خودرویت را بخری.",

            reply_markup=InlineKeyboardMarkup([

                [

                    InlineKeyboardButton(
                        "🏪 نمایشگاه",
                        callback_data=f"showroom|{user.id}"
                    )

                ],

                [

                    InlineKeyboardButton(
                        "🔙 وسایل نقلیه",
                        callback_data=f"vehicles|{user.id}"
                    )

                ]

            ])
        )

        return

    keyboard = []

    for vehicle in vehicles:

        keyboard.append([

            InlineKeyboardButton(

                f"🚗 {vehicle.get('brand', '')} "
                f"{vehicle.get('model', '')} "
                f"({vehicle.get('year', '-')})",

                callback_data=(
                    f"mycar|"
                    f"{vehicle.get('id')}|"
                    f"{user.id}"
                )
            )

        ])

    keyboard.append([

        InlineKeyboardButton(
            "🏪 نمایشگاه",
            callback_data=f"showroom|{user.id}"
        )

    ])

    keyboard.append([

        InlineKeyboardButton(
            "🔙 وسایل نقلیه",
            callback_data=f"vehicles|{user.id}"
        )

    ])

    await query.edit_message_text(

        f"🚘 گاراژ {player['name']}\n\n"

        f"تعداد خودروها: {len(vehicles)}\n\n"

        "برای دیدن مشخصات، خودرو را انتخاب کن:",

        reply_markup=InlineKeyboardMarkup(
            keyboard
        )
    )


# =========================================================
# MY VEHICLE DETAIL
# =========================================================

async def show_my_vehicle(
    query,
    user,
    vehicle_id
):

    player = get_player(user)

    vehicle = None

    for item in player.get(
        "vehicles",
        []
    ):

        if item.get("id") == vehicle_id:

            vehicle = item

            break

    if not vehicle:

        await query.answer(
            "❌ این خودرو متعلق به شما نیست یا پیدا نشد.",
            show_alert=True
        )

        return

    crash_status = (
        "⚠️ تصادفی"
        if vehicle.get("crashed", False)
        else "✅ بدون تصادف"
    )

    repair_status = (
        "🔧 نیازمند تعمیر"
        if vehicle.get("repair_needed", False)
        else "✅ سالم"
    )

    text = (

        "🚗 مشخصات خودرو\n\n"

        f"🏷️ {vehicle.get('brand', '-')}"
        f" {vehicle.get('model', '-')}\n\n"

        f"🆔 ID: {vehicle.get('id', '-')}\n"

        f"📅 سال: {vehicle.get('year', '-')}\n"

        f"🏷️ کلاس: {vehicle.get('category', '-')}\n"

        f"💰 ارزش پایه: "
        f"${vehicle.get('price', 0):,}\n"

        f"🛣️ کارکرد: "
        f"{vehicle.get('mileage', 0):,} km\n"

        f"🔧 وضعیت: "
        f"{vehicle.get('condition', '-')}\n"

        f"🎨 رنگ: "
        f"{vehicle.get('color', '-')}\n"

        f"⚙️ موتور: "
        f"{vehicle.get('engine', '-')}\n"

        f"🐎 قدرت: "
        f"{vehicle.get('power', 0)} hp\n"

        f"⚙️ گیربکس: "
        f"{vehicle.get('transmission', '-')}\n"

        f"🔩 تیونینگ: "
        f"{vehicle.get('tuning', '-')}\n\n"

        f"{crash_status}\n"

        f"{repair_status}\n\n"

        f"🛡️ بیمه: "
        f"{'دارد' if vehicle.get('insurance') else 'ندارد'}"
    )

    keyboard = [

        [

            InlineKeyboardButton(
                "🔧 تعمیرات",
                callback_data=f"carrepair|{vehicle_id}|{user.id}"
            )

        ],

        [

            InlineKeyboardButton(
                "🔩 تیونینگ",
                callback_data=f"cartuning|{vehicle_id}|{user.id}"
            )

        ],

        [

            InlineKeyboardButton(
                "📋 کارشناسی",
                callback_data=f"carinspect|{vehicle_id}|{user.id}"
            )

        ],

        [

            InlineKeyboardButton(
                "🔙 گاراژ",
                callback_data=f"garage|{user.id}"
            )

        ]

    ]

    await query.edit_message_text(

        text,

        reply_markup=InlineKeyboardMarkup(
            keyboard
        )
    )


# =========================================================
# VEHICLE PLACEHOLDER MENUS
# =========================================================

async def vehicle_placeholder(
    query,
    user,
    vehicle_id,
    section
):

    if section == "repair":

        title = "🔧 تعمیرات خودرو"

        body = (
            "سیستم تعمیرات در مرحله بعد فعال می‌شود.\n\n"
            "قرار است شامل:\n"
            "• موتور\n"
            "• گیربکس\n"
            "• ترمز\n"
            "• تعلیق\n"
            "• لاستیک\n"
            "• بدنه\n"
            "• قطعات OEM و افترمارکت\n"
        )

    elif section == "tuning":

        title = "🔩 تیونینگ خودرو"

        body = (
            "سیستم تیونینگ در مرحله بعد فعال می‌شود.\n\n"
            "قرار است شامل:\n"
            "• Stage 1\n"
            "• Stage 2\n"
            "• Stage 3\n"
            "• توربو\n"
            "• سوپرشارژر\n"
            "• ECU\n"
            "• اگزوز\n"
            "• ترمز\n"
            "• تعلیق\n"
            "• رینگ و لاستیک\n"
        )

    else:

        title = "📋 کارشناسی خودرو"

        body = (
            "سیستم کارشناسی در مرحله بعد فعال می‌شود.\n\n"
            "قرار است شامل:\n"
            "• تشخیص رنگ\n"
            "• شاسی\n"
            "• موتور\n"
            "• گیربکس\n"
            "• کیلومتر\n"
            "• تصادف\n"
            "• سلامت فنی\n"
        )

    await query.edit_message_text(

        f"{title}\n\n"

        f"🆔 خودرو: {vehicle_id}\n\n"

        f"{body}",

        reply_markup=InlineKeyboardMarkup([

            [

                InlineKeyboardButton(
                    "🔙 خودرو",
                    callback_data=f"mycar|{vehicle_id}|{user.id}"
                )

            ]

        ])
    )


# =========================================================
# MASTER PANEL
# =========================================================

async def master_panel(
    query,
    user
):

    if not is_master(user.id):

        await query.answer(
            "⛔ دسترسی غیرمجاز",
            show_alert=True
        )

        return

    player = get_player(user)

    players = load_players()

    total_players = len(
        players
    )

    total_cash = sum(

        int(
            p.get(
                "cash",
                0
            )
        )

        for p in players.values()
    )

    total_bank = sum(

        int(
            p.get(
                "bank_balance",
                0
            )
        )

        for p in players.values()
    )

    total_vehicles = sum(

        len(
            p.get(
                "vehicles",
                []
            )
        )

        for p in players.values()
    )

    text = (

        "👑 MASTER CONTROL\n\n"

        f"💵 نقد Master: "
        f"${player['cash']:,}\n"

        f"🏦 بانک Master: "
        f"${player['bank_balance']:,}\n\n"

        f"👥 بازیکنان: "
        f"{total_players}\n"

        f"🚗 خودروهای بازیکنان: "
        f"{total_vehicles}\n"

        f"💵 نقد کل بازیکنان: "
        f"${total_cash:,}\n"

        f"🏦 بانک کل بازیکنان: "
        f"${total_bank:,}\n\n"

        "مدیریت بازی:"
    )

    keyboard = [

        [

            InlineKeyboardButton(
                "👥 مدیریت بازیکنان",
                callback_data=f"master_players|{user.id}"
            )

        ],

        [

            InlineKeyboardButton(
                "🚗 مدیریت خودروها",
                callback_data=f"master_cars|{user.id}"
            )

        ],

        [

            InlineKeyboardButton(
                "📊 آمار بازی",
                callback_data=f"master_stats|{user.id}"
            )

        ],

        [

            InlineKeyboardButton(
                "🔙 منوی اصلی",
                callback_data=f"main|{user.id}"
            )

        ]

    ]

    await query.edit_message_text(

        text,

        reply_markup=InlineKeyboardMarkup(
            keyboard
        )
    )

# =========================================================
# MASTER PLAYERS
# =========================================================

async def master_players(
    query,
    user
):

    if not is_master(user.id):

        await query.answer(
            "⛔ دسترسی غیرمجاز",
            show_alert=True
        )

        return

    players = load_players()

    lines = [
        "👥 بازیکنان\n"
    ]

    for uid, player in list(
        players.items()
    )[:20]:

        status = (

            "🚫 BAN"

            if player.get(
                "banned",
                False
            )

            else "🟢"
        )

        username = player.get(
            "username",
            ""
        )

        username_text = (

            f"@{username}"

            if username

            else "-"
        )

        lines.append(

            f"{status} "
            f"{player.get('name', 'Player')}\n"

            f"🆔 {uid} | "
            f"{username_text}\n"

            f"💰 "
            f"${player.get('cash', 0) + player.get('bank_balance', 0):,}\n"
        )

    lines.append(
        "\nبرای مدیریت مستقیم از دستورات Master استفاده کن."
    )

    await query.edit_message_text(

        "\n".join(lines),

        reply_markup=InlineKeyboardMarkup([

            [

                InlineKeyboardButton(
                    "🔙 پنل Master",
                    callback_data=f"master|{user.id}"
                )

            ]

        ])
    )


# =========================================================
# MASTER CARS
# =========================================================

async def master_cars(
    query,
    user
):

    if not is_master(user.id):

        await query.answer(
            "⛔ دسترسی غیرمجاز",
            show_alert=True
        )

        return

    players = load_players()

    total = 0

    lines = [
        "🚗 خودروهای UNDERCITY\n"
    ]

    for uid, player in players.items():

        vehicles = player.get(
            "vehicles",
            []
        )

        if not vehicles:
            continue

        total += len(
            vehicles
        )

        lines.append(

            f"👤 {player.get('name', 'Player')}"
            f" — {len(vehicles)} خودرو"
        )

        for vehicle in vehicles[:5]:

            lines.append(

                f"  🚗 "
                f"{vehicle.get('brand', '')} "
                f"{vehicle.get('model', '')}"
                f" | "
                f"{vehicle.get('id', '-')}"
            )

    if total == 0:

        lines.append(
            "\nهنوز خودرویی خریداری نشده."
        )

    lines.append(
        f"\n🚘 مجموع خودروها: {total}"
    )

    await query.edit_message_text(

        "\n".join(lines),

        reply_markup=InlineKeyboardMarkup([

            [

                InlineKeyboardButton(
                    "🔙 پنل Master",
                    callback_data=f"master|{user.id}"
                )

            ]

        ])
    )


# =========================================================
# MASTER STATS
# =========================================================

async def master_stats(
    query,
    user
):

    if not is_master(user.id):

        await query.answer(
            "⛔ دسترسی غیرمجاز",
            show_alert=True
        )

        return

    players = load_players()

    total_players = len(
        players
    )

    banned = sum(

        1

        for p in players.values()

        if p.get(
            "banned",
            False
        )
    )

    total_cash = sum(

        p.get(
            "cash",
            0
        )

        for p in players.values()
    )

    total_bank = sum(

        p.get(
            "bank_balance",
            0
        )

        for p in players.values()
    )

    total_properties = sum(

        len(
            p.get(
                "properties",
                []
            )
        )

        for p in players.values()
    )

    total_vehicles = sum(

        len(
            p.get(
                "vehicles",
                []
            )
        )

        for p in players.values()
    )

    total_businesses = sum(

        len(
            p.get(
                "businesses",
                []
            )
        )

        for p in players.values()
    )

    text = (

        "📊 آمار UNDERCITY\n\n"

        f"👥 بازیکنان: "
        f"{total_players}\n"

        f"🚫 Ban شده: "
        f"{banned}\n\n"

        f"💵 پول نقد بازیکنان: "
        f"${total_cash:,}\n"

        f"🏦 پول بانک بازیکنان: "
        f"${total_bank:,}\n\n"

        f"🏠 املاک: "
        f"{total_properties}\n"

        f"🚗 خودروها: "
        f"{total_vehicles}\n"

        f"🏢 کسب‌وکارها: "
        f"{total_businesses}"
    )

    await query.edit_message_text(

        text,

        reply_markup=InlineKeyboardMarkup([

            [

                InlineKeyboardButton(
                    "🔙 پنل Master",
                    callback_data=f"master|{user.id}"
                )

            ]

        ])
    )


# =========================================================
# MASTER COMMANDS
# =========================================================

def get_target_id(argument):

    argument = normalize_digits(
        argument.strip()
    )

    if argument.isdigit():

        return argument

    uid, _ = find_by_username(
        argument
    )

    return uid


# =========================================================
# BAN
# =========================================================

async def master_ban(
    update,
    context
):

    user = update.effective_user

    if not is_master(user.id):
        return

    if len(context.args) < 1:

        await update.message.reply_text(

            "فرمت:\n"
            "/ban ID دلیل"
        )

        return

    target_id = get_target_id(
        context.args[0]
    )

    if not target_id:

        await update.message.reply_text(
            "❌ بازیکن پیدا نشد."
        )

        return

    players = load_players()

    if target_id not in players:

        await update.message.reply_text(
            "❌ بازیکن پیدا نشد."
        )

        return

    if target_id == str(
        MASTER_USER_ID
    ):
        await update.message.reply_text(
            "❌ Master را نمی‌توان Ban کرد."
        )

        return

    reason = (

        " ".join(
            context.args[1:]
        )

        if len(context.args) > 1

        else "تخلف از قوانین"
    )

    players[target_id][
        "banned"
    ] = True

    players[target_id][
        "ban_reason"
    ] = reason

    save_players(
        players
    )

    await update.message.reply_text(

        "🚫 بازیکن Ban شد.\n\n"

        f"🆔 {target_id}\n"

        f"📌 دلیل: {reason}"
    )


# =========================================================
# UNBAN
# =========================================================

async def master_unban(
    update,
    context
):

    user = update.effective_user

    if not is_master(user.id):
        return

    if len(context.args) < 1:

        await update.message.reply_text(
            "/unban ID"
        )

        return

    target_id = get_target_id(
        context.args[0]
    )

    if not target_id:

        await update.message.reply_text(
            "❌ بازیکن پیدا نشد."
        )

        return

    players = load_players()

    if target_id not in players:

        await update.message.reply_text(
            "❌ بازیکن پیدا نشد."
        )

        return

    players[target_id][
        "banned"
    ] = False

    players[target_id][
        "ban_reason"
    ] = ""

    save_players(
        players
    )

    await update.message.reply_text(

        f"✅ Ban بازیکن "
        f"{target_id} برداشته شد."
    )


# =========================================================
# FINE
# =========================================================

async def master_fine(
    update,
    context
):

    user = update.effective_user

    if not is_master(user.id):
        return

    if len(context.args) < 2:

        await update.message.reply_text(
            "/fine ID مبلغ"
        )

        return

    target_id = get_target_id(
        context.args[0]
    )

    try:

        amount = int(
            normalize_digits(
                context.args[1]
            )
        )

    except ValueError:

        await update.message.reply_text(
            "❌ مبلغ باید عدد باشد."
        )

        return

    if amount <= 0:

        await update.message.reply_text(
            "❌ مبلغ نامعتبر است."
        )

        return

    if target_id == str(
        MASTER_USER_ID
    ):

        await update.message.reply_text(
            "❌ نمی‌توان Master را جریمه کرد."
        )

        return

    players = load_players()

    if not target_id or target_id not in players:

        await update.message.reply_text(
            "❌ بازیکن پیدا نشد."
        )

        return

    player = players[
        target_id
    ]

    bank_taken = min(
        player.get(
            "bank_balance",
            0
        ),
        amount
    )

    remaining = (
        amount
        -
        bank_taken
    )

    cash_taken = min(
        player.get(
            "cash",
            0
        ),
        remaining
    )

    total_taken = (
        bank_taken
        +
        cash_taken
    )

    player["bank_balance"] -= (
        bank_taken
    )

    player["cash"] -= (
        cash_taken
    )

    add_transaction(

        player,

        "fine",

        total_taken,

        "جریمه توسط Master"
    )

    players[target_id] = player

    master_id = str(
        MASTER_USER_ID
    )

    master = players.get(
        master_id
    )

    if master:

        master["bank_balance"] += (
            total_taken
        )

        add_transaction(

            master,

            "fine_received",

            total_taken,

            (
                f"دریافت جریمه از "
                f"{player.get('name', 'Player')}"
            )
        )

        players[
            master_id
        ] = master

    save_players(
        players
    )

    await update.message.reply_text(

        "💸 جریمه اعمال شد.\n\n"

        f"👤 بازیکن: "
        f"{player.get('name', 'Player')}\n"

        f"💰 مبلغ واقعی برداشت‌شده: "
        f"${total_taken:,}\n"

        f"🏦 از بانک: "
        f"${bank_taken:,}\n"

        f"💵 از نقد: "
        f"${cash_taken:,}"
    )


# =========================================================
# SET CASH
# =========================================================

async def master_setcash(
    update,
    context
):

    user = update.effective_user

    if not is_master(user.id):
        return

    if len(context.args) != 2:

        await update.message.reply_text(
            "/setcash ID مبلغ"
        )

        return

    target_id = get_target_id(
        context.args[0]
    )

    try:

        amount = int(
            normalize_digits(
                context.args[1]
            )
        )

    except ValueError:

        await update.message.reply_text(
            "❌ مبلغ باید عدد باشد."
        )

        return

    if not target_id or amount < 0:

        await update.message.reply_text(
            "❌ اطلاعات نامعتبر."
        )

        return

    players = load_players()

    if target_id not in players:

        await update.message.reply_text(
            "❌ بازیکن پیدا نشد."
        )

        return

    old = players[target_id][
        "cash"
    ]

    players[target_id][
        "cash"
    ] = amount

    save_players(
        players
    )

    await update.message.reply_text(

        "✅ موجودی نقدی تغییر کرد.\n\n"

        f"قبل: ${old:,}\n"

        f"بعد: ${amount:,}"
    )


# =========================================================
# SET BANK
# =========================================================

async def master_setbank(
    update,
    context
):

    user = update.effective_user

    if not is_master(user.id):
        return

    if len(context.args) != 2:

        await update.message.reply_text(
            "/setbank ID مبلغ"
        )

        return

    target_id = get_target_id(
        context.args[0]
    )

    try:

        amount = int(
            normalize_digits(
                context.args[1]
            )
        )

    except ValueError:

        await update.message.reply_text(
            "❌ مبلغ باید عدد باشد."
        )

        return

    if not target_id or amount < 0:

        await update.message.reply_text(
            "❌ اطلاعات نامعتبر."
        )

        return

    players = load_players()

    if target_id not in players:

        await update.message.reply_text(
            "❌ بازیکن پیدا نشد."
        )

        return

    old = players[target_id][
        "bank_balance"
    ]

    players[target_id][
        "bank_balance"
    ] = amount

    save_players(
        players
    )

    await update.message.reply_text(

        "✅ موجودی بانک تغییر کرد.\n\n"

        f"قبل: ${old:,}\n"

        f"بعد: ${amount:,}"
    )


# =========================================================
# PLAYER INFO
# =========================================================

async def master_info(
    update,
    context
):

    user = update.effective_user

    if not is_master(user.id):
        return

    if len(context.args) < 1:

        await update.message.reply_text(
            "/player ID"
        )

        return

    target_id = get_target_id(
        context.args[0]
    )

    if not target_id:

        await update.message.reply_text(
            "❌ بازیکن پیدا نشد."
        )

        return

    players = load_players()

    if target_id not in players:

        await update.message.reply_text(
            "❌ بازیکن پیدا نشد."
        )

        return

    p = players[
        target_id
    ]

    username = p.get(
        "username",
        ""
    )

    await update.message.reply_text(

        "👤 اطلاعات بازیکن\n\n"

        f"نام: {p.get('name', '-')}\n"

        f"Username: "
        f"@{username if username else '-'}\n"

        f"🆔 ID: {target_id}\n\n"

        f"💵 نقد: "
        f"${p.get('cash', 0):,}\n"

        f"🏦 بانک: "
        f"${p.get('bank_balance', 0):,}\n"

        f"⭐ Level: "
        f"{p.get('level', 1)}\n"

        f"🚗 خودرو: "
        f"{len(p.get('vehicles', []))}\n"

        f"🚫 Ban: "
        f"{'بله' if p.get('banned', False) else 'خیر'}\n"

        f"📌 دلیل Ban: "
        f"{p.get('ban_reason', '-')}"
    )


# =========================================================
# CALLBACK SECURITY
# =========================================================

def callback_owner_is_user(
    query,
    user
):

    try:

        parts = query.data.split("|")

        owner_id = int(
            parts[-1]
        )

    except (
        ValueError,
        IndexError
    ):

        return False

    return owner_id == user.id


# =========================================================
# BUTTON HANDLER
# =========================================================

async def button_handler(
    update,
    context
):

    query = update.callback_query

    user = update.effective_user

    if not callback_owner_is_user(
        query,
        user
    ):

        await query.answer(

            "⛔ این منو متعلق به شما نیست.",

            show_alert=True
        )

        return

    await query.answer()

    parts = query.data.split("|")

    action = parts[0]

    # -----------------------------------------------------
    # MAIN
    # -----------------------------------------------------

    if action == "main":

        await query.edit_message_text(

            "🏙️ منوی اصلی UNDERCITY",

            reply_markup=main_menu(
                user.id
            )
        )

    # -----------------------------------------------------
    # PROFILE
    # -----------------------------------------------------

    elif action == "profile":

        await show_profile(
            query,
            user
        )

    # -----------------------------------------------------
    # WALLET
    # -----------------------------------------------------

    elif action == "wallet":

        await show_wallet(
            query,
            user
        )

    # -----------------------------------------------------
    # CASH
    # -----------------------------------------------------

    elif action == "cash":

        await show_cash(
            query,
            user
        )

    # -----------------------------------------------------
    # BANK
    # -----------------------------------------------------

    elif action == "bank":

        await show_bank(
            query,
            user
        )

    # -----------------------------------------------------
    # TRANSACTIONS
    # -----------------------------------------------------

    elif action == "transactions":

        await show_transactions(
            query,
            user
        )

    # -----------------------------------------------------
    # TRANSFER
    # -----------------------------------------------------

    elif action == "transfer":

        await show_transfer(
            query,
            user
        )

    # -----------------------------------------------------
    # DEPOSIT
    # -----------------------------------------------------

    elif action == "deposit":

        await query.edit_message_text(

            "📥 واریز به بانک\n\n"

            "یک پیام جدید بفرست:\n\n"

            "واریز 5000",

            reply_markup=InlineKeyboardMarkup([

                [

                    InlineKeyboardButton(
                        "🔙 بانک",
                        callback_data=f"bank|{user.id}"
                    )

                ]

            ])
        )

    # -----------------------------------------------------
    # WITHDRAW
    # -----------------------------------------------------

    elif action == "withdraw":

        await query.edit_message_text(

            "📤 برداشت از بانک\n\n"

            "یک پیام جدید بفرست:\n\n"

            "برداشت 5000",

            reply_markup=InlineKeyboardMarkup([

                [

                    InlineKeyboardButton(
                        "🔙 بانک",
                        callback_data=f"bank|{user.id}"
                    )

                ]

            ])
        )

    # -----------------------------------------------------
    # VEHICLES
    # -----------------------------------------------------

    elif action == "vehicles":

        player = get_player(user)

        vehicle_count = len(
            player.get(
                "vehicles",
                []
            )
        )

        await query.edit_message_text(

            "🚗 وسایل نقلیه\n\n"

            f"🚘 تعداد خودروهای شما: "
            f"{vehicle_count}\n\n"

            "در این بخش می‌توانی خودرو بخری "
            "و گاراژ خودت را مدیریت کنی.",

            reply_markup=vehicle_menu(
                user.id
            )
        )

    # -----------------------------------------------------
    # SHOWROOM
    # -----------------------------------------------------

    elif action == "showroom":

        await show_showroom(
            query,
            user
        )

    # -----------------------------------------------------
    # CATALOG VEHICLE
    # -----------------------------------------------------

    elif action == "carview":

        if len(parts) < 3:
            return

        catalog_id = parts[1]

        await show_catalog_vehicle(
            query,
            user,
            catalog_id
        )

    # -----------------------------------------------------
    # BUY CAR
    # -----------------------------------------------------

    elif action == "buycar":

        if len(parts) < 3:
            return

        catalog_id = parts[1]

        await buy_vehicle(
            query,
            user,
            catalog_id
        )

    # -----------------------------------------------------
    # GARAGE
    # -----------------------------------------------------

    elif action == "garage":

        await show_garage(
            query,
            user
        )

    # -----------------------------------------------------
    # MY CAR
    # -----------------------------------------------------

    elif action == "mycar":

        if len(parts) < 3:
            return

        vehicle_id = parts[1]

        await show_my_vehicle(
            query,
            user,
            vehicle_id
        )

    # -----------------------------------------------------
    # VEHICLE REPAIR
    # -----------------------------------------------------

    elif action == "carrepair":

        if len(parts) < 3:
            return

        vehicle_id = parts[1]

        await vehicle_placeholder(
            query,
            user,
            vehicle_id,
            "repair"
        )

    # -----------------------------------------------------
    # VEHICLE TUNING
    # -----------------------------------------------------

    elif action == "cartuning":

        if len(parts) < 3:
            return

        vehicle_id = parts[1]

        await vehicle_placeholder(
            query,
            user,
            vehicle_id,
            "tuning"
        )

    # -----------------------------------------------------
    # VEHICLE INSPECTION
    # -----------------------------------------------------

    elif action == "carinspect":

        if len(parts) < 3:
            return

        vehicle_id = parts[1]

        await vehicle_placeholder(
            query,
            user,
            vehicle_id,
            "inspection"
        )

    # -----------------------------------------------------
    # MASTER
    # -----------------------------------------------------

    elif action == "master":

        await master_panel(
            query,
            user
        )

    elif action == "master_players":

        await master_players(
            query,
            user
        )

    elif action == "master_cars":

        await master_cars(
            query,
            user
        )

    elif action == "master_stats":

        await master_stats(
            query,
            user
        )

    # -----------------------------------------------------
    # OTHER GAME SECTIONS
    # -----------------------------------------------------

    elif action in (

        "city",
        "properties",
        "businesses",
        "market",
        "underground",
        "gang",
        "clinic",
        "pharmacy",
        "settings"
    ):

        names = {

            "city": "🏙️ شهر",

            "properties": "🏠 املاک",

            "businesses": "🏢 کسب‌وکارها",

            "market": "📈 بازار",

            "underground": "🕶️ دنیای زیرزمینی",

            "gang": "🤝 باند و اتحاد",

            "clinic": "🏥 درمانگاه",

            "pharmacy": "💊 داروخانه",

            "settings": "⚙️ تنظیمات"
        }

        await query.edit_message_text(

            f"{names[action]}\n\n"

            "🚧 این بخش در مرحله بعد ساخته می‌شود.",

            reply_markup=InlineKeyboardMarkup([

                [

                    InlineKeyboardButton(
                        "🔙 منوی اصلی",
                        callback_data=f"main|{user.id}"
                    )

                ]

            ])
        )

# =========================================================
# TEXT HANDLER
# =========================================================

async def text_handler(
    update,
    context
):

    if not update.message:
        return

    if not update.message.text:
        return

    text = normalize_digits(
        update.message.text.strip()
    )

    # -----------------------------------------------------
    # MENU
    # -----------------------------------------------------

    if text.lower() in (
        "منو",
        "menu"
    ):

        await start(
            update,
            context
        )

        return

    # -----------------------------------------------------
    # MASTER PANEL
    # -----------------------------------------------------

    if text.lower() in (
        "پنل",
        "panel"
    ):

        user = update.effective_user

        if is_master(
            user.id
        ):

            player = get_player(
                user
            )

            players = load_players()

            total_players = len(
                players
            )

            await update.message.reply_text(

                "👑 MASTER CONTROL\n\n"

                f"💵 نقد: "
                f"${player['cash']:,}\n"

                f"🏦 بانک: "
                f"${player['bank_balance']:,}\n\n"

                f"👥 بازیکنان: "
                f"{total_players}\n\n"

                "از دکمه زیر استفاده کن:",

                reply_markup=InlineKeyboardMarkup([

                    [

                        InlineKeyboardButton(
                            "👑 باز کردن پنل Master",
                            callback_data=f"master|{user.id}"
                        )

                    ]

                ])
            )

        return

    # -----------------------------------------------------
    # TRANSFER
    # -----------------------------------------------------

    if text.startswith(
        "انتقال پول"
    ):

        await transfer_money(
            update,
            context
        )

        return

    # -----------------------------------------------------
    # DEPOSIT
    # -----------------------------------------------------

    if text.startswith(
        "واریز"
    ):

        await deposit_command(
            update,
            context
        )

        return

    # -----------------------------------------------------
    # WITHDRAW
    # -----------------------------------------------------

    if text.startswith(
        "برداشت"
    ):

        await withdraw_command(
            update,
            context
        )

        return


# =========================================================
# MAIN
# =========================================================

def main():

    token = os.environ.get(
        "BOT_TOKEN"
    )

    if not token:

        raise RuntimeError(
            "BOT_TOKEN is not set."
        )

    # Render health server

    threading.Thread(
        target=run_server,
        daemon=True
    ).start()

    app = (
        Application
        .builder()
        .token(token)
        .build()
    )

    # -----------------------------------------------------
    # START
    # -----------------------------------------------------

    app.add_handler(
        CommandHandler(
            "start",
            start
        )
    )

    # -----------------------------------------------------
    # MASTER COMMANDS
    # -----------------------------------------------------

    app.add_handler(
        CommandHandler(
            "ban",
            master_ban
        )
    )

    app.add_handler(
        CommandHandler(
            "unban",
            master_unban
        )
    )

    app.add_handler(
        CommandHandler(
            "fine",
            master_fine
        )
    )

    app.add_handler(
        CommandHandler(
            "setcash",
            master_setcash
        )
    )

    app.add_handler(
        CommandHandler(
            "setbank",
            master_setbank
        )
    )

    app.add_handler(
        CommandHandler(
            "player",
            master_info
        )
    )

    # -----------------------------------------------------
    # BUTTONS
    # -----------------------------------------------------

    app.add_handler(
        CallbackQueryHandler(
            button_handler
        )
    )

    # -----------------------------------------------------
    # TEXT
    # -----------------------------------------------------

    app.add_handler(
        MessageHandler(
            filters.TEXT
            & ~filters.COMMAND,
            text_handler
        )
    )

    print(
        "================================"
    )

    print(
        "UNDERCITY BOT IS RUNNING"
    )

    print(
        f"MASTER ID: {MASTER_USER_ID}"
    )

    print(
        "================================"
    )

    app.run_polling()


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    main()
