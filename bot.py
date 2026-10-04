import os
import json
import re
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

# =========================================================
# CONFIG
# =========================================================

PORT = int(os.environ.get("PORT", 10000))
PLAYERS_FILE = "players.json"

# Master account
MASTER_USER_ID = int(os.environ.get("MASTER_USER_ID", "5750241558"))

# Master starting assets
MASTER_CASH = 10_000_000_000_000
MASTER_BANK = 10_000_000_000_000


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
        self.wfile.write(b"UNDERCITY is alive")

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
# MASTER
# =========================================================

def is_master(user_id):
    return int(user_id) == MASTER_USER_ID


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

    # Keep Telegram information updated
    player["name"] = user.first_name or player.get(
        "name",
        "Player"
    )

    player["username"] = user.username or player.get(
        "username",
        ""
    )

    # Compatibility with older data
    player.setdefault("cash", player.get("money", 10_000))
    player.setdefault("bank_balance", 0)
    player.setdefault("level", 1)
    player.setdefault("xp", 0)
    player.setdefault("credit_score", 500)
    player.setdefault("reputation", 0)
    player.setdefault("transactions", [])
    player.setdefault("properties", [])
    player.setdefault("vehicles", [])
    player.setdefault("businesses", [])

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

    # Always guarantee Master's huge starting assets
    if is_master(user.id):
        player["is_master"] = True

        if player.get("cash", 0) < MASTER_CASH:
            player["cash"] = MASTER_CASH

        if player.get("bank_balance", 0) < MASTER_BANK:
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

    player.setdefault("transactions", [])

    player["transactions"].append({
        "type": transaction_type,
        "amount": amount,
        "description": description
    })

    # Keep latest 100
    player["transactions"] = player["transactions"][-100:]


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

    return InlineKeyboardMarkup(keyboard)


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

    return InlineKeyboardMarkup(keyboard)


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

    # -----------------------------------------------------
    # IMPORTANT:
    # Menu is sent ONLY to the chat where /start was used.
    # -----------------------------------------------------

    total = (
        player.get("cash", 0)
        +
        player.get("bank_balance", 0)
    )

    if is_master(user.id):

        title = "👑 UNDERCITY MASTER"

    else:

        title = "🏙️ UNDERCITY"

    if player.get("banned", False):

        await update.message.reply_text(
            "🚫 حساب شما در UNDERCITY مسدود شده است.\n\n"
            f"دلیل: {player.get('ban_reason', 'نامشخص')}"
        )

        return

    text = (
        f"{title}\n\n"
        f"سلام {player['name']} 👋\n\n"
        "به UNDERCITY خوش آمدی.\n\n"
        f"💵 نقد: ${player['cash']:,}\n"
        f"🏦 بانک: ${player['bank_balance']:,}\n"
        f"💰 مجموع: ${total:,}\n"
        f"⭐ Level: {player['level']}\n"
        f"📍 منطقه: {player['location']}\n\n"
        "از منوی زیر شروع کن:"
    )

    await update.message.reply_text(
        text,
        reply_markup=main_menu(user.id)
    )


# =========================================================
# PROFILE
# =========================================================

async def show_profile(query, user):

    player = get_player(user)

    username = player.get("username", "")

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
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================================================
# WALLET
# =========================================================

async def show_wallet(query, user):

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
        reply_markup=wallet_menu(user.id)
    )


# =========================================================
# CASH
# =========================================================

async def show_cash(query, user):

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

async def show_bank(query, user):

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

async def show_transactions(query, user):

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
                f"{sign}${amount:,} — {description}"
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

async def show_transfer(query, user):

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

    text = message.text.strip()

    # -----------------------------------------------------
    # Reply
    # انتقال پول 5000
    # -----------------------------------------------------

    reply = message.reply_to_message

    if reply:

        match = re.match(
            r"^انتقال\s+پول\s+(\d+)$",
            text
        )

        if not match:
            return

        amount = int(
            match.group(1)
        )

        target_user = reply.from_user

        if not target_user:
            await message.reply_text(
                "❌ بازیکن مقصد پیدا نشد."
            )
            return

        target_id = str(
            target_user.id
        )

    # -----------------------------------------------------
    # ID / Username
    # -----------------------------------------------------

    else:

        match = re.match(
            r"^انتقال\s+پول\s+(\d+)\s+به\s+(.+)$",
            text
        )

        if not match:
            return

        amount = int(
            match.group(1)
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

    # -----------------------------------------------------
    # Validation
    # -----------------------------------------------------

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

        get_player(sender_user)
        players = load_players()

    if target_id not in players:

        await message.reply_text(
            "❌ بازیکن مقصد در UNDERCITY ثبت نشده."
        )

        return

    sender = players[sender_id]
    target = players[target_id]

    # Banned users cannot transfer
    if sender.get("banned", False):

        await message.reply_text(
            "🚫 حساب شما مسدود است."
        )

        return

    if sender["bank_balance"] < amount:

        await message.reply_text(
            "❌ موجودی بانک کافی نیست.\n\n"
            f"🏦 موجودی: ${sender['bank_balance']:,}\n"
            f"💸 مبلغ: ${amount:,}"
        )

        return

    # -----------------------------------------------------
    # TRANSFER
    # -----------------------------------------------------

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

    players[sender_id] = sender
    players[target_id] = target

    save_players(players)

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

    match = re.match(
        r"^واریز\s+(\d+)$",
        message.text.strip()
    )

    if not match:
        return

    amount = int(
        match.group(1)
    )

    if amount <= 0:
        await message.reply_text(
            "❌ مبلغ نامعتبر است."
        )
        return

    players = load_players()
    uid = str(user.id)

    player = players.get(uid)

    if not player:
        player = get_player(user)
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
    save_players(players)

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

    match = re.match(
        r"^برداشت\s+(\d+)$",
        message.text.strip()
    )

    if not match:
        return

    amount = int(
        match.group(1)
    )

    if amount <= 0:
        await message.reply_text(
            "❌ مبلغ نامعتبر است."
        )
        return

    players = load_players()
    uid = str(user.id)

    player = players.get(uid)

    if not player:
        player = get_player(user)
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
    save_players(players)

    await message.reply_text(
        "✅ برداشت انجام شد.\n\n"
        f"📤 مبلغ: ${amount:,}\n"
        f"💵 نقد: ${player['cash']:,}\n"
        f"🏦 بانک: ${player['bank_balance']:,}"
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

    total_players = len(players)

    total_cash = sum(
        int(p.get("cash", 0))
        for p in players.values()
    )

    total_bank = sum(
        int(p.get("bank_balance", 0))
        for p in players.values()
    )

    text = (
        "👑 MASTER CONTROL\n\n"
        f"💵 نقد Master: ${player['cash']:,}\n"
        f"🏦 بانک Master: ${player['bank_balance']:,}\n\n"
        f"👥 بازیکنان: {total_players}\n"
        f"💵 نقد کل بازیکنان: ${total_cash:,}\n"
        f"🏦 بانک کل بازیکنان: ${total_bank:,}\n\n"
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
        reply_markup=InlineKeyboardMarkup(keyboard)
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
            if player.get("banned", False)
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
            f"{status} {player.get('name', 'Player')}\n"
            f"🆔 {uid} | {username_text}\n"
            f"💰 ${player.get('cash', 0) + player.get('bank_balance', 0):,}\n"
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

    total_players = len(players)

    banned = sum(
        1
        for p in players.values()
        if p.get("banned", False)
    )

    total_cash = sum(
        p.get("cash", 0)
        for p in players.values()
    )

    total_bank = sum(
        p.get("bank_balance", 0)
        for p in players.values()
    )

    total_properties = sum(
        len(p.get("properties", []))
        for p in players.values()
    )

    total_vehicles = sum(
        len(p.get("vehicles", []))
        for p in players.values()
    )

    total_businesses = sum(
        len(p.get("businesses", []))
        for p in players.values()
    )

    text = (
        "📊 آمار UNDERCITY\n\n"
        f"👥 بازیکنان: {total_players}\n"
        f"🚫 Ban شده: {banned}\n\n"
        f"💵 پول نقد بازیکنان: ${total_cash:,}\n"
        f"🏦 پول بانک بازیکنان: ${total_bank:,}\n\n"
        f"🏠 املاک: {total_properties}\n"
        f"🚗 خودروها: {total_vehicles}\n"
        f"🏢 کسب‌وکارها: {total_businesses}"
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

    argument = argument.strip()

    if argument.isdigit():
        return argument

    uid, _ = find_by_username(
        argument
    )

    return uid


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

    if target_id == str(MASTER_USER_ID):

        await update.message.reply_text(
            "❌ Master را نمی‌توان Ban کرد."
        )

        return

    reason = (
        " ".join(context.args[1:])
        if len(context.args) > 1
        else "تخلف از قوانین"
    )

    players[target_id]["banned"] = True
    players[target_id]["ban_reason"] = reason

    save_players(players)

    await update.message.reply_text(
        "🚫 بازیکن Ban شد.\n\n"
        f"🆔 {target_id}\n"
        f"📌 دلیل: {reason}"
    )


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

    players[target_id]["banned"] = False
    players[target_id]["ban_reason"] = ""

    save_players(players)

    await update.message.reply_text(
        f"✅ Ban بازیکن {target_id} برداشته شد."
    )


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

    if not target_id:

        await update.message.reply_text(
            "❌ بازیکن پیدا نشد."
        )

        return

    try:
        amount = int(
            context.args[1]
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

    if target_id == str(MASTER_USER_ID):

        await update.message.reply_text(
            "❌ نمی‌توان Master را جریمه کرد."
        )

        return

    players = load_players()

    if target_id not in players:

        await update.message.reply_text(
            "❌ بازیکن پیدا نشد."
        )

        return

    player = players[target_id]

    # First remove from bank
    bank_taken = min(
        player.get("bank_balance", 0),
        amount
    )

    remaining = amount - bank_taken

    cash_taken = min(
        player.get("cash", 0),
        remaining
    )

    total_taken = (
        bank_taken +
        cash_taken
    )

    player["bank_balance"] -= bank_taken
    player["cash"] -= cash_taken

    add_transaction(
        player,
        "fine",
        total_taken,
        "جریمه توسط Master"
    )

    players[target_id] = player

    # Fine goes to Master
    master = players.get(
        str(MASTER_USER_ID)
    )

    if master:

        master["bank_balance"] += total_taken

        add_transaction(
            master,
            "fine_received",
            total_taken,
            f"دریافت جریمه از {player.get('name', 'Player')}"
        )

        players[str(MASTER_USER_ID)] = master

    save_players(players)

    await update.message.reply_text(
        "💸 جریمه اعمال شد.\n\n"
        f"👤 بازیکن: {player.get('name', 'Player')}\n"
        f"💰 مبلغ واقعی برداشت‌شده: ${total_taken:,}\n"
        f"🏦 از بانک: ${bank_taken:,}\n"
        f"💵 از نقد: ${cash_taken:,}"
    )


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
            context.args[1]
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

    old = players[target_id]["cash"]

    players[target_id]["cash"] = amount

    save_players(players)

    await update.message.reply_text(
        "✅ موجودی نقدی تغییر کرد.\n\n"
        f"قبل: ${old:,}\n"
        f"بعد: ${amount:,}"
    )


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
            context.args[1]
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

    old = players[target_id]["bank_balance"]

    players[target_id]["bank_balance"] = amount

    save_players(players)

    await update.message.reply_text(
        "✅ موجودی بانک تغییر کرد.\n\n"
        f"قبل: ${old:,}\n"
        f"بعد: ${amount:,}"
    )


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

    p = players[target_id]

    username = p.get(
        "username",
        ""
    )

    await update.message.reply_text(
        "👤 اطلاعات بازیکن\n\n"
        f"نام: {p.get('name', '-')}\n"
        f"Username: @{username if username else '-'}\n"
        f"🆔 ID: {target_id}\n\n"
        f"💵 نقد: ${p.get('cash', 0):,}\n"
        f"🏦 بانک: ${p.get('bank_balance', 0):,}\n"
        f"⭐ Level: {p.get('level', 1)}\n"
        f"🚫 Ban: {'بله' if p.get('banned', False) else 'خیر'}\n"
        f"📌 دلیل Ban: {p.get('ban_reason', '-')}"
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

    # -----------------------------------------
    # SECURITY
    # -----------------------------------------

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

    # -----------------------------------------
    # Main
    # -----------------------------------------

    if action == "main":

        await query.edit_message_text(
            "🏙️ منوی اصلی UNDERCITY",
            reply_markup=main_menu(user.id)
        )

    # -----------------------------------------
    # Profile
    # -----------------------------------------

    elif action == "profile":

        await show_profile(
            query,
            user
        )

    # -----------------------------------------
    # Wallet
    # -----------------------------------------

    elif action == "wallet":

        await show_wallet(
            query,
            user
        )

    # -----------------------------------------
    # Cash
    # -----------------------------------------

    elif action == "cash":

        await show_cash(
            query,
            user
        )

    # -----------------------------------------
    # Bank
    # -----------------------------------------

    elif action == "bank":

        await show_bank(
            query,
            user
        )

    # -----------------------------------------
    # Transactions
    # -----------------------------------------

    elif action == "transactions":

        await show_transactions(
            query,
            user
        )

    # -----------------------------------------
    # Transfer
    # -----------------------------------------

    elif action == "transfer":

        await show_transfer(
            query,
            user
        )

    # -----------------------------------------
    # Deposit
    # -----------------------------------------

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

    # -----------------------------------------
    # Withdraw
    # -----------------------------------------

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

    # -----------------------------------------
    # Master
    # -----------------------------------------

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

    elif action == "master_stats":

        await master_stats(
            query,
            user
        )

    # -----------------------------------------
    # Other game sections
    # -----------------------------------------

    elif action in (
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

        names = {
            "city": "🏙️ شهر",
            "properties": "🏠 املاک",
            "vehicles": "🚗 وسایل نقلیه",
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

    text = update.message.text.strip()

    # Transfer
    if text.startswith("انتقال پول"):

        await transfer_money(
            update,
            context
        )

        return

    # Deposit
    if text.startswith("واریز"):

        await deposit_command(
            update,
            context
        )

        return

    # Withdraw
    if text.startswith("برداشت"):

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

    # Basic
    app.add_handler(
        CommandHandler(
            "start",
            start
        )
    )

    # Master commands
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

    # Buttons
    app.add_handler(
        CallbackQueryHandler(
            button_handler
        )
    )

    # Text commands
    app.add_handler(
        MessageHandler(
            filters.TEXT
            & ~filters.COMMAND,
            text_handler
        )
    )

    print("================================")
    print("UNDERCITY BOT IS RUNNING")
    print(f"MASTER ID: {MASTER_USER_ID}")
    print("================================")

    app.run_polling()


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":
    main()
