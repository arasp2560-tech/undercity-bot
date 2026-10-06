import os
import json
import re
import threading
import uuid
import random
import time
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
    os.environ.get("MASTER_USER_ID", "5750241558")
)

MASTER_CASH = 10_000_000_000_000
MASTER_BANK = 10_000_000_000_000

DATA_LOCK = threading.RLock()


# =========================================================
# VEHICLE CATALOG
# =========================================================

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
        "tuning": "فابریک",
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
        "tuning": "فابریک",
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
        "tuning": "فابریک",
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
        "tuning": "فابریک",
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
        "tuning": "فابریک",
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
        "tuning": "Nismo",
    },
}


# =========================================================
# BODY SYSTEM
# =========================================================

BODY_PARTS = {

    "سر": {
        "max_hp": 100,
        "armor": "head",
    },

    "صورت": {
        "max_hp": 100,
        "armor": "head",
    },

    "سینه": {
        "max_hp": 100,
        "armor": "chest",
    },

    "شکم": {
        "max_hp": 100,
        "armor": "chest",
    },

    "دست راست": {
        "max_hp": 100,
        "armor": "arms",
    },

    "دست چپ": {
        "max_hp": 100,
        "armor": "arms",
    },

    "شانه راست": {
        "max_hp": 100,
        "armor": "arms",
    },

    "شانه چپ": {
        "max_hp": 100,
        "armor": "arms",
    },

    "پای راست": {
        "max_hp": 100,
        "armor": "legs",
    },

    "پای چپ": {
        "max_hp": 100,
        "armor": "legs",
    },
}


# =========================================================
# ATTACKS
# =========================================================

ATTACKS = {

    "مشت": {
        "min": 6,
        "max": 14,
        "accuracy": 85,
        "xp": 5,
    },

    "لگد": {
        "min": 8,
        "max": 18,
        "accuracy": 75,
        "xp": 7,
    },

    "ضربه": {
        "min": 5,
        "max": 12,
        "accuracy": 90,
        "xp": 5,
    },

    "سیلی": {
        "min": 3,
        "max": 8,
        "accuracy": 95,
        "xp": 3,
    },

    "چاقو": {
        "min": 14,
        "max": 25,
        "accuracy": 70,
        "xp": 12,
        "level": 5,
    },
}


# =========================================================
# JOBS
# =========================================================

JOBS = {

    "barber": {

        "name": "💇 آرایشگری",

        "ranks": [
            "کارآموز",
            "مبتدی",
            "متوسط",
            "ماهر",
            "حرفه‌ای",
        ],

        "base_income": 70,
        "base_xp": 25,
        "duration": 15,

        "customers": {
            0: (1, 2),
            1: (2, 4),
            2: (3, 6),
            3: (5, 8),
            4: (7, 12),
        },
    },

    "mechanic": {

        "name": "🔧 مکانیکی",

        "ranks": [
            "کارآموز",
            "مبتدی",
            "متوسط",
            "ماهر",
            "حرفه‌ای",
        ],

        "base_income": 110,
        "base_xp": 35,
        "duration": 20,

        "customers": {
            0: (1, 2),
            1: (2, 4),
            2: (3, 6),
            3: (5, 9),
            4: (7, 13),
        },
    },
}


# =========================================================
# EQUIPMENT
# =========================================================

EQUIPMENT = {

    "normal_clothes": {
        "name": "👕 لباس معمولی",
        "price": 0,
        "level": 1,
        "protection": {
            "head": 0,
            "chest": 0,
            "arms": 0,
            "legs": 0,
        },
    },

    "leather_jacket": {
        "name": "🧥 کت چرمی",
        "price": 2_000_000,
        "level": 2,
        "protection": {
            "head": 0,
            "chest": 8,
            "arms": 5,
            "legs": 0,
        },
    },

    "body_armor": {
        "name": "🦺 جلیقه محافظ",
        "price": 15_000_000,
        "level": 3,
        "protection": {
            "head": 0,
            "chest": 35,
            "arms": 15,
            "legs": 5,
        },
    },

    "helmet": {
        "name": "⛑️ کلاه محافظ",
        "price": 7_000_000,
        "level": 4,
        "protection": {
            "head": 40,
            "chest": 0,
            "arms": 0,
            "legs": 0,
        },
    },

    "knife": {
        "name": "🔪 چاقو",
        "price": 10_000_000,
        "level": 5,
        "weapon": True,
    },
}


# =========================================================
# HEALTH SERVER
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

    with DATA_LOCK:

        try:

            with open(
                PLAYERS_FILE,
                "r",
                encoding="utf-8"
            ) as file:

                data = json.load(file)

                if isinstance(data, dict):
                    return data

        except (
            FileNotFoundError,
            json.JSONDecodeError,
            OSError,
        ):
            pass

        return {}


def save_players(players):

    with DATA_LOCK:

        temp_file = PLAYERS_FILE + ".tmp"

        with open(
            temp_file,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                players,
                file,
                ensure_ascii=False,
                indent=2
            )

        os.replace(
            temp_file,
            PLAYERS_FILE
        )


# =========================================================
# GENERAL HELPERS
# =========================================================

def normalize_digits(text):

    if not text:
        return ""

    table = str.maketrans(
        "۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩",
        "01234567890123456789"
    )

    return str(text).translate(table)


def parse_amount(value):

    try:

        value = normalize_digits(
            str(value)
        )

        value = (
            value
            .replace(",", "")
            .replace("_", "")
            .replace("٬", "")
            .strip()
        )

        return int(value)

    except Exception:
        return 0


def is_master(user_id):

    try:
        return int(user_id) == MASTER_USER_ID
    except Exception:
        return False


def make_id(prefix="ID"):

    return (
        f"{prefix}-"
        f"{uuid.uuid4().hex[:12].upper()}"
    )


def timestamp():

    return int(time.time())


def xp_required(level):

    return 100 + ((level - 1) * 75)


def add_xp(player, amount):

    amount = max(0, int(amount))

    player["xp"] = (
        player.get("xp", 0)
        + amount
    )

    level_ups = 0

    while (
        player["xp"]
        >= xp_required(player.get("level", 1))
    ):

        required = xp_required(
            player.get("level", 1)
        )

        player["xp"] -= required

        player["level"] = (
            player.get("level", 1) + 1
        )

        level_ups += 1

    return level_ups


def default_body():

    body = {}

    for part, data in BODY_PARTS.items():

        body[part] = {
            "hp": data["max_hp"],
            "max_hp": data["max_hp"],
            "injury": None,
            "bleeding": False,
            "fracture": False,
            "dislocated": False,
        }

    return body


# =========================================================
# TRANSACTIONS
# =========================================================

def add_transaction(
    player,
    tx_type,
    amount,
    description,
    tx_id=None,
    direction=None,
):

    player.setdefault(
        "transactions",
        []
    )

    tx_id = tx_id or make_id("TX")

    for old in player["transactions"]:

        if old.get("id") == tx_id:
            return False

    if direction is None:

        incoming = {
            "transfer_received",
            "deposit",
            "sale_received",
            "vehicle_received",
            "job_income",
            "fine_received",
        }

        direction = (
            "in"
            if tx_type in incoming
            else "out"
        )

    player["transactions"].append({

        "id": tx_id,

        "type": tx_type,

        "amount": int(amount),

        "description": description,

        "direction": direction,

        "time": timestamp(),
    })

    player["transactions"] = (
        player["transactions"][-100:]
    )

    return True


# =========================================================
# PLAYER CREATION
# =========================================================

def create_player(user):

    master = is_master(user.id)

    return {

        "name": (
            user.first_name
            or "Player"
        ),

        "username": (
            user.username
            or ""
        ),

        "level": 1,

        "xp": 0,

        "cash": (
            MASTER_CASH
            if master
            else 10_000
        ),

        "bank_balance": (
            MASTER_BANK
            if master
            else 0
        ),

        "credit_score": 500,

        "reputation": 0,

        "banned": False,

        "ban_reason": "",

        "transactions": [],

        "location": "پایین‌شهر",

        "home": {
            "type": "اتاق اجاره‌ای",
            "name": "اتاق کوچک پایین‌شهر",
            "rent": 200,
        },

        "properties": [],

        "vehicles": [],

        "businesses": [],

        "body": default_body(),

        "equipment": {
            "clothes": "normal_clothes",
            "armor": None,
            "weapons": [],
        },

        "jobs": {},

        "job_stats": {},

        "injuries": [],

        "vehicle_offers": [],

        "market_listings": [],

        "auctions": [],

        "stats": {
            "fights": 0,
            "hits": 0,
            "damage_dealt": 0,
            "damage_received": 0,
            "vehicles_bought": 0,
            "vehicles_sold": 0,
            "jobs_done": 0,
        },

        "pending_purchase": None,

        "pending_action": None,

        "last_actions": {},
    }


def normalize_player(player, user=None):

    if not isinstance(player, dict):
        player = {}

    if user:

        player["name"] = (
            user.first_name
            or player.get("name")
            or "Player"
        )

        player["username"] = (
            user.username
            or player.get("username")
            or ""
        )

        player["user_id"] = int(
            user.id
        )

    player.setdefault(
        "name",
        "Player"
    )

    player.setdefault(
        "username",
        ""
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
        "cash",
        10000
    )

    player.setdefault(
        "bank_balance",
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
        "banned",
        False
    )

    player.setdefault(
        "ban_reason",
        ""
    )

    player.setdefault(
        "loan",
        0
    )

    for key in (
        "transactions",
        "vehicles",
        "properties",
        "businesses",
        "vehicle_offers",
        "market_listings",
        "auctions",
        "direct_deals",
        "vehicle_history",
    ):
        if not isinstance(
            player.get(key),
            list
        ):
            player[key] = []

    for key in (
        "body",
        "equipment",
        "jobs",
        "stats",
        "last_actions",
    ):
        if not isinstance(
            player.get(key),
            dict
        ):
            player[key] = {}

    if "pending_action" not in player:
        player["pending_action"] = None

    if "pending_purchase" not in player:
        player["pending_purchase"] = None

    try:
        player["body"] = ensure_body_parts(
            player.get("body")
        )
    except Exception:
        try:
            player["body"] = default_body()
        except Exception:
            player["body"] = {}

    player["equipment"].setdefault(
        "clothing",
        []
    )

    player["equipment"].setdefault(
        "armor",
        []
    )

    player["equipment"].setdefault(
        "weapons",
        []
    )

    for job_id in (
        "barber",
        "mechanic",
    ):
        if not isinstance(
            player["jobs"].get(job_id),
            dict
        ):
            player["jobs"][job_id] = {
                "xp": 0,
                "sessions": 0,
                "rank": "apprentice",
            }

    for key in (
        "fights",
        "hits",
        "wins",
        "losses",
        "damage_dealt",
        "damage_received",
        "vehicles_bought",
        "vehicles_sold",
        "jobs_done",
        "money_sent",
        "money_received",
    ):
        player["stats"].setdefault(
            key,
            0
        )

    return player
       # ============================================================
# PART 2
# START / HELP / PROFILE / WALLET / MONEY TRANSFER
# ============================================================


# ============================================================
# START / WELCOME
# ============================================================

async def start_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    user = update.effective_user

    if not user:
        return

    player = get_player(user)

    if player.get("banned"):
        reason = player.get(
            "ban_reason",
            "بدون توضیح",
        )

        await update.message.reply_text(
            "🚫 حساب شما مسدود است.\n\n"
            f"دلیل: {reason}"
        )

        return

    name = player.get(
        "name",
        user.first_name or "بازیکن",
    )

    if is_master(user.id):

        title = "👑 MASTER"

    else:

        title = "🏙️ UNDERCITY"

    text = (
        f"{title}\n\n"
        f"درود {name} 👋\n\n"
        "به دنیای UNDERCITY خوش آمدی.\n\n"
        "اینجا شهری است که در آن می‌توانی "
        "پول به دست بیاوری، شغل داشته باشی، "
        "خانه و خودرو بخری، تجارت کنی، "
        "با بازیکنان دیگر وارد درگیری شوی "
        "و شخصیت خودت را توسعه بدهی.\n\n"
        "💡 برای ورود به منوی اصلی، یکی از این "
        "دستورها را بفرست:\n\n"
        "• منو\n"
        "• menu\n\n"
        "📖 برای آموزش کامل بازی:\n"
        "• /help\n\n"
        "⚠️ توجه:\n"
        "دستور /start فقط صفحه خوش‌آمدگویی را "
        "نمایش می‌دهد و منوی اصلی را باز نمی‌کند."
    )

    await update.message.reply_text(text)


# ============================================================
# MAIN MENU COMMAND
# ============================================================

async def menu_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    user = update.effective_user

    if not user:
        return

    player = get_player(user)

    if player.get("banned"):

        await update.message.reply_text(
            "🚫 حساب شما مسدود است."
        )

        return

    await update.message.reply_text(
        "🏙️ منوی اصلی UNDERCITY\n\n"
        "یکی از بخش‌های زیر را انتخاب کن:",
        reply_markup=main_menu(
            user.id,
            is_master(user.id),
        ),
    )


# ============================================================
# HELP SYSTEM
# ============================================================

HELP_PAGES = [

    {
        "title": "🏙️ UNDERCITY چیست؟",
        "text": (
            "UNDERCITY یک بازی شهری و اقتصادی است.\n\n"
            "تو یک شخصیت داری و می‌توانی در شهر "
            "زندگی کنی، پول دربیاوری، شغل داشته باشی، "
            "خودرو بخری، ملک داشته باشی و با دیگر "
            "بازیکنان تعامل کنی.\n\n"
            "هر بازیکن دارای سطح، XP، پول نقد، "
            "حساب بانکی، اعتبار، شهرت، سلامتی و "
            "دارایی‌های مختلف است.\n\n"
            "بخش زیادی از امکانات بازی به مرور و با "
            "افزایش سطح باز می‌شوند."
        ),
    },

    {
        "title": "💰 پول و بانک",
        "text": (
            "💵 پول نقد:\n"
            "برای بعضی خریدها و فعالیت‌ها استفاده می‌شود.\n\n"
            "🏦 بانک:\n"
            "موجودی امن حساب بانکی توست.\n\n"
            "دستورهای مهم:\n"
            "• منو\n"
            "• کیف پول\n"
            "• واریز\n"
            "• برداشت\n"
            "• انتقال پول\n"
            "• تراکنش‌ها\n\n"
            "برای انتقال پول می‌توانی از طریق شناسه "
            "کاربر یا با Reply به پیام او اقدام کنی."
        ),
    },

    {
        "title": "💸 انتقال پول",
        "text": (
            "برای انتقال پول به بازیکن دیگر می‌توانی "
            "پیام او را Reply کنی و بنویسی:\n\n"
            "انتقال پول 50000\n\n"
            "یا با نام کاربری:\n\n"
            "انتقال پول 50000 به @username\n\n"
            "انتقال فقط زمانی انجام می‌شود که:\n"
            "1️⃣ موجودی کافی داشته باشی.\n"
            "2️⃣ مقصد معتبر باشد.\n"
            "3️⃣ فرستنده و گیرنده یک نفر نباشند.\n\n"
            "سیستم قبل از انجام انتقال موجودی را بررسی "
            "می‌کند و تراکنش برای هر دو طرف ثبت می‌شود."
        ),
    },

    {
        "title": "🚗 خودرو",
        "text": (
            "در UNDERCITY می‌توانی خودرو بخری، "
            "نگهداری کنی و به بازیکنان دیگر بفروشی.\n\n"
            "بخش خودرو شامل:\n"
            "• نمایشگاه\n"
            "• گاراژ\n"
            "• بازار خودرو\n"
            "• پیشنهاد خرید\n"
            "• فروش خودرو\n"
            "• انتقال خودرو\n"
            "• مزایده\n\n"
            "هر خودرو دارای شناسه اختصاصی است تا "
            "از انتقال یا فروش دوباره جلوگیری شود."
        ),
    },

    {
        "title": "🤝 معامله خودرو",
        "text": (
            "در معاملات بازیکن‌به‌بازیکن، مالک خودرو "
            "می‌تواند خودرو را برای فروش قرار دهد.\n\n"
            "خریدار قیمت پیشنهادی خود را ارسال می‌کند.\n\n"
            "فروشنده می‌تواند:\n"
            "✅ قبول کند\n"
            "❌ رد کند\n\n"
            "در صورت قبول:\n"
            "• پول از خریدار کم می‌شود.\n"
            "• پول به فروشنده می‌رسد.\n"
            "• مالکیت خودرو تغییر می‌کند.\n"
            "• تراکنش برای هر دو طرف ثبت می‌شود.\n\n"
            "تمام این مراحل به‌صورت یک عملیات واحد "
            "انجام می‌شوند تا پرداخت یا انتقال دوباره "
            "اتفاق نیفتد."
        ),
    },

    {
        "title": "⚔️ مبارزه",
        "text": (
            "برای مبارزه با بازیکن دیگر، ابتدا به "
            "پیام او Reply کن و بنویس:\n\n"
            "ریپ\n\n"
            "سپس قسمت‌های مختلف بدن برای حمله "
            "نمایش داده می‌شوند.\n\n"
            "هر قسمت آسیب متفاوتی دارد.\n\n"
            "نمونه:\n"
            "🥊 مشت به شانه\n"
            "آسیب: ۱۰\n\n"
            "طرف مقابل نیز اعلان دریافت می‌کند "
            "که چه کسی و به کدام قسمت بدن او "
            "آسیب زده است."
        ),
    },

    {
        "title": "🩸 آسیب و سلامتی",
        "text": (
            "بدن شخصیت چند بخش دارد؛ از جمله:\n\n"
            "🧠 سر\n"
            "😶 صورت\n"
            "🫁 سینه\n"
            "🫃 شکم\n"
            "💪 دست راست\n"
            "💪 دست چپ\n"
            "🦵 پای راست\n"
            "🦵 پای چپ\n"
            "🔹 شانه‌ها\n\n"
            "آسیب می‌تواند باعث ایجاد:\n"
            "• کبودی\n"
            "• زخم\n"
            "• خونریزی\n"
            "• دررفتگی\n"
            "• شکستگی\n\n"
            "لباس و تجهیزات دفاعی می‌توانند در آینده "
            "آسیب وارده به قسمت محافظت‌شده را کاهش دهند."
        ),
    },

    {
        "title": "🏥 درمان",
        "text": (
            "اگر آسیب ببینی، وضعیت بدنت در پروفایل "
            "ثبت می‌شود.\n\n"
            "کلینیک برای درمان آسیب‌ها استفاده می‌شود.\n\n"
            "بعضی آسیب‌ها ارزان و سریع درمان می‌شوند، "
            "اما آسیب‌های جدی‌تر ممکن است هزینه و "
            "زمان بیشتری نیاز داشته باشند.\n\n"
            "سلامت کامل با HP شخصیت نیز ارتباط دارد."
        ),
    },

    {
        "title": "💼 شغل",
        "text": (
            "می‌توانی در شهر شغل داشته باشی.\n\n"
            "نمونه شغل‌ها:\n"
            "💈 آرایشگر\n"
            "🔧 مکانیک\n\n"
            "هر شغل دارای رتبه است:\n\n"
            "1️⃣ کارآموز\n"
            "2️⃣ مبتدی\n"
            "3️⃣ متوسط\n"
            "4️⃣ ماهر\n"
            "5️⃣ حرفه‌ای / استاد\n\n"
            "با آموزش، تمرین و انجام کارهای بیشتر "
            "می‌توانی رتبه خودت را افزایش بدهی."
        ),
    },

    {
        "title": "📈 XP و Level",
        "text": (
            "فعالیت‌های مختلف XP می‌دهند.\n\n"
            "مانند:\n"
            "• کار کردن\n"
            "• آموزش\n"
            "• فعالیت‌های شهری\n"
            "• مبارزه\n"
            "• بعضی معاملات و فعالیت‌های خاص\n\n"
            "با افزایش XP، Level بالا می‌رود.\n\n"
            "سطح بالاتر می‌تواند امکانات، تجهیزات "
            "و فعالیت‌های جدیدی را باز کند."
        ),
    },

    {
        "title": "🔪 تجهیزات",
        "text": (
            "تجهیزات شخصیت به‌مرور باز می‌شوند.\n\n"
            "بعضی آیتم‌ها از ابتدا قابل استفاده نیستند "
            "و برای دریافت آنها باید سطح مشخصی داشته باشی.\n\n"
            "تجهیزات می‌توانند روی مبارزه، دفاع، "
            "سلامت یا فعالیت‌های دیگر اثر بگذارند.\n\n"
            "مثلاً بعضی تجهیزات تهاجمی در Levelهای "
            "بالاتر قابل استفاده خواهند بود."
        ),
    },

    {
        "title": "🏠 ملک و زندگی",
        "text": (
            "املاک یکی از بخش‌های اقتصادی بازی هستند.\n\n"
            "می‌توانی در آینده خانه، ملک تجاری و "
            "دارایی‌های دیگر داشته باشی.\n\n"
            "ملک می‌تواند برای زندگی، کسب‌وکار یا "
            "سرمایه‌گذاری استفاده شود."
        ),
    },

    {
        "title": "🏪 کسب‌وکار",
        "text": (
            "در بخش کسب‌وکار می‌توانی فعالیت اقتصادی "
            "راه‌اندازی کنی.\n\n"
            "کسب‌وکارها می‌توانند درآمد ایجاد کنند "
            "اما ممکن است هزینه، مشتری، ریسک یا "
            "ضرر نیز داشته باشند.\n\n"
            "هدف این است که کسب‌وکارت را توسعه بدهی "
            "و درآمد بیشتری ایجاد کنی."
        ),
    },

    {
        "title": "🏆 پیشرفت",
        "text": (
            "در UNDERCITY فقط مقدار پول مهم نیست.\n\n"
            "مواردی مثل:\n"
            "• Level\n"
            "• XP\n"
            "• اعتبار\n"
            "• شهرت\n"
            "• مهارت شغلی\n"
            "• تجهیزات\n"
            "• خودرو\n"
            "• ملک\n"
            "• کسب‌وکار\n\n"
            "همگی بخشی از پیشرفت شخصیت هستند."
        ),
    },

]


def help_keyboard(
    user_id,
    page,
):

    total = len(HELP_PAGES)

    buttons = []

    navigation = []

    if page > 0:

        navigation.append(
            InlineKeyboardButton(
                "⬅️ قبلی",
                callback_data=(
                    f"help|{page - 1}|{user_id}"
                ),
            )
        )

    navigation.append(
        InlineKeyboardButton(
            f"📖 {page + 1}/{total}",
            callback_data=(
                f"help|noop|{user_id}"
            ),
        )
    )

    if page < total - 1:

        navigation.append(
            InlineKeyboardButton(
                "بعدی ➡️",
                callback_data=(
                    f"help|{page + 1}|{user_id}"
                ),
            )
        )

    buttons.append(navigation)

    buttons.append(
        [
            InlineKeyboardButton(
                "🏙️ منوی اصلی",
                callback_data=(
                    f"main|{user_id}"
                ),
            )
        ]
    )

    return InlineKeyboardMarkup(buttons)


def help_page_text(page):

    data = HELP_PAGES[page]

    return (
        f"{data['title']}\n\n"
        f"{data['text']}\n\n"
        "━━━━━━━━━━━━━━\n"
        f"صفحه {page + 1} از {len(HELP_PAGES)}"
    )


async def help_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    user = update.effective_user

    if not user:
        return

    player = get_player(user)

    if player.get("banned"):

        await update.message.reply_text(
            "🚫 حساب شما مسدود است."
        )

        return

    await update.message.reply_text(
        help_page_text(0),
        reply_markup=help_keyboard(
            user.id,
            0,
        ),
    )


# ============================================================
# PROFILE
# ============================================================

def profile_text(player):

    name = player.get(
        "name",
        "بازیکن",
    )

    username = player.get(
        "username",
        "",
    )

    if username:

        username_text = f"@{username}"

    else:

        username_text = "ندارد"

    level = player.get(
        "level",
        1,
    )

    xp = player.get(
        "xp",
        0,
    )

    next_xp = xp_required(level)

    cash = player.get(
        "cash",
        0,
    )

    bank = player.get(
        "bank_balance",
        0,
    )

    reputation = player.get(
        "reputation",
        0,
    )

    credit = player.get(
        "credit_score",
        0,
    )

    body = player.get(
        "body",
        {},
    )

    hp = body.get(
        "hp",
        100,
    )

    max_hp = body.get(
        "max_hp",
        100,
    )

    vehicles = player.get(
        "vehicles",
        [],
    )

    properties = player.get(
        "properties",
        [],
    )

    businesses = player.get(
        "businesses",
        [],
    )

    jobs = player.get(
        "jobs",
        {},
    )

    return (
        "👤 پروفایل شخصیت\n\n"
        f"🪪 نام: {name}\n"
        f"🔹 Username: {username_text}\n\n"
        f"⭐ Level: {level}\n"
        f"📈 XP: {xp:,} / {next_xp:,}\n\n"
        f"❤️ سلامت: {hp} / {max_hp}\n"
        f"💵 پول نقد: {cash:,}\n"
        f"🏦 بانک: {bank:,}\n"
        f"💳 اعتبار: {credit}\n"
        f"⭐ شهرت: {reputation}\n\n"
        f"🚗 خودروها: {len(vehicles)}\n"
        f"🏠 املاک: {len(properties)}\n"
        f"🏪 کسب‌وکارها: {len(businesses)}\n"
        f"💼 شغل‌ها: {len(jobs)}"
    )


async def show_profile(
    update,
    user_id,
):

    user = update.effective_user

    if not user:
        return

    if user.id != user_id:
        return

    player = get_player(user)

    if update.callback_query:

        await update.callback_query.edit_message_text(
            profile_text(player),
            reply_markup=back_button(
                user.id,
                "main",
            ),
        )

    else:

        await update.message.reply_text(
            profile_text(player),
            reply_markup=back_button(
                user.id,
                "main",
            ),
        )


# ============================================================
# WALLET
# ============================================================

def wallet_text(player):

    cash = player.get(
        "cash",
        0,
    )

    bank = player.get(
        "bank_balance",
        0,
    )

    total = cash + bank

    return (
        "💰 کیف پول\n\n"
        f"💵 پول نقد:\n"
        f"{cash:,}\n\n"
        f"🏦 موجودی بانک:\n"
        f"{bank:,}\n\n"
        f"💎 دارایی نقدی:\n"
        f"{total:,}"
    )


async def show_wallet(
    update,
    user_id,
):

    user = update.effective_user

    if not user:
        return

    if user.id != user_id:
        return

    player = get_player(user)

    if update.callback_query:

        await update.callback_query.edit_message_text(
            wallet_text(player),
            reply_markup=wallet_menu(
                user.id,
            ),
        )

    else:

        await update.message.reply_text(
            wallet_text(player),
            reply_markup=wallet_menu(
                user.id,
            ),
        )


# ============================================================
# TRANSACTION HISTORY
# ============================================================

def transaction_text(
    player,
    limit=15,
):

    transactions = player.get(
        "transactions",
        [],
    )

    if not transactions:

        return (
            "📜 تاریخچه تراکنش‌ها\n\n"
            "هنوز تراکنشی ثبت نشده است."
        )

    lines = [
        "📜 تاریخچه تراکنش‌ها",
        "",
    ]

    for transaction in reversed(
        transactions[-limit:]
    ):

        tx_type = transaction.get(
            "type",
            "unknown",
        )

        description = transaction.get(
            "description",
            "",
        )

        amount = transaction.get(
            "amount",
            0,
        )

        direction = transaction.get(
            "direction",
            "info",
        )

        if direction == "in":

            icon = "🟢"

            amount_text = (
                f"+{amount:,}"
            )

        elif direction == "out":

            icon = "🔴"

            amount_text = (
                f"-{amount:,}"
            )

        else:

            icon = "⚪"

            amount_text = (
                f"{amount:,}"
            )

        lines.append(
            f"{icon} {amount_text}"
        )

        if description:

            lines.append(
                f"   {description}"
            )

        if tx_type:

            lines.append(
                f"   نوع: {tx_type}"
            )

        lines.append("")

    return "\n".join(lines)


async def show_transactions(
    update,
    user_id,
):

    user = update.effective_user

    if not user:
        return

    if user.id != user_id:
        return

    player = get_player(user)

    await update.callback_query.edit_message_text(
        transaction_text(player),
        reply_markup=back_button(
            user.id,
            "wallet",
        ),
    )


# ============================================================
# MONEY OPERATION HELPERS
# ============================================================

def can_spend(
    player,
    amount,
    source="bank",
):

    amount = int(amount)

    if amount <= 0:
        return False

    if source == "cash":

        return (
            player.get(
                "cash",
                0,
            ) >= amount
        )

    return (
        player.get(
            "bank_balance",
            0,
        ) >= amount
    )


def spend_money(
    player,
    amount,
    source="bank",
):

    amount = int(amount)

    if amount <= 0:
        return False

    if not can_spend(
        player,
        amount,
        source,
    ):

        return False

    if source == "cash":

        player["cash"] -= amount

    else:

        player["bank_balance"] -= amount

    return True


def add_money(
    player,
    amount,
    destination="bank",
):

    amount = int(amount)

    if amount <= 0:
        return False

    if destination == "cash":

        player["cash"] = (
            player.get(
                "cash",
                0,
            )
            + amount
        )

    else:

        player["bank_balance"] = (
            player.get(
                "bank_balance",
                0,
            )
            + amount
        )

    return True


# ============================================================
# DEPOSIT
# ============================================================

async def deposit_money(
    update,
    amount,
):

    user = update.effective_user

    if not user:
        return

    player = get_player(user)

    amount = int(amount)

    if amount <= 0:

        await update.message.reply_text(
            "❌ مبلغ باید بیشتر از صفر باشد."
        )

        return

    if player.get(
        "cash",
        0,
    ) < amount:

        await update.message.reply_text(
            "❌ پول نقد کافی نیست."
        )

        return

    player["cash"] -= amount

    player["bank_balance"] = (
        player.get(
            "bank_balance",
            0,
        )
        + amount
    )

    add_transaction(
        player,
        "deposit",
        amount,
        "واریز پول نقد به بانک",
    )

    save_players(
        load_players()
    )

    players = load_players()

    players[str(user.id)] = player

    save_players(players)

    await update.message.reply_text(
        "✅ واریز انجام شد.\n\n"
        f"💵 مبلغ: {amount:,}\n"
        f"🏦 موجودی بانک: "
        f"{player['bank_balance']:,}",
    )


# ============================================================
# WITHDRAW
# ============================================================

async def withdraw_money(
    update,
    amount,
):

    user = update.effective_user

    if not user:
        return

    player = get_player(user)

    try:
        amount = int(amount)
    except (TypeError, ValueError):
        await update.message.reply_text(
            "❌ مبلغ نامعتبر است."
        )
        return

    if amount <= 0:
        await update.message.reply_text(
            "❌ مبلغ باید بیشتر از صفر باشد."
        )
        return

    if player.get(
        "bank_balance",
        0,
    ) < amount:
        await update.message.reply_text(
            "❌ موجودی بانک کافی نیست."
        )
        return

    player["bank_balance"] = (
        player.get(
            "bank_balance",
            0,
        )
        - amount
    )

    player["cash"] = (
        player.get(
            "cash",
            0,
        )
        + amount
    )

    add_transaction(
        player,
        "withdraw",
        amount,
        "برداشت پول از بانک",
    )

    players = load_players()

    players[str(user.id)] = player

    save_players(players)

    await update.message.reply_text(
        "✅ برداشت انجام شد.\n\n"
        f"💵 مبلغ دریافت‌شده: {amount:,}\n"
        f"💵 پول نقد: {player['cash']:,}\n"
        f"🏦 بانک: {player['bank_balance']:,}",
    )

# ============================================================
# FIND TARGET FOR TRANSFER
# ============================================================

def find_transfer_target(
    players,
    sender_id,
    username=None,
    user_id=None,
):

    if user_id is not None:

        key = str(user_id)

        if key in players:

            if int(key) != int(sender_id):

                return key, players[key]

    if username:

        username = username.lstrip("@").lower()

        for key, player in players.items():

            if int(key) == int(sender_id):
                continue

            saved_username = str(
                player.get(
                    "username",
                    "",
                )
            ).lstrip("@").lower()

            if (
                saved_username
                and saved_username == username
            ):

                return key, player

    return None, None


# ============================================================
# SAFE MONEY TRANSFER
# ============================================================

def execute_money_transfer(
    sender_id,
    receiver_id,
    amount,
):

    amount = int(amount)

    if amount <= 0:
        return False, "مبلغ نامعتبر است."

    if int(sender_id) == int(receiver_id):

        return False, (
            "نمی‌توانی به خودت پول انتقال بدهی."
        )

    players = load_players()

    sender_key = str(sender_id)
    receiver_key = str(receiver_id)

    if sender_key not in players:

        return False, (
            "حساب فرستنده پیدا نشد."
        )

    if receiver_key not in players:

        return False, (
            "حساب گیرنده پیدا نشد."
        )

    sender = players[sender_key]
    receiver = players[receiver_key]

    if sender.get("banned"):

        return False, (
            "حساب فرستنده مسدود است."
        )

    if receiver.get("banned"):

        return False, (
            "حساب گیرنده مسدود است."
        )

    balance = sender.get(
        "bank_balance",
        0,
    )

    if balance < amount:

        return False, (
            "موجودی بانکی کافی نیست."
        )

    # --------------------------------------------------------
    # ایجاد شناسه یکتای عملیات
    # --------------------------------------------------------

    transfer_id = (
        "transfer_"
        + str(sender_id)
        + "_"
        + str(receiver_id)
        + "_"
        + str(amount)
        + "_"
        + uuid.uuid4().hex
    )

    # --------------------------------------------------------
    # کسر از فرستنده
    # --------------------------------------------------------

    sender["bank_balance"] -= amount

    # --------------------------------------------------------
    # اضافه به گیرنده
    # --------------------------------------------------------

    receiver["bank_balance"] = (
        receiver.get(
            "bank_balance",
            0,
        )
        + amount
    )

    # --------------------------------------------------------
    # ثبت تراکنش فرستنده
    # --------------------------------------------------------

    add_transaction(
        sender,
        "transfer_sent",
        amount,
        f"انتقال به بازیکن {receiver_id}",
        direction="out",
        reference_id=transfer_id,
    )

    # --------------------------------------------------------
    # ثبت تراکنش گیرنده
    # --------------------------------------------------------

    add_transaction(
        receiver,
        "transfer_received",
        amount,
        f"دریافت از بازیکن {sender_id}",
        direction="in",
        reference_id=transfer_id,
    )

    # --------------------------------------------------------
    # ذخیره اتمیک‌تر هر دو بازیکن
    # --------------------------------------------------------

    players[sender_key] = sender
    players[receiver_key] = receiver

    save_players(players)

    return True, {
        "transfer_id": transfer_id,
        "amount": amount,
        "sender": sender,
        "receiver": receiver,
    }


# ============================================================
# TRANSFER COMMAND PARSER
# ============================================================

def parse_transfer_command(
    text,
):

    text = normalize_digits(
        text.strip()
    )

    pattern = re.compile(
        r"^انتقال\s+پول\s+"
        r"([\d,]+)"
        r"(?:\s+به\s+@?([A-Za-z0-9_]+))?"
        r"$",
        re.IGNORECASE,
    )

    match = pattern.match(text)

    if not match:

        return None

    amount_text = (
        match.group(1)
        .replace(",", "")
    )

    try:

        amount = int(
            amount_text
        )

    except Exception:

        return None

    username = match.group(2)

    return {
        "amount": amount,
        "username": username,
    }


# ============================================================
# TRANSFER FROM REPLY
# ============================================================

async def transfer_by_reply(
    update,
    amount,
):

    user = update.effective_user

    if not user:
        return

    message = update.message

    if not message:
        return

    reply = message.reply_to_message

    if not reply:

        await message.reply_text(
            "❌ برای انتقال با Reply باید "
            "روی پیام بازیکن موردنظر Reply کنی."
        )

        return

    target_user = reply.from_user

    if not target_user:

        await message.reply_text(
            "❌ صاحب این پیام شناسایی نشد."
        )

        return

    target_id = target_user.id

    if target_id == user.id:

        await message.reply_text(
            "❌ نمی‌توانی به خودت پول بدهی."
        )

        return

    players = load_players()

    if str(target_id) not in players:

        # ساخت حساب برای کاربری که قبلاً
        # وارد بازی نشده است
        target_player = get_player(
            target_user
        )

        players = load_players()

        target_player = players.get(
            str(target_id),
            target_player,
        )

        players[str(target_id)] = (
            target_player
        )

        save_players(players)

    success, result = execute_money_transfer(
        user.id,
        target_id,
        amount,
    )

    if not success:

        await message.reply_text(
            f"❌ انتقال انجام نشد.\n\n"
            f"{result}"
        )

        return

    sender = result["sender"]
    receiver = result["receiver"]

    receiver_name = receiver.get(
        "name",
        target_user.first_name or "بازیکن",
    )

    await message.reply_text(
        "✅ انتقال با موفقیت انجام شد.\n\n"
        f"👤 گیرنده: {receiver_name}\n"
        f"💸 مبلغ: {amount:,}\n\n"
        f"🏦 موجودی شما: "
        f"{sender.get('bank_balance', 0):,}"
    )

    try:

        await context.bot.send_message(
            chat_id=target_id,
            text=(
                "💰 دریافت وجه\n\n"
                f"👤 فرستنده: "
                f"{user.first_name or 'بازیکن'}\n"
                f"💵 مبلغ دریافت‌شده: {amount:,}\n\n"
                f"🏦 موجودی بانک شما: "
                f"{receiver.get('bank_balance', 0):,}"
            ),
        )

    except Exception:

        pass


# ============================================================
# TRANSFER BY USERNAME
# ============================================================

async def transfer_by_username(
    update,
    amount,
    username,
):

    user = update.effective_user

    if not user:
        return

    players = load_players()

    target_key, target = find_transfer_target(
        players,
        user.id,
        username=username,
    )

    if not target_key:

        await update.message.reply_text(
            "❌ بازیکنی با این Username پیدا نشد."
        )

        return

    target_id = int(target_key)

    success, result = execute_money_transfer(
        user.id,
        target_id,
        amount,
    )

    if not success:

        await update.message.reply_text(
            f"❌ انتقال انجام نشد.\n\n"
            f"{result}"
        )

        return

    sender = result["sender"]
    receiver = result["receiver"]

    receiver_name = receiver.get(
        "name",
        username,
    )

    await update.message.reply_text(
        "✅ انتقال با موفقیت انجام شد.\n\n"
        f"👤 گیرنده: {receiver_name}\n"
        f"💵 مبلغ: {amount:,}\n\n"
        f"🏦 موجودی بانک شما: "
        f"{sender.get('bank_balance', 0):,}"
    )

    try:

        await context.bot.send_message(
            chat_id=target_id,
            text=(
                "💰 دریافت وجه\n\n"
                f"👤 فرستنده: "
                f"{user.first_name or 'بازیکن'}\n"
                f"💵 مبلغ: {amount:,}\n\n"
                f"🏦 موجودی بانک: "
                f"{receiver.get('bank_balance', 0):,}"
            ),
        )

    except Exception:

        pass


# ============================================================
# GENERIC TRANSFER HANDLER
# ============================================================

async def handle_transfer_command(
    update,
    context,
    text,
):

    user = update.effective_user

    if not user:
        return

    parsed = parse_transfer_command(
        text
    )

    if not parsed:

        await update.message.reply_text(
            "❌ فرمت انتقال صحیح نیست.\n\n"
            "مثال:\n"
            "انتقال پول 50000\n\n"
            "یا:\n"
            "انتقال پول 50000 به @username\n\n"
            "برای انتقال با Reply نیز می‌توانی "
            "روی پیام شخص Reply کنی و فقط بنویسی:\n"
            "انتقال پول 50000"
        )

        return

    amount = parsed["amount"]
    username = parsed["username"]

    if amount <= 0:

        await update.message.reply_text(
            "❌ مبلغ باید بیشتر از صفر باشد."
        )

        return

    if username:

        await transfer_by_username(
            update,
            amount,
            username,
        )

        return

    if update.message.reply_to_message:

        await transfer_by_reply(
            update,
            amount,
        )

        return

    await update.message.reply_text(
        "❌ گیرنده مشخص نشده است.\n\n"
        "یا روی پیام شخص Reply کن، یا Username "
        "او را بنویس:\n\n"
        "انتقال پول 50000 به @username"
    )


# ============================================================
# MONEY COMMANDS
# ============================================================

async def handle_deposit_command(
    update,
    text,
):

    normalized = normalize_digits(
        text
    ).strip()

    match = re.match(
        r"^(?:واریز|deposit)\s+([\d,]+)$",
        normalized,
        re.IGNORECASE,
    )

    if not match:

        await update.message.reply_text(
            "❌ فرمت صحیح:\n"
            "واریز 50000"
        )

        return

    amount = int(
        match.group(1).replace(",", "")
    )

    await deposit_money(
        update,
        amount,
    )


async def handle_withdraw_command(
    update,
    text,
):

    normalized = normalize_digits(
        text
    ).strip()

    match = re.match(
        r"^(?:برداشت|withdraw)\s+([\d,]+)$",
        normalized,
        re.IGNORECASE,
    )

    if not match:

        await update.message.reply_text(
            "❌ فرمت صحیح:\n"
            "برداشت 50000"
        )

        return

    amount = int(
        match.group(1).replace(",", "")
    )

    await withdraw_money(
        update,
        amount,
    )


# ============================================================
# GENERIC COMMAND HELP TEXT
# ============================================================

async def wallet_command(
    update,
    context,
):

    user = update.effective_user

    if not user:
        return

    player = get_player(user)

    await update.message.reply_text(
        wallet_text(player),
        reply_markup=wallet_menu(
            user.id
        ),
    )


# ============================================================
# SIMPLE PLAYER CARD
# ============================================================

def player_card_text(
    player,
):

    name = player.get(
        "name",
        "بازیکن",
    )

    level = player.get(
        "level",
        1,
    )

    reputation = player.get(
        "reputation",
        0,
    )

    body = player.get(
        "body",
        {},
    )

    hp = body.get(
        "hp",
        100,
    )

    max_hp = body.get(
        "max_hp",
        100,
    )

    return (
        "🪪 کارت بازیکن\n\n"
        f"👤 {name}\n"
        f"⭐ Level {level}\n"
        f"❤️ HP: {hp}/{max_hp}\n"
        f"⭐ شهرت: {reputation}"
    )


# ============================================================
# CALLBACK SECURITY
# ============================================================

def callback_owner_id(
    callback_data,
):

    if not callback_data:
        return None

    parts = callback_data.split("|")

    if not parts:
        return None

    try:

        return int(
            parts[-1]
        )

    except Exception:

        return None


def callback_is_owner(
    query,
):

    if not query:

        return False

    owner_id = callback_owner_id(
        query.data
    )

    if owner_id is None:

        return False

    if not query.from_user:

        return False

    return (
        int(owner_id)
        == int(query.from_user.id)
    )


# ============================================================
# SAFE CALLBACK ANSWER
# ============================================================

async def answer_callback(
    query,
    text=None,
    alert=False,
):

    try:

        await query.answer(
            text=text,
            show_alert=alert,
        )

    except Exception:

        pass


# ============================================================
# HELP CALLBACK
# ============================================================

async def handle_help_callback(
    query,
    parts,
):

    if not callback_is_owner(
        query
    ):

        await answer_callback(
            query,
            "❌ این منو متعلق به شما نیست.",
            True,
        )

        return

    if len(parts) < 3:

        return

    page_value = parts[1]

    if page_value == "noop":

        await answer_callback(
            query
        )

        return

    try:

        page = int(
            page_value
        )

    except Exception:

        return

    if page < 0:

        page = 0

    if page >= len(HELP_PAGES):

        page = len(HELP_PAGES) - 1

    await answer_callback(
        query
    )

    await query.edit_message_text(
        help_page_text(page),
        reply_markup=help_keyboard(
            query.from_user.id,
            page,
        ),
    )


# ============================================================
# PROFILE CALLBACK
# ============================================================

async def handle_profile_callback(
    query,
):

    if not callback_is_owner(
        query
    ):

        await answer_callback(
            query,
            "❌ دسترسی ندارید.",
            True,
        )

        return

    await answer_callback(
        query
    )

    user = query.from_user

    player = get_player(user)

    await query.edit_message_text(
        profile_text(player),
        reply_markup=back_button(
            user.id,
            "main",
        ),
    )


# ============================================================
# WALLET CALLBACK
# ============================================================

async def handle_wallet_callback(
    query,
):

    if not callback_is_owner(
        query
    ):

        await answer_callback(
            query,
            "❌ دسترسی ندارید.",
            True,
        )

        return

    await answer_callback(
        query
    )

    user = query.from_user

    player = get_player(user)

    await query.edit_message_text(
        wallet_text(player),
        reply_markup=wallet_menu(
            user.id,
        ),
    )


# ============================================================
# TRANSACTION CALLBACK
# ============================================================

async def handle_transactions_callback(
    query,
):

    if not callback_is_owner(
        query
    ):

        await answer_callback(
            query,
            "❌ دسترسی ندارید.",
            True,
        )

        return

    await answer_callback(
        query
    )

    player = get_player(
        query.from_user
    )

    await query.edit_message_text(
        transaction_text(player),
        reply_markup=back_button(
            query.from_user.id,
            "wallet",
        ),
    )


# ============================================================
# PART 2 END
# ============================================================# ============================================================
# PART 3
# VEHICLES / SHOWROOM / GARAGE / PLAYER MARKET
# ============================================================


# ============================================================
# VEHICLE HELPERS
# ============================================================

def get_vehicle_by_id(
    player,
    vehicle_id,
):

    vehicles = player.get(
        "vehicles",
        [],
    )

    for vehicle in vehicles:

        if str(
            vehicle.get("id")
        ) == str(vehicle_id):

            return vehicle

    return None


def remove_vehicle_by_id(
    player,
    vehicle_id,
):

    vehicles = player.get(
        "vehicles",
        [],
    )

    original_length = len(
        vehicles
    )

    player["vehicles"] = [
        vehicle
        for vehicle in vehicles
        if str(
            vehicle.get("id")
        ) != str(vehicle_id)
    ]

    return (
        len(player["vehicles"])
        != original_length
    )


def vehicle_owner(
    players,
    vehicle_id,
):

    for player_id, player in players.items():

        if get_vehicle_by_id(
            player,
            vehicle_id,
        ):

            return player_id

    return None


def vehicle_catalog_item(
    catalog_id,
):

    try:

        catalog_id = int(
            catalog_id
        )

    except Exception:

        return None

    return VEHICLE_CATALOG.get(
        catalog_id
    )


def vehicle_price(
    vehicle,
):

    try:

        return int(
            vehicle.get(
                "price",
                0,
            )
        )

    except Exception:

        return 0


def vehicle_display_name(
    vehicle,
):

    brand = vehicle.get(
        "brand",
        "Unknown",
    )

    model = vehicle.get(
        "model",
        "Vehicle",
    )

    year = vehicle.get(
        "year",
        "",
    )

    return (
        f"{brand} {model} {year}"
    )


def vehicle_condition_text(
    condition,
):

    mapping = {
        "new": "نو",
        "excellent": "عالی",
        "good": "خوب",
        "normal": "معمولی",
        "damaged": "آسیب‌دیده",
    }

    return mapping.get(
        condition,
        str(condition),
    )


# ============================================================
# VEHICLE DETAIL TEXT
# ============================================================

def vehicle_detail_text(
    vehicle,
):

    name = vehicle_display_name(
        vehicle
    )

    price = vehicle_price(
        vehicle
    )

    mileage = vehicle.get(
        "mileage",
        0,
    )

    condition = vehicle_condition_text(
        vehicle.get(
            "condition",
            "normal",
        )
    )

    color = vehicle.get(
        "color",
        "نامشخص",
    )

    engine = vehicle.get(
        "engine",
        "نامشخص",
    )

    power = vehicle.get(
        "power",
        "نامشخص",
    )

    transmission = vehicle.get(
        "transmission",
        "نامشخص",
    )

    tuning = vehicle.get(
        "tuning",
        "استاندارد",
    )

    vehicle_id = vehicle.get(
        "id",
        "N/A",
    )

    return (
        f"🚗 {name}\n\n"
        f"🆔 شناسه: {vehicle_id}\n"
        f"💰 قیمت: {price:,}\n"
        f"🛣️ کارکرد: {mileage:,} km\n"
        f"🔧 وضعیت: {condition}\n"
        f"🎨 رنگ: {color}\n"
        f"⚙️ موتور: {engine}\n"
        f"🐎 قدرت: {power}\n"
        f"🔄 گیربکس: {transmission}\n"
        f"🛠️ تیونینگ: {tuning}"
    )


# ============================================================
# SHOWROOM LIST
# ============================================================

def showroom_keyboard(
    user_id,
):

    rows = []

    for catalog_id, vehicle in VEHICLE_CATALOG.items():

        name = (
            f"{vehicle.get('brand', '')} "
            f"{vehicle.get('model', '')}"
        )

        rows.append(
            [
                InlineKeyboardButton(
                    (
                        f"🚗 {name} — "
                        f"{vehicle.get('price', 0):,}"
                    ),
                    callback_data=(
                        f"showcar|"
                        f"{catalog_id}|"
                        f"{user_id}"
                    ),
                )
            ]
        )

    rows.append(
        [
            InlineKeyboardButton(
                "🔙 بازگشت",
                callback_data=(
                    f"vehicles|{user_id}"
                ),
            )
        ]
    )

    return InlineKeyboardMarkup(
        rows
    )


async def show_showroom(
    query,
):

    if not callback_is_owner(
        query
    ):

        await answer_callback(
            query,
            "❌ دسترسی ندارید.",
            True,
        )

        return

    await answer_callback(
        query
    )

    await query.edit_message_text(
        "🏢 نمایشگاه خودرو\n\n"
        "خودروی موردنظر را انتخاب کن:",
        reply_markup=showroom_keyboard(
            query.from_user.id
        ),
    )


# ============================================================
# CATALOG VEHICLE
# ============================================================

def catalog_vehicle_keyboard(
    catalog_id,
    user_id,
):

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "💳 خرید خودرو",
                callback_data=(
                    f"buycar|"
                    f"{catalog_id}|"
                    f"{user_id}"
                ),
            )
        ],
        [
            InlineKeyboardButton(
                "🔙 نمایشگاه",
                callback_data=(
                    f"showroom|{user_id}"
                ),
            ),
            InlineKeyboardButton(
                "🚗 خودروها",
                callback_data=(
                    f"vehicles|{user_id}"
                ),
            ),
        ],
    ])


async def show_catalog_vehicle(
    query,
    catalog_id,
):

    if not callback_is_owner(
        query
    ):

        await answer_callback(
            query,
            "❌ دسترسی ندارید.",
            True,
        )

        return

    vehicle = vehicle_catalog_item(
        catalog_id
    )

    if not vehicle:

        await answer_callback(
            query,
            "❌ خودرو پیدا نشد.",
            True,
        )

        return

    await answer_callback(
        query
    )

    text = vehicle_detail_text(
        {
            **vehicle,
            "id": f"catalog-{catalog_id}",
        }
    )

    await query.edit_message_text(
        text,
        reply_markup=catalog_vehicle_keyboard(
            catalog_id,
            query.from_user.id,
        ),
    )


# ============================================================
# PURCHASE TOKEN
# ============================================================

def make_purchase_reference(
    buyer_id,
    catalog_id,
):

    return (
        "purchase_"
        + str(buyer_id)
        + "_"
        + str(catalog_id)
        + "_"
        + uuid.uuid4().hex
    )


# ============================================================
# CHECK DUPLICATE PURCHASE
# ============================================================

def has_reference_transaction(
    player,
    reference_id,
):

    if not reference_id:

        return False

    for transaction in player.get(
        "transactions",
        [],
    ):

        if (
            transaction.get(
                "reference_id"
            )
            == reference_id
        ):

            return True

    return False


# ============================================================
# BUY VEHICLE
# ============================================================

def execute_vehicle_purchase(
    buyer_id,
    catalog_id,
):

    players = load_players()

    buyer_key = str(
        buyer_id
    )

    if buyer_key not in players:

        return False, (
            "حساب خریدار پیدا نشد."
        )

    buyer = players[
        buyer_key
    ]

    if buyer.get("banned"):

        return False, (
            "حساب شما مسدود است."
        )

    catalog = vehicle_catalog_item(
        catalog_id
    )

    if not catalog:

        return False, (
            "خودرو پیدا نشد."
        )

    price = int(
        catalog.get(
            "price",
            0,
        )
    )

    if price <= 0:

        return False, (
            "قیمت خودرو نامعتبر است."
        )

    if buyer.get(
        "bank_balance",
        0,
    ) < price:

        return False, (
            "❌ موجودی بانک برای خرید "
            "این خودرو کافی نیست."
        )

    purchase_reference = make_purchase_reference(
        buyer_id,
        catalog_id,
    )

    # --------------------------------------------------------
    # جلوگیری از اجرای تکراری عملیات
    # --------------------------------------------------------
    for transaction in buyer.get(
        "transactions",
        [],
    ):

        if transaction.get(
            "type"
        ) == "vehicle_purchase":

            description = str(
                transaction.get(
                    "description",
                    "",
                )
            )

            if (
                str(catalog.get("model", ""))
                in description
                and transaction.get(
                    "reference_id"
                )
            ):
                # این بررسی فقط برای خریدهای ثبت‌شده
                # قبلی است؛ خرید جدید reference جدید دارد.
                pass

    # --------------------------------------------------------
    # کسر پول از خریدار
    # --------------------------------------------------------

    buyer["bank_balance"] -= price

    # --------------------------------------------------------
    # ساخت خودرو
    # --------------------------------------------------------

    vehicle = create_vehicle(
        catalog_id,
        buyer_id,
    )

    vehicle["purchase_price"] = price

    vehicle["purchase_reference"] = (
        purchase_reference
    )

    vehicle["owner_id"] = int(
        buyer_id
    )

    buyer.setdefault(
        "vehicles",
        [],
    ).append(
        vehicle
    )

    add_transaction(
        buyer,
        "vehicle_purchase",
        price,
        (
            "خرید "
            + vehicle_display_name(
                vehicle
            )
        ),
        direction="out",
        reference_id=purchase_reference,
    )

    # --------------------------------------------------------
    # اگر خریدار Master نیست، فروش به Master ثبت می‌شود.
    #
    # دلیل:
    # Master فروشنده نمایشگاه است.
    #
    # اگر Master خودش خودرو بخرد، نباید یک خرید و
    # یک فروش جداگانه روی تاریخچه خودش ثبت شود.
    # --------------------------------------------------------

    if int(buyer_id) != int(
        MASTER_USER_ID
    ):

        master_key = str(
            MASTER_USER_ID
        )

        if master_key not in players:

            master_player = create_player(
                MASTER_USER_ID,
                "Master",
                "",
            )

            players[
                master_key
            ] = master_player

        master = players[
            master_key
        ]

        master["bank_balance"] = (
            master.get(
                "bank_balance",
                MASTER_BANK,
            )
            + price
        )

        add_transaction(
            master,
            "vehicle_sale",
            price,
            (
                "فروش "
                + vehicle_display_name(
                    vehicle
                )
                + " به بازیکن "
                + str(buyer_id)
            ),
            direction="in",
            reference_id=purchase_reference,
        )

        players[
            master_key
        ] = master

    else:

        # Master پول نمایشگاه را به خودش برنمی‌گرداند
        # و تراکنش فروش دوم نیز ثبت نمی‌شود.
        pass

    players[
        buyer_key
    ] = buyer

    save_players(
        players
    )

    return True, {
        "vehicle": vehicle,
        "price": price,
        "buyer": buyer,
        "reference_id": purchase_reference,
    }


async def buy_vehicle(
    query,
    catalog_id,
):

    if not callback_is_owner(
        query
    ):

        await answer_callback(
            query,
            "❌ این دکمه متعلق به شما نیست.",
            True,
        )

        return

    user_id = query.from_user.id

    success, result = execute_vehicle_purchase(
        user_id,
        catalog_id,
    )

    if not success:

        await answer_callback(
            query,
            result,
            True,
        )

        return

    vehicle = result[
        "vehicle"
    ]

    price = result[
        "price"
    ]

    await answer_callback(
        query,
        "✅ خودرو خریداری شد.",
    )

    await query.edit_message_text(
        "✅ خرید با موفقیت انجام شد!\n\n"
        f"🚗 {vehicle_display_name(vehicle)}\n"
        f"💰 قیمت: {price:,}\n"
        f"🆔 شناسه خودرو: "
        f"{vehicle.get('id')}\n\n"
        "🚗 خودرو به گاراژ شما اضافه شد.",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "🚗 گاراژ من",
                    callback_data=(
                        f"garage|{user_id}"
                    ),
                )
            ],
            [
                InlineKeyboardButton(
                    "🏙️ منوی اصلی",
                    callback_data=(
                        f"main|{user_id}"
                    ),
                )
            ],
        ]),
    )


# ============================================================
# GARAGE
# ============================================================

def garage_keyboard(
    player,
):

    user_id = player.get(
        "_id",
        0,
    )

    rows = []

    vehicles = player.get(
        "vehicles",
        [],
    )

    for vehicle in vehicles:

        vehicle_id = vehicle.get(
            "id"
        )

        name = vehicle_display_name(
            vehicle
        )

        rows.append(
            [
                InlineKeyboardButton(
                    f"🚗 {name}",
                    callback_data=(
                        f"mycar|"
                        f"{vehicle_id}|"
                        f"{user_id}"
                    ),
                )
            ]
        )

    rows.append(
        [
            InlineKeyboardButton(
                "🏢 نمایشگاه",
                callback_data=(
                    f"showroom|{user_id}"
                ),
            )
        ]
    )

    rows.append(
        [
            InlineKeyboardButton(
                "🔙 بازگشت",
                callback_data=(
                    f"vehicles|{user_id}"
                ),
            )
        ]
    )

    return InlineKeyboardMarkup(
        rows
    )


async def show_garage(
    query,
):

    if not callback_is_owner(
        query
    ):

        await answer_callback(
            query,
            "❌ دسترسی ندارید.",
            True,
        )

        return

    user = query.from_user

    player = get_player(
        user
    )

    player["_id"] = user.id

    vehicles = player.get(
        "vehicles",
        [],
    )

    await answer_callback(
        query
    )

    if not vehicles:

        await query.edit_message_text(
            "🚗 گاراژ من\n\n"
            "گاراژ شما خالی است.\n\n"
            "از نمایشگاه می‌توانی خودرو بخری.",
            reply_markup=garage_keyboard(
                player
            ),
        )

        return

    text = (
        "🚗 گاراژ من\n\n"
        f"تعداد خودروها: {len(vehicles)}\n\n"
    )

    for index, vehicle in enumerate(
        vehicles,
        1,
    ):

        text += (
            f"{index}. "
            f"{vehicle_display_name(vehicle)}\n"
            f"   🆔 {vehicle.get('id')}\n"
            f"   💰 ارزش: "
            f"{vehicle_price(vehicle):,}\n\n"
        )

    await query.edit_message_text(
        text,
        reply_markup=garage_keyboard(
            player
        ),
    )


# ============================================================
# MY VEHICLE
# ============================================================

def my_vehicle_keyboard(
    vehicle_id,
    user_id,
):

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "💰 فروش",
                callback_data=(
                    f"sellcar|"
                    f"{vehicle_id}|"
                    f"{user_id}"
                ),
            ),
            InlineKeyboardButton(
                "🤝 پیشنهاد فروش",
                callback_data=(
                    f"offer|"
                    f"{vehicle_id}|"
                    f"{user_id}"
                ),
            ),
        ],
        [
            InlineKeyboardButton(
                "🎁 انتقال خودرو",
                callback_data=(
                    f"giftcar|"
                    f"{vehicle_id}|"
                    f"{user_id}"
                ),
            )
        ],
        [
            InlineKeyboardButton(
                "🔙 گاراژ",
                callback_data=(
                    f"garage|{user_id}"
                ),
            )
        ],
    ])


async def show_my_vehicle(
    query,
    vehicle_id,
):

    if not callback_is_owner(
        query
    ):

        await answer_callback(
            query,
            "❌ دسترسی ندارید.",
            True,
        )

        return

    player = get_player(
        query.from_user
    )

    vehicle = get_vehicle_by_id(
        player,
        vehicle_id,
    )

    if not vehicle:

        await answer_callback(
            query,
            "❌ این خودرو در گاراژ شما نیست.",
            True,
        )

        return

    await answer_callback(
        query
    )

    text = (
        vehicle_detail_text(
            vehicle
        )
        + "\n\n"
        "📌 وضعیت مالکیت: متعلق به شما"
    )

    await query.edit_message_text(
        text,
        reply_markup=my_vehicle_keyboard(
            vehicle_id,
            query.from_user.id,
        ),
    )


# ============================================================
# VEHICLE SALE STATE
# ============================================================

def set_vehicle_sale_state(
    player,
    vehicle_id,
):

    player.setdefault(
        "vehicle_sale_state",
        {},
    )

    player[
        "vehicle_sale_state"
    ] = {
        "vehicle_id": str(
            vehicle_id
        ),
        "created_at": time.time(),
    }


def clear_vehicle_sale_state(
    player,
):

    player.pop(
        "vehicle_sale_state",
        None,
    )


# ============================================================
# PLAYER-TO-PLAYER VEHICLE OFFER
# ============================================================

def create_vehicle_offer(
    seller_id,
    buyer_id,
    vehicle_id,
    amount,
):

    players = load_players()

    seller_key = str(
        seller_id
    )

    buyer_key = str(
        buyer_id
    )

    if seller_key not in players:

        return False, (
            "فروشنده پیدا نشد."
        )

    if buyer_key not in players:

        return False, (
            "خریدار پیدا نشد."
        )

    if seller_key == buyer_key:

        return False, (
            "نمی‌توانی به خودت پیشنهاد بدهی."
        )

    seller = players[
        seller_key
    ]

    buyer = players[
        buyer_key
    ]

    vehicle = get_vehicle_by_id(
        seller,
        vehicle_id,
    )

    if not vehicle:

        return False, (
            "خودرو متعلق به فروشنده نیست."
        )

    amount = int(
        amount
    )

    if amount <= 0:

        return False, (
            "قیمت پیشنهادی نامعتبر است."
        )

    offer_id = (
        "offer_"
        + uuid.uuid4().hex
    )

    offer = {
        "id": offer_id,
        "seller_id": int(
            seller_id
        ),
        "buyer_id": int(
            buyer_id
        ),
        "vehicle_id": str(
            vehicle_id
        ),
        "amount": amount,
        "status": "pending",
        "created_at": timestamp(),
    }

    seller.setdefault(
        "vehicle_offers",
        [],
    ).append(
        offer
    )

    buyer.setdefault(
        "vehicle_offers",
        [],
    ).append(
        offer
    )

    players[
        seller_key
    ] = seller

    players[
        buyer_key
    ] = buyer

    save_players(
        players
    )

    return True, offer


# ============================================================
# EXECUTE ACCEPTED VEHICLE OFFER
# ============================================================

def execute_vehicle_offer(
    offer_id,
    buyer_id,
):
    players = load_players()

    buyer_key = str(
        buyer_id
    )

    if buyer_key not in players:

        return False, (
            "خریدار پیدا نشد."
        )

    buyer = players[
        buyer_key
    ]

    all_offers = []

    for player in players.values():

        for offer in player.get(
            "vehicle_offers",
            [],
        ):

            if offer.get("id") == offer_id:

                all_offers.append(
                    offer
                )

    if not all_offers:

        return False, (
            "پیشنهاد پیدا نشد."
        )

    offer = all_offers[0]

    if int(
        offer.get("buyer_id", 0)
    ) != int(buyer_id):

        return False, (
            "این پیشنهاد متعلق به شما نیست."
        )

    if offer.get(
        "status"
    ) != "pending":

        return False, (
            "این پیشنهاد قبلاً تعیین تکلیف شده است."
        )

    seller_id = int(
        offer.get(
            "seller_id"
        )
    )

    seller_key = str(
        seller_id
    )

    if seller_key not in players:

        return False, (
            "فروشنده پیدا نشد."
        )

    seller = players[
        seller_key
    ]

    vehicle_id = offer.get(
        "vehicle_id"
    )

    vehicle = get_vehicle_by_id(
        seller,
        vehicle_id,
    )

    if not vehicle:

        return False, (
            "خودرو دیگر متعلق به فروشنده نیست."
)

    amount = int(
        offer.get(
            "amount",
            0,
        )
    )

    if amount <= 0:

        return False, (
            "مبلغ معامله نامعتبر است."
        )

    if buyer.get(
        "bank_balance",
        0,
    ) < amount:

        return False, (
            "موجودی بانکی خریدار کافی نیست."
        )

    transaction_id = (
        "vehicle_sale_"
        + offer_id
    )

    # --------------------------------------------------------
    # پرداخت
    # --------------------------------------------------------

    buyer["bank_balance"] -= amount

    seller["bank_balance"] = (
        seller.get(
            "bank_balance",
            0,
        )
        + amount
    )

    # --------------------------------------------------------
    # انتقال مالکیت
    # --------------------------------------------------------

    transferred_vehicle = dict(
        vehicle
    )

    transferred_vehicle[
        "owner_id"
    ] = int(
        buyer_id
    )

    transferred_vehicle[
        "last_sale_price"
    ] = amount

    transferred_vehicle[
        "last_sale_at"
    ] = timestamp()

    remove_vehicle_by_id(
        seller,
        vehicle_id,
    )

    buyer.setdefault(
        "vehicles",
        [],
    ).append(
        transferred_vehicle
    )

    # --------------------------------------------------------
    # وضعیت پیشنهاد
    # --------------------------------------------------------

    offer["status"] = "accepted"

    offer["completed_at"] = timestamp()

    # --------------------------------------------------------
    # تراکنش‌ها
    # --------------------------------------------------------

    add_transaction(
        buyer,
        "vehicle_purchase_player",
        amount,
        (
            "خرید "
            + vehicle_display_name(
                vehicle
            )
            + " از بازیکن "
            + str(seller_id)
        ),
        direction="out",
        reference_id=transaction_id,
    )

    add_transaction(
        seller,
        "vehicle_sale_player",
        amount,
        (
            "فروش "
            + vehicle_display_name(
                vehicle
            )
            + " به بازیکن "
            + str(buyer_id)
        ),
        direction="in",
        reference_id=transaction_id,
    )

    # --------------------------------------------------------
    # ذخیره پیشنهاد روی هر دو حساب
    # --------------------------------------------------------

    for player in players.values():

        offers = player.get(
            "vehicle_offers",
            [],
        )

        for stored_offer in offers:

            if stored_offer.get(
                "id"
            ) == offer_id:

                stored_offer[
                    "status"
                ] = "accepted"

                stored_offer[
                    "completed_at"
                ] = timestamp()

    players[
        buyer_key
    ] = buyer

    players[
        seller_key
    ] = seller

    save_players(
        players
    )

    return True, {
        "vehicle": transferred_vehicle,
        "amount": amount,
        "seller_id": seller_id,
        "buyer_id": buyer_id,
        "reference_id": transaction_id,
    }


# ============================================================
# REJECT VEHICLE OFFER
# ============================================================

def reject_vehicle_offer(
    offer_id,
    user_id,
):

    players = load_players()

    user_key = str(
        user_id
    )

    if user_key not in players:

        return False, (
            "حساب پیدا نشد."
        )

    found = False

    for player in players.values():

        for offer in player.get(
            "vehicle_offers",
            [],
        ):

            if offer.get(
                "id"
            ) == offer_id:

                if (
                    int(
                        offer.get(
                            "buyer_id",
                            0,
                        )
                    )
                    != int(user_id)
                    and
                    int(
                        offer.get(
                            "seller_id",
                            0,
                        )
                    )
                    != int(user_id)
                ):

                    continue

                if offer.get(
                    "status"
                ) != "pending":

                    return False, (
                        "این پیشنهاد قبلاً تعیین تکلیف شده است."
                    )

                offer[
                    "status"
                ] = "rejected"

                offer[
                    "rejected_at"
                ] = timestamp()

                found = True

    if not found:

        return False, (
            "پیشنهاد پیدا نشد."
        )

    save_players(
        players
    )

    return True, "پیشنهاد رد شد."


# ============================================================
# OFFER KEYBOARD
# ============================================================

def offer_keyboard(
    offer_id,
    user_id,
):

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "✅ قبول پیشنهاد",
                callback_data=(
                    f"acceptoffer|"
                    f"{offer_id}|"
                    f"{user_id}"
                ),
            ),
            InlineKeyboardButton(
                "❌ رد",
                callback_data=(
                    f"rejectoffer|"
                    f"{offer_id}|"
                    f"{user_id}"
                ),
            ),
        ],
        [
            InlineKeyboardButton(
                "🏙️ منوی اصلی",
                callback_data=(
                    f"main|{user_id}"
                ),
            )
        ],
    ])


# ============================================================
# SEND VEHICLE OFFER
# ============================================================

async def send_vehicle_offer_message(
    context,
    seller_id,
    buyer_id,
    offer,
    vehicle,
):

    amount = int(
        offer.get(
            "amount",
            0,
        )
    )

    await context.bot.send_message(
        chat_id=buyer_id,
        text=(
            "🚗 پیشنهاد خرید خودرو\n\n"
            f"🚘 خودرو: "
            f"{vehicle_display_name(vehicle)}\n"
            f"💰 قیمت پیشنهادی: {amount:,}\n\n"
            f"👤 فروشنده: {seller_id}\n\n"
            "آیا پیشنهاد را قبول می‌کنی؟"
        ),
        reply_markup=offer_keyboard(
            offer.get("id"),
            buyer_id,
        ),
    )


# ============================================================
# LIST VEHICLE FOR SALE
# ============================================================

def create_market_listing(
    seller_id,
    vehicle_id,
    price,
):

    players = load_players()

    seller_key = str(
        seller_id
    )

    if seller_key not in players:

        return False, (
            "فروشنده پیدا نشد."
        )

    seller = players[
        seller_key
    ]

    vehicle = get_vehicle_by_id(
        seller,
        vehicle_id,
    )

    if not vehicle:

        return False, (
            "خودرو متعلق به شما نیست."
        )

    price = int(
        price
    )

    if price <= 0:

        return False, (
            "قیمت نامعتبر است."
        )

    for listing in seller.get(
        "market_listings",
        [],
    ):

        if (
            listing.get("status")
            == "active"
            and
            str(
                listing.get(
                    "vehicle_id"
                )
            )
            == str(vehicle_id)
        ):

            return False, (
                "این خودرو قبلاً برای فروش "
                "گذاشته شده است."
            )

    listing_id = (
        "listing_"
        + uuid.uuid4().hex
    )

    listing = {
        "id": listing_id,
        "seller_id": int(
            seller_id
        ),
        "vehicle_id": str(
            vehicle_id
        ),
        "price": price,
        "status": "active",
        "created_at": timestamp(),
    }

    seller.setdefault(
        "market_listings",
        [],
    ).append(
        listing
    )

    players[
        seller_key
    ] = seller

    save_players(
        players
    )

    return True, listing


# ============================================================
# MARKET LISTINGS
# ============================================================

def active_market_listings():

    players = load_players()

    result = []

    for player_id, player in players.items():

        for listing in player.get(
            "market_listings",
            [],
        ):

            if listing.get(
                "status"
            ) != "active":

                continue

            vehicle = get_vehicle_by_id(
                player,
                listing.get(
                    "vehicle_id"
                ),
            )

            if not vehicle:

                continue

            item = dict(
                listing
            )

            item[
                "vehicle"
            ] = vehicle

            result.append(
                item
            )

    return result


def market_keyboard(
    listings,
    user_id,
):

    rows = []

    for listing in listings[:20]:

        vehicle = listing[
            "vehicle"
        ]

        price = int(
            listing.get(
                "price",
                0,
            )
        )

        listing_id = listing.get(
            "id"
        )

        rows.append(
            [
                InlineKeyboardButton(
                    (
                        f"🚗 "
                        f"{vehicle_display_name(vehicle)} "
                        f"— {price:,}"
                    ),
                    callback_data=(
                        f"listing|"
                        f"{listing_id}|"
                        f"{user_id}"
                    ),
                )
            ]
        )

    rows.append(
        [
            InlineKeyboardButton(
                "🔙 خودروها",
                callback_data=(
                    f"vehicles|{user_id}"
                ),
            )
        ]
    )

    return InlineKeyboardMarkup(
        rows
    )


async def show_vehicle_market(
    query,
):

    if not callback_is_owner(
        query
    ):

        await answer_callback(
            query,
            "❌ دسترسی ندارید.",
            True,
        )

        return

    listings = active_market_listings()

    await answer_callback(
        query
    )

    if not listings:

        await query.edit_message_text(
            "🏪 بازار خودرو\n\n"
            "در حال حاضر خودرویی برای فروش "
            "ثبت نشده است.",
            reply_markup=back_button(
                query.from_user.id,
                "vehicles",
            ),
        )

        return

    text = (
        "🏪 بازار خودرو\n\n"
        "خودروی موردنظر را انتخاب کن:"
    )

    await query.edit_message_text(
        text,
        reply_markup=market_keyboard(
            listings,
            query.from_user.id,
        ),
    )


# ============================================================
# FIND LISTING
# ============================================================

def find_listing(
    listing_id,
):

    players = load_players()

    for player_id, player in players.items():

        for listing in player.get(
            "market_listings",
            [],
        ):

            if listing.get(
                "id"
            ) != listing_id:

                continue

            if listing.get(
                "status"
            ) != "active":

                continue

            vehicle = get_vehicle_by_id(
                player,
                listing.get(
                    "vehicle_id"
                ),
            )

            if not vehicle:

                continue

            return (
                players,
                player_id,
                player,
                listing,
                vehicle,
            )

    return (
        None,
        None,
        None,
        None,
        None,
    )


# ============================================================
# LISTING DETAIL
# ============================================================

async def show_listing(
    query,
    listing_id,
):

    if not callback_is_owner(
        query
    ):

        await answer_callback(
            query,
            "❌ دسترسی ندارید.",
            True,
        )

        return

    (
        players,
        seller_id,
        seller,
        listing,
        vehicle,
    ) = find_listing(
        listing_id
    )

    if not listing:

        await answer_callback(
            query,
            "❌ آگهی پیدا نشد یا فروخته شده است.",
            True,
        )

        return

    price = int(
        listing.get(
            "price",
            0,
        )
    )

    seller_name = seller.get(
        "name",
        seller_id,
    )

    text = (
        "🏪 آگهی خودرو\n\n"
        + vehicle_detail_text(
            vehicle
        )
        + "\n\n"
        f"👤 فروشنده: {seller_name}\n"
        f"💰 قیمت فروش: {price:,}"
    )

    await answer_callback(
        query
    )

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "💳 خرید",
                    callback_data=(
                        f"buylisting|"
                        f"{listing_id}|"
                        f"{query.from_user.id}"
                    ),
                )
            ],
            [
                InlineKeyboardButton(
                    "🤝 پیشنهاد قیمت",
                    callback_data=(
                        f"offerlisting|"
                        f"{listing_id}|"
                        f"{query.from_user.id}"
                    ),
                )
            ],
            [
                InlineKeyboardButton(
                    "🔙 بازار",
                    callback_data=(
                        f"carmarket|"
                        f"{query.from_user.id}"
                    ),
                )
            ],
        ]),
    )


# ============================================================
# DIRECT MARKET PURCHASE
# ============================================================

def execute_market_purchase(
    buyer_id,
    listing_id,
):

    (
        players,
        seller_id,
        seller,
        listing,
        vehicle,
    ) = find_listing(
        listing_id
    )

    if not listing:

        return False, (
            "آگهی پیدا نشد یا قبلاً فروخته شده است."
        )

    buyer_key = str(
        buyer_id
    )

    if buyer_key not in players:

        return False, (
            "خریدار پیدا نشد."
        )

    buyer = players[
        buyer_key
    ]

    if int(
        seller_id
    ) == int(
        buyer_id
    ):

        return False, (
            "نمی‌توانی خودرو خودت را بخری."
        )

    price = int(
        listing.get(
            "price",
            0,
        )
    )

    if price <= 0:

        return False, (
            "قیمت خودرو نامعتبر است."
        )

    if buyer.get(
        "bank_balance",
        0,
    ) < price:

        return False, (
            "موجودی بانکی کافی نیست."
        )

    reference_id = (
        "market_purchase_"
        + str(listing_id)
    )

    # --------------------------------------------------------
    # پرداخت
    # --------------------------------------------------------

    buyer["bank_balance"] -= price

    seller["bank_balance"] = (
        seller.get(
            "bank_balance",
            0,
        )
        + price
    )

    # --------------------------------------------------------
    # انتقال خودرو
    # --------------------------------------------------------

    transferred_vehicle = dict(
        vehicle
    )

    transferred_vehicle[
        "owner_id"
    ] = int(
        buyer_id
    )

    transferred_vehicle[
        "last_sale_price"
    ] = price

    transferred_vehicle[
        "last_sale_at"
    ] = timestamp()

    remove_vehicle_by_id(
        seller,
        vehicle.get("id"),
    )

    buyer.setdefault(
        "vehicles",
        [],
    ).append(
        transferred_vehicle
    )

    # --------------------------------------------------------
    # غیرفعال کردن آگهی
    # --------------------------------------------------------

    listing["status"] = "sold"

    listing[
        "sold_to"
    ] = int(
        buyer_id
    )

    listing[
        "sold_at"
    ] = timestamp()

    # --------------------------------------------------------
    # ثبت تراکنش
    # --------------------------------------------------------

    add_transaction(
        buyer,
        "vehicle_market_purchase",
        price,
        (
            "خرید "
            + vehicle_display_name(
                vehicle
            )
            + " از "
            + str(seller_id)
        ),
        direction="out",
        reference_id=reference_id,
    )

    add_transaction(
        seller,
        "vehicle_market_sale",
        price,
        (
            "فروش "
            + vehicle_display_name(
                vehicle
            )
            + " به "
            + str(buyer_id)
        ),
        direction="in",
        reference_id=reference_id,
    )

    players[
        buyer_key
    ] = buyer

    players[
        str(seller_id)
    ] = seller

    save_players(
        players
    )

    return True, {
        "vehicle": transferred_vehicle,
        "price": price,
        "seller_id": int(
            seller_id
        ),
        "buyer_id": int(
            buyer_id
        ),
        "reference_id": reference_id,
    }


async def buy_market_vehicle(
    query,
    listing_id,
):

    if not callback_is_owner(
        query
    ):

        await answer_callback(
            query,
            "❌ دسترسی ندارید.",
            True,
        )

        return

    success, result = execute_market_purchase(
        query.from_user.id,
        listing_id,
    )

    if not success:

        await answer_callback(
            query,
            result,
            True,
        )

        return

    vehicle = result[
        "vehicle"
    ]

    price = result[
        "price"
    ]

    await answer_callback(
        query,
        "✅ معامله انجام شد.",
    )

    await query.edit_message_text(
        "✅ معامله با موفقیت انجام شد!\n\n"
        f"🚗 {vehicle_display_name(vehicle)}\n"
        f"💰 مبلغ: {price:,}\n\n"
        "مالکیت خودرو به شما منتقل شد.",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "🚗 گاراژ من",
                    callback_data=(
                        f"garage|"
                        f"{query.from_user.id}"
                    ),
                )
            ],
            [
                InlineKeyboardButton(
                    "🏙️ منوی اصلی",
                    callback_data=(
                        f"main|"
                        f"{query.from_user.id}"
                    ),
                )
            ],
        ]),
    )


# ============================================================
# CREATE LISTING FROM VEHICLE
# ============================================================

async def prepare_vehicle_sale(
    query,
    vehicle_id,
):

    if not callback_is_owner(
        query
    ):

        await answer_callback(
            query,
            "❌ دسترسی ندارید.",
            True,
        )

        return

    player = get_player(
        query.from_user
    )

    vehicle = get_vehicle_by_id(
        player,
        vehicle_id,
    )

    if not vehicle:

        await answer_callback(
            query,
            "❌ خودرو پیدا نشد.",
            True,
        )

        return

    set_vehicle_sale_state(
        player,
        vehicle_id,
    )

    players = load_players()

    players[
        str(query.from_user.id)
    ] = player

    save_players(
        players
    )

    await answer_callback(
        query
    )

    await query.edit_message_text(
        "💰 فروش خودرو\n\n"
        f"🚗 {vehicle_display_name(vehicle)}\n\n"
        "حالا قیمت فروش را به‌صورت پیام ارسال کن.\n\n"
        "مثال:\n"
        "فروش خودرو 150000000\n\n"
        "یا اگر می‌خواهی لغو کنی:\n"
        "لغو",
    )


# ============================================================
# COMPLETE VEHICLE LISTING FROM TEXT
# ============================================================

async def complete_vehicle_listing(
    update,
    price,
):

    user = update.effective_user

    if not user:
        return

    players = load_players()

    key = str(
        user.id
    )

    if key not in players:

        return

    player = players[
        key
    ]

    state = player.get(
        "vehicle_sale_state"
    )

    if not state:

        return

    vehicle_id = state.get(
        "vehicle_id"
    )

    vehicle = get_vehicle_by_id(
        player,
        vehicle_id,
    )

    if not vehicle:

        clear_vehicle_sale_state(
            player
        )

        players[key] = player

        save_players(players)

        await update.message.reply_text(
            "❌ خودرو پیدا نشد."
        )

        return

    success, result = create_market_listing(
        user.id,
        vehicle_id,
        price,
    )

    clear_vehicle_sale_state(
        player
    )

    players = load_players()

    players[key] = player

    save_players(players)

    if not success:

        await update.message.reply_text(
            f"❌ آگهی ثبت نشد.\n\n"
            f"{result}"
        )

        return

    await update.message.reply_text(
        "✅ آگهی خودرو ثبت شد.\n\n"
        f"🚗 {vehicle_display_name(vehicle)}\n"
        f"💰 قیمت فروش: {price:,}\n\n"
        "خودرو تا زمان فروش در گاراژ شما باقی می‌ماند."
    )


# ============================================================
# VEHICLE OFFER BY LISTING
# ============================================================

def get_listing_by_id(
    listing_id,
):

    return find_listing(
        listing_id
    )


def prepare_listing_offer(
    player,
    listing_id,
):

    player.setdefault(
        "pending_listing_offer",
        {},
    )

    player[
        "pending_listing_offer"
    ] = {
        "listing_id": listing_id,
        "created_at": time.time(),
    }


async def prepare_listing_offer_message(
    query,
    listing_id,
):

    if not callback_is_owner(
        query
    ):

        await answer_callback(
            query,
            "❌ دسترسی ندارید.",
            True,
        )

        return

    (
        players,
        seller_id,
        seller,
        listing,
        vehicle,
    ) = find_listing(
        listing_id
    )

    if not listing:

        await answer_callback(
            query,
            "❌ آگهی پیدا نشد.",
            True,
        )

        return

    if int(
        seller_id
    ) == int(
        query.from_user.id
    ):

        await answer_callback(
            query,
            "❌ نمی‌توانی برای خودت پیشنهاد بدهی.",
            True,
        )

        return

    player = players[
        str(
            query.from_user.id
        )
    ]

    prepare_listing_offer(
        player,
        listing_id,
    )

    players[
        str(
            query.from_user.id
        )
    ] = player

    save_players(
        players
    )

    await answer_callback(
        query
    )

    await query.edit_message_text(
        "🤝 پیشنهاد قیمت\n\n"
        f"🚗 {vehicle_display_name(vehicle)}\n"
        f"💰 قیمت فروشنده: "
        f"{listing.get('price', 0):,}\n\n"
        "قیمت پیشنهادی خودت را ارسال کن.\n\n"
        "مثال:\n"
        "پیشنهاد خودرو 120000000\n\n"
        "برای لغو:\n"
        "لغو"
    )


# ============================================================
# COMPLETE LISTING OFFER
# ============================================================

async def complete_listing_offer(
    update,
    amount,
):

    user = update.effective_user

    if not user:
        return

    players = load_players()

    key = str(
        user.id
    )

    player = players.get(
        key
    )

    if not player:

        return

    state = player.get(
        "pending_listing_offer"
    )

    if not state:

        return

    listing_id = state.get(
        "listing_id"
    )

    (
        players,
        seller_id,
        seller,
        listing,
        vehicle,
    ) = find_listing(
        listing_id
    )

    if not listing:

        player.pop(
            "pending_listing_offer",
            None,
        )

        players[key] = player

        save_players(players)

        await update.message.reply_text(
            "❌ این آگهی دیگر فعال نیست."
        )

        return

    success, offer = create_vehicle_offer(
        seller_id,
        user.id,
        vehicle.get("id"),
        amount,
    )

    player.pop(
        "pending_listing_offer",
        None,
    )

    players = load_players()

    players[key] = player

    save_players(players)

    if not success:

        await update.message.reply_text(
            f"❌ پیشنهاد ثبت نشد.\n\n"
            f"{offer}"
        )

        return

    await update.message.reply_text(
        "✅ پیشنهاد شما ثبت شد.\n\n"
        f"🚗 {vehicle_display_name(vehicle)}\n"
        f"💰 پیشنهاد: {amount:,}\n\n"
        "منتظر پاسخ فروشنده بمان."
    )

    try:

        await context.bot.send_message(
            chat_id=int(
                seller_id
            ),
            text=(
                "🤝 پیشنهاد خرید خودرو\n\n"
                f"🚗 {vehicle_display_name(vehicle)}\n"
                f"💰 مبلغ پیشنهادی: {amount:,}\n\n"
                f"👤 خریدار: {user.first_name or 'بازیکن'}"
            ),
            reply_markup=offer_keyboard(
                offer.get("id"),
                int(seller_id),
            ),
        )

    except Exception:

        pass


# ============================================================
# SELL / OFFER COMMAND PARSING
# ============================================================

def parse_vehicle_price_command(
    text,
    command_names,
):

    normalized = normalize_digits(
        text
    ).strip()

    escaped = "|".join(
        re.escape(name)
        for name in command_names
    )

    pattern = re.compile(
        rf"^(?:{escaped})\s+([\d,]+)$",
        re.IGNORECASE,
    )

    match = pattern.match(
        normalized
    )

    if not match:

        return None

    try:

        return int(
            match.group(1).replace(",", "")
        )

    except Exception:

        return None


# ============================================================
# VEHICLE GIFT
# ============================================================

def execute_vehicle_gift(
    sender_id,
    receiver_id,
    vehicle_id,
):

    if int(sender_id) == int(receiver_id):

        return False, (
            "نمی‌توانی خودرو را به خودت انتقال بدهی."
        )

    players = load_players()

    sender_key = str(
        sender_id
    )

    receiver_key = str(
        receiver_id
    )

    if sender_key not in players:

        return False, (
            "فرستنده پیدا نشد."
        )

    if receiver_key not in players:

        return False, (
            "گیرنده پیدا نشد."
        )

    sender = players[
        sender_key
    ]

    receiver = players[
        receiver_key
    ]

    vehicle = get_vehicle_by_id(
        sender,
        vehicle_id,
    )

    if not vehicle:

        return False, (
            "این خودرو متعلق به شما نیست."
        )

    gift_reference = (
        "vehicle_gift_"
        + uuid.uuid4().hex
    )

    remove_vehicle_by_id(
        sender,
        vehicle_id,
    )

    gifted_vehicle = dict(
        vehicle
    )

    gifted_vehicle[
        "owner_id"
    ] = int(
        receiver_id
    )

    gifted_vehicle[
        "gifted_at"
    ] = timestamp()

    receiver.setdefault(
        "vehicles",
        [],
    ).append(
        gifted_vehicle
    )

    add_transaction(
        sender,
        "vehicle_gift_sent",
        0,
        (
            "هدیه خودرو "
            + vehicle_display_name(
                vehicle
            )
            + " به "
            + str(receiver_id)
        ),
        direction="out",
        reference_id=gift_reference,
    )

    add_transaction(
        receiver,
        "vehicle_gift_received",
        0,
        (
            "دریافت هدیه خودرو "
            + vehicle_display_name(
                vehicle
            )
            + " از "
            + str(sender_id)
        ),
        direction="in",
        reference_id=gift_reference,
    )

    players[
        sender_key
    ] = sender

    players[
        receiver_key
    ] = receiver

    save_players(
        players
    )

    return True, {
        "vehicle": gifted_vehicle,
        "reference_id": gift_reference,
    }


# ============================================================
# VEHICLE GIFT PREPARATION
# ============================================================

async def prepare_vehicle_gift(
    query,
    vehicle_id,
):

    if not callback_is_owner(
        query
    ):

        await answer_callback(
            query,
            "❌ دسترسی ندارید.",
            True,
        )

        return

    player = get_player(
        query.from_user
    )

    vehicle = get_vehicle_by_id(
        player,
        vehicle_id,
    )

    if not vehicle:

        await answer_callback(
            query,
            "❌ خودرو پیدا نشد.",
            True,
        )

        return

    player[
        "pending_vehicle_gift"
    ] = {
        "vehicle_id": str(
            vehicle_id
        ),
        "created_at": time.time(),
    }

    players = load_players()

    players[
        str(query.from_user.id)
    ] = player

    save_players(
        players
    )

    await answer_callback(
        query
    )

    await query.edit_message_text(
        "🎁 انتقال خودرو\n\n"
        f"🚗 {vehicle_display_name(vehicle)}\n\n"
        "شناسه یا Username گیرنده را ارسال کن.\n\n"
        "مثال:\n"
        "انتقال خودرو به 123456789\n\n"
        "یا:\n"
        "انتقال خودرو به @username\n\n"
        "برای لغو:\n"
        "لغو"
    )


# ============================================================
# VEHICLE GIFT COMPLETION
# ============================================================

def find_player_by_identifier(
    players,
    identifier,
):

    identifier = str(
        identifier
    ).strip()

    identifier = identifier.lstrip(
        "@"
    )

    if identifier.isdigit():

        key = identifier

        if key in players:

            return key, players[key]

    identifier_lower = (
        identifier.lower()
    )

    for key, player in players.items():

        username = str(
            player.get(
                "username",
                "",
            )
        ).lstrip("@").lower()

        if (
            username
            and username == identifier_lower
        ):

            return key, player

    return None, None


async def complete_vehicle_gift(
    update,
    identifier,
):

    user = update.effective_user

    if not user:
        return

    players = load_players()

    sender_key = str(
        user.id
    )

    sender = players.get(
        sender_key
    )

    if not sender:

        return

    state = sender.get(
        "pending_vehicle_gift"
    )

    if not state:

        return

    vehicle_id = state.get(
        "vehicle_id"
    )

    receiver_key, receiver = (
        find_player_by_identifier(
            players,
            identifier,
        )
    )

    if not receiver_key:

        await update.message.reply_text(
            "❌ گیرنده پیدا نشد."
        )

        return

    success, result = execute_vehicle_gift(
        user.id,
        int(receiver_key),
        vehicle_id,
    )

    players = load_players()

    sender = players.get(
        sender_key
    )

    if sender:

        sender.pop(
            "pending_vehicle_gift",
            None,
        )

        players[
            sender_key
        ] = sender

    save_players(
        players
    )

    if not success:

        await update.message.reply_text(
            f"❌ انتقال انجام نشد.\n\n"
            f"{result}"
        )

        return

    vehicle = result[
        "vehicle"
    ]

    await update.message.reply_text(
        "🎁 خودرو با موفقیت منتقل شد.\n\n"
        f"🚗 {vehicle_display_name(vehicle)}\n"
        f"👤 گیرنده: {receiver.get('name', receiver_key)}"
    )

    try:

        await context.bot.send_message(
            chat_id=int(
                receiver_key
            ),
            text=(
                "🎁 دریافت خودرو\n\n"
                f"🚗 {vehicle_display_name(vehicle)}\n"
                f"👤 فرستنده: "
                f"{user.first_name or 'بازیکن'}\n\n"
                "خودرو به گاراژ شما اضافه شد."
            ),
        )

    except Exception:

        pass


# ============================================================
# VEHICLE MARKET TEXT HELPERS
# ============================================================

def vehicle_command_help():

    return (
        "🚗 دستورات خودرو\n\n"
        "• منو → خودروها\n"
        "• نمایشگاه\n"
        "• گاراژ\n\n"
        "فروش خودرو:\n"
        "فروش خودرو 500000000\n\n"
        "پیشنهاد قیمت:\n"
        "پیشنهاد خودرو 450000000\n\n"
        "انتقال خودرو:\n"
        "انتقال خودرو به @username"
    )


# ============================================================
# PART 3 END
# ============================================================# ============================================================
# PART 4
# COMBAT / BODY PARTS / DAMAGE / INJURIES / DEFENSE
# ============================================================


# ============================================================
# COMBAT HELPERS
# ============================================================

def get_body_part(
    player,
    part_id,
):

    body = player.setdefault(
        "body",
        default_body(),
    )

    parts = body.setdefault(
        "parts",
        {},
    )

    return parts.get(
        part_id
    )


def body_part_name(
    part_id,
):

    data = BODY_PARTS.get(
        part_id
    )

    if not data:

        return part_id

    return data.get(
        "name",
        part_id,
    )


def body_part_max_hp(
    part_id,
):

    data = BODY_PARTS.get(
        part_id
    )

    if not data:

        return 100

    return int(
        data.get(
            "hp",
            100,
        )
    )


def ensure_body_parts(
    player,
):

    body = player.setdefault(
        "body",
        default_body(),
    )

    body.setdefault(
        "hp",
        100,
    )

    body.setdefault(
        "max_hp",
        100,
    )

    body.setdefault(
        "parts",
        {},
    )

    body.setdefault(
        "injuries",
        [],
    )

    for part_id, part_data in BODY_PARTS.items():

        if part_id not in body["parts"]:

            body["parts"][part_id] = {
                "hp": int(
                    part_data.get(
                        "hp",
                        100,
                    )
                ),
                "max_hp": int(
                    part_data.get(
                        "hp",
                        100,
                    )
                ),
            }

    return body


def total_body_hp(
    player,
):

    body = ensure_body_parts(
        player
    )

    return int(
        body.get(
            "hp",
            100,
        )
    )


# ============================================================
# INJURY TYPES
# ============================================================

INJURY_TYPES = {
    "bruise": {
        "name": "کبودی",
        "severity": 1,
        "clinic_cost": 5000,
        "heal_time": 10,
    },

    "wound": {
        "name": "زخم",
        "severity": 2,
        "clinic_cost": 15000,
        "heal_time": 20,
    },

    "bleeding": {
        "name": "خونریزی",
        "severity": 3,
        "clinic_cost": 30000,
        "heal_time": 30,
    },

    "dislocation": {
        "name": "دررفتگی",
        "severity": 4,
        "clinic_cost": 60000,
        "heal_time": 45,
    },

    "fracture": {
        "name": "شکستگی",
        "severity": 5,
        "clinic_cost": 100000,
        "heal_time": 60,
    },
}


# ============================================================
# ATTACK DATA
# ============================================================

DEFAULT_ATTACKS = {
    "fist": {
        "name": "👊 مشت",
        "min_damage": 6,
        "max_damage": 12,
        "level": 1,
    },

    "kick": {
        "name": "🦵 لگد",
        "min_damage": 8,
        "max_damage": 15,
        "level": 1,
    },

    "knife": {
        "name": "🔪 چاقو",
        "min_damage": 18,
        "max_damage": 30,
        "level": 5,
    },

    "heavy_attack": {
        "name": "💥 ضربه سنگین",
        "min_damage": 12,
        "max_damage": 22,
        "level": 3,
    },
}


# ============================================================
# BODY PART DATA
# ============================================================

if "BODY_PARTS" not in globals():

    BODY_PARTS = {
        "head": {
            "name": "🧠 سر",
            "hp": 80,
            "multiplier": 1.5,
        },

        "face": {
            "name": "😶 صورت",
            "hp": 70,
            "multiplier": 1.4,
        },

        "chest": {
            "name": "🫁 سینه",
            "hp": 120,
            "multiplier": 1.1,
        },

        "abdomen": {
            "name": "🫃 شکم",
            "hp": 110,
            "multiplier": 1.0,
        },

        "right_arm": {
            "name": "💪 دست راست",
            "hp": 90,
            "multiplier": 0.8,
        },

        "left_arm": {
            "name": "💪 دست چپ",
            "hp": 90,
            "multiplier": 0.8,
        },

        "right_leg": {
            "name": "🦵 پای راست",
            "hp": 100,
            "multiplier": 0.9,
        },

        "left_leg": {
            "name": "🦵 پای چپ",
            "hp": 100,
            "multiplier": 0.9,
        },

        "right_shoulder": {
            "name": "🔹 شانه راست",
            "hp": 90,
            "multiplier": 0.8,
        },

        "left_shoulder": {
            "name": "🔹 شانه چپ",
            "hp": 90,
            "multiplier": 0.8,
        },
    }


# ============================================================
# ATTACK BODY PART KEYBOARD
# ============================================================

def attack_part_keyboard(
    attacker_id,
    attack_type,
    target_id,
):

    rows = []

    parts = [
        ("head", "🧠 سر"),
        ("face", "😶 صورت"),
        ("chest", "🫁 سینه"),
        ("abdomen", "🫃 شکم"),
        ("right_shoulder", "🔹 شانه راست"),
        ("left_shoulder", "🔹 شانه چپ"),
        ("right_arm", "💪 دست راست"),
        ("left_arm", "💪 دست چپ"),
        ("right_leg", "🦵 پای راست"),
        ("left_leg", "🦵 پای چپ"),
    ]

    current = []

    for part_id, name in parts:

        current.append(
            InlineKeyboardButton(
                name,
                callback_data=(
                    f"attackpart|"
                    f"{attack_type}|"
                    f"{part_id}|"
                    f"{target_id}|"
                    f"{attacker_id}"
                ),
            )
        )

        if len(current) == 2:

            rows.append(
                current
            )

            current = []

    if current:

        rows.append(
            current
        )

    rows.append(
        [
            InlineKeyboardButton(
                "❌ لغو",
                callback_data=(
                    f"fightcancel|"
                    f"{attacker_id}"
                ),
            )
        ]
    )

    return InlineKeyboardMarkup(
        rows
    )


# ============================================================
# ATTACK TYPE KEYBOARD
# ============================================================

def attack_type_keyboard(
    attacker_id,
    target_id,
):

    rows = []

    attacks = DEFAULT_ATTACKS

    for attack_id, attack in attacks.items():

        rows.append(
            [
                InlineKeyboardButton(
                    (
                        f"{attack.get('name')} "
                        f"(Lv.{attack.get('level', 1)})"
                    ),
                    callback_data=(
                        f"attacktype|"
                        f"{attack_id}|"
                        f"{target_id}|"
                        f"{attacker_id}"
                    ),
                )
            ]
        )

    rows.append(
        [
            InlineKeyboardButton(
                "❌ لغو",
                callback_data=(
                    f"fightcancel|"
                    f"{attacker_id}"
                ),
            )
        ]
    )

    return InlineKeyboardMarkup(
        rows
    )


# ============================================================
# COMBAT STATUS
# ============================================================

def combat_status_text(
    player,
):

    body = ensure_body_parts(
        player
    )

    hp = int(
        body.get(
            "hp",
            100,
        )
    )

    max_hp = int(
        body.get(
            "max_hp",
            100,
        )
    )

    injuries = body.get(
        "injuries",
        [],
    )

    lines = [
        "⚔️ وضعیت مبارزه",
        "",
        f"❤️ HP کلی: {hp}/{max_hp}",
        "",
        "🩸 آسیب‌ها:",
    ]

    if not injuries:

        lines.append(
            "هیچ آسیب فعالی نداری."
        )

    else:

        for injury in injuries:

            injury_type = injury.get(
                "type",
                "bruise",
            )

            data = INJURY_TYPES.get(
                injury_type,
                {},
            )

            lines.append(
                f"• {data.get('name', injury_type)} "
                f"در {body_part_name(injury.get('part', ''))}"
            )

    return "\n".join(
        lines
    )


# ============================================================
# COMBAT SESSION
# ============================================================

def create_combat_session(
    attacker_id,
    target_id,
):

    session_id = (
        "fight_"
        + uuid.uuid4().hex
    )

    return {
        "id": session_id,
        "attacker_id": int(
            attacker_id
        ),
        "target_id": int(
            target_id
        ),
        "created_at": time.time(),
        "status": "active",
    }


def store_combat_session(
    player,
    session,
):

    player.setdefault(
        "combat_sessions",
        {},
    )

    player[
        "combat_sessions"
    ][
        session["id"]
    ] = session


# ============================================================
# FIND PLAYER FROM REPLY
# ============================================================

def target_from_reply(
    message,
):

    if not message:

        return None

    reply = message.reply_to_message

    if not reply:

        return None

    target = reply.from_user

    if not target:

        return None

    return target


# ============================================================
# START FIGHT
# ============================================================

async def start_fight_from_reply(
    update,
    context,
):

    user = update.effective_user

    if not user:

        return

    message = update.message

    target_user = target_from_reply(
        message
    )

    if not target_user:

        await message.reply_text(
            "❌ برای مبارزه باید روی پیام "
            "بازیکن موردنظر Reply کنی."
        )

        return

    attacker_id = user.id
    target_id = target_user.id

    if attacker_id == target_id:

        await message.reply_text(
            "❌ نمی‌توانی با خودت مبارزه کنی."
        )

        return

    players = load_players()

    attacker_key = str(
        attacker_id
    )

    target_key = str(
        target_id
    )

    if attacker_key not in players:

        get_player(user)

        players = load_players()

    if target_key not in players:

        get_player(target_user)

        players = load_players()

    attacker = players[
        attacker_key
    ]

    target = players[
        target_key
    ]

    if attacker.get("banned"):

        await message.reply_text(
            "🚫 حساب شما مسدود است."
        )

        return

    if target.get("banned"):

        await message.reply_text(
            "❌ این بازیکن در دسترس نیست."
        )

        return

    ensure_body_parts(
        attacker
    )

    ensure_body_parts(
        target
    )

    if attacker["body"]["hp"] <= 0:

        await message.reply_text(
            "❌ HP شما صفر است و فعلاً "
            "قادر به مبارزه نیستید."
        )

        return

    if target["body"]["hp"] <= 0:

        await message.reply_text(
            "❌ این بازیکن فعلاً قادر به مبارزه نیست."
        )

        return

    session = create_combat_session(
        attacker_id,
        target_id,
    )

    store_combat_session(
        attacker,
        session,
    )

    players[
        attacker_key
    ] = attacker

    save_players(
        players
    )

    target_name = target.get(
        "name",
        target_user.first_name or "بازیکن",
    )

    await message.reply_text(
        "⚔️ مبارزه\n\n"
        f"🎯 هدف: {target_name}\n\n"
        "نوع حمله را انتخاب کن:",
        reply_markup=attack_type_keyboard(
            attacker_id,
            target_id,
        ),
    )


# ============================================================
# CHECK ATTACK LEVEL
# ============================================================

def attack_unlocked(
    player,
    attack_type,
):

    attack = DEFAULT_ATTACKS.get(
        attack_type
    )

    if not attack:

        return False

    required_level = int(
        attack.get(
            "level",
            1,
        )
    )

    current_level = int(
        player.get(
            "level",
            1,
        )
    )

    return (
        current_level
        >= required_level
    )


# ============================================================
# EQUIPMENT DEFENSE
# ============================================================

def equipment_for_region(
    player,
    part_id,
):

    equipment = player.get(
        "equipment",
        [],
    )

    protection = 0

    for item_id in equipment:

        item = EQUIPMENT.get(
            item_id
        )

        if not item:

            continue

        protected_parts = item.get(
            "protected_parts",
            [],
        )

        if part_id not in protected_parts:

            continue

        protection += int(
            item.get(
                "protection",
                0,
            )
        )

    return min(
        protection,
        80,
    )


# ============================================================
# DAMAGE CALCULATION
# ============================================================

def calculate_damage(
    attacker,
    target,
    attack_type,
    part_id,
):

    attack = DEFAULT_ATTACKS.get(
        attack_type
    )

    if not attack:

        return 0, 0

    base_damage = random.randint(
        int(
            attack.get(
                "min_damage",
                1,
            )
        ),
        int(
            attack.get(
                "max_damage",
                1,
            )
        ),
    )

    part = BODY_PARTS.get(
        part_id,
        {},
    )

    multiplier = float(
        part.get(
            "multiplier",
            1.0,
        )
    )

    raw_damage = int(
        base_damage
        * multiplier
    )

    protection = equipment_for_region(
        target,
        part_id,
    )

    final_damage = int(
        raw_damage
        * (
            100 - protection
        )
        / 100
    )

    if final_damage < 1:

        final_damage = 1

    return (
        final_damage,
        protection,
    )


# ============================================================
# INJURY GENERATION
# ============================================================

def injury_from_damage(
    damage,
    part_id,
    attack_type,
):

    roll = random.randint(
        1,
        100,
    )

    if damage >= 25:

        if roll <= 10:

            return "fracture"

        if roll <= 22:

            return "dislocation"

        if roll <= 38:

            return "bleeding"

        if roll <= 65:

            return "wound"

        return "bruise"

    if damage >= 15:

        if roll <= 5:

            return "fracture"

        if roll <= 15:

            return "dislocation"

        if roll <= 30:

            return "bleeding"

        if roll <= 60:

            return "wound"

        return "bruise"

    if damage >= 8:

        if roll <= 15:

            return "bleeding"

        if roll <= 50:

            return "wound"

        return "bruise"

    if roll <= 50:

        return "bruise"

    return None


# ============================================================
# APPLY INJURY
# ============================================================

def apply_injury(
    target,
    injury_type,
    part_id,
    damage,
):

    if not injury_type:

        return None

    data = INJURY_TYPES.get(
        injury_type
    )

    if not data:

        return None

    body = ensure_body_parts(
        target
    )

    injury_id = (
        "injury_"
        + uuid.uuid4().hex
    )

    injury = {
        "id": injury_id,
        "type": injury_type,
        "part": part_id,
        "damage": damage,
        "created_at": timestamp(),
        "treated": False,
    }

    body.setdefault(
        "injuries",
        [],
    ).append(
        injury
    )

    return injury


# ============================================================
# APPLY DAMAGE
# ============================================================

def apply_damage(
    target,
    damage,
    part_id,
    attack_type,
):

    body = ensure_body_parts(
        target
    )

    part = body[
        "parts"
    ].get(
        part_id
    )

    if not part:

        part = {
            "hp": body_part_max_hp(
                part_id
            ),
            "max_hp": body_part_max_hp(
                part_id
            ),
        }

        body[
            "parts"
        ][part_id] = part

    current_part_hp = int(
        part.get(
            "hp",
            part.get(
                "max_hp",
                100,
            ),
        )
    )

    part_max_hp = int(
        part.get(
            "max_hp",
            100,
        )
    )

    current_part_hp -= damage

    if current_part_hp < 0:

        current_part_hp = 0

    part[
        "hp"
    ] = current_part_hp

    current_total_hp = int(
        body.get(
            "hp",
            100,
        )
    )

    current_total_hp -= damage

    if current_total_hp < 0:

        current_total_hp = 0

    body[
        "hp"
    ] = current_total_hp

    injury_type = injury_from_damage(
        damage,
        part_id,
        attack_type,
    )

    injury = apply_injury(
        target,
        injury_type,
        part_id,
        damage,
    )

    return {
        "damage": damage,
        "part_hp": current_part_hp,
        "part_max_hp": part_max_hp,
        "total_hp": current_total_hp,
        "injury": injury,
    }


# ============================================================
# ATTACK EXECUTION
# ============================================================

def execute_attack(
    attacker_id,
    target_id,
    attack_type,
    part_id,
):

    players = load_players()

    attacker_key = str(
        attacker_id
    )

    target_key = str(
        target_id
    )

    if attacker_key not in players:

        return False, (
            "بازیکن حمله‌کننده پیدا نشد."
        )

    if target_key not in players:

        return False, (
            "هدف پیدا نشد."
        )

    attacker = players[
        attacker_key
    ]

    target = players[
        target_key
    ]

    if int(attacker_id) == int(
        target_id
    ):

        return False, (
            "نمی‌توانی به خودت حمله کنی."
        )

    if target.get("banned"):

        return False, (
            "این بازیکن در دسترس نیست."
        )

    if not BODY_PARTS.get(
        part_id
    ):

        return False, (
            "قسمت بدن نامعتبر است."
        )

    if not DEFAULT_ATTACKS.get(
        attack_type
    ):

        return False, (
            "نوع حمله نامعتبر است."
        )

    if not attack_unlocked(
        attacker,
        attack_type,
    ):

        required_level = DEFAULT_ATTACKS[
            attack_type
        ].get(
            "level",
            1,
        )

        return False, (
            f"❌ این حمله در Level "
            f"{required_level} باز می‌شود."
        )

    ensure_body_parts(
        attacker
    )

    ensure_body_parts(
        target
    )

    if target["body"]["hp"] <= 0:

        return False, (
            "این بازیکن دیگر HP کافی ندارد."
        )

    damage, protection = calculate_damage(
        attacker,
        target,
        attack_type,
        part_id,
    )

    result = apply_damage(
        target,
        damage,
        part_id,
        attack_type,
    )

    attack_reference = (
        "attack_"
        + uuid.uuid4().hex
    )

    attack_data = {
        "id": attack_reference,
        "attacker_id": int(
            attacker_id
        ),
        "target_id": int(
            target_id
        ),
        "attack_type": attack_type,
        "part": part_id,
        "damage": damage,
        "protection": protection,
        "created_at": timestamp(),
    }

    attacker.setdefault(
        "combat_history",
        [],
    ).append(
        attack_data
    )

    target.setdefault(
        "combat_history",
        [],
    ).append(
        attack_data
    )

    attacker[
        "combat_history"
    ] = attacker[
        "combat_history"
    ][-100:]

    target[
        "combat_history"
    ] = target[
        "combat_history"
    ][-100:]

    # XP برای حمله
    xp_gain = max(
        1,
        int(
            damage / 2
        ),
    )

    # اینجا فقط XP را روی بازیکن حمله‌کننده
    # اعمال می‌کنیم.
    level_before = attacker.get(
        "level",
        1,
    )

    add_xp(
        attacker,
        xp_gain,
    )

    level_after = attacker.get(
        "level",
        1,
    )

    add_transaction(
        attacker,
        "combat",
        0,
        (
            f"حمله به "
            f"{target.get('name', target_id)}؛ "
            f"{body_part_name(part_id)}؛ "
            f"{damage} آسیب"
        ),
        direction="info",
        reference_id=attack_reference,
    )

    players[
        attacker_key
    ] = attacker

    players[
        target_key
    ] = target

    save_players(
        players
    )

    return True, {
        "attacker": attacker,
        "target": target,
        "damage": damage,
        "protection": protection,
        "part_id": part_id,
        "part_name": body_part_name(
            part_id
        ),
        "attack_type": attack_type,
        "injury": result.get(
            "injury"
        ),
        "target_hp": result.get(
            "total_hp"
        ),
        "target_part_hp": result.get(
            "part_hp"
        ),
        "target_part_max_hp": result.get(
            "part_max_hp"
        ),
        "xp_gain": xp_gain,
        "level_up": (
            level_after
            > level_before
        ),
        "reference_id": attack_reference,
    }


# ============================================================
# ATTACK CALLBACK
# ============================================================

async def handle_attack_type_callback(
    query,
    attack_type,
    target_id,
):

    if not callback_is_owner(
        query
    ):

        await answer_callback(
            query,
            "❌ این دکمه متعلق به شما نیست.",
            True,
        )

        return

    attacker_id = query.from_user.id

    players = load_players()

    attacker = players.get(
        str(attacker_id)
    )

    target = players.get(
        str(target_id)
    )

    if not attacker or not target:

        await answer_callback(
            query,
            "❌ بازیکن پیدا نشد.",
            True,
        )

        return

    if not attack_unlocked(
        attacker,
        attack_type,
    ):

        required_level = DEFAULT_ATTACKS.get(
            attack_type,
            {}
        ).get(
            "level",
            1,
        )

        await answer_callback(
            query,
            f"این حمله در Level {required_level} باز می‌شود.",
            True,
        )

        return

    attack_name = DEFAULT_ATTACKS.get(
        attack_type,
        {}
    ).get(
        "name",
        "حمله",
    )

    target_name = target.get(
        "name",
        str(target_id),
    )

    await answer_callback(
        query
    )

    await query.edit_message_text(
        f"⚔️ {attack_name}\n\n"
        f"🎯 هدف: {target_name}\n\n"
        "قسمت بدن موردنظر برای حمله را انتخاب کن:",
        reply_markup=attack_part_keyboard(
            attacker_id,
            attack_type,
            target_id,
        ),
    )

# ============================================================
# ATTACK PART CALLBACK
# ============================================================

async def handle_attack_part_callback(
    query,
    attack_type,
    part_id,
    target_id,
):

    if not callback_is_owner(
        query
    ):

        await answer_callback(
            query,
            "❌ این دکمه متعلق به شما نیست.",
            True,
        )

        return

    attacker_id = query.from_user.id

    success, result = execute_attack(
        attacker_id,
        int(target_id),
        attack_type,
        part_id,
    )

    if not success:

        await answer_callback(
            query,
            result,
            True,
        )

        return

    damage = result[
        "damage"
    ]

    part_name = result[
        "part_name"
    ]

    target_hp = result[
        "target_hp"
    ]

    protection = result[
        "protection"
    ]

    injury = result.get(
        "injury"
    )

    target = result[
        "target"
    ]

    attacker = result[
        "attacker"
    ]

    attack_name = DEFAULT_ATTACKS.get(
        attack_type,
        {}
    ).get(
        "name",
        "حمله",
    )

    attacker_name = attacker.get(
        "name",
        query.from_user.first_name or "بازیکن",
    )

    injury_text = ""

    if injury:

        injury_data = INJURY_TYPES.get(
            injury.get(
                "type"
            ),
            {},
        )

        injury_text = (
            "\n"
            f"🩸 جراحت: "
            f"{injury_data.get('name', 'آسیب')}"
        )

    protection_text = ""

    if protection > 0:

        protection_text = (
            "\n"
            f"🛡️ کاهش آسیب لباس/تجهیزات: "
            f"{protection}%"
        )

    await answer_callback(
        query,
        "⚔️ حمله انجام شد.",
    )

    await query.edit_message_text(
        f"{attack_name} به {part_name}\n\n"
        f"💥 آسیب واردشده: {damage}\n"
        f"❤️ HP هدف: {target_hp}\n"
        f"{protection_text}"
        f"{injury_text}\n\n"
        f"🎁 XP دریافت‌شده: "
        f"{result.get('xp_gain', 0)}",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "⚔️ حمله دوباره",
                    callback_data=(
                        f"attacktype|"
                        f"{attack_type}|"
                        f"{target_id}|"
                        f"{attacker_id}"
                    ),
                )
            ],
            [
                InlineKeyboardButton(
                    "🏙️ منوی اصلی",
                    callback_data=(
                        f"main|{attacker_id}"
                    ),
                )
            ],
        ]),
    )

    # --------------------------------------------------------
    # اعلان برای هدف
    # --------------------------------------------------------

    try:

        target_user_id = int(
            target_id
        )

        notification = (
            "⚠️ مورد حمله قرار گرفتی!\n\n"
            f"👤 مهاجم: {attacker_name}\n"
            f"⚔️ نوع حمله: {attack_name}\n"
            f"🎯 محل اصابت: {part_name}\n"
            f"💥 آسیب: {damage}\n"
            f"❤️ HP فعلی: {target_hp}"
        )

        if injury:

            injury_data = INJURY_TYPES.get(
                injury.get(
                    "type"
                ),
                {},
            )

            notification += (
                "\n"
                f"🩸 جراحت: "
                f"{injury_data.get('name', 'آسیب')}"
            )

        await context.bot.send_message(
            chat_id=target_user_id,
            text=notification,
        )

    except Exception:

        pass


# ============================================================
# FIGHT CANCEL
# ============================================================

async def handle_fight_cancel(
    query,
):

    if not callback_is_owner(
        query
    ):

        await answer_callback(
            query,
            "❌ دسترسی ندارید.",
            True,
        )

        return

    await answer_callback(
        query,
        "مبارزه لغو شد.",
    )

    await query.edit_message_text(
        "❌ مبارزه لغو شد.",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "🏙️ منوی اصلی",
                    callback_data=(
                        f"main|"
                        f"{query.from_user.id}"
                    ),
                )
            ]
        ]),
    )


# ============================================================
# INJURY TEXT
# ============================================================

def injury_list_text(
    player,
):

    body = ensure_body_parts(
        player
    )

    injuries = body.get(
        "injuries",
        [],
    )

    if not injuries:

        return (
            "🩹 جراحت‌ها\n\n"
            "هیچ جراحت فعالی نداری."
        )

    lines = [
        "🩹 جراحت‌های فعال",
        "",
    ]

    for injury in injuries:

        if injury.get(
            "treated"
        ):

            continue

        injury_type = injury.get(
            "type",
            "bruise",
        )

        data = INJURY_TYPES.get(
            injury_type,
            {},
        )

        part_id = injury.get(
            "part",
            "",
        )

        lines.append(
            f"🩸 {data.get('name', injury_type)}"
        )

        lines.append(
            f"   📍 {body_part_name(part_id)}"
        )

        lines.append("")

    if len(lines) == 2:

        lines.append(
            "هیچ جراحت فعال درمان‌نشده‌ای نداری."
        )

    return "\n".join(
        lines
    )


# ============================================================
# CLINIC TREATMENT
# ============================================================

def clinic_cost_for_player(
    player,
):

    body = ensure_body_parts(
        player
    )

    total = 0

    for injury in body.get(
        "injuries",
        [],
    ):

        if injury.get(
            "treated"
        ):

            continue

        data = INJURY_TYPES.get(
            injury.get(
                "type"
            ),
            {},
        )

        total += int(
            data.get(
                "clinic_cost",
                0,
            )
        )

    return total


def treat_all_injuries(
    player,
):

    body = ensure_body_parts(
        player
    )

    active = []

    total_cost = 0

    for injury in body.get(
        "injuries",
        [],
    ):

        if injury.get(
            "treated"
        ):

            continue

        injury_type = injury.get(
            "type"
        )

        data = INJURY_TYPES.get(
            injury_type,
            {},
        )

        total_cost += int(
            data.get(
                "clinic_cost",
                0,
            )
        )

        injury[
            "treated"
        ] = True

        injury[
            "treated_at"
        ] = timestamp()

        active.append(
            injury
        )

    # بازیابی بخشی از HP
    if active:

        body[
            "hp"
        ] = body.get(
            "max_hp",
            100,
        )

        for part_id, part in body.get(
            "parts",
            {},
        ).items():

            part[
                "hp"
            ] = part.get(
                "max_hp",
                100,
            )

    return total_cost, len(active)


# ============================================================
# CLINIC KEYBOARD
# ============================================================

def clinic_keyboard(
    user_id,
):

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🩺 وضعیت جراحات",
                callback_data=(
                    f"injuries|{user_id}"
                ),
            )
        ],
        [
            InlineKeyboardButton(
                "💊 درمان کامل",
                callback_data=(
                    f"treatall|{user_id}"
                ),
            )
        ],
        [
            InlineKeyboardButton(
                "🔙 منوی اصلی",
                callback_data=(
                    f"main|{user_id}"
                ),
            )
        ],
    ])


async def show_clinic(
    query,
):

    if not callback_is_owner(
        query
    ):

        await answer_callback(
            query,
            "❌ دسترسی ندارید.",
            True,
        )

        return

    player = get_player(
        query.from_user
    )

    body = ensure_body_parts(
        player
    )

    hp = body.get(
        "hp",
        100,
    )

    max_hp = body.get(
        "max_hp",
        100,
    )

    cost = clinic_cost_for_player(
        player
    )

    await answer_callback(
        query
    )

    await query.edit_message_text(
        "🏥 کلینیک UNDERCITY\n\n"
        f"❤️ سلامت: {hp}/{max_hp}\n"
        f"💰 هزینه درمان کامل: {cost:,}\n\n"
        "برای مشاهده آسیب‌ها یا درمان کامل "
        "از دکمه‌های زیر استفاده کن.",
        reply_markup=clinic_keyboard(
            query.from_user.id
        ),
    )


# ============================================================
# SHOW INJURIES
# ============================================================

async def show_injuries(
    query,
):

    if not callback_is_owner(
        query
    ):

        await answer_callback(
            query,
            "❌ دسترسی ندارید.",
            True,
        )

        return

    player = get_player(
        query.from_user
    )

    await answer_callback(
        query
    )

    await query.edit_message_text(
        injury_list_text(
            player
        ),
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "🏥 کلینیک",
                    callback_data=(
                        f"clinic|"
                        f"{query.from_user.id}"
                    ),
                )
            ]
        ]),
    )


# ============================================================
# TREAT ALL
# ============================================================

async def treat_all_callback(
    query,
):

    if not callback_is_owner(
        query
    ):

        await answer_callback(
            query,
            "❌ دسترسی ندارید.",
            True,
        )

        return

    players = load_players()

    key = str(
        query.from_user.id
    )

    player = players.get(
        key
    )

    if not player:

        await answer_callback(
            query,
            "❌ حساب پیدا نشد.",
            True,
        )

        return

    cost = clinic_cost_for_player(
        player
    )

    if cost <= 0:

        await answer_callback(
            query,
            "آسیب فعالی برای درمان وجود ندارد.",
            True,
        )

        return

    if player.get(
        "cash",
        0,
    ) + player.get(
        "bank_balance",
        0,
    ) < cost:

        await answer_callback(
            query,
            "❌ پول کافی برای درمان نداری.",
            True,
        )

        return

    # ابتدا از بانک پرداخت می‌شود
    if player.get(
        "bank_balance",
        0,
    ) >= cost:

        player[
            "bank_balance"
        ] -= cost

    else:

        remaining = cost - player.get(
            "bank_balance",
            0,
        )

        player[
            "bank_balance"
        ] = 0

        player[
            "cash"
        ] -= remaining

    treated_cost, count = treat_all_injuries(
        player
    )

    add_transaction(
        player,
        "clinic",
        treated_cost,
        f"درمان {count} آسیب",
        direction="out",
        reference_id=(
            "clinic_"
            + uuid.uuid4().hex
        ),
    )

    players[key] = player

    save_players(
        players
    )

    await answer_callback(
        query,
        "✅ درمان انجام شد.",
    )

    await query.edit_message_text(
        "🏥 درمان با موفقیت انجام شد.\n\n"
        f"🩹 تعداد آسیب‌های درمان‌شده: {count}\n"
        f"💰 هزینه: {treated_cost:,}\n"
        f"❤️ HP: "
        f"{player.get('body', {}).get('hp', 100)}/"
        f"{player.get('body', {}).get('max_hp', 100)}",
        reply_markup=clinic_keyboard(
            query.from_user.id
        ),
    )


# ============================================================
# BODY STATUS
# ============================================================

def body_status_text(
    player,
):

    body = ensure_body_parts(
        player
    )

    lines = [
        "🫀 وضعیت بدن",
        "",
        (
            f"❤️ HP کلی: "
            f"{body.get('hp', 100)}/"
            f"{body.get('max_hp', 100)}"
        ),
        "",
    ]

    for part_id, part_data in BODY_PARTS.items():

        current = body[
            "parts"
        ].get(
            part_id,
            {}
        ).get(
            "hp",
            part_data.get(
                "hp",
                100,
            ),
        )

        maximum = body[
            "parts"
        ].get(
            part_id,
            {}
        ).get(
            "max_hp",
            part_data.get(
                "hp",
                100,
            ),
        )

        lines.append(
            f"{part_data.get('name', part_id)}: "
            f"{current}/{maximum}"
        )

    return "\n".join(
        lines
    )


# ============================================================
# COMBAT MENU
# ============================================================

def combat_menu_keyboard(
    user_id,
):

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "❤️ وضعیت بدن",
                callback_data=(
                    f"bodystatus|{user_id}"
                ),
            )
        ],
        [
            InlineKeyboardButton(
                "🩹 جراحات",
                callback_data=(
                    f"injuries|{user_id}"
                ),
            )
        ],
        [
            InlineKeyboardButton(
                "🏥 کلینیک",
                callback_data=(
                    f"clinic|{user_id}"
                ),
            )
        ],
        [
            InlineKeyboardButton(
                "🔙 منوی اصلی",
                callback_data=(
                    f"main|{user_id}"
                ),
            )
        ],
    ])


async def show_combat_menu(
    query,
):

    if not callback_is_owner(
        query
    ):

        await answer_callback(
            query,
            "❌ دسترسی ندارید.",
            True,
        )

        return

    player = get_player(
        query.from_user
    )

    await answer_callback(
        query
    )

    await query.edit_message_text(
        combat_status_text(
            player
        ),
        reply_markup=combat_menu_keyboard(
            query.from_user.id
        ),
    )


# ============================================================
# BODY STATUS CALLBACK
# ============================================================

async def show_body_status(
    query,
):

    if not callback_is_owner(
        query
    ):

        await answer_callback(
            query,
            "❌ دسترسی ندارید.",
            True,
        )

        return

    player = get_player(
        query.from_user
    )

    await answer_callback(
        query
    )

    await query.edit_message_text(
        body_status_text(
            player
        ),
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "⚔️ مبارزه",
                    callback_data=(
                        f"fight|"
                        f"{query.from_user.id}"
                    ),
                )
            ],
            [
                InlineKeyboardButton(
                    "🏥 کلینیک",
                    callback_data=(
                        f"clinic|"
                        f"{query.from_user.id}"
                    ),
                )
            ],
            [
                InlineKeyboardButton(
                    "🔙 بازگشت",
                    callback_data=(
                        f"main|"
                        f"{query.from_user.id}"
                    ),
                )
            ],
        ]),
    )


# ============================================================
# EQUIPMENT DEFENSE TEXT
# ============================================================

def equipment_defense_text(
    player,
):

    equipment = player.get(
        "equipment",
        [],
    )

    if not equipment:

        return (
            "🛡️ تجهیزات دفاعی\n\n"
            "در حال حاضر تجهیزاتی نداری."
        )

    lines = [
        "🛡️ تجهیزات دفاعی",
        "",
    ]

    for item_id in equipment:

        item = EQUIPMENT.get(
            item_id
        )

        if not item:

            continue

        lines.append(
            f"• {item.get('name', item_id)}"
        )

        lines.append(
            f"  🛡️ محافظت: "
            f"{item.get('protection', 0)}%"
        )

        protected = item.get(
            "protected_parts",
            [],
        )

        if protected:

            names = [
                body_part_name(
                    part
                )
                for part in protected
            ]

            lines.append(
                "  📍 "
                + "، ".join(names)
            )

        lines.append("")

    return "\n".join(
        lines
    )


# ============================================================
# EQUIPMENT CALLBACK
# ============================================================

async def show_equipment(
    query,
):

    if not callback_is_owner(
        query
    ):

        await answer_callback(
            query,
            "❌ دسترسی ندارید.",
            True,
        )

        return

    player = get_player(
        query.from_user
    )

    await answer_callback(
        query
    )

    await query.edit_message_text(
        equipment_defense_text(
            player
        ),
        reply_markup=back_button(
            query.from_user.id,
            "main",
        ),
    )


# ============================================================
# COMBAT COMMAND TEXT
# ============================================================

def combat_command_help():

    return (
        "⚔️ مبارزه\n\n"
        "برای شروع مبارزه:\n"
        "1. روی پیام بازیکن Reply کن.\n"
        "2. بنویس: ریپ\n"
        "3. نوع حمله را انتخاب کن.\n"
        "4. قسمت بدن هدف را انتخاب کن.\n\n"
        "هر حمله Damage متفاوتی دارد و تجهیزات "
        "می‌توانند بخشی از آسیب را کاهش دهند."
    )


# ============================================================
# PART 4 END
# ============================================================# ============================================================
# PART 5
# JOBS / CAREERS / TRAINING / WORK SYSTEM
# ============================================================

import random
import time


# ------------------------------------------------------------
# JOB RANKS
# ------------------------------------------------------------

JOB_RANKS = [
    {
        "id": "apprentice",
        "name": "🧹 کارآموز",
        "min_xp": 0,
        "multiplier": 0.75,
    },
    {
        "id": "beginner",
        "name": "🔧 مبتدی",
        "min_xp": 100,
        "multiplier": 0.90,
    },
    {
        "id": "intermediate",
        "name": "🛠 نیمه‌ماهر",
        "min_xp": 300,
        "multiplier": 1.00,
    },
    {
        "id": "skilled",
        "name": "⚙️ ماهر",
        "min_xp": 700,
        "multiplier": 1.15,
    },
    {
        "id": "professional",
        "name": "💼 حرفه‌ای",
        "min_xp": 1500,
        "multiplier": 1.35,
    },
    {
        "id": "master",
        "name": "👑 استادکار",
        "min_xp": 3000,
        "multiplier": 1.60,
    },
]


# ------------------------------------------------------------
# JOB DEFINITIONS
# ------------------------------------------------------------

JOB_DEFINITIONS = {
    "barber": {
        "name": "💈 آرایشگری",
        "emoji": "💈",
        "description": (
            "اصلاح مو، کوتاهی، مدل‌دهی و خدمات آرایشی"
        ),
        "base_income": 90_000,
        "max_income": 450_000,
        "base_xp": 20,
        "max_customers": 5,
        "training_cost": 250_000,
        "training_xp": 70,
        "practice_cost": 30_000,
        "practice_xp": 25,
    },

    "mechanic": {
        "name": "🔧 مکانیکی",
        "emoji": "🔧",
        "description": (
            "عیب‌یابی، تعمیر، سرویس و کار روی خودرو"
        ),
        "base_income": 130_000,
        "max_income": 700_000,
        "base_xp": 25,
        "max_customers": 4,
        "training_cost": 400_000,
        "training_xp": 90,
        "practice_cost": 50_000,
        "practice_xp": 30,
    },
}


# ------------------------------------------------------------
# SAFE JOB INITIALIZATION
# ------------------------------------------------------------

def ensure_jobs(player):
    """
    ساختار شغل‌های بازیکن را بدون پاک کردن اطلاعات قبلی
    تکمیل می‌کند.
    """

    player.setdefault("jobs", {})

    for job_id in JOB_DEFINITIONS:
        if job_id not in player["jobs"]:
            player["jobs"][job_id] = {
                "unlocked": False,
                "rank": "apprentice",
                "xp": 0,
                "total_work": 0,
                "total_customers": 0,
                "total_income": 0,
                "total_loss": 0,
                "training_count": 0,
                "practice_count": 0,
                "last_work": 0,
                "last_training": 0,
                "last_practice": 0,
            }

        job = player["jobs"][job_id]

        job.setdefault("unlocked", False)
        job.setdefault("rank", "apprentice")
        job.setdefault("xp", 0)
        job.setdefault("total_work", 0)
        job.setdefault("total_customers", 0)
        job.setdefault("total_income", 0)
        job.setdefault("total_loss", 0)
        job.setdefault("training_count", 0)
        job.setdefault("practice_count", 0)
        job.setdefault("last_work", 0)
        job.setdefault("last_training", 0)
        job.setdefault("last_practice", 0)

    return player


# ------------------------------------------------------------
# RANK HELPERS
# ------------------------------------------------------------

def get_job_rank(job_xp):
    """
    تعیین رتبه بر اساس XP شغل.
    """

    current = JOB_RANKS[0]

    for rank in JOB_RANKS:
        if job_xp >= rank["min_xp"]:
            current = rank
        else:
            break

    return current


def get_next_job_rank(job_xp):
    """
    رتبه بعدی را برمی‌گرداند.
    """

    for rank in JOB_RANKS:
        if job_xp < rank["min_xp"]:
            return rank

    return None


def update_job_rank(job):
    """
    رتبه شغل را با توجه به XP به‌روزرسانی می‌کند.
    """

    old_rank = job.get("rank", "apprentice")

    rank = get_job_rank(
        int(job.get("xp", 0))
    )

    job["rank"] = rank["id"]

    return old_rank, rank["id"]


def rank_name(rank_id):
    for rank in JOB_RANKS:
        if rank["id"] == rank_id:
            return rank["name"]

    return "🧹 کارآموز"


def rank_multiplier(rank_id):
    for rank in JOB_RANKS:
        if rank["id"] == rank_id:
            return rank["multiplier"]

    return 0.75


# ------------------------------------------------------------
# JOB XP
# ------------------------------------------------------------

def add_job_xp(player, job_id, amount):
    """
    XP مخصوص همان شغل.
    """

    ensure_jobs(player)

    if job_id not in JOB_DEFINITIONS:
        return {
            "amount": 0,
            "old_rank": "apprentice",
            "new_rank": "apprentice",
            "promoted": False,
        }

    job = player["jobs"][job_id]

    old_rank = job.get(
        "rank",
        "apprentice"
    )

    amount = max(0, int(amount))

    job["xp"] = int(
        job.get("xp", 0)
    ) + amount

    before_rank = old_rank

    update_job_rank(job)

    new_rank = job.get(
        "rank",
        "apprentice"
    )

    return {
        "amount": amount,
        "old_rank": before_rank,
        "new_rank": new_rank,
        "promoted": before_rank != new_rank,
    }


# ------------------------------------------------------------
# JOB UNLOCK
# ------------------------------------------------------------

def unlock_job(player, job_id):
    """
    باز کردن یک شغل.
    """

    ensure_jobs(player)

    if job_id not in JOB_DEFINITIONS:
        return False, "شغل وجود ندارد."

    job = player["jobs"][job_id]

    if job["unlocked"]:
        return False, "این شغل قبلاً برای شما فعال شده است."

    job["unlocked"] = True

    save_players(load_players())

    return True, "شغل با موفقیت فعال شد."


# ------------------------------------------------------------
# JOB ACCESS
# ------------------------------------------------------------

def job_is_unlocked(player, job_id):
    ensure_jobs(player)

    if job_id not in player["jobs"]:
        return False

    return bool(
        player["jobs"][job_id].get(
            "unlocked",
            False
        )
    )


# ------------------------------------------------------------
# AUTO UNLOCK FIRST JOB
# ------------------------------------------------------------

def initialize_player_jobs(player):
    """
    شغل اولیه برای بازیکن جدید.
    """

    ensure_jobs(player)

    # برای جلوگیری از تغییر ناخواسته بازیکنان قدیمی
    # فقط در صورتی که هیچ شغلی فعال نیست
    if not any(
        job.get("unlocked", False)
        for job in player["jobs"].values()
    ):
        player["jobs"]["barber"]["unlocked"] = True

    return player


# ------------------------------------------------------------
# JOB DISPLAY
# ------------------------------------------------------------

def job_status_text(player, job_id):
    ensure_jobs(player)

    if job_id not in JOB_DEFINITIONS:
        return "❌ شغل پیدا نشد."

    info = JOB_DEFINITIONS[job_id]
    job = player["jobs"][job_id]

    rank = get_job_rank(
        int(job.get("xp", 0))
    )

    next_rank = get_next_job_rank(
        int(job.get("xp", 0))
    )

    lines = []

    lines.append(
        f"{info['emoji']} <b>{info['name']}</b>"
    )

    lines.append(
        f"📌 وضعیت: "
        f"{'فعال' if job.get('unlocked') else 'قفل'}"
    )

    lines.append(
        f"🏅 رتبه: {rank['name']}"
    )

    lines.append(
        f"⭐ XP شغل: {job.get('xp', 0)}"
    )

    if next_rank:
        remaining = (
            next_rank["min_xp"]
            - int(job.get("xp", 0))
        )

        lines.append(
            f"⬆️ تا رتبه بعدی: {remaining} XP"
        )

    lines.append("")

    lines.append(
        f"👥 مشتری انجام‌شده: "
        f"{job.get('total_customers', 0)}"
    )

    lines.append(
        f"🧰 دفعات کار: "
        f"{job.get('total_work', 0)}"
    )

    lines.append(
        f"💰 درآمد کل: "
        f"{job.get('total_income', 0):,}"
    )

    lines.append(
        f"📉 ضرر کل: "
        f"{job.get('total_loss', 0):,}"
    )

    return "\n".join(lines)


# ------------------------------------------------------------
# JOB LIST KEYBOARD
# ------------------------------------------------------------

def jobs_keyboard(user_id):
    ensure = load_players()

    buttons = []

    buttons.append([
        InlineKeyboardButton(
            "💈 آرایشگری",
            callback_data=f"job|barber|{user_id}"
        )
    ])

    buttons.append([
        InlineKeyboardButton(
            "🔧 مکانیکی",
            callback_data=f"job|mechanic|{user_id}"
        )
    ])

    buttons.append([
        InlineKeyboardButton(
            "📚 آموزش و دوره‌ها",
            callback_data=f"jobtraining|{user_id}"
        )
    ])

    buttons.append([
        InlineKeyboardButton(
            "🔙 بازگشت",
            callback_data=f"main|{user_id}"
        )
    ])

    return InlineKeyboardMarkup(buttons)


# ------------------------------------------------------------
# JOB MENU
# ------------------------------------------------------------

async def show_jobs(update, context):
    query = update.callback_query

    if query:
        user_id = query.from_user.id

        if not callback_is_owner(
            query,
            user_id
        ):
            await answer_callback(
                query,
                "❌ دسترسی ندارید.",
                True
            )
            return

        await query.answer()

        text = (
            "💼 <b>مرکز مشاغل UNDERCITY</b>\n\n"
            "در این بخش می‌توانید شغل انتخاب کنید، "
            "مهارت یاد بگیرید، کار کنید و رتبه خود را "
            "از کارآموز تا استادکار افزایش دهید."
        )

        await query.edit_message_text(
            text,
            parse_mode="HTML",
            reply_markup=jobs_keyboard(user_id)
        )


# ------------------------------------------------------------
# SINGLE JOB MENU KEYBOARD
# ------------------------------------------------------------

def single_job_keyboard(
    job_id,
    user_id
):

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "💼 شروع کار",
                callback_data=(
                    f"work|{job_id}|{user_id}"
                )
            )
        ],
        [
            InlineKeyboardButton(
                "📚 تمرین",
                callback_data=(
                    f"practice|{job_id}|{user_id}"
                )
            )
        ],
        [
            InlineKeyboardButton(
                "🎓 دوره آموزشی",
                callback_data=(
                    f"training|{job_id}|{user_id}"
                )
            )
        ],
        [
            InlineKeyboardButton(
                "📊 وضعیت شغل",
                callback_data=(
                    f"jobstats|{job_id}|{user_id}"
                )
            )
        ],
        [
            InlineKeyboardButton(
                "🔙 مشاغل",
                callback_data=(
                    f"jobs|{user_id}"
                )
            )
        ],
    ])


# ------------------------------------------------------------
# SHOW SINGLE JOB
# ------------------------------------------------------------

async def show_single_job(
    update,
    context,
    job_id
):

    query = update.callback_query

    if not query:
        return

    user_id = query.from_user.id

    if not callback_is_owner(
        query,
        user_id
    ):
        await answer_callback(
            query,
            "❌ دسترسی ندارید.",
            True
        )
        return

    await query.answer()

    players = load_players()

    key = str(user_id)

    player = players.get(key)

    if not player:
        player = get_player(
            query.from_user
        )
        players = load_players()
        player = players[str(user_id)]

    ensure_jobs(player)

    if job_id not in JOB_DEFINITIONS:
        await query.edit_message_text(
            "❌ شغل نامعتبر است."
        )
        return

    text = job_status_text(
        player,
        job_id
    )

    await query.edit_message_text(
        text,
        parse_mode="HTML",
        reply_markup=single_job_keyboard(
            job_id,
            user_id
        )
    )


# ------------------------------------------------------------
# WORK DURATION
# ------------------------------------------------------------

WORK_DURATIONS = {
    "quick": {
        "name": "⚡ شیفت کوتاه",
        "minutes": 10,
        "multiplier": 0.60,
    },

    "normal": {
        "name": "🕐 شیفت عادی",
        "minutes": 30,
        "multiplier": 1.00,
    },

    "long": {
        "name": "⏱ شیفت طولانی",
        "minutes": 60,
        "multiplier": 1.45,
    },
}


# ------------------------------------------------------------
# WORK DURATION KEYBOARD
# ------------------------------------------------------------

def work_duration_keyboard(
    job_id,
    user_id
):

    buttons = []

    for duration_id, info in WORK_DURATIONS.items():

        buttons.append([
            InlineKeyboardButton(
                (
                    f"{info['name']} "
                    f"({info['minutes']} دقیقه)"
                ),
                callback_data=(
                    f"workstart|"
                    f"{job_id}|"
                    f"{duration_id}|"
                    f"{user_id}"
                )
            )
        ])

    buttons.append([
        InlineKeyboardButton(
            "🔙 بازگشت",
            callback_data=(
                f"job|{job_id}|{user_id}"
            )
        )
    ])

    return InlineKeyboardMarkup(buttons)


# ------------------------------------------------------------
# SHOW WORK OPTIONS
# ------------------------------------------------------------

async def show_work_options(
    update,
    context,
    job_id
):

    query = update.callback_query

    if not query:
        return

    user_id = query.from_user.id

    if not callback_is_owner(
        query,
        user_id
    ):
        await answer_callback(
            query,
            "❌ دسترسی ندارید.",
            True
        )
        return

    await query.answer()

    players = load_players()

    player = players.get(
        str(user_id)
    )

    if not player:
        await query.edit_message_text(
            "❌ اطلاعات بازیکن پیدا نشد."
        )
        return

    ensure_jobs(player)

    if not job_is_unlocked(
        player,
        job_id
    ):
        await query.edit_message_text(
            "🔒 این شغل هنوز برای شما فعال نشده است."
        )
        return

    info = JOB_DEFINITIONS[job_id]

    text = (
        f"{info['emoji']} <b>{info['name']}</b>\n\n"
        "مدت شیفت را انتخاب کنید:\n\n"
        "هرچه شیفت طولانی‌تر باشد، "
        "مشتری و درآمد بیشتری خواهید داشت؛ "
        "اما احتمال هزینه و خستگی نیز بیشتر می‌شود."
    )

    await query.edit_message_text(
        text,
        parse_mode="HTML",
        reply_markup=work_duration_keyboard(
            job_id,
            user_id
        )
    )


# ------------------------------------------------------------
# WORK COOLDOWN
# ------------------------------------------------------------

WORK_COOLDOWN = 5


def work_cooldown_remaining(
    job,
    now=None
):

    if now is None:
        now = time.time()

    last = float(
        job.get(
            "last_work",
            0
        )
    )

    elapsed = now - last

    if elapsed >= WORK_COOLDOWN:
        return 0

    return int(
        WORK_COOLDOWN - elapsed
    ) + 1


# ------------------------------------------------------------
# CUSTOMER GENERATION
# ------------------------------------------------------------

def generate_customers(
    job_id,
    duration_id,
    rank_id
):

    duration = WORK_DURATIONS[
        duration_id
    ]

    base = {
        "quick": 1,
        "normal": 2,
        "long": 3,
    }.get(
        duration_id,
        1
    )

    rank_bonus = {
        "apprentice": 0,
        "beginner": 0,
        "intermediate": 1,
        "skilled": 1,
        "professional": 2,
        "master": 2,
    }.get(
        rank_id,
        0
    )

    customers = (
        base
        + random.randint(0, 1)
        + rank_bonus
    )

    max_customers = JOB_DEFINITIONS[
        job_id
    ]["max_customers"]

    return max(
        1,
        min(
            customers,
            max_customers
        )
    )


# ------------------------------------------------------------
# JOB TASKS
# ------------------------------------------------------------

BARBER_TASKS = [
    ("✂️ کوتاهی مو", 1.0),
    ("💈 اصلاح صورت", 0.8),
    ("💇 مدل‌دهی مو", 1.25),
    ("🧴 شست‌وشوی مو", 0.7),
    ("🎨 رنگ و فرم‌دهی", 1.40),
]


MECHANIC_TASKS = [
    ("🔧 تعویض روغن", 0.8),
    ("🛞 بررسی لاستیک", 0.7),
    ("🔋 بررسی باتری", 0.9),
    ("⚙️ عیب‌یابی موتور", 1.25),
    ("🛠 تعمیر سیستم ترمز", 1.35),
    ("🚗 سرویس کامل خودرو", 1.55),
]


def random_job_task(job_id):
    if job_id == "barber":
        return random.choice(
            BARBER_TASKS
        )

    if job_id == "mechanic":
        return random.choice(
            MECHANIC_TASKS
        )

    return (
        "🔨 کار عمومی",
        1.0
    )

# ------------------------------------------------------------
# WORK PAYMENT
# ------------------------------------------------------------

def calculate_customer_income(
    player,
    job_id,
    duration_id,
    difficulty
):

    info = JOB_DEFINITIONS[
        job_id
    ]

    job = player["jobs"][job_id]

    rank_id = job.get(
        "rank",
        "apprentice"
    )

    multiplier = rank_multiplier(
        rank_id
    )

    duration_multiplier = (
        WORK_DURATIONS[
            duration_id
        ]["multiplier"]
    )

    base = random.randint(
        info["base_income"],
        info["max_income"]
    )

    income = (
        base
        * multiplier
        * duration_multiplier
        * difficulty
    )

    # نوسان طبیعی درآمد
    income *= random.uniform(
        0.75,
        1.15
    )

    return max(
        1,
        int(income)
    )


# ------------------------------------------------------------
# WORK LOSS / EXPENSE
# ------------------------------------------------------------

def calculate_work_expense(
    player,
    job_id,
    customers,
    duration_id
):

    duration_multiplier = WORK_DURATIONS[
        duration_id
    ]["multiplier"]

    base = {
        "barber": 20_000,
        "mechanic": 45_000,
    }.get(
        job_id,
        20_000
    )

    expense = (
        base
        * customers
        * duration_multiplier
    )

    expense *= random.uniform(
        0.70,
        1.30
    )

    return max(
        0,
        int(expense)
    )


# ------------------------------------------------------------
# PERFORM WORK
# ------------------------------------------------------------

def perform_work(
    player,
    job_id,
    duration_id
):

    ensure_jobs(player)

    if job_id not in JOB_DEFINITIONS:
        return {
            "success": False,
            "message": "شغل نامعتبر است."
        }

    if duration_id not in WORK_DURATIONS:
        return {
            "success": False,
            "message": "مدت شیفت نامعتبر است."
        }

    job = player["jobs"][job_id]

    if not job.get("unlocked"):
        return {
            "success": False,
            "message": "این شغل برای شما فعال نیست."
        }

    remaining = work_cooldown_remaining(
        job
    )

    if remaining > 0:
        return {
            "success": False,
            "message": (
                f"⏳ کمی صبر کنید.\n"
                f"زمان باقی‌مانده: {remaining} ثانیه"
            )
        }

    rank_id = job.get(
        "rank",
        "apprentice"
    )

    customers = generate_customers(
        job_id,
        duration_id,
        rank_id
    )

    income = 0
    expense = calculate_work_expense(
        player,
        job_id,
        customers,
        duration_id
    )

    tasks = []

    xp_total = 0

    for _ in range(customers):

        task_name, difficulty = random_job_task(
            job_id
        )

        tasks.append(
            (
                task_name,
                difficulty
            )
        )

        customer_income = (
            calculate_customer_income(
                player,
                job_id,
                duration_id,
                difficulty
            )
        )

        income += customer_income

        base_xp = JOB_DEFINITIONS[
            job_id
        ]["base_xp"]

        task_xp = int(
            base_xp
            * difficulty
            * WORK_DURATIONS[
                duration_id
            ]["multiplier"]
        )

        xp_total += max(
            1,
            task_xp
        )

    net = income - expense

    # --------------------------------------------------------
    # MONEY
    # --------------------------------------------------------

    old_cash = int(
        player.get(
            "cash",
            0
        )
    )

    player["cash"] = (
        old_cash
        + net
    )

    # --------------------------------------------------------
    # JOB STATS
    # --------------------------------------------------------

    job["total_work"] = int(
        job.get(
            "total_work",
            0
        )
    ) + 1

    job["total_customers"] = int(
        job.get(
            "total_customers",
            0
        )
    ) + customers

    job["total_income"] = int(
        job.get(
            "total_income",
            0
        )
    ) + income

    job["total_loss"] = int(
        job.get(
            "total_loss",
            0
        )
    ) + expense

    job["last_work"] = time.time()

    xp_result = add_job_xp(
        player,
        job_id,
        xp_total
    )

    # --------------------------------------------------------
    # GLOBAL XP
    # --------------------------------------------------------

    global_xp = max(
        1,
        int(xp_total * 0.35)
    )

    try:
        add_xp(
            player,
            global_xp
        )
    except Exception:
        pass

    # --------------------------------------------------------
    # TRANSACTION
    # --------------------------------------------------------

    if net >= 0:

        add_transaction(
            player,
            "job_income",
            net,
            (
                f"درآمد {JOB_DEFINITIONS[job_id]['name']} "
                f"از {customers} مشتری"
            ),
            direction="in"
        )

    else:

        add_transaction(
            player,
            "job_loss",
            abs(net),
            (
                f"زیان {JOB_DEFINITIONS[job_id]['name']} "
                f"در یک شیفت"
            ),
            direction="out"
        )

    return {
        "success": True,
        "customers": customers,
        "income": income,
        "expense": expense,
        "net": net,
        "xp": xp_total,
        "global_xp": global_xp,
        "tasks": tasks,
        "promoted": xp_result["promoted"],
        "old_rank": xp_result["old_rank"],
        "new_rank": xp_result["new_rank"],
    }


# ------------------------------------------------------------
# WORK RESULT TEXT
# ------------------------------------------------------------

def work_result_text(
    player,
    job_id,
    duration_id,
    result
):

    info = JOB_DEFINITIONS[
        job_id
    ]

    lines = []

    lines.append(
        f"{info['emoji']} <b>گزارش شیفت</b>"
    )

    lines.append("")

    lines.append(
        f"🕐 مدت: "
        f"{WORK_DURATIONS[duration_id]['name']}"
    )

    lines.append(
        f"👥 مشتری: "
        f"{result['customers']}"
    )

    lines.append("")

    lines.append(
        "📋 <b>کارهای انجام‌شده:</b>"
    )

    for task, difficulty in result["tasks"]:
        lines.append(
            f"• {task}"
        )

    lines.append("")

    lines.append(
        f"💰 درآمد ناخالص: "
        f"{result['income']:,}"
    )

    lines.append(
        f"📉 هزینه: "
        f"{result['expense']:,}"
    )

    if result["net"] >= 0:
        lines.append(
            f"💵 سود خالص: "
            f"+{result['net']:,}"
        )
    else:
        lines.append(
            f"🔻 ضرر خالص: "
            f"{result['net']:,}"
        )

    lines.append("")

    lines.append(
        f"⭐ XP شغل: +{result['xp']}"
    )

    lines.append(
        f"🌟 XP کلی: +{result['global_xp']}"
    )

    if result["promoted"]:
        lines.append("")

        lines.append(
            "🎉 <b>تبریک!</b>"
        )

        lines.append(
            f"🏅 رتبه شغلی شما ارتقا یافت:\n"
            f"{rank_name(result['old_rank'])} "
            f"➡️ "
            f"{rank_name(result['new_rank'])}"
        )

    return "\n".join(lines)


# ------------------------------------------------------------
# WORK START CALLBACK
# ------------------------------------------------------------

async def handle_work_start_callback(
    update,
    context
):

    query = update.callback_query

    if not query:
        return

    parts = query.data.split("|")

    if len(parts) != 4:
        await query.answer(
            "❌ درخواست نامعتبر است.",
            show_alert=True
        )
        return

    job_id = parts[1]
    duration_id = parts[2]
    user_id = int(parts[3])

    if not callback_is_owner(
        query,
        user_id
    ):
        await query.answer(
            "❌ دسترسی ندارید.",
            show_alert=True
        )
        return

    await query.answer(
        "🔧 در حال انجام شیفت..."
    )

    players = load_players()

    player = players.get(
        str(user_id)
    )

    if not player:
        await query.edit_message_text(
            "❌ بازیکن پیدا نشد."
        )
        return

    result = perform_work(
        player,
        job_id,
        duration_id
    )

    if not result["success"]:
        await query.edit_message_text(
            result["message"],
            reply_markup=single_job_keyboard(
                job_id,
                user_id
            )
        )
        return

    players[str(user_id)] = player

    save_players(
        players
    )

    text = work_result_text(
        player,
        job_id,
        duration_id,
        result
    )

    await query.edit_message_text(
        text,
        parse_mode="HTML",
        reply_markup=single_job_keyboard(
            job_id,
            user_id
        )
    )


# ------------------------------------------------------------
# PRACTICE SYSTEM
# ------------------------------------------------------------

def practice_job(
    player,
    job_id
):

    ensure_jobs(player)

    if job_id not in JOB_DEFINITIONS:
        return {
            "success": False,
            "message": "شغل نامعتبر است."
        }

    job = player["jobs"][job_id]

    if not job.get("unlocked"):
        return {
            "success": False,
            "message": "ابتدا این شغل را فعال کنید."
        }

    info = JOB_DEFINITIONS[
        job_id
    ]

    cost = int(
        info["practice_cost"]
    )

    if int(player.get("cash", 0)) < cost:
        return {
            "success": False,
            "message": (
                f"💰 برای تمرین به "
                f"{cost:,} پول نیاز دارید."
            )
        }

    player["cash"] -= cost

    xp = int(
        info["practice_xp"]
        * random.uniform(
            0.80,
            1.20
        )
    )

    job["practice_count"] = int(
        job.get(
            "practice_count",
            0
        )
    ) + 1

    job["last_practice"] = time.time()

    xp_result = add_job_xp(
        player,
        job_id,
        xp
    )

    add_transaction(
        player,
        "job_practice",
        cost,
        f"تمرین شغل {info['name']}",
        direction="out"
    )

    try:
        add_xp(
            player,
            max(1, xp // 3)
        )
    except Exception:
        pass

    return {
        "success": True,
        "cost": cost,
        "xp": xp,
        "promoted": xp_result["promoted"],
        "old_rank": xp_result["old_rank"],
        "new_rank": xp_result["new_rank"],
    }


# ------------------------------------------------------------
# PRACTICE CALLBACK
# ------------------------------------------------------------

async def handle_practice_callback(
    update,
    context
):

    query = update.callback_query

    if not query:
        return

    parts = query.data.split("|")

    if len(parts) != 3:
        await query.answer(
            "❌ درخواست نامعتبر.",
            show_alert=True
        )
        return

    job_id = parts[1]
    user_id = int(parts[2])

    if not callback_is_owner(
        query,
        user_id
    ):
        await query.answer(
            "❌ دسترسی ندارید.",
            show_alert=True
        )
        return

    await query.answer()

    players = load_players()

    player = players.get(
        str(user_id)
    )

    if not player:
        return

    result = practice_job(
        player,
        job_id
    )

    if not result["success"]:

        await query.answer(
            result["message"],
            show_alert=True
        )
        return

    players[str(user_id)] = player

    save_players(
        players
    )

    text = (
        "🏋️ <b>تمرین انجام شد</b>\n\n"
        f"💰 هزینه: {result['cost']:,}\n"
        f"⭐ XP شغل: +{result['xp']}\n"
    )

    if result["promoted"]:
        text += (
            "\n🎉 <b>ارتقای رتبه!</b>\n"
            f"{rank_name(result['old_rank'])}"
            f" ➡️ "
            f"{rank_name(result['new_rank'])}"
        )

    await query.edit_message_text(
        text,
        parse_mode="HTML",
        reply_markup=single_job_keyboard(
            job_id,
            user_id
        )
    )


# ------------------------------------------------------------
# TRAINING SYSTEM
# ------------------------------------------------------------

TRAINING_COOLDOWN = 5


def training_job(
    player,
    job_id
):

    ensure_jobs(player)

    if job_id not in JOB_DEFINITIONS:
        return {
            "success": False,
            "message": "شغل نامعتبر است."
        }

    job = player["jobs"][job_id]

    if not job.get("unlocked"):
        return {
            "success": False,
            "message": "این شغل فعال نیست."
        }

    now = time.time()

    last_training = float(
        job.get(
            "last_training",
            0
        )
    )

    if now - last_training < TRAINING_COOLDOWN:
        remaining = int(
            TRAINING_COOLDOWN
            - (now - last_training)
        ) + 1

        return {
            "success": False,
            "message": (
                f"⏳ برای دوره بعدی "
                f"{remaining} ثانیه صبر کنید."
            )
        }

    info = JOB_DEFINITIONS[
        job_id
    ]

    cost = int(
        info["training_cost"]
    )

    if int(player.get("cash", 0)) < cost:
        return {
            "success": False,
            "message": (
                f"💰 هزینه دوره "
                f"{cost:,} است."
            )
        }

    player["cash"] -= cost

    base_xp = int(
        info["training_xp"]
    )

    xp = random.randint(
        int(base_xp * 0.90),
        int(base_xp * 1.15)
    )

    job["training_count"] = int(
        job.get(
            "training_count",
            0
        )
    ) + 1

    job["last_training"] = now

    xp_result = add_job_xp(
        player,
        job_id,
        xp
    )

    add_transaction(
        player,
        "job_training",
        cost,
        f"دوره آموزشی {info['name']}",
        direction="out"
    )

    try:
        add_xp(
            player,
            max(1, xp // 2)
        )
    except Exception:
        pass

    return {
        "success": True,
        "cost": cost,
        "xp": xp,
        "promoted": xp_result["promoted"],
        "old_rank": xp_result["old_rank"],
        "new_rank": xp_result["new_rank"],
    }


# ------------------------------------------------------------
# TRAINING CALLBACK
# ------------------------------------------------------------

async def handle_training_callback(
    update,
    context
):

    query = update.callback_query

    if not query:
        return

    parts = query.data.split("|")

    if len(parts) != 3:
        await query.answer(
            "❌ درخواست نامعتبر.",
            show_alert=True
        )
        return

    job_id = parts[1]
    user_id = int(parts[2])

    if not callback_is_owner(
        query,
        user_id
    ):
        await query.answer(
            "❌ دسترسی ندارید.",
            show_alert=True
        )
        return

    await query.answer()

    players = load_players()

    player = players.get(
        str(user_id)
    )

    if not player:
        return

    result = training_job(
        player,
        job_id
    )

    if not result["success"]:

        await query.answer(
            result["message"],
            show_alert=True
        )
        return

    players[str(user_id)] = player

    save_players(
        players
    )

    text = (
        "🎓 <b>دوره آموزشی با موفقیت انجام شد</b>\n\n"
        f"💰 هزینه دوره: {result['cost']:,}\n"
        f"⭐ XP شغل: +{result['xp']}\n"
    )

    if result["promoted"]:
        text += (
            "\n🎉 <b>ارتقای رتبه!</b>\n"
            f"{rank_name(result['old_rank'])}"
            f" ➡️ "
            f"{rank_name(result['new_rank'])}"
        )

    await query.edit_message_text(
        text,
        parse_mode="HTML",
        reply_markup=single_job_keyboard(
            job_id,
            user_id
        )
    )


# ------------------------------------------------------------
# JOB STATS CALLBACK
# ------------------------------------------------------------

async def handle_job_stats_callback(
    update,
    context
):

    query = update.callback_query

    if not query:
        return

    parts = query.data.split("|")

    if len(parts) != 3:
        await query.answer(
            "❌ درخواست نامعتبر.",
            show_alert=True
        )
        return

    job_id = parts[1]
    user_id = int(parts[2])

    if not callback_is_owner(
        query,
        user_id
    ):
        await query.answer(
            "❌ دسترسی ندارید.",
            show_alert=True
        )
        return

    await query.answer()

    players = load_players()

    player = players.get(
        str(user_id)
    )

    if not player:
        return

    ensure_jobs(player)

    text = job_status_text(
        player,
        job_id
    )

    await query.edit_message_text(
        text,
        parse_mode="HTML",
        reply_markup=single_job_keyboard(
            job_id,
            user_id
        )
    )


# ------------------------------------------------------------
# TRAINING MENU
# ------------------------------------------------------------

def training_menu_keyboard(user_id):

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "💈 دوره آرایشگری",
                callback_data=(
                    f"training|barber|{user_id}"
                )
            )
        ],
        [
            InlineKeyboardButton(
                "🔧 دوره مکانیکی",
                callback_data=(
                    f"training|mechanic|{user_id}"
                )
            )
        ],
        [
            InlineKeyboardButton(
                "🔙 بازگشت",
                callback_data=(
                    f"jobs|{user_id}"
                )
            )
        ],
    ])


async def show_training_menu(
    update,
    context
):

    query = update.callback_query

    if not query:
        return

    user_id = query.from_user.id

    if not callback_is_owner(
        query,
        user_id
    ):
        await query.answer(
            "❌ دسترسی ندارید.",
            show_alert=True
        )
        return

    await query.answer()

    text = (
        "🎓 <b>مرکز آموزش UNDERCITY</b>\n\n"
        "با گذراندن دوره‌ها می‌توانید "
        "مهارت شغلی خود را سریع‌تر افزایش دهید.\n\n"
        "📈 دوره‌ها XP بیشتری نسبت به تمرین "
        "معمولی می‌دهند."
    )

    await query.edit_message_text(
        text,
        parse_mode="HTML",
        reply_markup=training_menu_keyboard(
            user_id
        )
    )


# ------------------------------------------------------------
# JOB COMMAND TEXT
# ------------------------------------------------------------

def jobs_help_text():

    return (
        "💼 <b>سیستم مشاغل UNDERCITY</b>\n\n"

        "💈 <b>آرایشگری</b>\n"
        "کوتاهی، اصلاح، مدل‌دهی و خدمات مو.\n\n"

        "🔧 <b>مکانیکی</b>\n"
        "عیب‌یابی، سرویس و تعمیر خودرو.\n\n"

        "🏅 <b>رتبه‌ها</b>\n"
        "🧹 کارآموز\n"
        "🔧 مبتدی\n"
        "🛠 نیمه‌ماهر\n"
        "⚙️ ماهر\n"
        "💼 حرفه‌ای\n"
        "👑 استادکار\n\n"

        "⭐ با کار کردن، تمرین و آموزش XP می‌گیرید.\n"
        "هرچه رتبه بالاتر باشد، درآمد و تعداد "
        "مشتری بیشتر می‌شود."
    )


# ------------------------------------------------------------
# JOB CALLBACK ROUTER
# ------------------------------------------------------------

async def handle_job_callback(
    update,
    context
):

    query = update.callback_query

    if not query:
        return

    data = query.data
    parts = data.split("|")

    if not parts:
        return

    action = parts[0]

    if action == "jobs":
        await show_jobs(
            update,
            context
        )
        return

    if action == "job":
        if len(parts) != 3:
            await query.answer(
                "❌ درخواست نامعتبر.",
                show_alert=True
            )
            return

        job_id = parts[1]

        await show_single_job(
            update,
            context,
            job_id
        )
        return

    if action == "work":
        if len(parts) != 3:
            await query.answer(
                "❌ درخواست نامعتبر.",
                show_alert=True
            )
            return

        job_id = parts[1]

        await show_work_options(
            update,
            context,
            job_id
        )
        return

    if action == "workstart":
        await handle_work_start_callback(
            update,
            context
        )
        return

    if action == "practice":
        await handle_practice_callback(
            update,
            context
        )
        return

    if action == "training":
        await handle_training_callback(
            update,
            context
        )
        return

    if action == "jobtraining":
        await show_training_menu(
            update,
            context
        )
        return

    if action == "jobstats":
        await handle_job_stats_callback(
            update,
            context
        )
        return


# ------------------------------------------------------------
# PLAYER JOB INITIALIZATION HELPER
# ------------------------------------------------------------

def prepare_player_for_jobs(
    player
):

    ensure_jobs(player)
    initialize_player_jobs(player)

    return player


# ------------------------------------------------------------
# END OF PART 5
# ============================================================# ============================================================
# PART 6
# VEHICLE MARKET / PLAYER SALES / GIFT / TRADE
# ============================================================

import time
import uuid


# ------------------------------------------------------------
# VEHICLE TRANSACTION STATES
# ------------------------------------------------------------

VEHICLE_DEAL_STATES = {
    "pending": "در انتظار",
    "accepted": "تأیید شده",
    "rejected": "رد شده",
    "cancelled": "لغو شده",
    "completed": "تکمیل شده",
    "failed": "ناموفق",
}


# ------------------------------------------------------------
# VEHICLE HELPERS
# ------------------------------------------------------------

def ensure_vehicle_system(player):
    """
    ساختارهای لازم برای سیستم معاملات خودرو.
    اطلاعات قبلی بازیکن حذف نمی‌شود.
    """

    player.setdefault(
        "vehicles",
        []
    )

    player.setdefault(
        "vehicle_offers",
        []
    )

    player.setdefault(
        "market_listings",
        []
    )

    player.setdefault(
        "vehicle_deals",
        []
    )

    player.setdefault(
        "vehicle_history",
        []
    )

    return player


def get_player_vehicle(
    player,
    vehicle_id
):
    """
    پیدا کردن خودرو از گاراژ بازیکن.
    """

    ensure_vehicle_system(player)

    for vehicle in player["vehicles"]:

        if str(
            vehicle.get("id")
        ) == str(vehicle_id):

            return vehicle

    return None


def player_owns_vehicle(
    player,
    vehicle_id
):

    return (
        get_player_vehicle(
            player,
            vehicle_id
        ) is not None
    )


# ------------------------------------------------------------
# REMOVE / ADD VEHICLE
# ------------------------------------------------------------

def remove_vehicle_from_player(
    player,
    vehicle_id
):

    ensure_vehicle_system(player)

    for index, vehicle in enumerate(
        player["vehicles"]
    ):

        if str(
            vehicle.get("id")
        ) == str(vehicle_id):

            return player["vehicles"].pop(
                index
            )

    return None


def add_vehicle_to_player(
    player,
    vehicle
):

    ensure_vehicle_system(player)

    player["vehicles"].append(
        vehicle
    )

    return vehicle


# ------------------------------------------------------------
# DEAL ID
# ------------------------------------------------------------

def generate_deal_id():

    return (
        "DEAL-"
        + uuid.uuid4().hex[:16].upper()
    )


def generate_offer_id():

    return (
        "OFFER-"
        + uuid.uuid4().hex[:16].upper()
    )


def generate_listing_id():

    return (
        "LIST-"
        + uuid.uuid4().hex[:16].upper()
    )


# ------------------------------------------------------------
# FIND PLAYERS
# ------------------------------------------------------------

def find_player_by_id(
    players,
    user_id
):

    return players.get(
        str(user_id)
    )


def player_display_name(
    player,
    fallback="بازیکن"
):

    if not player:
        return fallback

    name = (
        player.get("name")
        or player.get("username")
        or fallback
    )

    return str(name)


# ------------------------------------------------------------
# VEHICLE DISPLAY
# ------------------------------------------------------------

def vehicle_name(vehicle):

    brand = vehicle.get(
        "brand",
        ""
    )

    model = vehicle.get(
        "model",
        ""
    )

    year = vehicle.get(
        "year",
        ""
    )

    return (
        f"{brand} {model} "
        f"{year}"
    ).strip()


def vehicle_details_text(
    vehicle
):

    lines = []

    lines.append(
        f"🚗 <b>{vehicle_name(vehicle)}</b>"
    )

    if vehicle.get("color"):
        lines.append(
            f"🎨 رنگ: "
            f"{vehicle['color']}"
        )

    if vehicle.get("mileage") is not None:
        lines.append(
            f"🛣 کارکرد: "
            f"{vehicle['mileage']:,} km"
        )

    if vehicle.get("condition"):
        lines.append(
            f"🔧 وضعیت: "
            f"{vehicle['condition']}"
        )

    if vehicle.get("engine"):
        lines.append(
            f"⚙️ موتور: "
            f"{vehicle['engine']}"
        )

    if vehicle.get("power"):
        lines.append(
            f"🐎 قدرت: "
            f"{vehicle['power']}"
        )

    if vehicle.get("transmission"):
        lines.append(
            f"🔄 گیربکس: "
            f"{vehicle['transmission']}"
        )

    if vehicle.get("tuning"):
        lines.append(
            f"🏁 تیونینگ: "
            f"{vehicle['tuning']}"
        )

    if vehicle.get("price") is not None:
        lines.append(
            f"💰 قیمت پایه: "
            f"{int(vehicle['price']):,}"
        )

    return "\n".join(lines)


# ------------------------------------------------------------
# VEHICLE OWNERSHIP SNAPSHOT
# ------------------------------------------------------------

def vehicle_owner_snapshot(
    player,
    vehicle
):

    return {
        "vehicle_id": str(
            vehicle.get("id")
        ),
        "owner_id": str(
            player.get(
                "_user_id",
                ""
            )
        ),
        "owner_name": player_display_name(
            player
        ),
        "timestamp": time.time(),
    }


# ------------------------------------------------------------
# ACTIVE DEAL FINDER
# ------------------------------------------------------------

def find_deal(
    players,
    deal_id
):

    for player_id, player in players.items():

        ensure_vehicle_system(player)

        for deal in player.get(
            "vehicle_deals",
            []
        ):

            if str(
                deal.get("id")
            ) == str(deal_id):

                return deal, player_id

    return None, None


# ------------------------------------------------------------
# ACTIVE OFFER FINDER
# ------------------------------------------------------------

def find_offer(
    players,
    offer_id
):

    for player_id, player in players.items():

        ensure_vehicle_system(player)

        for offer in player.get(
            "vehicle_offers",
            []
        ):

            if str(
                offer.get("id")
            ) == str(offer_id):

                return offer, player_id

    return None, None


# ------------------------------------------------------------
# ACTIVE LISTING FINDER
# ------------------------------------------------------------

def find_listing(
    players,
    listing_id
):

    for player_id, player in players.items():

        ensure_vehicle_system(player)

        for listing in player.get(
            "market_listings",
            []
        ):

            if str(
                listing.get("id")
            ) == str(listing_id):

                return listing, player_id

    return None, None


# ------------------------------------------------------------
# DEAL STATUS
# ------------------------------------------------------------

def deal_is_active(deal):

    return deal.get(
        "status"
    ) in (
        "pending",
        "accepted",
    )


# ------------------------------------------------------------
# DUPLICATE PROTECTION
# ------------------------------------------------------------

def transaction_reference_exists(
    player,
    reference
):

    for transaction in player.get(
        "transactions",
        []
    ):

        if str(
            transaction.get(
                "reference"
            )
        ) == str(reference):

            return True

    return False


def vehicle_deal_completed(
    players,
    deal_id
):

    for player in players.values():

        for deal in player.get(
            "vehicle_deals",
            []
        ):

            if str(
                deal.get("id")
            ) == str(deal_id):

                if deal.get(
                    "status"
                ) == "completed":

                    return True

    return False


# ------------------------------------------------------------
# MONEY CHECK
# ------------------------------------------------------------

def player_available_cash(
    player
):

    return max(
        0,
        int(
            player.get(
                "cash",
                0
            )
        )
    )


def can_afford(
    player,
    amount
):

    return (
        player_available_cash(
            player
        )
        >= int(amount)
    )


# ------------------------------------------------------------
# PLAYER TO PLAYER OFFER
# ------------------------------------------------------------

def create_vehicle_offer(
    players,
    seller_id,
    buyer_id,
    vehicle_id,
    amount
):

    seller = players.get(
        str(seller_id)
    )

    buyer = players.get(
        str(buyer_id)
    )

    if not seller:
        return {
            "success": False,
            "message": "فروشنده پیدا نشد."
        }

    if not buyer:
        return {
            "success": False,
            "message": "خریدار پیدا نشد."
        }

    if str(
        seller_id
    ) == str(
        buyer_id
    ):
        return {
            "success": False,
            "message": "نمی‌توانید به خودتان خودرو بفروشید."
        }

    ensure_vehicle_system(
        seller
    )

    ensure_vehicle_system(
        buyer
    )

    vehicle = get_player_vehicle(
        seller,
        vehicle_id
    )

    if not vehicle:
        return {
            "success": False,
            "message": "این خودرو متعلق به فروشنده نیست."
        }

    amount = int(amount)

    if amount <= 0:
        return {
            "success": False,
            "message": "قیمت باید بیشتر از صفر باشد."
        }

    if not can_afford(
        buyer,
        amount
    ):
        return {
            "success": False,
            "message": (
                "💰 موجودی نقدی خریدار "
                "برای این پیشنهاد کافی نیست."
            )
        }

    # جلوگیری از چند پیشنهاد همزمان
    for old_offer in seller["vehicle_offers"]:

        if old_offer.get(
            "status"
        ) != "pending":

            continue

        if str(
            old_offer.get("vehicle_id")
        ) != str(vehicle_id):

            continue

        if str(
            old_offer.get("buyer_id")
        ) != str(buyer_id):

            continue

        return {
            "success": False,
            "message": (
                "برای این خودرو قبلاً "
                "یک پیشنهاد فعال ثبت شده است."
            )
        }

    offer_id = generate_offer_id()

    offer = {
        "id": offer_id,
        "vehicle_id": str(vehicle_id),
        "seller_id": str(seller_id),
        "buyer_id": str(buyer_id),
        "amount": amount,
        "status": "pending",
        "created_at": time.time(),
        "updated_at": time.time(),
    }

    seller["vehicle_offers"].append(
        offer
    )

    # یک نسخه برای خریدار هم ذخیره می‌کنیم
    buyer.setdefault(
        "vehicle_offers_sent",
        []
    )

    buyer["vehicle_offers_sent"].append(
        offer.copy()
    )

    return {
        "success": True,
        "offer": offer,
    }


# ------------------------------------------------------------
# ACCEPT VEHICLE OFFER
# ------------------------------------------------------------

def accept_vehicle_offer(
    players,
    offer_id,
    seller_id
):

    offer, owner_id = find_offer(
        players,
        offer_id
    )

    if not offer:

        return {
            "success": False,
            "message": "پیشنهاد پیدا نشد."
        }

    if str(owner_id) != str(seller_id):

        return {
            "success": False,
            "message": "شما فروشنده این پیشنهاد نیستید."
        }

    if offer.get(
        "status"
    ) != "pending":

        return {
            "success": False,
            "message": (
                "این پیشنهاد دیگر فعال نیست."
            )
        }

    seller = players.get(
        str(offer["seller_id"])
    )

    buyer = players.get(
        str(offer["buyer_id"])
    )

    if not seller or not buyer:

        return {
            "success": False,
            "message": "یکی از طرفین معامله پیدا نشد."
        }

    vehicle = get_player_vehicle(
        seller,
        offer["vehicle_id"]
    )

    if not vehicle:

        offer["status"] = "failed"
        offer["updated_at"] = time.time()

        return {
            "success": False,
            "message": (
                "❌ خودرو دیگر در گاراژ فروشنده نیست."
            )
        }

    amount = int(
        offer["amount"]
    )

    # بررسی دوباره پول در لحظه قبول
    if not can_afford(
        buyer,
        amount
    ):

        offer["status"] = "failed"
        offer["updated_at"] = time.time()

        return {
            "success": False,
            "message": (
                "❌ خریدار دیگر پول کافی ندارد."
            )
        }

    deal_id = generate_deal_id()

    # --------------------------------------------------------
    # ایجاد معامله
    # --------------------------------------------------------

    deal = {
        "id": deal_id,
        "offer_id": offer_id,
        "vehicle_id": str(
            offer["vehicle_id"]
        ),
        "seller_id": str(
            offer["seller_id"]
        ),
        "buyer_id": str(
            offer["buyer_id"]
        ),
        "amount": amount,
        "status": "accepted",
        "created_at": time.time(),
        "accepted_at": time.time(),
        "completed_at": None,
    }

    seller.setdefault(
        "vehicle_deals",
        []
    )

    buyer.setdefault(
        "vehicle_deals",
        []
    )

    seller["vehicle_deals"].append(
        deal.copy()
    )

    buyer["vehicle_deals"].append(
        deal.copy()
    )

    # --------------------------------------------------------
    # قفل منطقی قبل از انتقال
    # --------------------------------------------------------

    offer["status"] = "accepted"
    offer["deal_id"] = deal_id
    offer["updated_at"] = time.time()

    # --------------------------------------------------------
    # دوباره بررسی مالکیت و پول
    # --------------------------------------------------------

    vehicle_check = get_player_vehicle(
        seller,
        offer["vehicle_id"]
    )

    if not vehicle_check:

        deal["status"] = "failed"
        offer["status"] = "failed"

        return {
            "success": False,
            "message": (
                "❌ خودرو قبل از نهایی شدن معامله "
                "دیگر متعلق به فروشنده نیست."
            )
        }

    if not can_afford(
        buyer,
        amount
    ):

        deal["status"] = "failed"
        offer["status"] = "failed"

        return {
            "success": False,
            "message": (
                "❌ موجودی خریدار کافی نیست."
            )
        }

    # --------------------------------------------------------
    # انتقال پول
    # --------------------------------------------------------

    buyer["cash"] = (
        int(
            buyer.get(
                "cash",
                0
            )
        )
        - amount
    )

    seller["cash"] = (
        int(
            seller.get(
                "cash",
                0
            )
        )
        + amount
    )

    # --------------------------------------------------------
    # انتقال خودرو
    # --------------------------------------------------------

    moved_vehicle = remove_vehicle_from_player(
        seller,
        offer["vehicle_id"]
    )

    if not moved_vehicle:

        # وضعیت بحرانی؛ پول را برمی‌گردانیم
        buyer["cash"] += amount
        seller["cash"] -= amount

        deal["status"] = "failed"
        offer["status"] = "failed"

        return {
            "success": False,
            "message": (
                "❌ انتقال خودرو انجام نشد؛ "
                "پول به خریدار برگشت."
            )
        }

    moved_vehicle["previous_owner_id"] = str(
        seller_id
    )

    moved_vehicle["owner_id"] = str(
        offer["buyer_id"]
    )

    moved_vehicle["purchase_price"] = amount
    moved_vehicle["purchase_timestamp"] = time.time()

    add_vehicle_to_player(
        buyer,
        moved_vehicle
    )

    # --------------------------------------------------------
    # تراکنش‌ها
    # --------------------------------------------------------

    reference = (
        f"vehicle_deal:{deal_id}"
    )

    add_transaction(
        buyer,
        "vehicle_purchase",
        amount,
        (
            f"خرید {vehicle_name(moved_vehicle)} "
            f"از {player_display_name(seller)}"
        ),
        direction="out",
        reference=reference
    )

    add_transaction(
        seller,
        "vehicle_sale",
        amount,
        (
            f"فروش {vehicle_name(moved_vehicle)} "
            f"به {player_display_name(buyer)}"
        ),
        direction="in",
        reference=reference
    )

    # --------------------------------------------------------
    # تکمیل معامله
    # --------------------------------------------------------

    deal["status"] = "completed"
    deal["completed_at"] = time.time()

    offer["status"] = "completed"
    offer["updated_at"] = time.time()

    return {
        "success": True,
        "deal": deal,
        "vehicle": moved_vehicle,
        "amount": amount,
    }


# ------------------------------------------------------------
# REJECT OFFER
# ------------------------------------------------------------

def reject_vehicle_offer(
    players,
    offer_id,
    seller_id
):

    offer, owner_id = find_offer(
        players,
        offer_id
    )

    if not offer:

        return {
            "success": False,
            "message": "پیشنهاد پیدا نشد."
        }

    if str(owner_id) != str(seller_id):

        return {
            "success": False,
            "message": "این پیشنهاد برای شما نیست."
        }

    if offer.get(
        "status"
    ) != "pending":

        return {
            "success": False,
            "message": "این پیشنهاد قبلاً تعیین تکلیف شده."
        }

    offer["status"] = "rejected"
    offer["updated_at"] = time.time()

    return {
        "success": True,
        "offer": offer,
    }


# ------------------------------------------------------------
# CANCEL OFFER
# ------------------------------------------------------------

def cancel_vehicle_offer(
    players,
    offer_id,
    user_id
):

    offer, owner_id = find_offer(
        players,
        offer_id
    )

    if not offer:

        return {
            "success": False,
            "message": "پیشنهاد پیدا نشد."
        }

    if str(
        offer.get("buyer_id")
    ) != str(user_id):

        return {
            "success": False,
            "message": "شما خریدار این پیشنهاد نیستید."
        }

    if offer.get(
        "status"
    ) != "pending":

        return {
            "success": False,
            "message": "این پیشنهاد دیگر فعال نیست."
        }

    offer["status"] = "cancelled"
    offer["updated_at"] = time.time()

    return {
        "success": True,
        "offer": offer,
    }


# ------------------------------------------------------------
# MARKET LISTING
# ------------------------------------------------------------

def create_market_listing(
    players,
    seller_id,
    vehicle_id,
    asking_price
):

    seller = players.get(
        str(seller_id)
    )

    if not seller:

        return {
            "success": False,
            "message": "فروشنده پیدا نشد."
        }

    ensure_vehicle_system(
        seller
    )

    vehicle = get_player_vehicle(
        seller,
        vehicle_id
    )

    if not vehicle:

        return {
            "success": False,
            "message": (
                "این خودرو در گاراژ شما نیست."
            )
        }

    asking_price = int(
        asking_price
    )

    if asking_price <= 0:

        return {
            "success": False,
            "message": (
                "قیمت باید بیشتر از صفر باشد."
            )
        }

    # یک خودرو نباید همزمان چند بار در بازار باشد
    for listing in seller[
        "market_listings"
    ]:

        if listing.get(
            "status"
        ) != "active":

            continue

        if str(
            listing.get("vehicle_id")
        ) == str(vehicle_id):

            return {
                "success": False,
                "message": (
                    "این خودرو قبلاً در بازار قرار گرفته."
                )
            }

    listing_id = generate_listing_id()

    listing = {
        "id": listing_id,
        "vehicle_id": str(vehicle_id),
        "seller_id": str(seller_id),
        "asking_price": asking_price,
        "status": "active",
        "created_at": time.time(),
        "updated_at": time.time(),
    }

    seller["market_listings"].append(
        listing
    )

    return {
        "success": True,
        "listing": listing,
    }


# ------------------------------------------------------------
# REMOVE MARKET LISTING
# ------------------------------------------------------------

def remove_market_listing(
    players,
    listing_id,
    seller_id
):

    listing, owner_id = find_listing(
        players,
        listing_id
    )

    if not listing:

        return {
            "success": False,
            "message": "آگهی پیدا نشد."
        }

    if str(owner_id) != str(seller_id):

        return {
            "success": False,
            "message": "این آگهی متعلق به شما نیست."
        }

    if listing.get(
        "status"
    ) != "active":

        return {
            "success": False,
            "message": "آگهی فعال نیست."
        }

    listing["status"] = "cancelled"
    listing["updated_at"] = time.time()

return {
        "success": True,
        "listing": listing,
    }


# ------------------------------------------------------------
# MARKET BUY
# ------------------------------------------------------------

def buy_market_vehicle(
    players,
    listing_id,
    buyer_id
):

    listing, seller_id = find_listing(
        players,
        listing_id
    )

    if not listing:

        return {
            "success": False,
            "message": "آگهی پیدا نشد."
        }

    if listing.get(
        "status"
    ) != "active":

        return {
            "success": False,
            "message": (
                "این خودرو دیگر برای فروش فعال نیست."
            )
        }

    seller = players.get(
        str(
            listing["seller_id"]
        )
    )

    buyer = players.get(
        str(buyer_id)
    )

    if not seller or not buyer:

        return {
            "success": False,
            "message": "خریدار یا فروشنده پیدا نشد."
        }

    if str(
        listing["seller_id"]
    ) == str(buyer_id):

        return {
            "success": False,
            "message": (
                "نمی‌توانید خودروی خودتان را بخرید."
            )
        }

    vehicle = get_player_vehicle(
        seller,
        listing["vehicle_id"]
    )

    if not vehicle:

        listing["status"] = "failed"

        return {
            "success": False,
            "message": (
                "خودرو دیگر در گاراژ فروشنده نیست."
            )
        }

    amount = int(
        listing["asking_price"]
    )

    if not can_afford(
        buyer,
        amount
    ):

        return {
            "success": False,
            "message": (
                "💰 موجودی شما برای خرید کافی نیست."
            )
        }

    # --------------------------------------------------------
    # Deal ID
    # --------------------------------------------------------

    deal_id = generate_deal_id()

    reference = (
        f"vehicle_market:{deal_id}"
    )

    # --------------------------------------------------------
    # دوباره چک کردن برای جلوگیری از خرید دوباره
    # --------------------------------------------------------

    if vehicle_deal_completed(
        players,
        deal_id
    ):

        return {
            "success": False,
            "message": "این معامله قبلاً انجام شده."
        }

    # --------------------------------------------------------
    # انتقال پول
    # --------------------------------------------------------

    buyer["cash"] -= amount
    seller["cash"] += amount

    # --------------------------------------------------------
    # انتقال خودرو
    # --------------------------------------------------------

    moved_vehicle = remove_vehicle_from_player(
        seller,
        listing["vehicle_id"]
    )

    if not moved_vehicle:

        buyer["cash"] += amount
        seller["cash"] -= amount

        listing["status"] = "failed"

        return {
            "success": False,
            "message": (
                "❌ انتقال خودرو انجام نشد؛ "
                "وجه برگشت داده شد."
            )
        }

    moved_vehicle["previous_owner_id"] = str(
        seller["vehicle_id"]
        if "vehicle_id" in seller
        else seller_id
    )

    moved_vehicle["owner_id"] = str(
        buyer_id
    )

    moved_vehicle["purchase_price"] = amount
    moved_vehicle["purchase_timestamp"] = time.time()

    add_vehicle_to_player(
        buyer,
        moved_vehicle
    )

    # --------------------------------------------------------
    # Transactions
    # --------------------------------------------------------

    add_transaction(
        buyer,
        "vehicle_purchase",
        amount,
        (
            f"خرید {vehicle_name(moved_vehicle)} "
            f"از {player_display_name(seller)}"
        ),
        direction="out",
        reference=reference
    )

    add_transaction(
        seller,
        "vehicle_sale",
        amount,
        (
            f"فروش {vehicle_name(moved_vehicle)} "
            f"به {player_display_name(buyer)}"
        ),
        direction="in",
        reference=reference
    )

    # --------------------------------------------------------
    # Deal history
    # --------------------------------------------------------

    deal = {
        "id": deal_id,
        "vehicle_id": str(
            moved_vehicle.get("id")
        ),
        "seller_id": str(
            seller_id
        ),
        "buyer_id": str(
            buyer_id
        ),
        "amount": amount,
        "status": "completed",
        "type": "market",
        "created_at": time.time(),
        "completed_at": time.time(),
    }

    seller.setdefault(
        "vehicle_deals",
        []
    )

    buyer.setdefault(
        "vehicle_deals",
        []
    )

    seller["vehicle_deals"].append(
        deal.copy()
    )

    buyer["vehicle_deals"].append(
        deal.copy()
    )

    listing["status"] = "sold"
    listing["buyer_id"] = str(
        buyer_id
    )

    listing["deal_id"] = deal_id
    listing["updated_at"] = time.time()

    return {
        "success": True,
        "deal": deal,
        "vehicle": moved_vehicle,
        "amount": amount,
    }


# ------------------------------------------------------------
# GIFT VEHICLE
# ------------------------------------------------------------

def gift_vehicle(
    players,
    sender_id,
    receiver_id,
    vehicle_id
):

    sender = players.get(
        str(sender_id)
    )

    receiver = players.get(
        str(receiver_id)
    )

    if not sender:

        return {
            "success": False,
            "message": "فرستنده پیدا نشد."
        }

    if not receiver:

        return {
            "success": False,
            "message": "گیرنده پیدا نشد."
        }

    if str(sender_id) == str(receiver_id):

        return {
            "success": False,
            "message": (
                "نمی‌توانید خودرو را به خودتان هدیه دهید."
            )
        }

    vehicle = get_player_vehicle(
        sender,
        vehicle_id
    )

    if not vehicle:

        return {
            "success": False,
            "message": (
                "این خودرو متعلق به شما نیست."
            )
        }

    # بررسی آگهی فعال
    for listing in sender.get(
        "market_listings",
        []
    ):

        if (
            listing.get("status") == "active"
            and str(
                listing.get("vehicle_id")
            ) == str(vehicle_id)
        ):

            listing["status"] = "cancelled"
            listing["updated_at"] = time.time()

    # حذف خودرو
    moved_vehicle = remove_vehicle_from_player(
        sender,
        vehicle_id
    )

    if not moved_vehicle:

        return {
            "success": False,
            "message": (
                "انتقال خودرو انجام نشد."
            )
        }

    moved_vehicle["previous_owner_id"] = str(
        sender_id
    )

    moved_vehicle["owner_id"] = str(
        receiver_id
    )

    moved_vehicle["gift_timestamp"] = time.time()

    add_vehicle_to_player(
        receiver,
        moved_vehicle
    )

    reference = (
        f"vehicle_gift:"
        f"{uuid.uuid4().hex}"
    )

    add_transaction(
        sender,
        "vehicle_gift",
        0,
        (
            f"هدیه {vehicle_name(moved_vehicle)} "
            f"به {player_display_name(receiver)}"
        ),
        direction="out",
        reference=reference
    )

    add_transaction(
        receiver,
        "vehicle_received",
        0,
        (
            f"دریافت هدیه "
            f"{vehicle_name(moved_vehicle)} "
            f"از {player_display_name(sender)}"
        ),
        direction="in",
        reference=reference
    )

    return {
        "success": True,
        "vehicle": moved_vehicle,
    }


# ------------------------------------------------------------
# VEHICLE MARKET TEXT
# ------------------------------------------------------------

def market_listing_text(
    listing,
    vehicle,
    seller
):

    return (
        "🚗 <b>آگهی فروش خودرو</b>\n\n"
        f"{vehicle_details_text(vehicle)}\n\n"
        f"👤 فروشنده: "
        f"{player_display_name(seller)}\n"
        f"💰 قیمت فروش: "
        f"{int(listing['asking_price']):,}"
    )


# ------------------------------------------------------------
# MARKET KEYBOARD
# ------------------------------------------------------------

def market_menu_keyboard(
    user_id
):

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🏪 خودروهای بازار",
                callback_data=(
                    f"marketlist|{user_id}"
                )
            )
        ],
        [
            InlineKeyboardButton(
                "📤 فروش خودرو",
                callback_data=(
                    f"marketsell|{user_id}"
                )
            )
        ],
        [
            InlineKeyboardButton(
                "📋 آگهی‌های من",
                callback_data=(
                    f"mylistings|{user_id}"
                )
            )
        ],
        [
            InlineKeyboardButton(
                "🔙 بازگشت",
                callback_data=(
                    f"vehicles|{user_id}"
                )
            )
        ],
    ])


# ------------------------------------------------------------
# SHOW MARKET
# ------------------------------------------------------------

async def show_market(
    update,
    context
):

    query = update.callback_query

    if not query:
        return

    user_id = query.from_user.id

    if not callback_is_owner(
        query,
        user_id
    ):
        await query.answer(
            "❌ دسترسی ندارید.",
            show_alert=True
        )
        return

    await query.answer()

    players = load_players()

    listings = []

    for seller_id, seller in players.items():

        ensure_vehicle_system(
            seller
        )

        for listing in seller[
            "market_listings"
        ]:

            if listing.get(
                "status"
            ) != "active":

                continue

            vehicle = get_player_vehicle(
                seller,
                listing.get(
                    "vehicle_id"
                )
            )

            if not vehicle:
                continue

            listings.append(
                (
                    listing,
                    vehicle,
                    seller
                )
            )

    buttons = []

    if not listings:

        text = (
            "🏪 <b>بازار خودرو</b>\n\n"
            "در حال حاضر خودرویی برای فروش "
            "در بازار وجود ندارد."
        )

    else:

        text = (
            "🏪 <b>بازار خودرو</b>\n\n"
            "خودروی موردنظر را انتخاب کنید:"
        )

        for listing, vehicle, seller in listings[:20]:

            buttons.append([
                InlineKeyboardButton(
                    (
                        f"🚗 {vehicle_name(vehicle)} | "
                        f"{int(listing['asking_price']):,}"
                    ),
                    callback_data=(
                        f"marketview|"
                        f"{listing['id']}|"
                        f"{user_id}"
                    )
                )
            ])

    buttons.append([
        InlineKeyboardButton(
            "🔙 بازگشت",
            callback_data=(
                f"market|{user_id}"
            )
        )
    ])

    await query.edit_message_text(
        text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(
            buttons
        )
    )


# ------------------------------------------------------------
# MARKET VIEW
# ------------------------------------------------------------

async def view_market_listing(
    update,
    context
):

    query = update.callback_query

    if not query:
        return

    parts = query.data.split("|")

    if len(parts) != 3:
        await query.answer(
            "❌ درخواست نامعتبر.",
            show_alert=True
        )
        return

    listing_id = parts[1]
    user_id = int(parts[2])

    if not callback_is_owner(
        query,
        user_id
    ):
        await query.answer(
            "❌ دسترسی ندارید.",
            show_alert=True
        )
        return

    await query.answer()

    players = load_players()

    listing, seller_id = find_listing(
        players,
        listing_id
    )

    if not listing:

        await query.edit_message_text(
            "❌ آگهی پیدا نشد."
        )
        return

    seller = players.get(
        str(
            listing["seller_id"]
        )
    )

    if not seller:

        await query.edit_message_text(
            "❌ فروشنده پیدا نشد."
        )
        return

    vehicle = get_player_vehicle(
        seller,
        listing["vehicle_id"]
    )

    if not vehicle:

        await query.edit_message_text(
            "❌ خودرو دیگر موجود نیست."
        )
        return

    buttons = []

    if str(
        listing["seller_id"]
    ) != str(user_id):

        buttons.append([
            InlineKeyboardButton(
                "💰 خرید خودرو",
                callback_data=(
                    f"marketbuy|"
                    f"{listing_id}|"
                    f"{user_id}"
                )
            )
        ])

    buttons.append([
        InlineKeyboardButton(
            "🔙 بازار",
            callback_data=(
                f"marketlist|{user_id}"
            )
        )
    ])

    await query.edit_message_text(
        market_listing_text(
            listing,
            vehicle,
            seller
        ),
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(
            buttons
        )
    )


# ------------------------------------------------------------
# MARKET BUY CALLBACK
# ------------------------------------------------------------

async def handle_market_buy(
    update,
    context
):

    query = update.callback_query

    if not query:
        return

    parts = query.data.split("|")

    if len(parts) != 3:
        await query.answer(
            "❌ درخواست نامعتبر.",
            show_alert=True
        )
        return

    listing_id = parts[1]
    buyer_id = int(parts[2])

    if not callback_is_owner(
        query,
        buyer_id
    ):
        await query.answer(
            "❌ دسترسی ندارید.",
            show_alert=True
        )
        return

    # پاسخ سریع به تلگرام
    await query.answer(
        "⏳ در حال نهایی کردن معامله..."
    )

    players = load_players()

    result = buy_market_vehicle(
        players,
        listing_id,
        buyer_id
    )

    if not result["success"]:

        await query.edit_message_text(
            result["message"]
        )
        return

    save_players(
        players
    )

    vehicle = result["vehicle"]

    text = (
        "✅ <b>خرید خودرو موفق بود!</b>\n\n"
        f"🚗 {vehicle_name(vehicle)}\n"
        f"💰 مبلغ پرداخت‌شده: "
        f"{result['amount']:,}\n\n"
        "🚘 خودرو به گاراژ شما منتقل شد."
    )

    await query.edit_message_text(
        text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "🚘 گاراژ",
                    callback_data=(
                        f"garage|{buyer_id}"
                    )
                )
            ],
            [
                InlineKeyboardButton(
                    "🏪 بازار",
                    callback_data=(
                        f"marketlist|{buyer_id}"
                    )
                )
            ]
        ])
    )


# ------------------------------------------------------------
# MY LISTINGS
# ------------------------------------------------------------

async def show_my_listings(
    update,
    context
):

    query = update.callback_query

    if not query:
        return

    user_id = query.from_user.id

    if not callback_is_owner(
        query,
        user_id
    ):
        await query.answer(
            "❌ دسترسی ندارید.",
            show_alert=True
        )
        return

    await query.answer()

    players = load_players()

    player = players.get(
        str(user_id)
    )

    if not player:

        await query.edit_message_text(
            "❌ بازیکن پیدا نشد."
        )
        return

    ensure_vehicle_system(
        player
    )

    buttons = []

    active_count = 0

    for listing in player[
        "market_listings"
    ]:

        if listing.get(
            "status"
        ) != "active":

            continue

        vehicle = get_player_vehicle(
            player,
            listing.get(
                "vehicle_id"
            )
        )

        if not vehicle:
            continue

        active_count += 1

        buttons.append([
            InlineKeyboardButton(
                (
                    f"🚗 {vehicle_name(vehicle)} | "
                    f"{int(listing['asking_price']):,}"
                ),
                callback_data=(
                    f"mylisting|"
                    f"{listing['id']}|"
                    f"{user_id}"
                )
            )
        ])

    if active_count == 0:

        text = (
            "📋 <b>آگهی‌های من</b>\n\n"
            "آگهی فعالی ندارید."
        )

    else:

        text = (
            "📋 <b>آگهی‌های من</b>\n\n"
            f"تعداد آگهی فعال: {active_count}"
        )

    buttons.append([
        InlineKeyboardButton(
            "🔙 بازار",
            callback_data=(
                f"market|{user_id}"
            )
        )
    ])

    await query.edit_message_text(
        text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(
            buttons
        )
    )


# ------------------------------------------------------------
# MY LISTING VIEW
# ------------------------------------------------------------

async def view_my_listing(
    update,
    context
):

    query = update.callback_query

    if not query:
        return

    parts = query.data.split("|")

    if len(parts) != 3:
        await query.answer(
            "❌ درخواست نامعتبر.",
            show_alert=True
        )
        return

    listing_id = parts[1]
    user_id = int(parts[2])

    if not callback_is_owner(
        query,
        user_id
    ):
        await query.answer(
            "❌ دسترسی ندارید.",
            show_alert=True
        )
        return

    await query.answer()

    players = load_players()

    listing, seller_id = find_listing(
        players,
        listing_id
    )

    if not listing:

        await query.edit_message_text(
            "❌ آگهی پیدا نشد."
        )
        return

    if str(seller_id) != str(user_id):

        await query.edit_message_text(
            "❌ این آگهی متعلق به شما نیست."
        )
        return

    seller = players.get(
        str(user_id)
    )

    vehicle = get_player_vehicle(
        seller,
        listing["vehicle_id"]
    )

    if not vehicle:

        await query.edit_message_text(
            "❌ خودرو دیگر در گاراژ شما نیست."
        )
        return

    buttons = [
        [
            InlineKeyboardButton(
                "❌ حذف آگهی",
                callback_data=(
                    f"listingcancel|"
                    f"{listing_id}|"
                    f"{user_id}"
                )
            )
        ],
        [
            InlineKeyboardButton(
                "🔙 آگهی‌های من",
                callback_data=(
                    f"mylistings|{user_id}"
                )
            )
        ]
    ]

    await query.edit_message_text(
        market_listing_text(
            listing,
            vehicle,
            seller
        ),
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(
            buttons
        )
    )


# ------------------------------------------------------------
# CANCEL LISTING CALLBACK
# ------------------------------------------------------------

async def handle_listing_cancel(
    update,
    context
):

    query = update.callback_query

    if not query:
        return

    parts = query.data.split("|")

    if len(parts) != 3:
        await query.answer(
            "❌ درخواست نامعتبر.",
            show_alert=True
        )
        return

    listing_id = parts[1]
    user_id = int(parts[2])

    if not callback_is_owner(
        query,
        user_id
    ):
        await query.answer(
            "❌ دسترسی ندارید.",
            show_alert=True
        )
        return

    await query.answer()

    players = load_players()

    result = remove_market_listing(
        players,
        listing_id,
        user_id
    )

    if not result["success"]:

        await query.edit_message_text(
            result["message"]
        )
        return

    save_players(
        players
    )

    await query.edit_message_text(
        "✅ آگهی با موفقیت حذف شد.",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "📋 آگهی‌های من",
                    callback_data=(
                        f"mylistings|{user_id}"
                    )
                )
            ],
            [
                InlineKeyboardButton(
                    "🏪 بازار",
                    callback_data=(
                        f"market|{user_id}"
                    )
                )
            ]
        ])
    )


# ------------------------------------------------------------
# VEHICLE MARKET CALLBACK ROUTER
# ------------------------------------------------------------

async def handle_vehicle_market_callback(
    update,
    context
):

    query = update.callback_query

    if not query:
        return

    data = query.data
    parts = data.split("|")

    if not parts:
        return

    action = parts[0]

    if action == "market":
        await show_market_menu(
            update,
            context
        )
        return

    if action == "marketlist":
        await show_market(
            update,
            context
        )
        return

    if action == "marketview":
        await view_market_listing(
            update,
            context
        )
        return

    if action == "marketbuy":
        await handle_market_buy(
            update,
            context
        )
        return

    if action == "mylistings":
        await show_my_listings(
            update,
            context
        )
        return

    if action == "mylisting":
        await view_my_listing(
            update,
            context
        )
        return

    if action == "listingcancel":
        await handle_listing_cancel(
            update,
            context
        )
        return


# ------------------------------------------------------------
# MARKET MAIN MENU
# ------------------------------------------------------------

async def show_market_menu(
    update,
    context
):

    query = update.callback_query

    if not query:
        return

    user_id = query.from_user.id

    if not callback_is_owner(
        query,
        user_id
    ):
        await query.answer(
            "❌ دسترسی ندارید.",
            show_alert=True
        )
        return

    await query.answer()

    text = (
        "🏪 <b>بازار خودرو</b>\n\n"
        "در بازار می‌توانید خودرو بخرید "
        "یا خودروی خودتان را برای فروش قرار دهید.\n\n"
        "💰 خرید مستقیم\n"
        "📤 فروش خودرو\n"
        "📋 مدیریت آگهی‌ها"
    )

    await query.edit_message_text(
        text,
        parse_mode="HTML",
        reply_markup=market_menu_keyboard(
            user_id
        )
    )


# ------------------------------------------------------------
# VEHICLE GIFT CONFIRMATION
# ------------------------------------------------------------

def gift_confirm_keyboard(
    sender_id,
    receiver_id,
    vehicle_id
):

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🎁 تأیید هدیه",
                callback_data=(
                    f"giftconfirm|"
                    f"{receiver_id}|"
                    f"{vehicle_id}|"
                    f"{sender_id}"
                )
            )
        ],
        [
            InlineKeyboardButton(
                "❌ لغو",
                callback_data=(
                    f"garage|{sender_id}"
                )
            )
        ]
    ])


async def handle_gift_confirm(
    update,
    context
):

    query = update.callback_query

    if not query:
        return

    parts = query.data.split("|")

    if len(parts) != 4:
        await query.answer(
            "❌ درخواست نامعتبر.",
            show_alert=True
        )
        return

    receiver_id = int(parts[1])
    vehicle_id = parts[2]
    sender_id = int(parts[3])

    if not callback_is_owner(
        query,
        sender_id
    ):
        await query.answer(
            "❌ دسترسی ندارید.",
            show_alert=True
        )
        return

    await query.answer(
        "⏳ در حال انتقال..."
    )

    players = load_players()

    result = gift_vehicle(
        players,
        sender_id,
        receiver_id,
        vehicle_id
    )

    if not result["success"]:

        await query.edit_message_text(
            result["message"]
        )
        return

    save_players(
        players
    )

    vehicle = result["vehicle"]

    await query.edit_message_text(
        (
            "🎁 <b>هدیه با موفقیت ارسال شد!</b>\n\n"
            f"🚗 {vehicle_name(vehicle)}\n"
            f"👤 گیرنده: "
            f"{player_display_name(players[str(receiver_id)])}"
        ),
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "🚘 گاراژ",
                    callback_data=(
                        f"garage|{sender_id}"
                    )
                )
            ]
        ])
    )


# ------------------------------------------------------------
# END OF PART 6
# ============================================================# ============================================================
# PART 7
# DIRECT VEHICLE DEALS / NEGOTIATION / AUCTION / DEALERSHIP
# ============================================================

import time
import uuid


# ------------------------------------------------------------
# NEGOTIATION HELPERS
# ------------------------------------------------------------

def normalize_price(value):
    try:
        return int(
            str(value).replace(",", "").strip()
        )
    except Exception:
        return 0


def make_negotiation_id():
    return (
        "NEG-"
        + uuid.uuid4().hex[:14].upper()
    )


def make_auction_id():
    return (
        "AUC-"
        + uuid.uuid4().hex[:14].upper()
    )


def make_bid_id():
    return (
        "BID-"
        + uuid.uuid4().hex[:14].upper()
    )


# ------------------------------------------------------------
# PLAYER DEAL DATA
# ------------------------------------------------------------

def ensure_direct_deals(player):

    player.setdefault(
        "direct_vehicle_deals",
        []
    )

    player.setdefault(
        "negotiations",
        []
    )

    player.setdefault(
        "auctions",
        []
    )

    player.setdefault(
        "auction_bids",
        []
    )

    return player


# ------------------------------------------------------------
# FIND NEGOTIATION
# ------------------------------------------------------------

def find_negotiation(
    players,
    negotiation_id
):

    for owner_id, player in players.items():

        ensure_direct_deals(player)

        for negotiation in player[
            "negotiations"
        ]:

            if str(
                negotiation.get("id")
            ) == str(negotiation_id):

                return negotiation, owner_id

    return None, None


# ------------------------------------------------------------
# FIND AUCTION
# ------------------------------------------------------------

def find_auction(
    players,
    auction_id
):

    for owner_id, player in players.items():

        ensure_direct_deals(player)

        for auction in player[
            "auctions"
        ]:

            if str(
                auction.get("id")
            ) == str(auction_id):

                return auction, owner_id

    return None, None


# ------------------------------------------------------------
# CREATE DIRECT SALE PROPOSAL
# ------------------------------------------------------------

def create_direct_sale_offer(
    players,
    seller_id,
    buyer_id,
    vehicle_id,
    price
):

    seller = players.get(
        str(seller_id)
    )

    buyer = players.get(
        str(buyer_id)
    )

    if not seller:
        return {
            "success": False,
            "message": "❌ فروشنده پیدا نشد."
        }

    if not buyer:
        return {
            "success": False,
            "message": "❌ خریدار پیدا نشد."
        }

    if str(seller_id) == str(buyer_id):
        return {
            "success": False,
            "message": (
                "❌ نمی‌توانید با خودتان معامله کنید."
            )
        }

    ensure_vehicle_system(seller)
    ensure_vehicle_system(buyer)
    ensure_direct_deals(seller)
    ensure_direct_deals(buyer)

    vehicle = get_player_vehicle(
        seller,
        vehicle_id
    )

    if not vehicle:
        return {
            "success": False,
            "message": (
                "❌ این خودرو دیگر در گاراژ فروشنده نیست."
            )
        }

    price = normalize_price(price)

    if price <= 0:
        return {
            "success": False,
            "message": (
                "❌ قیمت باید بیشتر از صفر باشد."
            )
        }

    if not can_afford(
        buyer,
        price
    ):
        return {
            "success": False,
            "message": (
                "💰 خریدار در حال حاضر "
                "موجودی کافی ندارد."
            )
        }

    # جلوگیری از پیشنهادهای تکراری
    for old in seller[
        "negotiations"
    ]:

        if old.get("status") != "pending":
            continue

        if str(
            old.get("vehicle_id")
        ) != str(vehicle_id):
            continue

        if str(
            old.get("buyer_id")
        ) != str(buyer_id):
            continue

        return {
            "success": False,
            "message": (
                "⚠️ برای این خودرو "
                "قبلاً یک پیشنهاد فعال وجود دارد."
            )
        }

    negotiation_id = make_negotiation_id()

    negotiation = {
        "id": negotiation_id,
        "vehicle_id": str(vehicle_id),
        "seller_id": str(seller_id),
        "buyer_id": str(buyer_id),
        "price": price,
        "status": "pending",
        "created_at": time.time(),
        "updated_at": time.time(),
    }

    seller[
        "negotiations"
    ].append(
        negotiation.copy()
    )

    buyer[
        "negotiations"
    ].append(
        negotiation.copy()
    )

    return {
        "success": True,
        "negotiation": negotiation,
        "vehicle": vehicle,
    }


# ------------------------------------------------------------
# ACCEPT DIRECT SALE
# ------------------------------------------------------------

def accept_direct_sale(
    players,
    negotiation_id,
    seller_id
):

    negotiation, owner_id = find_negotiation(
        players,
        negotiation_id
    )

    if not negotiation:
        return {
            "success": False,
            "message": "❌ پیشنهاد پیدا نشد."
        }

    if str(owner_id) != str(seller_id):
        return {
            "success": False,
            "message": (
                "❌ این پیشنهاد متعلق به این فروشنده نیست."
            )
        }

    if negotiation.get(
        "status"
    ) != "pending":

        return {
            "success": False,
            "message": (
                "⚠️ این پیشنهاد قبلاً تعیین تکلیف شده."
            )
        }

    seller = players.get(
        str(
            negotiation["seller_id"]
        )
    )

    buyer = players.get(
        str(
            negotiation["buyer_id"]
        )
    )

    if not seller or not buyer:
        return {
            "success": False,
            "message": (
                "❌ اطلاعات یکی از طرفین پیدا نشد."
            )
        }

    vehicle = get_player_vehicle(
        seller,
        negotiation["vehicle_id"]
    )

    if not vehicle:
        negotiation["status"] = "failed"

        return {
            "success": False,
            "message": (
                "❌ خودرو دیگر متعلق به فروشنده نیست."
            )
        }

    price = normalize_price(
        negotiation["price"]
    )

    # آخرین بررسی موجودی
    if not can_afford(
        buyer,
        price
    ):

        negotiation["status"] = "failed"

        return {
            "success": False,
            "message": (
                "❌ خریدار دیگر پول کافی ندارد."
            )
        }

    # --------------------------------------------------------
    # معامله اتمیک
    # --------------------------------------------------------

    deal_id = (
        "DIRECT-"
        + uuid.uuid4().hex[:14].upper()
    )

    reference = (
        f"direct_vehicle:{deal_id}"
    )

    # قبل از برداشت پول
    negotiation["status"] = "processing"
    negotiation["updated_at"] = time.time()

    # انتقال پول
    buyer["cash"] = (
        int(
            buyer.get("cash", 0)
        )
        - price
    )

    seller["cash"] = (
        int(
            seller.get("cash", 0)
        )
        + price
    )

    # انتقال خودرو
    moved_vehicle = remove_vehicle_from_player(
        seller,
        negotiation["vehicle_id"]
    )

    if not moved_vehicle:

        # Rollback
        buyer["cash"] += price
        seller["cash"] -= price

        negotiation["status"] = "failed"
        negotiation["updated_at"] = time.time()

        return {
            "success": False,
            "message": (
                "❌ انتقال خودرو انجام نشد؛ "
                "مبلغ به خریدار برگشت."
            )
        }

    moved_vehicle[
        "previous_owner_id"
    ] = str(seller_id)

    moved_vehicle[
        "owner_id"
    ] = str(
        negotiation["buyer_id"]
    )

    moved_vehicle[
        "purchase_price"
    ] = price

    moved_vehicle[
        "purchase_timestamp"
    ] = time.time()

    add_vehicle_to_player(
        buyer,
        moved_vehicle
    )

    # --------------------------------------------------------
    # Transaction history
    # --------------------------------------------------------

    add_transaction(
        buyer,
        "vehicle_purchase",
        price,
        (
            f"خرید {vehicle_name(moved_vehicle)} "
            f"از {player_display_name(seller)}"
        ),
        direction="out",
        reference=reference
    )

    add_transaction(
        seller,
        "vehicle_sale",
        price,
        (
            f"فروش {vehicle_name(moved_vehicle)} "
            f"به {player_display_name(buyer)}"
        ),
        direction="in",
        reference=reference
    )

    deal = {
        "id": deal_id,
        "negotiation_id": negotiation_id,
        "vehicle_id": str(
            moved_vehicle.get("id")
        ),
        "seller_id": str(seller_id),
        "buyer_id": str(
            negotiation["buyer_id"]
        ),
        "price": price,
        "status": "completed",
        "type": "direct",
        "created_at": time.time(),
        "completed_at": time.time(),
    }

    seller.setdefault(
        "vehicle_deals",
        []
    )

    buyer.setdefault(
        "vehicle_deals",
        []
    )

    seller[
        "vehicle_deals"
    ].append(
        deal.copy()
    )

    buyer[
        "vehicle_deals"
    ].append(
        deal.copy()
    )

    # هر دو نسخه پیشنهاد باید بسته شوند
    negotiation["status"] = "completed"
    negotiation["deal_id"] = deal_id
    negotiation["updated_at"] = time.time()

    for player in (
        seller,
        buyer
    ):

        for item in player.get(
            "negotiations",
            []
        ):

            if str(
                item.get("id")
            ) == str(
                negotiation_id
            ):

                item["status"] = "completed"
                item["deal_id"] = deal_id
                item["updated_at"] = time.time()

    return {
        "success": True,
        "deal": deal,
        "vehicle": moved_vehicle,
    }


# ------------------------------------------------------------
# REJECT DIRECT SALE
# ------------------------------------------------------------

def reject_direct_sale(
    players,
    negotiation_id,
    seller_id
):

    negotiation, owner_id = find_negotiation(
        players,
        negotiation_id
    )

    if not negotiation:
        return {
            "success": False,
            "message": "❌ پیشنهاد پیدا نشد."
        }

    if str(owner_id) != str(seller_id):
        return {
            "success": False,
            "message": "❌ دسترسی ندارید."
        }

    if negotiation.get(
        "status"
    ) != "pending":

        return {
            "success": False,
            "message": (
                "این پیشنهاد قبلاً تعیین تکلیف شده."
            )
        }

    negotiation["status"] = "rejected"
    negotiation["updated_at"] = time.time()

    for player in players.values():

        for item in player.get(
            "negotiations",
            []
        ):

            if str(
                item.get("id")
            ) == str(
                negotiation_id
            ):

                item["status"] = "rejected"
                item["updated_at"] = time.time()

    return {
        "success": True
    }


# ------------------------------------------------------------
# CANCEL DIRECT OFFER
# ------------------------------------------------------------

def cancel_direct_sale(
    players,
    negotiation_id,
    buyer_id
):

    negotiation, owner_id = find_negotiation(
        players,
        negotiation_id
    )

    if not negotiation:
        return {
            "success": False,
            "message": "❌ پیشنهاد پیدا نشد."
        }

    if str(
        negotiation.get("buyer_id")
    ) != str(buyer_id):

        return {
            "success": False,
            "message": (
                "❌ شما خریدار این پیشنهاد نیستید."
            )
        }

    if negotiation.get(
        "status"
    ) != "pending":

        return {
            "success": False,
            "message": (
                "این پیشنهاد دیگر فعال نیست."
            )
        }

    for player in players.values():

        for item in player.get(
            "negotiations",
            []
        ):

            if str(
                item.get("id")
            ) == str(
                negotiation_id
            ):

                item["status"] = "cancelled"
                item["updated_at"] = time.time()

    return {
        "success": True
    }


# ------------------------------------------------------------
# NEGOTIATION BUTTONS
# ------------------------------------------------------------

def negotiation_buttons(
    negotiation,
    user_id
):

    status = negotiation.get(
        "status"
    )

    seller_id = str(
        negotiation.get(
            "seller_id"
        )
    )

    buyer_id = str(
        negotiation.get(
            "buyer_id"
        )
    )

    buttons = []

    if (
        str(user_id) == seller_id
        and status == "pending"
    ):

        buttons.append([
            InlineKeyboardButton(
                "✅ قبول قیمت",
                callback_data=(
                    f"dealaccept|"
                    f"{negotiation['id']}|"
                    f"{user_id}"
                )
            )
        ])

        buttons.append([
            InlineKeyboardButton(
                "❌ رد پیشنهاد",
                callback_data=(
                    f"dealreject|"
                    f"{negotiation['id']}|"
                    f"{user_id}"
                )
            )
        ])

    elif (
        str(user_id) == buyer_id
        and status == "pending"
    ):

        buttons.append([
            InlineKeyboardButton(
                "❌ لغو پیشنهاد",
                callback_data=(
                    f"dealcancel|"
                    f"{negotiation['id']}|"
                    f"{user_id}"
                )
            )
        ])

    return InlineKeyboardMarkup(
        buttons
    )


# ------------------------------------------------------------
# NEGOTIATION TEXT
# ------------------------------------------------------------

def negotiation_text(
    negotiation,
    vehicle,
    seller,
    buyer
):

    status = negotiation.get(
        "status",
        "pending"
    )

    return (
        "🤝 <b>پیشنهاد معامله خودرو</b>\n\n"
        f"{vehicle_details_text(vehicle)}\n\n"
        f"👤 فروشنده: "
        f"{player_display_name(seller)}\n"
        f"👤 خریدار: "
        f"{player_display_name(buyer)}\n\n"
        f"💰 قیمت پیشنهادی: "
        f"{normalize_price(negotiation['price']):,}\n"
        f"📌 وضعیت: "
        f"{VEHICLE_DEAL_STATES.get(status, status)}"
    )


# ------------------------------------------------------------
# SHOW INCOMING DEALS
# ------------------------------------------------------------

async def show_incoming_deals(
    update,
    context
):

    query = update.callback_query

    if not query:
        return

    user_id = query.from_user.id

    if not callback_is_owner(
        query,
        user_id
    ):
        await query.answer(
            "❌ دسترسی ندارید.",
            show_alert=True
        )
        return

    await query.answer()

    players = load_players()

    player = players.get(
        str(user_id)
    )

    if not player:
        return

    ensure_direct_deals(player)

    incoming = []

    for negotiation in player[
        "negotiations"
    ]:

        if (
            str(
                negotiation.get("seller_id")
            ) == str(user_id)
            and negotiation.get(
                "status"
            ) == "pending"
        ):

            incoming.append(
                negotiation
            )

    buttons = []

    for negotiation in incoming[:20]:

        seller = players.get(
            str(
                negotiation["seller_id"]
            )
        )

        vehicle = get_player_vehicle(
            seller,
            negotiation["vehicle_id"]
        )

        if not vehicle:
            continue

        buttons.append([
            InlineKeyboardButton(
                (
                    f"💰 {vehicle_name(vehicle)} | "
                    f"{normalize_price(negotiation['price']):,}"
                ),
                callback_data=(
                    f"dealview|"
                    f"{negotiation['id']}|"
                    f"{user_id}"
                )
            )
        ])

    if not buttons:

        text = (
            "📨 <b>پیشنهادهای دریافتی</b>\n\n"
            "پیشنهاد فعالی ندارید."
        )

    else:

        text = (
            "📨 <b>پیشنهادهای دریافتی</b>\n\n"
            "پیشنهاد موردنظر را انتخاب کنید:"
        )

    buttons.append([
        InlineKeyboardButton(
            "🔙 خودرو",
            callback_data=(
                f"vehicles|{user_id}"
            )
        )
    ])

    await query.edit_message_text(
        text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(
            buttons
        )
    )


# ------------------------------------------------------------
# SHOW OUTGOING DEALS
# ------------------------------------------------------------

async def show_outgoing_deals(
    update,
    context
):

    query = update.callback_query

    if not query:
        return

    user_id = query.from_user.id

    if not callback_is_owner(
        query,
        user_id
    ):
        await query.answer(
            "❌ دسترسی ندارید.",
            show_alert=True
        )
        return

    await query.answer()

    players = load_players()

    player = players.get(
        str(user_id)
    )

    if not player:
        return

    ensure_direct_deals(player)

    outgoing = []

    for negotiation in player[
        "negotiations"
    ]:

        if (
            str(
                negotiation.get("buyer_id")
            ) == str(user_id)
            and negotiation.get(
                "status"
            ) == "pending"
        ):

            outgoing.append(
                negotiation
            )

    buttons = []

    for negotiation in outgoing[:20]:

        seller = players.get(
            str(
                negotiation["seller_id"]
            )
        )

        if not seller:
            continue

        vehicle = get_player_vehicle(
            seller,
            negotiation["vehicle_id"]
        )

        if not vehicle:
            continue

        buttons.append([
            InlineKeyboardButton(
                (
                    f"📤 {vehicle_name(vehicle)} | "
                    f"{normalize_price(negotiation['price']):,}"
                ),
                callback_data=(
                    f"dealview|"
                    f"{negotiation['id']}|"
                    f"{user_id}"
                )
            )
        ])

    if not buttons:

        text = (
            "📤 <b>پیشنهادهای من</b>\n\n"
            "پیشنهاد فعالی ندارید."
        )

    else:

        text = (
            "📤 <b>پیشنهادهای من</b>\n\n"
            "پیشنهاد موردنظر را انتخاب کنید:"
        )

    buttons.append([
        InlineKeyboardButton(
            "🔙 خودرو",
            callback_data=(
                f"vehicles|{user_id}"
            )
        )
    ])

    await query.edit_message_text(
        text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(
            buttons
        )
    )


# ------------------------------------------------------------
# VIEW NEGOTIATION
# ------------------------------------------------------------

async def view_negotiation(
    update,
    context
):

    query = update.callback_query

    if not query:
        return

    parts = query.data.split("|")

    if len(parts) != 3:
        await query.answer(
            "❌ درخواست نامعتبر.",
            show_alert=True
        )
        return

    negotiation_id = parts[1]
    user_id = int(parts[2])

    if not callback_is_owner(
        query,
        user_id
    ):
        await query.answer(
            "❌ دسترسی ندارید.",
            show_alert=True
        )
        return

    await query.answer()

    players = load_players()

    negotiation, owner_id = find_negotiation(
        players,
        negotiation_id
    )

    if not negotiation:
        await query.edit_message_text(
            "❌ پیشنهاد پیدا نشد."
        )
        return

    if str(user_id) not in (
        str(
            negotiation["seller_id"]
        ),
        str(
            negotiation["buyer_id"]
        ),
    ):
        await query.edit_message_text(
            "❌ شما در این معامله نیستید."
        )
        return

    seller = players.get(
        str(
            negotiation["seller_id"]
        )
    )

    buyer = players.get(
        str(
            negotiation["buyer_id"]
        )
    )

    vehicle = get_player_vehicle(
        seller,
        negotiation["vehicle_id"]
    )

    if not vehicle:
        await query.edit_message_text(
            "❌ خودرو دیگر موجود نیست."
        )
        return

    await query.edit_message_text(
        negotiation_text(
            negotiation,
            vehicle,
            seller,
            buyer
        ),
        parse_mode="HTML",
        reply_markup=negotiation_buttons(
            negotiation,
            user_id
        )
    )


# ------------------------------------------------------------
# ACCEPT DEAL CALLBACK
# ------------------------------------------------------------

async def handle_deal_accept(
    update,
    context
):

    query = update.callback_query

    if not query:
        return

    parts = query.data.split("|")

    if len(parts) != 3:
        await query.answer(
            "❌ درخواست نامعتبر.",
            show_alert=True
        )
        return

    negotiation_id = parts[1]
    seller_id = int(parts[2])

    if not callback_is_owner(
        query,
        seller_id
    ):
        await query.answer(
            "❌ دسترسی ندارید.",
            show_alert=True
        )
        return

    await query.answer(
        "⏳ در حال نهایی کردن معامله..."
    )

    players = load_players()

    result = accept_direct_sale(
        players,
        negotiation_id,
        seller_id
    )

    if not result["success"]:

        await query.edit_message_text(
            result["message"]
        )
        return

    save_players(
        players
    )

    vehicle = result["vehicle"]

    buyer_id = result[
        "deal"
    ]["buyer_id"]

    seller_id = result[
        "deal"
    ]["seller_id"]

    await query.edit_message_text(
        (
            "✅ <b>معامله با موفقیت انجام شد!</b>\n\n"
            f"🚗 {vehicle_name(vehicle)}\n"
            f"💰 مبلغ معامله: "
            f"{result['deal']['price']:,}\n\n"
            "🔄 مالکیت خودرو منتقل شد."
        ),
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "🚘 گاراژ",
                    callback_data=(
                        f"garage|{buyer_id}"
                    )
                )
            ]
        ])
    )

    # اطلاع به خریدار
    try:

        await context.bot.send_message(
            chat_id=int(buyer_id),
            text=(
                "🎉 <b>خودرو خریداری شد!</b>\n\n"
                f"🚗 {vehicle_name(vehicle)}\n"
                f"💰 مبلغ: "
                f"{result['deal']['price']:,}\n\n"
                "خودرو به گاراژ شما منتقل شد."
            ),
            parse_mode="HTML"
        )

    except Exception:
        pass


# ------------------------------------------------------------
# REJECT DEAL CALLBACK
# ------------------------------------------------------------

async def handle_deal_reject(
    update,
    context
):

    query = update.callback_query

    if not query:
        return

    parts = query.data.split("|")

    if len(parts) != 3:
        await query.answer(
            "❌ درخواست نامعتبر.",
            show_alert=True
        )
        return

    negotiation_id = parts[1]
    seller_id = int(parts[2])

    if not callback_is_owner(
        query,
        seller_id
    ):
        await query.answer(
            "❌ دسترسی ندارید.",
            show_alert=True
        )
        return

    await query.answer()

    players = load_players()

    result = reject_direct_sale(
        players,
        negotiation_id,
        seller_id
    )

    if not result["success"]:

        await query.edit_message_text(
            result["message"]
        )
        return

    save_players(
        players
    )

    await query.edit_message_text(
        "❌ پیشنهاد رد شد.",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "📨 پیشنهادها",
                    callback_data=(
                        f"incomingdeals|{seller_id}"
                    )
                )
            ]
        ])
    )


# ------------------------------------------------------------
# CANCEL DEAL CALLBACK
# ------------------------------------------------------------

async def handle_deal_cancel(
    update,
    context
):

    query = update.callback_query

    if not query:
        return

    parts = query.data.split("|")

    if len(parts) != 3:
        await query.answer(
            "❌ درخواست نامعتبر.",
            show_alert=True
        )
        return

    negotiation_id = parts[1]
    buyer_id = int(parts[2])

    if not callback_is_owner(
        query,
        buyer_id
    ):
        await query.answer(
            "❌ دسترسی ندارید.",
            show_alert=True
        )
        return

    await query.answer()

    players = load_players()

    result = cancel_direct_sale(
        players,
        negotiation_id,
        buyer_id
    )

    if not result["success"]:

        await query.edit_message_text(
            result["message"]
        )
        return

    save_players(
        players
    )

    await query.edit_message_text(
        "✅ پیشنهاد شما لغو شد."
    )


# ------------------------------------------------------------
# AUCTION CREATION
# ------------------------------------------------------------

def create_vehicle_auction(
    players,
    seller_id,
    vehicle_id,
    start_price,
    duration_seconds=300
):

    seller = players.get(
        str(seller_id)
    )

    if not seller:

        return {
            "success": False,
            "message": "❌ فروشنده پیدا نشد."
        }

    ensure_vehicle_system(seller)
    ensure_direct_deals(seller)

    vehicle = get_player_vehicle(
        seller,
        vehicle_id
    )

    if not vehicle:

        return {
            "success": False,
            "message": (
                "❌ خودرو در گاراژ شما نیست."
            )
        }

    start_price = normalize_price(
        start_price
    )

    if start_price <= 0:

        return {
            "success": False,
            "message": (
                "❌ قیمت شروع نامعتبر است."
            )
        }

    duration_seconds = max(
        60,
        min(
            int(duration_seconds),
            86400
        )
    )

    # خودرو فقط یک حراج فعال داشته باشد
    for auction in seller[
        "auctions"
    ]:

        if (
            auction.get("status") == "active"
            and str(
                auction.get("vehicle_id")
            ) == str(vehicle_id)
        ):

            return {
                "success": False,
                "message": (
                    "⚠️ این خودرو قبلاً "
                    "در یک حراج فعال است."
                )
            }

    auction_id = make_auction_id()

    auction = {
        "id": auction_id,
        "vehicle_id": str(vehicle_id),
        "seller_id": str(seller_id),
        "start_price": start_price,
        "current_price": start_price,
        "highest_bidder_id": None,
        "status": "active",
        "created_at": time.time(),
        "ends_at": (
            time.time()
            + duration_seconds
        ),
        "duration": duration_seconds,
        "bids": [],
    }

    seller[
        "auctions"
    ].append(
        auction
    )

    return {
        "success": True,
        "auction": auction,
    }


# ------------------------------------------------------------
# PLACE AUCTION BID
# ------------------------------------------------------------

def place_auction_bid(
    players,
    auction_id,
    bidder_id,
    amount
):

    auction, seller_id = find_auction(
        players,
        auction_id
    )

    if not auction:

        return {
            "success": False,
            "message": "❌ حراج پیدا نشد."
        }

    if auction.get(
        "status"
    ) != "active":

        return {
            "success": False,
            "message": (
                "❌ این حراج فعال نیست."
            )
        }

    if time.time() >= float(
        auction.get(
            "ends_at",
            0
        )
    ):

        auction["status"] = "ended"

        return {
            "success": False,
            "message": (
                "⏰ زمان حراج به پایان رسیده."
            )
        }

    if str(
        auction["seller_id"]
    ) == str(bidder_id):

        return {
            "success": False,
            "message": (
                "❌ فروشنده نمی‌تواند "
                "روی خودروی خودش پیشنهاد بدهد."
            )
        }

    bidder = players.get(
        str(bidder_id)
    )

    seller = players.get(
        str(
            auction["seller_id"]
        )
    )

    if not bidder or not seller:

        return {
            "success": False,
            "message": (
                "❌ اطلاعات بازیکن پیدا نشد."
            )
        }

    amount = normalize_price(
        amount
    )

    minimum = max(
        int(
            auction.get(
                "start_price",
                0
            )
        ),
        int(
            auction.get(
                "current_price",
                0
            )
        ) + 1
    )

    if amount < minimum:

        return {
            "success": False,
            "message": (
                f"💰 پیشنهاد باید حداقل "
                f"{minimum:,} باشد."
            )
        }

    if not can_afford(
        bidder,
        amount
    ):

        return {
            "success": False,
            "message": (
                "💰 موجودی شما برای این پیشنهاد کافی نیست."
            )
        }

    bid = {
        "id": make_bid_id(),
        "auction_id": auction_id,
        "bidder_id": str(bidder_id),
        "amount": amount,
        "created_at": time.time(),
    }

    auction.setdefault(
        "bids",
        []
    )

    auction["bids"].append(
        bid
    )

    auction["current_price"] = amount
    auction["highest_bidder_id"] = str(
        bidder_id
    )

    return {
        "success": True,
        "bid": bid,
        "auction": auction,
    }


# ------------------------------------------------------------
# FINISH AUCTION
# ------------------------------------------------------------

def finish_vehicle_auction(
    players,
    auction_id
):

    auction, owner_id = find_auction(
        players,
        auction_id
    )

    if not auction:

        return {
            "success": False,
            "message": "❌ حراج پیدا نشد."
        }

    if auction.get(
        "status"
    ) == "completed":

        return {
            "success": False,
            "message": (
                "این حراج قبلاً تکمیل شده."
            )
        }

    if auction.get(
        "status"
    ) == "cancelled":

        return {
            "success": False,
            "message": (
                "این حراج لغو شده."
            )
        }

    if time.time() < float(
        auction.get(
            "ends_at",
            0
        )
    ):

        return {
            "success": False,
            "message": (
                "⏳ زمان حراج هنوز تمام نشده."
            )
        }

    seller = players.get(
        str(
            auction["seller_id"]
        )
    )

    bidder_id = auction.get(
        "highest_bidder_id"
    )

    if not bidder_id:

        auction["status"] = "ended"

        return {
            "success": True,
            "sold": False,
            "message": (
                "حراج بدون پیشنهاد به پایان رسید."
            )
        }

    buyer = players.get(
        str(bidder_id)
    )

    if not seller or not buyer:

        auction["status"] = "failed"

        return {
            "success": False,
            "message": (
                "❌ خریدار یا فروشنده پیدا نشد."
            )
        }

    vehicle = get_player_vehicle(
        seller,
        auction["vehicle_id"]
    )

    if not vehicle:

        auction["status"] = "failed"

        return {
            "success": False,
            "message": (
                "❌ خودرو دیگر در گاراژ فروشنده نیست."
            )
        }

    amount = normalize_price(
        auction["current_price"]
    )

    if not can_afford(
        buyer,
        amount
    ):

        auction["status"] = "failed"

        return {
            "success": False,
            "message": (
                "❌ برنده دیگر پول کافی ندارد."
            )
        }

    # --------------------------------------------------------
    # انتقال
    # --------------------------------------------------------

    deal_id = (
        "AUCTION-DEAL-"
        + uuid.uuid4().hex[:14].upper()
    )

    reference = (
        f"auction_vehicle:{deal_id}"
    )

    buyer["cash"] -= amount
    seller["cash"] += amount

    moved_vehicle = remove_vehicle_from_player(
        seller,
        auction["vehicle_id"]
    )

    if not moved_vehicle:

        buyer["cash"] += amount
        seller["cash"] -= amount

        auction["status"] = "failed"

        return {
            "success": False,
            "message": (
                "❌ انتقال خودرو شکست خورد؛ "
                "وجه برگشت داده شد."
            )
        }

    moved_vehicle[
        "previous_owner_id"
    ] = str(
        auction["seller_id"]
    )

    moved_vehicle[
        "owner_id"
    ] = str(
        bidder_id
    )

    moved_vehicle[
        "purchase_price"
    ] = amount

    moved_vehicle[
        "purchase_timestamp"
    ] = time.time()

    add_vehicle_to_player(
        buyer,
        moved_vehicle
    )

    # --------------------------------------------------------
    # Transactions
    # --------------------------------------------------------

    add_transaction(
        buyer,
        "vehicle_auction_purchase",
        amount,
        (
            f"خرید {vehicle_name(moved_vehicle)} "
            f"در حراج"
        ),
        direction="out",
        reference=reference
    )

    add_transaction(
        seller,
        "vehicle_auction_sale",
        amount,
        (
            f"فروش {vehicle_name(moved_vehicle)} "
            f"در حراج"
        ),
        direction="in",
        reference=reference
    )

    deal = {
        "id": deal_id,
        "auction_id": auction_id,
        "vehicle_id": str(
            moved_vehicle.get("id")
        ),
        "seller_id": str(
            auction["seller_id"]
        ),
        "buyer_id": str(
            bidder_id
        ),
        "price": amount,
        "status": "completed",
        "type": "auction",
        "created_at": time.time(),
        "completed_at": time.time(),
    }

    seller.setdefault(
        "vehicle_deals",
        []
    )

    buyer.setdefault(
        "vehicle_deals",
        []
    )

    seller[
        "vehicle_deals"
    ].append(
        deal.copy()
    )

    buyer[
        "vehicle_deals"
    ].append(
        deal.copy()
    )

    auction["status"] = "completed"
    auction["deal_id"] = deal_id
    auction["completed_at"] = time.time()

    return {
        "success": True,
        "sold": True,
        "deal": deal,
        "vehicle": moved_vehicle,
    }


# ------------------------------------------------------------
# CANCEL AUCTION
# ------------------------------------------------------------

def cancel_vehicle_auction(
    players,
    auction_id,
    seller_id
):

    auction, owner_id = find_auction(
        players,
        auction_id
    )

    if not auction:

        return {
            "success": False,
            "message": "❌ حراج پیدا نشد."
        }

    if str(
        auction.get("seller_id")
    ) != str(seller_id):

        return {
            "success": False,
            "message": "❌ این حراج متعلق به شما نیست."
        }

    if auction.get(
        "status"
    ) != "active":

        return {
            "success": False,
            "message": (
                "این حراج فعال نیست."
            )
        }

    auction["status"] = "cancelled"
    auction["cancelled_at"] = time.time()

    return {
        "success": True
    }


# ------------------------------------------------------------
# AUCTION TEXT
# ------------------------------------------------------------

def auction_text(
    auction,
    vehicle,
    seller
):

    remaining = max(
        0,
        int(
            auction.get(
                "ends_at",
                0
            ) - time.time()
        )
    )

    minutes = remaining // 60
    seconds = remaining % 60

    highest = auction.get(
        "highest_bidder_id"
    )

    return (
        "🔨 <b>حراج خودرو</b>\n\n"
        f"{vehicle_details_text(vehicle)}\n\n"
        f"👤 فروشنده: "
        f"{player_display_name(seller)}\n"
        f"💰 قیمت شروع: "
        f"{normalize_price(auction['start_price']):,}\n"
        f"🔥 بالاترین پیشنهاد: "
        f"{normalize_price(auction['current_price']):,}\n"
        f"👑 بالاترین پیشنهاددهنده: "
        f"{highest or 'هنوز کسی پیشنهاد نداده'}\n\n"
        f"⏳ زمان باقی‌مانده: "
        f"{minutes:02d}:{seconds:02d}"
    )


# ------------------------------------------------------------
# AUCTION KEYBOARD
# ------------------------------------------------------------

def auction_keyboard(
    auction,
    user_id
):

    buttons = []

    if str(
        auction.get("seller_id")
    ) != str(user_id):

        next_price = (
            normalize_price(
                auction.get(
                    "current_price",
                    0
                )
            )
            + 1
        )

        buttons.append([
            InlineKeyboardButton(
                f"💰 پیشنهاد {next_price:,}",
                callback_data=(
                    f"bidquick|"
                    f"{auction['id']}|"
                    f"{next_price}|"
                    f"{user_id}"
                )
            )
        ])

    if str(
        auction.get("seller_id")
    ) == str(user_id):

        buttons.append([
            InlineKeyboardButton(
                "❌ لغو حراج",
                callback_data=(
                    f"auctioncancel|"
                    f"{auction['id']}|"
                    f"{user_id}"
                )
            )
        ])

    buttons.append([
        InlineKeyboardButton(
            "🔨 حراج‌ها",
            callback_data=(
                f"auctions|{user_id}"
            )
        )
    ])

    return InlineKeyboardMarkup(
        buttons
    )


# ------------------------------------------------------------
# SHOW AUCTIONS
# ------------------------------------------------------------

async def show_auctions(
    update,
    context
):

    query = update.callback_query

    if not query:
        return

    user_id = query.from_user.id

    if not callback_is_owner(
        query,
        user_id
    ):
        await query.answer(
            "❌ دسترسی ندارید.",
            show_alert=True
        )
        return

    await query.answer()

    players = load_players()

    auctions = []

    for seller_id, seller in players.items():

        ensure_direct_deals(seller)

        for auction in seller[
            "auctions"
        ]:

            if auction.get(
                "status"
            ) != "active":
                continue

            if time.time() >= float(
                auction.get(
                    "ends_at",
                    0
                )
            ):
                auction["status"] = "ended"
                continue

            vehicle = get_player_vehicle(
                seller,
                auction["vehicle_id"]
            )

            if not vehicle:
                continue

            auctions.append(
                (
                    auction,
                    vehicle,
                    seller
                )
            )

    buttons = []

    for auction, vehicle, seller in auctions[:20]:

        buttons.append([
            InlineKeyboardButton(
                (
                    f"🔨 {vehicle_name(vehicle)} | "
                    f"{normalize_price(auction['current_price']):,}"
                ),
                callback_data=(
                    f"auctionview|"
                    f"{auction['id']}|"
                    f"{user_id}"
                )
            )
        ])

    if not buttons:

        text = (
            "🔨 <b>حراج خودرو</b>\n\n"
            "در حال حاضر حراج فعالی وجود ندارد."
        )

    else:

        text = (
            "🔨 <b>حراج خودرو</b>\n\n"
            "حراج موردنظر را انتخاب کنید:"
        )

    buttons.append([
        InlineKeyboardButton(
            "🔙 خودرو",
            callback_data=(
                f"vehicles|{user_id}"
            )
        )
    ])

    await query.edit_message_text(
        text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(
            buttons
        )
    )


# ------------------------------------------------------------
# VIEW AUCTION
# ------------------------------------------------------------

async def view_auction(
    update,
    context
):

    query = update.callback_query

    if not query:
        return

    parts = query.data.split("|")

    if len(parts) != 3:
        await query.answer(
            "❌ درخواست نامعتبر.",
            show_alert=True
        )
        return

    auction_id = parts[1]
    user_id = int(parts[2])

    if not callback_is_owner(
        query,
        user_id
    ):
        await query.answer(
            "❌ دسترسی ندارید.",
            show_alert=True
        )
        return

    await query.answer()

    players = load_players()

    auction, owner_id = find_auction(
        players,
        auction_id
    )

    if not auction:

        await query.edit_message_text(
            "❌ حراج پیدا نشد."
        )
        return

    seller = players.get(
        str(
            auction["seller_id"]
        )
    )

    if not seller:

        await query.edit_message_text(
            "❌ فروشنده پیدا نشد."
        )
        return

    vehicle = get_player_vehicle(
        seller,
        auction["vehicle_id"]
    )

    if not vehicle:

        await query.edit_message_text(
            "❌ خودرو دیگر موجود نیست."
        )
        return

    await query.edit_message_text(
        auction_text(
            auction,
            vehicle,
            seller
        ),
        parse_mode="HTML",
        reply_markup=auction_keyboard(
            auction,
            user_id
        )
    )


# ------------------------------------------------------------
# QUICK BID CALLBACK
# ------------------------------------------------------------

async def handle_quick_bid(
    update,
    context
):

    query = update.callback_query

    if not query:
        return

    parts = query.data.split("|")

    if len(parts) != 4:
        await query.answer(
            "❌ درخواست نامعتبر.",
            show_alert=True
        )
        return

    auction_id = parts[1]
    amount = normalize_price(
        parts[2]
    )
    user_id = int(parts[3])

    if not callback_is_owner(
        query,
        user_id
    ):
        await query.answer(
            "❌ دسترسی ندارید.",
            show_alert=True
        )
        return

    await query.answer(
        "⏳ ثبت پیشنهاد..."
    )

    players = load_players()

    result = place_auction_bid(
        players,
        auction_id,
        user_id,
        amount
    )

    if not result["success"]:

        await query.answer(
            result["message"],
            show_alert=True
        )
        return

    save_players(
        players
    )

    auction = result[
        "auction"
    ]

    await query.edit_message_text(
        auction_text(
            auction,
            get_player_vehicle(
                players[
                    str(
                        auction["seller_id"]
                    )
                ],
                auction["vehicle_id"]
            ),
            players[
                str(
                    auction["seller_id"]
                )
            ]
        ),
        parse_mode="HTML",
        reply_markup=auction_keyboard(
            auction,
            user_id
        )
    )


# ------------------------------------------------------------
# CANCEL AUCTION CALLBACK
# ------------------------------------------------------------

async def handle_auction_cancel(
    update,
    context
):

    query = update.callback_query

    if not query:
        return

    parts = query.data.split("|")

    if len(parts) != 3:
        await query.answer(
            "❌ درخواست نامعتبر.",
            show_alert=True
        )
        return

    auction_id = parts[1]
    seller_id = int(parts[2])

    if not callback_is_owner(
        query,
        seller_id
    ):
        await query.answer(
            "❌ دسترسی ندارید.",
            show_alert=True
        )
        return

    await query.answer()

    players = load_players()

    result = cancel_vehicle_auction(
        players,
        auction_id,
        seller_id
    )

    if not result["success"]:

        await query.edit_message_text(
            result["message"]
        )
        return

    save_players(
        players
    )

    await query.edit_message_text(
        "❌ حراج لغو شد.",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "🔨 حراج‌ها",
                    callback_data=(
                        f"auctions|{seller_id}"
                    )
                )
            ]
        ])
    )


# ------------------------------------------------------------
# DIRECT DEAL MENU
# ------------------------------------------------------------

def direct_deal_menu_keyboard(
    user_id
):

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "📨 پیشنهادهای دریافتی",
                callback_data=(
                    f"incomingdeals|{user_id}"
                )
            )
        ],
        [
            InlineKeyboardButton(
                "📤 پیشنهادهای من",
                callback_data=(
                    f"outgoingdeals|{user_id}"
                )
            )
        ],
        [
            InlineKeyboardButton(
                "🔨 حراج خودرو",
                callback_data=(
                    f"auctions|{user_id}"
                )
            )
        ],
        [
            InlineKeyboardButton(
                "🏪 بازار",
                callback_data=(
                    f"market|{user_id}"
                )
            )
        ],
        [
            InlineKeyboardButton(
                "🔙 خودرو",
                callback_data=(
                    f"vehicles|{user_id}"
                )
            )
        ],
    ])


async def show_direct_deals_menu(
    update,
    context
):

    query = update.callback_query

    if not query:
        return

    user_id = query.from_user.id

    if not callback_is_owner(
        query,
        user_id
    ):
        await query.answer(
            "❌ دسترسی ندارید.",
            show_alert=True
        )
        return

    await query.answer()

    text = (
        "🤝 <b>معاملات خودرو</b>\n\n"
        "از این قسمت می‌توانید پیشنهادهای "
        "خرید و فروش خود را مدیریت کنید.\n\n"
        "📨 پیشنهادهای دریافتی\n"
        "📤 پیشنهادهای ارسال‌شده\n"
        "🔨 حراج\n"
        "🏪 بازار"
    )

    await query.edit_message_text(
        text,
        parse_mode="HTML",
        reply_markup=direct_deal_menu_keyboard(
            user_id
        )
    )


# ------------------------------------------------------------
# DIRECT DEAL CALLBACK ROUTER
# ------------------------------------------------------------

async def handle_direct_deal_callback(
    update,
    context
):

    query = update.callback_query

    if not query:
        return

    parts = query.data.split("|")

    if not parts:
        return

    action = parts[0]

    if action == "deals":
        await show_direct_deals_menu(
            update,
            context
        )
        return

    if action == "incomingdeals":
        await show_incoming_deals(
            update,
            context
        )
        return

    if action == "outgoingdeals":
        await show_outgoing_deals(
            update,
            context
        )
        return

    if action == "dealview":
        await view_negotiation(
            update,
            context
        )
        return

    if action == "dealaccept":
        await handle_deal_accept(
            update,
            context
        )
        return

    if action == "dealreject":
        await handle_deal_reject(
            update,
            context
        )
        return

    if action == "dealcancel":
        await handle_deal_cancel(
            update,
            context
        )
        return

    if action == "auctions":
        await show_auctions(
            update,
            context
        )
        return

    if action == "auctionview":
        await view_auction(
            update,
            context
        )
        return

    if action == "bidquick":
        await handle_quick_bid(
            update,
            context
        )
        return

    if action == "auctioncancel":
        await handle_auction_cancel(
            update,
            context
        )
        return


# ------------------------------------------------------------
# END OF PART 7
# ============================================================# ============================================================
# PART 8 — GARAGE / VEHICLE SALE / GIFT / MARKET / SHOWROOM
# ============================================================

# این بخش با سیستم خودرو و معامله بخش‌های قبلی کار می‌کند.
# اگر بعضی توابع قبلاً تعریف شده باشند، دوباره تعریف نمی‌شوند.


# ------------------------------------------------------------
# VEHICLE HELPERS
# ------------------------------------------------------------

def ensure_vehicle_system(player):
    player.setdefault("vehicles", [])
    player.setdefault("vehicle_offers", [])
    player.setdefault("market_listings", [])
    player.setdefault("auctions", [])
    return player


def vehicle_display_name(vehicle):
    if not vehicle:
        return "خودروی نامشخص"

    brand = vehicle.get("brand", "")
    model = vehicle.get("model", "")
    year = vehicle.get("year", "")

    name = f"{brand} {model}".strip()

    if year:
        name += f" {year}"

    return name


def vehicle_price(vehicle):
    if not vehicle:
        return 0

    try:
        return int(
            vehicle.get(
                "price",
                vehicle.get("base_price", 0)
            )
        )
    except Exception:
        return 0


def vehicle_sell_price(vehicle):
    """
    قیمت فروش به سیستم/نمایندگی.
    برای خودروهای سالم، درصدی از قیمت پایه برگردانده می‌شود.
    """
    price = vehicle_price(vehicle)

    condition = str(
        vehicle.get("condition", "سالم")
    ).lower()

    multiplier = 0.75

    if "عالی" in condition:
        multiplier = 0.82
    elif "خوب" in condition:
        multiplier = 0.78
    elif "متوسط" in condition:
        multiplier = 0.70
    elif "ضعیف" in condition:
        multiplier = 0.60

    return max(1, int(price * multiplier))


def find_player_vehicle(player, vehicle_id):
    ensure_vehicle_system(player)

    vehicle_id = str(vehicle_id)

    for vehicle in player.get("vehicles", []):
        if str(vehicle.get("id")) == vehicle_id:
            return vehicle

    return None


if "get_player_vehicle" not in globals():

    def get_player_vehicle(player, vehicle_id):
        return find_player_vehicle(player, vehicle_id)


def remove_player_vehicle(player, vehicle_id):
    ensure_vehicle_system(player)

    vehicle_id = str(vehicle_id)

    old_count = len(player["vehicles"])

    player["vehicles"] = [
        vehicle
        for vehicle in player["vehicles"]
        if str(vehicle.get("id")) != vehicle_id
    ]

    return len(player["vehicles"]) < old_count


if "remove_vehicle_from_player" not in globals():

    def remove_vehicle_from_player(player, vehicle_id):
        return remove_player_vehicle(player, vehicle_id)


def add_player_vehicle(player, vehicle):
    ensure_vehicle_system(player)

    player["vehicles"].append(vehicle)

    return True


if "add_vehicle_to_player" not in globals():

    def add_vehicle_to_player(player, vehicle):
        return add_player_vehicle(player, vehicle)


def vehicle_condition_text(vehicle):
    condition = vehicle.get("condition", "سالم")

    mileage = vehicle.get("mileage", 0)

    try:
        mileage = int(mileage)
    except Exception:
        mileage = 0

    return (
        f"🛠 وضعیت: {condition}\n"
        f"🛣 کارکرد: {mileage:,} km"
    )


def vehicle_details_text(vehicle):
    if not vehicle:
        return "❌ خودرو پیدا نشد."

    name = vehicle_display_name(vehicle)
    price = vehicle_price(vehicle)

    return (
        f"🚗 <b>{name}</b>\n\n"
        f"💰 ارزش پایه: {price:,}\n"
        f"🎨 رنگ: {vehicle.get('color', 'نامشخص')}\n"
        f"⚙️ موتور: {vehicle.get('engine', 'نامشخص')}\n"
        f"🐎 قدرت: {vehicle.get('power', 'نامشخص')}\n"
        f"🔧 گیربکس: {vehicle.get('transmission', 'نامشخص')}\n"
        f"{vehicle_condition_text(vehicle)}\n"
        f"🏷 تیونینگ: {vehicle.get('tuning', 'استاندارد')}"
    )


# ------------------------------------------------------------
# GARAGE
# ------------------------------------------------------------

def garage_keyboard(player):
    user_id = player["id"] if "id" in player else player.get("user_id")

    rows = []

    for vehicle in player.get("vehicles", []):
        vehicle_id = vehicle.get("id")

        rows.append([
            InlineKeyboardButton(
                f"🚗 {vehicle_display_name(vehicle)}",
                callback_data=f"garagecar|{vehicle_id}|{user_id}"
            )
        ])

    rows.append([
        InlineKeyboardButton(
            "🏪 نمایشگاه",
            callback_data=f"showroom|{user_id}"
        ),
        InlineKeyboardButton(
            "🔨 حراجی",
            callback_data=f"auctions|{user_id}"
        )
    ])

    rows.append([
        InlineKeyboardButton(
            "🤝 معاملات من",
            callback_data=f"deals|{user_id}"
        )
    ])

    rows.append([
        InlineKeyboardButton(
            "🔙 منوی خودرو",
            callback_data=f"vehicles|{user_id}"
        )
    ])

    return InlineKeyboardMarkup(rows)


async def show_garage(update, context):
    query = update.callback_query

    if query:
        await query.answer()

        user_id = query.from_user.id
        player = get_player(query.from_user)
    else:
        user_id = update.effective_user.id
        player = get_player(update.effective_user)

    ensure_vehicle_system(player)

    vehicles = player.get("vehicles", [])

    if not vehicles:
        text = (
            "🏠 <b>گاراژ من</b>\n\n"
            "🚗 گاراژت خالیه.\n\n"
            "از نمایشگاه می‌تونی خودرو خریداری کنی."
        )
    else:
        text = (
            "🏠 <b>گاراژ من</b>\n\n"
            f"🚗 تعداد خودروها: <b>{len(vehicles)}</b>\n\n"
            "برای مشاهده جزئیات روی خودرو بزن."
        )

    keyboard = garage_keyboard(player)

    if query:
        await query.edit_message_text(
            text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    else:
        await update.message.reply_text(
            text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )


# ------------------------------------------------------------
# GARAGE VEHICLE DETAIL
# ------------------------------------------------------------

def garage_vehicle_keyboard(vehicle, user_id):
    vehicle_id = vehicle.get("id")

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "💰 فروش",
                callback_data=f"vehiclesell|{vehicle_id}|{user_id}"
            ),
            InlineKeyboardButton(
                "🎁 هدیه",
                callback_data=f"vehiclegift|{vehicle_id}|{user_id}"
            )
        ],
        [
            InlineKeyboardButton(
                "📢 آگهی فروش",
                callback_data=f"marketlist|{vehicle_id}|{user_id}"
            )
        ],
        [
            InlineKeyboardButton(
                "🔙 گاراژ",
                callback_data=f"garage|{user_id}"
            )
        ]
    ])


async def show_garage_vehicle(update, context, vehicle_id):
    query = update.callback_query

    if query:
        user = query.from_user
    else:
        user = update.effective_user

    player = get_player(user)

    vehicle = get_player_vehicle(
        player,
        vehicle_id
    )

    if not vehicle:
        if query:
            await query.answer(
                "❌ این خودرو دیگر در گاراژ شما نیست.",
                show_alert=True
            )
        return

    text = (
        "🏠 <b>خودروی گاراژ</b>\n\n"
        + vehicle_details_text(vehicle)
        + "\n\n"
        "🔽 عملیات موردنظر را انتخاب کن:"
    )

    keyboard = garage_vehicle_keyboard(
        vehicle,
        user.id
    )

    if query:
        await query.edit_message_text(
            text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    else:
        await update.message.reply_text(
            text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )


# ------------------------------------------------------------
# SELL VEHICLE TO DEALER
# ------------------------------------------------------------

def dealer_sell_preview(vehicle):
    amount = vehicle_sell_price(vehicle)

    return (
        f"💰 مبلغ دریافتی:\n"
        f"<b>{amount:,}</b>"
    )


def dealer_sell_keyboard(vehicle, user_id):
    vehicle_id = vehicle.get("id")

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "✅ تأیید فروش",
                callback_data=f"vehiclesellconfirm|{vehicle_id}|{user_id}"
            )
        ],
        [
            InlineKeyboardButton(
                "❌ انصراف",
                callback_data=f"garagecar|{vehicle_id}|{user_id}"
            )
        ]
    ])


async def show_vehicle_sell(update, context, vehicle_id):
    query = update.callback_query

    user = query.from_user
    player = get_player(user)

    vehicle = get_player_vehicle(
        player,
        vehicle_id
    )

    if not vehicle:
        await query.answer(
            "❌ خودرو پیدا نشد.",
            show_alert=True
        )
        return

    amount = vehicle_sell_price(vehicle)

    text = (
        "🏪 <b>فروش به نمایندگی</b>\n\n"
        f"🚗 {vehicle_display_name(vehicle)}\n\n"
        f"💵 قیمت پایه: {vehicle_price(vehicle):,}\n"
        f"💰 قیمت خرید نمایندگی: <b>{amount:,}</b>\n\n"
        "⚠️ فروش به نمایندگی قطعی است و خودرو از گاراژ حذف می‌شود."
    )

    await query.edit_message_text(
        text,
        reply_markup=dealer_sell_keyboard(
            vehicle,
            user.id
        ),
        parse_mode="HTML"
    )


async def confirm_vehicle_sell(update, context, vehicle_id):
    query = update.callback_query

    user = query.from_user
    user_id = user.id

    players = load_players()

    player = players.get(str(user_id))

    if not player:
        await query.answer(
            "❌ بازیکن پیدا نشد.",
            show_alert=True
        )
        return

    ensure_vehicle_system(player)

    vehicle = get_player_vehicle(
        player,
        vehicle_id
    )

    if not vehicle:
        await query.answer(
            "❌ این خودرو قبلاً فروخته شده یا وجود ندارد.",
            show_alert=True
        )
        return

    # جلوگیری از فروش دوباره
    if vehicle.get("sale_locked"):
        await query.answer(
            "⏳ عملیات فروش در حال انجام است.",
            show_alert=True
        )
        return

    vehicle["sale_locked"] = True

    amount = vehicle_sell_price(vehicle)

    removed = remove_vehicle_from_player(
        player,
        vehicle_id
    )

    if not removed:
        vehicle["sale_locked"] = False

        await query.answer(
            "❌ فروش خودرو انجام نشد.",
            show_alert=True
        )
        return

    player["cash"] = int(
        player.get("cash", 0)
    ) + amount

    add_transaction(
        player,
        "vehicle_sale",
        amount,
        f"فروش {vehicle_display_name(vehicle)} به نمایندگی",
        reference=f"dealer-sale:{vehicle_id}:{user_id}"
    )

    players[str(user_id)] = player

    save_players(players)

    await query.answer(
        "✅ خودرو فروخته شد.",
        show_alert=True
    )

    await query.edit_message_text(
        (
            "✅ <b>فروش موفق</b>\n\n"
            f"🚗 {vehicle_display_name(vehicle)}\n"
            f"💰 مبلغ دریافتی: <b>{amount:,}</b>\n\n"
            "💵 پول به کیف پول نقدی شما اضافه شد."
        ),
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "🏠 گاراژ",
                    callback_data=f"garage|{user_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    "🚗 منوی خودرو",
                    callback_data=f"vehicles|{user_id}"
                )
            ]
        ]),
        parse_mode="HTML"
    )


# ------------------------------------------------------------
# GIFT / TRANSFER VEHICLE
# ------------------------------------------------------------

def gift_vehicle_keyboard(vehicle, user_id):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "❌ انصراف",
                callback_data=f"garagecar|{vehicle.get('id')}|{user_id}"
            )
        ]
    ])


async def start_vehicle_gift(update, context, vehicle_id):
    query = update.callback_query

    user = query.from_user
    player = get_player(user)

    vehicle = get_player_vehicle(
        player,
        vehicle_id
    )

    if not vehicle:
        await query.answer(
            "❌ خودرو پیدا نشد.",
            show_alert=True
        )
        return

    context.user_data["vehicle_gift"] = {
        "vehicle_id": str(vehicle_id),
        "owner_id": user.id
    }

    await query.edit_message_text(
        (
            "🎁 <b>انتقال خودرو</b>\n\n"
            f"🚗 {vehicle_display_name(vehicle)}\n\n"
            "آیدی عددی کاربری که می‌خواهی خودرو را به او هدیه بدهی ارسال کن.\n\n"
            "مثال:\n"
            "<code>123456789</code>\n\n"
            "برای لغو، بنویس: لغو"
        ),
        reply_markup=gift_vehicle_keyboard(
            vehicle,
            user.id
        ),
        parse_mode="HTML"
    )


async def process_vehicle_gift_message(update, context):
    user = update.effective_user

    state = context.user_data.get(
        "vehicle_gift"
    )

    if not state:
        return False

    text = normalize_digits(
        update.message.text.strip()
    )

    if text.lower() in (
        "لغو",
        "cancel"
    ):
        context.user_data.pop(
            "vehicle_gift",
            None
        )

        await update.message.reply_text(
            "❌ انتقال خودرو لغو شد."
        )

        return True

    if not text.isdigit():
        await update.message.reply_text(
            "❌ آیدی عددی معتبر ارسال کن."
        )
        return True

    target_id = int(text)
    owner_id = int(state["owner_id"])
    vehicle_id = str(state["vehicle_id"])

    if target_id == owner_id:
        await update.message.reply_text(
            "❌ نمی‌توانی خودرو را به خودت منتقل کنی."
        )
        return True

    players = load_players()

    owner = players.get(str(owner_id))
    target = players.get(str(target_id))

    if not owner:
        await update.message.reply_text(
            "❌ مالک خودرو پیدا نشد."
        )
        return True

    if not target:
        await update.message.reply_text(
            "❌ بازیکن مقصد پیدا نشد."
        )
        return True

    vehicle = get_player_vehicle(
        owner,
        vehicle_id
    )

    if not vehicle:
        await update.message.reply_text(
            "❌ خودرو در گاراژ شما پیدا نشد."
        )
        return True

    # انتقال اتمیک
    transfer_id = (
        f"gift:{owner_id}:{target_id}:{vehicle_id}"
    )

    existing = owner.setdefault(
        "vehicle_transfers",
        []
    )

    for item in existing:
        if item.get("id") == transfer_id:
            await update.message.reply_text(
                "⚠️ این انتقال قبلاً انجام شده است."
            )
            context.user_data.pop(
                "vehicle_gift",
                None
            )
            return True

    removed = remove_vehicle_from_player(
        owner,
        vehicle_id
    )

    if not removed:
        await update.message.reply_text(
            "❌ انتقال خودرو انجام نشد."
        )
        return True

    vehicle["owner_id"] = target_id

    add_vehicle_to_player(
        target,
        vehicle
    )

    transfer_record = {
        "id": transfer_id,
        "from": owner_id,
        "to": target_id,
        "vehicle_id": vehicle_id,
        "timestamp": timestamp(),
    }

    owner.setdefault(
        "vehicle_transfers",
        []
    ).append(transfer_record)

    target.setdefault(
        "vehicle_transfers_received",
        []
    ).append(transfer_record)

    add_transaction(
        owner,
        "vehicle_gift",
        0,
        f"هدیه خودرو به {target_id}: {vehicle_display_name(vehicle)}",
        reference=transfer_id
    )

    add_transaction(
        target,
        "vehicle_received",
        0,
        f"دریافت خودرو از {owner_id}: {vehicle_display_name(vehicle)}",
        reference=transfer_id
    )

    players[str(owner_id)] = owner
    players[str(target_id)] = target

    save_players(players)

    context.user_data.pop(
        "vehicle_gift",
        None
    )

    await update.message.reply_text(
        (
            "🎁 <b>انتقال موفق</b>\n\n"
            f"🚗 {vehicle_display_name(vehicle)}\n"
            f"👤 گیرنده: <code>{target_id}</code>"
        ),
        parse_mode="HTML"
    )

    try:
        await context.bot.send_message(
            chat_id=target_id,
            text=(
                "🎁 <b>خودرو دریافت کردی!</b>\n\n"
                f"🚗 {vehicle_display_name(vehicle)}\n"
                f"👤 فرستنده: <code>{owner_id}</code>"
            ),
            parse_mode="HTML"
        )
    except Exception:
        pass

    return True


# ------------------------------------------------------------
# MARKET LISTING
# ------------------------------------------------------------

def market_listing_id(owner_id, vehicle_id):
    return f"market:{owner_id}:{vehicle_id}"

def ensure_market(player):
    player.setdefault(
        "market_listings",
        []
    )


def find_market_listing(players, listing_id):
    for owner_id, player in players.items():
        ensure_market(player)

        for listing in player.get(
            "market_listings",
            []
        ):
            if listing.get("id") == listing_id:
                return owner_id, player, listing

    return None, None, None


def create_market_listing(
    player,
    vehicle,
    price,
    negotiable=True
):
    ensure_market(player)

    owner_id = player.get(
        "id",
        player.get("user_id")
    )

    listing_id = market_listing_id(
        owner_id,
        vehicle.get("id")
    )

    for item in player["market_listings"]:
        if item.get("id") == listing_id:
            return None

    listing = {
        "id": listing_id,
        "vehicle_id": str(vehicle.get("id")),
        "owner_id": int(owner_id),
        "price": int(price),
        "negotiable": bool(negotiable),
        "status": "active",
        "created_at": timestamp(),
    }

    player["market_listings"].append(
        listing
    )

    return listing


def market_keyboard(player):
    user_id = player.get(
        "id",
        player.get("user_id")
    )

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "📢 خودروهای من",
                callback_data=f"mymarket|{user_id}"
            )
        ],
        [
            InlineKeyboardButton(
                "🏠 گاراژ",
                callback_data=f"garage|{user_id}"
            )
        ]
    ])


async def start_market_listing(update, context, vehicle_id):
    query = update.callback_query

    user = query.from_user
    player = get_player(user)

    vehicle = get_player_vehicle(
        player,
        vehicle_id
    )

    if not vehicle:
        await query.answer(
            "❌ خودرو پیدا نشد.",
            show_alert=True
        )
        return

    context.user_data["market_listing"] = {
        "vehicle_id": str(vehicle_id),
        "owner_id": user.id
    }

    suggested = vehicle_price(vehicle)

    await query.edit_message_text(
        (
            "📢 <b>ثبت آگهی فروش</b>\n\n"
            f"🚗 {vehicle_display_name(vehicle)}\n\n"
            f"💰 ارزش پایه: {suggested:,}\n\n"
            "قیمت پیشنهادی خودت را به عدد ارسال کن.\n\n"
            "مثال:\n"
            "<code>1500000000</code>\n\n"
            "برای لغو بنویس: لغو"
        ),
        parse_mode="HTML"
    )


async def process_market_listing_message(
    update,
    context
):
    state = context.user_data.get(
        "market_listing"
    )

    if not state:
        return False

    text = normalize_digits(
        update.message.text.strip()
    )

    if text.lower() in (
        "لغو",
        "cancel"
    ):
        context.user_data.pop(
            "market_listing",
            None
        )

        await update.message.reply_text(
            "❌ ثبت آگهی لغو شد."
        )

        return True

    price = parse_amount(text)

    if price <= 0:
        await update.message.reply_text(
            "❌ قیمت معتبر وارد کن."
        )
        return True

    owner_id = int(
        state["owner_id"]
    )

    vehicle_id = str(
        state["vehicle_id"]
    )

    players = load_players()

    owner = players.get(
        str(owner_id)
    )

    if not owner:
        await update.message.reply_text(
            "❌ مالک خودرو پیدا نشد."
        )
        return True

    vehicle = get_player_vehicle(
        owner,
        vehicle_id
    )

    if not vehicle:
        await update.message.reply_text(
            "❌ خودرو دیگر در گاراژ نیست."
        )

        context.user_data.pop(
            "market_listing",
            None
        )

        return True

    listing = create_market_listing(
        owner,
        vehicle,
        price,
        True
    )

    if not listing:
        await update.message.reply_text(
            "⚠️ این خودرو قبلاً آگهی شده است."
        )

        context.user_data.pop(
            "market_listing",
            None
        )

        return True

    save_players(players)

    context.user_data.pop(
        "market_listing",
        None
    )

    await update.message.reply_text(
        (
            "📢 <b>آگهی ثبت شد</b>\n\n"
            f"🚗 {vehicle_display_name(vehicle)}\n"
            f"💰 قیمت: <b>{price:,}</b>\n\n"
            "خریداران می‌توانند برای این خودرو پیشنهاد قیمت ارسال کنند."
        ),
        parse_mode="HTML"
    )

    return True


# ------------------------------------------------------------
# MY MARKET LISTINGS
# ------------------------------------------------------------

def my_market_keyboard(player):
    user_id = player.get(
        "id",
        player.get("user_id")
    )

    rows = []

    for listing in player.get(
        "market_listings",
        []
    ):
        if listing.get("status") != "active":
            continue

        vehicle = get_player_vehicle(
            player,
            listing.get("vehicle_id")
        )

        if not vehicle:
            continue

        rows.append([
            InlineKeyboardButton(
                f"📢 {vehicle_display_name(vehicle)} | {listing.get('price', 0):,}",
                callback_data=(
                    f"marketmy|"
                    f"{listing.get('id')}|"
                    f"{user_id}"
                )
            )
        ])

    rows.append([
        InlineKeyboardButton(
            "🔙 گاراژ",
            callback_data=f"garage|{user_id}"
        )
    ])

    return InlineKeyboardMarkup(rows)


async def show_my_market(update, context):
    query = update.callback_query

    user = query.from_user
    player = get_player(user)

    ensure_market(player)

    active = [
        x
        for x in player.get(
            "market_listings",
            []
        )
        if x.get("status") == "active"
    ]

    if not active:
        text = (
            "📢 <b>آگهی‌های من</b>\n\n"
            "آگهی فعالی نداری."
        )
    else:
        text = (
            "📢 <b>آگهی‌های من</b>\n\n"
            f"تعداد آگهی فعال: <b>{len(active)}</b>\n\n"
            "برای مدیریت آگهی روی آن بزن."
        )

    await query.edit_message_text(
        text,
        reply_markup=my_market_keyboard(player),
        parse_mode="HTML"
    )


# ------------------------------------------------------------
# MARKET LISTING MANAGEMENT
# ------------------------------------------------------------

def market_manage_keyboard(
    listing,
    user_id
):
    listing_id = listing.get("id")

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "❌ حذف آگهی",
                callback_data=f"marketremove|{listing_id}|{user_id}"
            )
        ],
        [
            InlineKeyboardButton(
                "🔙 آگهی‌های من",
                callback_data=f"mymarket|{user_id}"
            )
        ]
    ])


async def view_my_listing(
    update,
    context,
    listing_id
):
    query = update.callback_query

    user = query.from_user
    player = get_player(user)

    ensure_market(player)

    listing = None

    for item in player.get(
        "market_listings",
        []
    ):
        if item.get("id") == listing_id:
            listing = item
            break

    if not listing:
        await query.answer(
            "❌ آگهی پیدا نشد.",
            show_alert=True
        )
        return

    vehicle = get_player_vehicle(
        player,
        listing.get("vehicle_id")
    )

    if not vehicle:
        await query.answer(
            "❌ خودرو دیگر در گاراژ نیست.",
            show_alert=True
        )
        return

    text = (
        "📢 <b>مدیریت آگهی</b>\n\n"
        + vehicle_details_text(vehicle)
        + "\n\n"
        f"💰 قیمت آگهی: <b>{listing.get('price', 0):,}</b>\n"
        f"🤝 قابل مذاکره: "
        f"{'بله' if listing.get('negotiable') else 'خیر'}"
    )

    await query.edit_message_text(
        text,
        reply_markup=market_manage_keyboard(
            listing,
            user.id
        ),
        parse_mode="HTML"
    )


async def remove_market_listing(
    update,
    context,
    listing_id
):
    query = update.callback_query

    user = query.from_user
    player = get_player(user)

    ensure_market(player)

    found = False

    for listing in player.get(
        "market_listings",
        []
    ):
        if listing.get("id") == listing_id:
            if listing.get("status") != "active":
                await query.answer(
                    "⚠️ این آگهی قبلاً غیرفعال شده.",
                    show_alert=True
                )
                return

            listing["status"] = "cancelled"
            listing["cancelled_at"] = timestamp()

            found = True
            break

    if not found:
        await query.answer(
            "❌ آگهی پیدا نشد.",
            show_alert=True
        )
        return

    save_players(
        load_players()
    )

    # دوباره ذخیره بازیکن فعلی
    players = load_players()
    players[str(user.id)] = player
    save_players(players)

    await query.answer(
        "✅ آگهی حذف شد.",
        show_alert=True
    )

    await show_my_market(
        update,
        context
    )


# ------------------------------------------------------------
# VEHICLE SHOWROOM
# ------------------------------------------------------------

def showroom_keyboard(user_id):
    rows = []

    for vehicle_id, vehicle in VEHICLES.items():
        rows.append([
            InlineKeyboardButton(
                (
                    f"🚗 {vehicle.get('brand', '')} "
                    f"{vehicle.get('model', '')} "
                    f"— {vehicle.get('price', 0):,}"
                ),
                callback_data=f"showcar|{vehicle_id}|{user_id}"
            )
        ])

    rows.append([
        InlineKeyboardButton(
            "🏠 گاراژ",
            callback_data=f"garage|{user_id}"
        )
    ])

    return InlineKeyboardMarkup(rows)


async def show_showroom(update, context):
    query = update.callback_query

    user = query.from_user

    await query.edit_message_text(
        (
            "🏪 <b>نمایشگاه خودرو</b>\n\n"
            "خودروی موردنظر را انتخاب کن:"
        ),
        reply_markup=showroom_keyboard(
            user.id
        ),
        parse_mode="HTML"
    )


async def show_showroom_vehicle(
    update,
    context,
    vehicle_id
):
    query = update.callback_query

    user = query.from_user

    vehicle = VEHICLES.get(
        int(vehicle_id)
    )

    if not vehicle:
        await query.answer(
            "❌ خودرو پیدا نشد.",
            show_alert=True
        )
        return

    price = vehicle_price(vehicle)

    await query.edit_message_text(
        (
            "🏪 <b>نمایشگاه</b>\n\n"
            f"{vehicle_details_text(vehicle)}\n\n"
            f"💰 قیمت خرید: <b>{price:,}</b>"
        ),
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "🛒 خرید",
                    callback_data=(
                        f"buyvehicle|"
                        f"{vehicle_id}|"
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
        ]),
        parse_mode="HTML"
    )


# ------------------------------------------------------------
# VEHICLE CALLBACK ROUTER
# ------------------------------------------------------------

async def handle_vehicle_garage_callback(
    update,
    context
):
    query = update.callback_query

    if not query:
        return

    data = query.data or []

    parts = data.split("|")

    if not parts:
        return

    action = parts[0]

    try:
        if action == "garage":
            if not callback_is_owner(
                query,
                parts[-1]
            ):
                return

            await show_garage(
                update,
                context
            )
            return

        if action == "garagecar":
            if len(parts) < 3:
                return

            if not callback_is_owner(
                query,
                parts[-1]
            ):
                return

            await show_garage_vehicle(
                update,
                context,
                parts[1]
            )
            return

        if action == "vehiclesell":
            if len(parts) < 3:
                return

            if not callback_is_owner(
                query,
                parts[-1]
            ):
                return

            await show_vehicle_sell(
                update,
                context,
                parts[1]
            )
            return

        if action == "vehiclesellconfirm":
            if len(parts) < 3:
                return

            if not callback_is_owner(
                query,
                parts[-1]
            ):
                return

            await confirm_vehicle_sell(
                update,
                context,
                parts[1]
            )
            return

        if action == "vehiclegift":
            if len(parts) < 3:
                return

            if not callback_is_owner(
                query,
                parts[-1]
            ):
                return

            await start_vehicle_gift(
                update,
                context,
                parts[1]
            )
            return

        if action == "marketlist":
            if len(parts) < 3:
                return

            if not callback_is_owner(
                query,
                parts[-1]
            ):
                return

            await start_market_listing(
                update,
                context,
                parts[1]
            )
            return

        if action == "mymarket":
            if not callback_is_owner(
                query,
                parts[-1]
            ):
                return

            await show_my_market(
                update,
                context
            )
            return

        if action == "marketmy":
            if len(parts) < 3:
                return

            if not callback_is_owner(
                query,
                parts[-1]
            ):
                return

            await view_my_listing(
                update,
                context,
                parts[1]
            )
            return

        if action == "marketremove":
            if len(parts) < 3:
                return

            if not callback_is_owner(
                query,
                parts[-1]
            ):
                return

            await remove_market_listing(
                update,
                context,
                parts[1]
            )
            return

        if action == "showroom":
            if not callback_is_owner(
                query,
                parts[-1]
            ):
                return

            await show_showroom(
                update,
                context
            )
            return

        if action == "showcar":
            if len(parts) < 3:
                return

            if not callback_is_owner(
                query,
                parts[-1]
            ):
                return

            await show_showroom_vehicle(
                update,
                context,
                parts[1]
            )
            return

    except Exception as e:
        print(
            "Vehicle callback error:",
            repr(e)
        )

        try:
            await query.answer(
                "❌ خطایی در انجام عملیات رخ داد.",
                show_alert=True
            )
        except Exception:
            pass


# ------------------------------------------------------------
# VEHICLE TEXT COMMANDS
# ------------------------------------------------------------

async def vehicle_command_menu(
    update,
    context
):
    user = update.effective_user
    player = get_player(user)

    ensure_vehicle_system(player)

    await update.message.reply_text(
        (
            "🚗 <b>سیستم خودرو</b>\n\n"
            "🏠 گاراژ: خودروهای خودت\n"
            "🏪 نمایشگاه: خرید خودرو\n"
            "🤝 معاملات: خرید و فروش با بازیکنان\n"
            "🔨 حراجی: مزایده خودروها\n\n"
            "از دکمه‌های زیر استفاده کن:"
        ),
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "🏠 گاراژ",
                    callback_data=f"garage|{user.id}"
                ),
                InlineKeyboardButton(
                    "🏪 نمایشگاه",
                    callback_data=f"showroom|{user.id}"
                )
            ],
            [
                InlineKeyboardButton(
                    "🤝 معاملات",
                    callback_data=f"deals|{user.id}"
                ),
                InlineKeyboardButton(
                    "🔨 حراجی",
                    callback_data=f"auctions|{user.id}"
                )
            ]
        ]),
        parse_mode="HTML"
    )


# ------------------------------------------------------------
# SHOWROOM BUY WRAPPER
# ------------------------------------------------------------

async def showroom_buy_callback(
    update,
    context,
    vehicle_id
):
    query = update.callback_query

    user = query.from_user

    vehicle = VEHICLES.get(
        int(vehicle_id)
    )

    if not vehicle:
        await query.answer(
            "❌ خودرو پیدا نشد.",
            show_alert=True
        )
        return

    player = get_player(user)

    price = vehicle_price(vehicle)

    if int(player.get("cash", 0)) < price:
        await query.answer(
            "❌ پول نقد کافی نیست.",
            show_alert=True
        )
        return

    # توکن یکتا برای جلوگیری از خرید دوباره
    purchase_token = (
        f"showroom:{user.id}:{vehicle_id}"
    )

    completed = player.setdefault(
        "completed_purchases",
        []
    )

    if purchase_token in completed:
        await query.answer(
            "⚠️ این خرید قبلاً انجام شده.",
            show_alert=True
        )
        return

    player["cash"] = (
        int(player.get("cash", 0))
        - price
    )

    new_vehicle = dict(vehicle)

    new_vehicle["id"] = (
        generate_vehicle_id()
        if "generate_vehicle_id" in globals()
        else str(uuid.uuid4())
    )

    new_vehicle["owner_id"] = user.id

    add_vehicle_to_player(
        player,
        new_vehicle
    )

    completed.append(
        purchase_token
    )

    add_transaction(
        player,
        "vehicle_purchase",
        price,
        f"خرید {vehicle_display_name(vehicle)} از نمایشگاه",
        reference=purchase_token
    )

    players = load_players()
    players[str(user.id)] = player

    save_players(players)

    await query.answer(
        "✅ خودرو خریداری شد.",
        show_alert=True
    )

    await query.edit_message_text(
        (
            "🎉 <b>خرید موفق!</b>\n\n"
            f"🚗 {vehicle_display_name(vehicle)}\n"
            f"💰 مبلغ پرداختی: <b>{price:,}</b>\n\n"
            "خودرو وارد گاراژت شد."
        ),
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "🏠 گاراژ",
                    callback_data=f"garage|{user.id}"
                )
            ],
            [
                InlineKeyboardButton(
                    "🏪 نمایشگاه",
                    callback_data=f"showroom|{user.id}"
                )
            ]
        ]),
        parse_mode="HTML"
    )


# ------------------------------------------------------------
# MASTER / DEBUG VEHICLE SUMMARY
# ------------------------------------------------------------

def vehicle_system_summary(players):
    total_vehicles = 0
    total_market = 0
    total_deals = 0

    for player in players.values():
        total_vehicles += len(
            player.get("vehicles", [])
        )

        total_market += len([
            x
            for x in player.get(
                "market_listings",
                []
            )
            if x.get("status") == "active"
        ])

        total_deals += len(
            player.get(
                "vehicle_deals",
                []
            )
        )

    return {
        "vehicles": total_vehicles,
        "market": total_market,
        "deals": total_deals,
        }# ============================================================
# PART 9 — JOBS / TRAINING / RANK / WORK SHIFT / XP
# ============================================================

# ------------------------------------------------------------
# JOB HELPERS
# ------------------------------------------------------------

JOB_RANKS = [
    {
        "id": "apprentice",
        "name": "کارآموز",
        "min_level": 1,
        "xp": 0,
        "income_multiplier": 0.70,
    },
    {
        "id": "beginner",
        "name": "مبتدی",
        "min_level": 2,
        "xp": 250,
        "income_multiplier": 0.85,
    },
    {
        "id": "intermediate",
        "name": "متوسط",
        "min_level": 4,
        "xp": 700,
        "income_multiplier": 1.00,
    },
    {
        "id": "skilled",
        "name": "ماهر",
        "min_level": 7,
        "xp": 1600,
        "income_multiplier": 1.20,
    },
    {
        "id": "professional",
        "name": "حرفه‌ای",
        "min_level": 11,
        "xp": 3500,
        "income_multiplier": 1.45,
    },
    {
        "id": "master",
        "name": "استادکار",
        "min_level": 16,
        "xp": 7000,
        "income_multiplier": 1.80,
    },
]


JOB_DEFINITIONS = {
    "barber": {
        "name": "💈 آرایشگری",
        "description": (
            "اصلاح، کوتاهی، استایل مو و خدمات آرایشگری."
        ),
        "base_income": 70000,
        "base_xp": 35,
        "energy": 12,
        "training_cost": 80000,
    },
    "mechanic": {
        "name": "🔧 مکانیکی",
        "description": (
            "تعمیر موتور، ترمز، برق خودرو و سرویس خودرو."
        ),
        "base_income": 110000,
        "base_xp": 45,
        "energy": 15,
        "training_cost": 120000,
    },
}


WORK_DIFFICULTIES = {
    "easy": {
        "name": "آسان",
        "income": 0.75,
        "xp": 0.75,
        "failure": 0.03,
    },
    "normal": {
        "name": "عادی",
        "income": 1.00,
        "xp": 1.00,
        "failure": 0.08,
    },
    "hard": {
        "name": "سخت",
        "income": 1.45,
        "xp": 1.35,
        "failure": 0.15,
    },
    "expert": {
        "name": "تخصصی",
        "income": 2.10,
        "xp": 1.90,
        "failure": 0.23,
    },
}


def ensure_jobs(player):
    player.setdefault("jobs", {})
    player.setdefault("work_history", [])
    player.setdefault("training_history", [])
    player.setdefault("energy", 100)
    player.setdefault("last_work", 0)

    for job_id in JOB_DEFINITIONS:
        if job_id not in player["jobs"]:
            player["jobs"][job_id] = {
                "unlocked": False,
                "rank": "locked",
                "xp": 0,
                "level": 0,
                "sessions": 0,
                "successful": 0,
                "failed": 0,
                "income": 0,
                "loss": 0,
            }

    return player


def job_rank_data(job):
    rank_id = job.get(
        "rank",
        "apprentice"
    )

    for rank in JOB_RANKS:
        if rank["id"] == rank_id:
            return rank

    return JOB_RANKS[0]


def job_rank_name(job):
    return job_rank_data(job)["name"]


def calculate_job_rank(job):
    xp = int(job.get("xp", 0))

    selected = JOB_RANKS[0]

    for rank in JOB_RANKS:
        if xp >= rank["xp"]:
            selected = rank

    return selected


def update_job_rank(job):
    if not job.get("unlocked"):
        return False

    old_rank = job.get("rank")

    new_rank = calculate_job_rank(job)

    job["rank"] = new_rank["id"]

    changed = (
        old_rank is not None
        and old_rank != new_rank["id"]
    )

    return changed


def job_income_multiplier(job):
    return float(
        job_rank_data(job).get(
            "income_multiplier",
            1.0
        )
    )


def job_xp_to_next(job):
    current = int(
        job.get("xp", 0)
    )

    for rank in JOB_RANKS:
        if current < rank["xp"]:
            return rank["xp"] - current

    return 0


def job_rank_progress_text(job):
    current_rank = job_rank_data(job)

    current_xp = int(
        job.get("xp", 0)
    )

    next_xp = job_xp_to_next(job)

    if next_xp <= 0:
        return (
            f"🏆 رتبه: <b>{current_rank['name']}</b>\n"
            f"⭐ XP شغلی: <b>{current_xp:,}</b>\n"
            "👑 بالاترین رتبه"
        )

    return (
        f"🏅 رتبه: <b>{current_rank['name']}</b>\n"
        f"⭐ XP شغلی: <b>{current_xp:,}</b>\n"
        f"📈 تا رتبه بعد: <b>{next_xp:,}</b> XP"
    )


# ------------------------------------------------------------
# UNLOCK JOB
# ------------------------------------------------------------

def can_unlock_job(player, job_id):
    ensure_jobs(player)

    if job_id not in JOB_DEFINITIONS:
        return False, "❌ شغل نامعتبر است."

    job = player["jobs"][job_id]

    if job.get("unlocked"):
        return False, "⚠️ این شغل قبلاً فعال شده."

    if int(player.get("level", 1)) < 1:
        return False, "❌ سطح کافی نیست."

    return True, ""


async def unlock_job(
    update,
    context,
    job_id
):
    query = update.callback_query

    user = query.from_user
    player = get_player(user)

    ensure_jobs(player)

    if job_id not in JOB_DEFINITIONS:
        await query.answer(
            "❌ شغل نامعتبر است.",
            show_alert=True
        )
        return

    job = player["jobs"][job_id]

    if job.get("unlocked"):
        await query.answer(
            "⚠️ این شغل قبلاً فعال شده.",
            show_alert=True
        )
        return

    definition = JOB_DEFINITIONS[job_id]

    cost = int(
        definition["training_cost"]
    )

    if int(player.get("cash", 0)) < cost:
        await query.answer(
            "❌ پول کافی برای شروع آموزش نداری.",
            show_alert=True
        )
        return

    player["cash"] -= cost

    job["unlocked"] = True
    job["rank"] = "apprentice"
    job["level"] = 1

    training_id = (
        f"training:{user.id}:{job_id}"
    )

    player["training_history"].append({
        "id": training_id,
        "job": job_id,
        "cost": cost,
        "timestamp": timestamp(),
    })

    add_transaction(
        player,
        "job_training",
        cost,
        f"شروع آموزش {definition['name']}",
        reference=training_id
    )

    players = load_players()
    players[str(user.id)] = player
    save_players(players)

    await query.answer(
        "✅ آموزش شروع شد.",
        show_alert=True
    )

    await show_job(
        update,
        context,
        job_id
    )


# ------------------------------------------------------------
# JOB MENU
# ------------------------------------------------------------

def jobs_keyboard(player):
    user_id = player.get(
        "id",
        player.get("user_id")
    )

    rows = []

    for job_id, definition in JOB_DEFINITIONS.items():
        job = player["jobs"].get(job_id, {})

        if job.get("unlocked"):
            rank = job_rank_name(job)

            rows.append([
                InlineKeyboardButton(
                    f"{definition['name']} — {rank}",
                    callback_data=f"job|{job_id}|{user_id}"
                )
            ])
        else:
            rows.append([
                InlineKeyboardButton(
                    f"🔒 {definition['name']}",
                    callback_data=f"jobunlock|{job_id}|{user_id}"
                )
            ])

    rows.append([
        InlineKeyboardButton(
            "📊 آمار کار",
            callback_data=f"jobstats|{user_id}"
        )
    ])

    rows.append([
        InlineKeyboardButton(
            "🔙 منوی اصلی",
            callback_data=f"main|{user_id}"
        )
    ])

    return InlineKeyboardMarkup(rows)


async def show_jobs(update, context):
    query = update.callback_query

    user = query.from_user
    player = get_player(user)

    ensure_jobs(player)

    text = (
        "💼 <b>مرکز مشاغل UNDERCITY</b>\n\n"
        "هر شغل سیستم رتبه و XP جداگانه دارد.\n\n"
        "🏅 کارآموز\n"
        "🟢 مبتدی\n"
        "🔵 متوسط\n"
        "🟣 ماهر\n"
        "🔴 حرفه‌ای\n"
        "👑 استادکار\n\n"
        "با تمرین و آموزش می‌توانی رتبه‌ات را بالا ببری."
    )

    await query.edit_message_text(
        text,
        reply_markup=jobs_keyboard(player),
        parse_mode="HTML"
    )


# ------------------------------------------------------------
# JOB DETAILS
# ------------------------------------------------------------

def job_keyboard(player, job_id):
    user_id = player.get(
        "id",
        player.get("user_id")
    )

    job = player["jobs"][job_id]

    rows = [
        [
            InlineKeyboardButton(
                "▶️ شروع شیفت",
                callback_data=f"work|{job_id}|{user_id}"
            )
        ],
        [
            InlineKeyboardButton(
                "🎓 آموزش",
                callback_data=f"jobtraining|{job_id}|{user_id}"
            )
        ],
        [
            InlineKeyboardButton(
                "📊 آمار",
                callback_data=f"jobstatsone|{job_id}|{user_id}"
            )
        ],
        [
            InlineKeyboardButton(
                "🔙 مشاغل",
                callback_data=f"jobs|{user_id}"
            )
        ]
    ]

    return InlineKeyboardMarkup(rows)


async def show_job(
    update,
    context,
    job_id
):
    query = update.callback_query

    user = query.from_user
    player = get_player(user)

    ensure_jobs(player)

    if job_id not in JOB_DEFINITIONS:
        await query.answer(
            "❌ شغل نامعتبر است.",
            show_alert=True
        )
        return

    job = player["jobs"][job_id]
    definition = JOB_DEFINITIONS[job_id]

    if not job.get("unlocked"):
        await query.answer(
            "🔒 این شغل هنوز فعال نشده.",
            show_alert=True
        )
        return

    text = (
        f"{definition['name']}\n\n"
        f"📖 {definition['description']}\n\n"
        f"{job_rank_progress_text(job)}\n"
        f"🧰 شیفت‌ها: {job.get('sessions', 0):,}\n"
        f"✅ موفق: {job.get('successful', 0):,}\n"
        f"❌ ناموفق: {job.get('failed', 0):,}\n"
        f"💰 درآمد کل: {job.get('income', 0):,}\n"
        f"📉 ضرر کل: {job.get('loss', 0):,}\n\n"
        f"⚡ انرژی فعلی: {player.get('energy', 100)}/100"
    )

    await query.edit_message_text(
        text,
        reply_markup=job_keyboard(
            player,
            job_id
        ),
        parse_mode="HTML"
    )


# ------------------------------------------------------------
# TRAINING
# ------------------------------------------------------------

TRAINING_LEVELS = {
    1: {
        "name": "مقدماتی",
        "cost": 80000,
        "xp": 80,
    },
    2: {
        "name": "پایه",
        "cost": 150000,
        "xp": 160,
    },
    3: {
        "name": "پیشرفته",
        "cost": 300000,
        "xp": 300,
    },
    4: {
        "name": "تخصصی",
        "cost": 600000,
        "xp": 550,
    },
}


def next_training_level(job):
    current = int(
        job.get("level", 1)
    )

    next_level = current + 1

    if next_level not in TRAINING_LEVELS:
        return None

    return next_level


def training_keyboard(
    player,
    job_id
):
    user_id = player.get(
        "id",
        player.get("user_id")
    )

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🎓 آموزش بعدی",
                callback_data=(
                    f"jobtrainingdo|"
                    f"{job_id}|"
                    f"{user_id}"
                )
            )
        ],
        [
            InlineKeyboardButton(
                "🔙 بازگشت",
                callback_data=f"job|{job_id}|{user_id}"
            )
        ]
    ])


async def show_job_training(
    update,
    context,
    job_id
):
    query = update.callback_query

    user = query.from_user
    player = get_player(user)

    ensure_jobs(player)

    job = player["jobs"].get(job_id)

    if not job or not job.get("unlocked"):
        await query.answer(
            "❌ شغل فعال نیست.",
            show_alert=True
        )
        return

    next_level = next_training_level(job)

    if next_level is None:
        text = (
            "🎓 <b>آموزش</b>\n\n"
            "👑 تمام دوره‌های این شغل را گذرانده‌ای."
        )

        await query.edit_message_text(
            text,
            reply_markup=training_keyboard(
                player,
                job_id
            ),
            parse_mode="HTML"
        )

        return

    course = TRAINING_LEVELS[next_level]

    text = (
        "🎓 <b>دوره آموزشی</b>\n\n"
        f"📚 دوره: <b>{course['name']}</b>\n"
        f"🔢 سطح دوره: {next_level}\n"
        f"💰 هزینه: <b>{course['cost']:,}</b>\n"
        f"⭐ XP شغلی: +{course['xp']}\n\n"
        "با گذراندن دوره، توانایی انجام کارهای سخت‌تر افزایش پیدا می‌کند."
    )

    await query.edit_message_text(
        text,
        reply_markup=training_keyboard(
            player,
            job_id
        ),
        parse_mode="HTML"
    )


async def do_job_training(
    update,
    context,
    job_id
):
    query = update.callback_query

    user = query.from_user
    player = get_player(user)

    ensure_jobs(player)

    job = player["jobs"].get(job_id)

    if not job or not job.get("unlocked"):
        await query.answer(
            "❌ شغل فعال نیست.",
            show_alert=True
        )
        return

    next_level = next_training_level(job)

    if next_level is None:
        await query.answer(
            "👑 تمام دوره‌ها تکمیل شده.",
            show_alert=True
        )
        return

    course = TRAINING_LEVELS[next_level]
    cost = int(course["cost"])

    if int(player.get("cash", 0)) < cost:
        await query.answer(
            "❌ پول کافی برای این دوره نداری.",
            show_alert=True
        )
        return

    player["cash"] -= cost

    job["level"] = next_level
    job["xp"] = int(
        job.get("xp", 0)
    ) + int(course["xp"])

    rank_changed = update_job_rank(job)

    reference = (
        f"course:{user.id}:{job_id}:{next_level}"
    )

    add_transaction(
        player,
        "job_course",
        cost,
        f"دوره {course['name']} برای {JOB_DEFINITIONS[job_id]['name']}",
        reference=reference
    )

    player["training_history"].append({
        "id": reference,
        "job": job_id,
        "level": next_level,
        "cost": cost,
        "xp": course["xp"],
        "timestamp": timestamp(),
    })

    players = load_players()
    players[str(user.id)] = player
    save_players(players)

    await query.answer(
        "🎓 دوره با موفقیت تکمیل شد.",
        show_alert=True
    )

    if rank_changed:
        await context.bot.send_message(
            chat_id=user.id,
            text=(
                "🏆 <b>ارتقای رتبه شغلی!</b>\n\n"
                f"{JOB_DEFINITIONS[job_id]['name']}\n"
                f"رتبه جدید: <b>{job_rank_name(job)}</b>"
            ),
            parse_mode="HTML"
        )

    await show_job(
        update,
        context,
        job_id
    )


# ------------------------------------------------------------
# WORK SHIFT
# ------------------------------------------------------------

def work_difficulty_keyboard(
    player,
    job_id
):
    user_id = player.get(
        "id",
        player.get("user_id")
    )
return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🟢 آسان",
                callback_data=f"workdo|{job_id}|easy|{user_id}"
            )
        ],
        [
            InlineKeyboardButton(
                "🟡 عادی",
                callback_data=f"workdo|{job_id}|normal|{user_id}"
            )
        ],
        [
            InlineKeyboardButton(
                "🟠 سخت",
                callback_data=f"workdo|{job_id}|hard|{user_id}"
            )
        ],
        [
            InlineKeyboardButton(
                "🔴 تخصصی",
                callback_data=f"workdo|{job_id}|expert|{user_id}"
            )
        ],
        [
            InlineKeyboardButton(
                "🔙 بازگشت",
                callback_data=f"job|{job_id}|{user_id}"
            )
        ]
    ])


async def start_work_shift(
    update,
    context,
    job_id
):
    query = update.callback_query

    user = query.from_user
    player = get_player(user)

    ensure_jobs(player)

    job = player["jobs"].get(job_id)

    if not job or not job.get("unlocked"):
        await query.answer(
            "❌ شغل فعال نیست.",
            show_alert=True
        )
        return

    energy = int(
        player.get("energy", 100)
    )

    definition = JOB_DEFINITIONS[job_id]

    if energy < definition["energy"]:
        await query.answer(
            "😴 انرژی کافی نداری.",
            show_alert=True
        )
        return

    text = (
        f"{definition['name']}\n\n"
        "🕐 نوع شیفت را انتخاب کن:\n\n"
        "هرچه کار سخت‌تر باشد، درآمد و XP بیشتر است؛ "
        "اما احتمال اشتباه و ضرر هم افزایش پیدا می‌کند."
    )

    await query.edit_message_text(
        text,
        reply_markup=work_difficulty_keyboard(
            player,
            job_id
        ),
        parse_mode="HTML"
    )


def generate_work_result(
    player,
    job_id,
    difficulty_id
):
    definition = JOB_DEFINITIONS[job_id]
    difficulty = WORK_DIFFICULTIES[difficulty_id]

    job = player["jobs"][job_id]

    rank_multiplier = job_income_multiplier(job)

    customers = random.randint(
        1,
        3 + int(job.get("level", 1))
    )

    base_income = int(
        definition["base_income"]
        * customers
    )

    income = int(
        base_income
        * difficulty["income"]
        * rank_multiplier
    )

    base_xp = int(
        definition["base_xp"]
        * customers
    )

    xp = max(
        1,
        int(
            base_xp
            * difficulty["xp"]
        )
    )

    failure = (
        random.random()
        < difficulty["failure"]
    )

    loss = 0

    if failure:
        loss = int(
            income
            * random.uniform(
                0.15,
                0.40
            )
        )

        income = max(
            0,
            income - loss
        )

    return {
        "customers": customers,
        "income": income,
        "xp": xp,
        "loss": loss,
        "failed": failure,
    }


async def execute_work_shift(
    update,
    context,
    job_id,
    difficulty_id
):
    query = update.callback_query

    user = query.from_user
    player = get_player(user)

    ensure_jobs(player)

    if difficulty_id not in WORK_DIFFICULTIES:
        await query.answer(
            "❌ نوع شیفت نامعتبر است.",
            show_alert=True
        )
        return

    job = player["jobs"].get(job_id)

    if not job or not job.get("unlocked"):
        await query.answer(
            "❌ شغل فعال نیست.",
            show_alert=True
        )
        return

    definition = JOB_DEFINITIONS[job_id]

    energy_cost = int(
        definition["energy"]
    )

    if int(player.get("energy", 100)) < energy_cost:
        await query.answer(
            "😴 انرژی کافی نداری.",
            show_alert=True
        )
        return

    # شناسه یکتا برای هر شیفت
    shift_id = (
        f"shift:{user.id}:"
        f"{job_id}:"
        f"{time.time_ns()}"
    )

    result = generate_work_result(
        player,
        job_id,
        difficulty_id
    )

    player["energy"] = max(
        0,
        int(player.get("energy", 100))
        - energy_cost
    )

    player["cash"] = (
        int(player.get("cash", 0))
        + result["income"]
    )

    job["sessions"] = (
        int(job.get("sessions", 0))
        + 1
    )

    if result["failed"]:
        job["failed"] = (
            int(job.get("failed", 0))
            + 1
        )
    else:
        job["successful"] = (
            int(job.get("successful", 0))
            + 1
        )

    job["income"] = (
        int(job.get("income", 0))
        + result["income"]
    )

    job["loss"] = (
        int(job.get("loss", 0))
        + result["loss"]
    )

    job["xp"] = (
        int(job.get("xp", 0))
        + result["xp"]
    )

    old_rank = job.get("rank")

    rank_changed = update_job_rank(job)

    # XP کلی بازیکن
    level_before = int(
        player.get("level", 1)
    )

    add_xp(
        player,
        result["xp"]
    )

    level_after = int(
        player.get("level", 1)
    )

    job_result = {
        "id": shift_id,
        "job": job_id,
        "difficulty": difficulty_id,
        "customers": result["customers"],
        "income": result["income"],
        "loss": result["loss"],
        "xp": result["xp"],
        "failed": result["failed"],
        "energy": energy_cost,
        "timestamp": timestamp(),
    }

    player["work_history"].append(
        job_result
    )

    player["work_history"] = (
        player["work_history"][-100:]
    )

    add_transaction(
        player,
        "job_income",
        result["income"],
        (
            f"درآمد شیفت "
            f"{JOB_DEFINITIONS[job_id]['name']}"
        ),
        reference=shift_id
    )

    if result["loss"] > 0:
        add_transaction(
            player,
            "job_loss",
            result["loss"],
            "ضرر ناشی از خطای کاری",
            reference=f"{shift_id}:loss"
        )

    players = load_players()
    players[str(user.id)] = player
    save_players(players)

    difficulty_name = (
        WORK_DIFFICULTIES[
            difficulty_id
        ]["name"]
    )

    status = (
        "⚠️ این شیفت با مشکل همراه بود."
        if result["failed"]
        else "✅ شیفت با موفقیت انجام شد."
    )

    text = (
        f"💼 <b>گزارش شیفت</b>\n\n"
        f"🏢 شغل: {JOB_DEFINITIONS[job_id]['name']}\n"
        f"🎯 سختی: {difficulty_name}\n"
        f"👥 مشتری/خودرو: <b>{result['customers']}</b>\n\n"
        f"{status}\n\n"
        f"💰 درآمد خالص: <b>+{result['income']:,}</b>\n"
        f"📉 ضرر: <b>{result['loss']:,}</b>\n"
        f"⭐ XP شغلی: <b>+{result['xp']}</b>\n"
        f"⚡ انرژی مصرف‌شده: <b>-{energy_cost}</b>\n\n"
        f"🏅 رتبه: <b>{job_rank_name(job)}</b>\n"
        f"⭐ XP کلی: <b>{player.get('xp', 0):,}</b>\n"
        f"📈 Level: <b>{player.get('level', 1)}</b>"
    )

    if rank_changed and old_rank != job.get("rank"):
        text += (
            "\n\n"
            f"🏆 <b>ارتقای رتبه!</b>\n"
            f"رتبه جدید: {job_rank_name(job)}"
        )

    if level_after > level_before:
        text += (
            "\n\n"
            f"🎉 <b>LEVEL UP!</b>\n"
            f"سطح جدید: {level_after}"
        )

    await query.edit_message_text(
        text,
        reply_markup=job_keyboard(
            player,
            job_id
        ),
        parse_mode="HTML"
    )


# ------------------------------------------------------------
# JOB STATISTICS
# ------------------------------------------------------------

async def show_job_stats(
    update,
    context,
    job_id=None
):
    query = update.callback_query

    user = query.from_user
    player = get_player(user)

    ensure_jobs(player)

    if job_id:
        job = player["jobs"].get(job_id)

        if not job:
            await query.answer(
                "❌ شغل پیدا نشد.",
                show_alert=True
            )
            return

        definition = JOB_DEFINITIONS[job_id]

        text = (
            f"📊 <b>آمار {definition['name']}</b>\n\n"
            f"🏅 رتبه: <b>{job_rank_name(job)}</b>\n"
            f"⭐ XP: <b>{job.get('xp', 0):,}</b>\n"
            f"🎓 سطح آموزشی: <b>{job.get('level', 0)}</b>\n\n"
            f"🕐 تعداد شیفت: {job.get('sessions', 0):,}\n"
            f"✅ موفق: {job.get('successful', 0):,}\n"
            f"❌ ناموفق: {job.get('failed', 0):,}\n"
            f"💰 درآمد: {job.get('income', 0):,}\n"
            f"📉 ضرر: {job.get('loss', 0):,}"
        )

        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "🔙 بازگشت",
                    callback_data=f"job|{job_id}|{user.id}"
                )
            ]
        ])

    else:
        total_income = 0
        total_loss = 0
        total_sessions = 0

        lines = [
            "📊 <b>آمار کلی مشاغل</b>",
            ""
        ]

        for jid, definition in JOB_DEFINITIONS.items():
            job = player["jobs"][jid]

            total_income += int(
                job.get("income", 0)
            )

            total_loss += int(
                job.get("loss", 0)
            )

            total_sessions += int(
                job.get("sessions", 0)
            )

            if job.get("unlocked"):
                lines.append(
                    f"{definition['name']} — "
                    f"{job_rank_name(job)} | "
                    f"XP {job.get('xp', 0):,}"
                )
            else:
                lines.append(
                    f"🔒 {definition['name']}"
                )

        lines.extend([
            "",
            f"🕐 کل شیفت‌ها: {total_sessions:,}",
            f"💰 کل درآمد: {total_income:,}",
            f"📉 کل ضرر: {total_loss:,}",
        ])

        text = "\n".join(lines)

        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "🔙 مشاغل",
                    callback_data=f"jobs|{user.id}"
                )
            ]
        ])

    await query.edit_message_text(
        text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )


# ------------------------------------------------------------
# JOB CALLBACK ROUTER
# ------------------------------------------------------------

async def handle_job_callback(
    update,
    context
):
    query = update.callback_query

    if not query:
        return

    parts = (query.data or "").split("|")

    if not parts:
        return

    action = parts[0]

    try:
        if action == "jobs":
            if not callback_is_owner(
                query,
                parts[-1]
            ):
                return

            await show_jobs(
                update,
                context
            )
            return

        if action == "job":
            if len(parts) < 3:
                return

            if not callback_is_owner(
                query,
                parts[-1]
            ):
                return

            await show_job(
                update,
                context,
                parts[1]
            )
            return

        if action == "jobunlock":
            if len(parts) < 3:
                return

            if not callback_is_owner(
                query,
                parts[-1]
            ):
                return

            await unlock_job(
                update,
                context,
                parts[1]
            )
            return

        if action == "jobtraining":
            if len(parts) < 3:
                return

            if not callback_is_owner(
                query,
                parts[-1]
            ):
                return

            await show_job_training(
                update,
                context,
                parts[1]
            )
            return

        if action == "jobtrainingdo":
            if len(parts) < 3:
                return

            if not callback_is_owner(
                query,
                parts[-1]
            ):
                return

            await do_job_training(
                update,
                context,
                parts[1]
            )
            return

        if action == "work":
            if len(parts) < 3:
                return

            if not callback_is_owner(
                query,
                parts[-1]
            ):
                return

            await start_work_shift(
                update,
                context,
                parts[1]
            )
            return

        if action == "workdo":
            if len(parts) < 4:
                return

            if not callback_is_owner(
                query,
                parts[-1]
            ):
                return

            await execute_work_shift(
                update,
                context,
                parts[1],
                parts[2]
            )
            return

        if action == "jobstats":
            if not callback_is_owner(
                query,
                parts[-1]
            ):
                return

            await show_job_stats(
                update,
                context
            )
            return

        if action == "jobstatsone":
            if len(parts) < 3:
                return

            if not callback_is_owner(
                query,
                parts[-1]
            ):
                return

            await show_job_stats(
                update,
                context,
                parts[1]
            )
            return

    except Exception as e:
        print(
            "Job callback error:",
            repr(e)
        )

        try:
            await query.answer(
                "❌ خطایی در سیستم شغل رخ داد.",
                show_alert=True
            )
        except Exception:
            pass


# ------------------------------------------------------------
# ENERGY RECOVERY
# ------------------------------------------------------------

def recover_energy(player):
    """
    بازیابی تدریجی انرژی بر اساس زمان.
    """
    now = time.time()

    last = float(
        player.get(
            "last_energy_update",
            now
        )
    )

    elapsed = max(
        0,
        now - last
    )

    # هر 10 دقیقه یک واحد انرژی
    recovered = int(
        elapsed // 600
    )

    if recovered <= 0:
        return False

    old_energy = int(
        player.get("energy", 100)
    )

    new_energy = min(
        100,
        old_energy + recovered
    )

    player["energy"] = new_energy
    player["last_energy_update"] = now

    return new_energy != old_energy


# ------------------------------------------------------------
# JOB COMMAND
# ------------------------------------------------------------

async def jobs_command(
    update,
    context
):
    player = get_player(
        update.effective_user
    )

    ensure_jobs(player)
    recover_energy(player)

    players = load_players()
    players[str(update.effective_user.id)] = player
    save_players(players)

    await update.message.reply_text(
        (
            "💼 <b>مشاغل</b>\n\n"
            "در UNDERCITY می‌توانی مهارت واقعی بسازی، "
            "XP بگیری، رتبه ارتقا بدهی و درآمدت را افزایش دهی."
        ),
        reply_markup=jobs_keyboard(player),
        parse_mode="HTML"
        )# ============================================================
# PART 10 — START / HELP / MAIN MENU / MONEY / TEXT ROUTER
# ============================================================

# ------------------------------------------------------------
# SAFE CALLBACK HELPERS
# ------------------------------------------------------------

def callback_owner_id(query):
    try:
        return int(str(query.data).split("|")[-1])
    except Exception:
        return None


def callback_is_owner(query, user_id):
    try:
        return int(query.from_user.id) == int(user_id)
    except Exception:
        return False


async def answer_callback(query, text=None, alert=False):
    try:
        if text:
            await query.answer(
                text,
                show_alert=alert
            )
        else:
            await query.answer()
    except Exception:
        pass


# ------------------------------------------------------------
# PLAYER DISPLAY
# ------------------------------------------------------------

def player_display_name(player):
    if not player:
        return "بازیکن"

    name = player.get("name")

    if name:
        return str(name)

    username = player.get("username")

    if username:
        return f"@{username}"

    return str(
        player.get(
            "id",
            player.get("user_id", "بازیکن")
        )
    )


def player_id(player):
    return int(
        player.get(
            "id",
            player.get("user_id", 0)
        )
    )


# ------------------------------------------------------------
# MAIN MENU
# ------------------------------------------------------------

def main_menu_keyboard(user_id):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "💰 کیف پول",
                callback_data=f"wallet|{user_id}"
            ),
            InlineKeyboardButton(
                "🚗 خودرو",
                callback_data=f"vehicles|{user_id}"
            )
        ],
        [
            InlineKeyboardButton(
                "💼 مشاغل",
                callback_data=f"jobs|{user_id}"
            ),
            InlineKeyboardButton(
                "🥊 مبارزه",
                callback_data=f"combat|{user_id}"
            )
        ],
        [
            InlineKeyboardButton(
                "🏥 کلینیک",
                callback_data=f"clinic|{user_id}"
            ),
            InlineKeyboardButton(
                "🎒 تجهیزات",
                callback_data=f"equipment|{user_id}"
            )
        ],
        [
            InlineKeyboardButton(
                "📊 پروفایل",
                callback_data=f"profile|{user_id}"
            ),
            InlineKeyboardButton(
                "❓ راهنما",
                callback_data=f"help|1|{user_id}"
            )
        ],
    ])


async def show_main_menu(update, context):
    query = update.callback_query

    if query:
        user = query.from_user
        player = get_player(user)

        if not callback_is_owner(
            query,
            query.data.split("|")[-1]
        ):
            await answer_callback(
                query,
                "❌ این منو متعلق به شما نیست.",
                True
            )
            return

        text = (
            "🏙 <b>UNDERCITY</b>\n\n"
            f"👤 {player_display_name(player)}\n"
            f"⭐ Level: <b>{player.get('level', 1)}</b>\n"
            f"💰 پول نقد: <b>{player.get('cash', 0):,}</b>\n"
            f"🏦 بانک: <b>{player.get('bank_balance', 0):,}</b>\n\n"
            "یکی از بخش‌ها را انتخاب کن:"
        )

        await query.edit_message_text(
            text,
            reply_markup=main_menu_keyboard(user.id),
            parse_mode="HTML"
        )

    else:
        user = update.effective_user
        player = get_player(user)

        text = (
            "🏙 <b>UNDERCITY</b>\n\n"
            f"👤 {player_display_name(player)}\n"
            f"⭐ Level: <b>{player.get('level', 1)}</b>\n"
            f"💰 پول نقد: <b>{player.get('cash', 0):,}</b>\n"
            f"🏦 بانک: <b>{player.get('bank_balance', 0):,}</b>\n\n"
            "یکی از بخش‌ها را انتخاب کن:"
        )

        await update.message.reply_text(
            text,
            reply_markup=main_menu_keyboard(user.id),
            parse_mode="HTML"
        )


# ------------------------------------------------------------
# /START — ONLY WELCOME
# ------------------------------------------------------------

async def start_command(update, context):
    user = update.effective_user

    player = get_player(user)

    text = (
        "🏙 <b>به UNDERCITY خوش آمدی</b>\n\n"
        "اینجا یک شهر زیرزمینیه؛ جایی که می‌تونی "
        "از صفر شروع کنی و مسیر خودت رو بسازی.\n\n"
        "💰 پول به دست بیار\n"
        "🚗 خودرو بخر و معامله کن\n"
        "💼 شغل یاد بگیر و پیشرفت کن\n"
        "🥊 با بازیکن‌ها مبارزه کن\n"
        "🏥 آسیب‌هات رو درمان کن\n"
        "📈 Level و مهارت‌هات رو بالا ببر\n\n"
        "برای ورود به بازی، دستور زیر رو بزن:\n\n"
        "👉 <code>منو</code>\n\n"
        "اگر تازه‌واردی، اول <code>/help</code> رو بخون."
    )

    await update.message.reply_text(
        text,
        parse_mode="HTML"
    )


# ------------------------------------------------------------
# MENU COMMAND
# ------------------------------------------------------------

async def menu_command(update, context):
    await show_main_menu(
        update,
        context
    )


# ------------------------------------------------------------
# HELP PAGES
# ------------------------------------------------------------

HELP_PAGES = [

    {
        "title": "🏙 شروع بازی",
        "text": (
            "UNDERCITY یک بازی نقش‌آفرینی شهریه.\n\n"
            "از صفر شروع می‌کنی و با کار، معامله، "
            "خرید خودرو، مبارزه و پیشرفت اقتصادی "
            "می‌تونی شخصیتت رو قوی‌تر کنی.\n\n"
            "🔹 /start\n"
            "فقط پیام خوش‌آمدگویی را نمایش می‌دهد.\n\n"
            "🔹 منو\n"
            "منوی اصلی بازی را باز می‌کند.\n\n"
            "🔹 /help\n"
            "همین راهنمای آموزشی را باز می‌کند."
        )
    },

    {
        "title": "💰 اقتصاد و پول",
        "text": (
            "💵 دو نوع موجودی اصلی داری:\n\n"
            "💰 پول نقد\n"
            "🏦 موجودی بانک\n\n"
            "از کیف پول می‌توانی:\n"
            "• پول را به بانک واریز کنی\n"
            "• از بانک برداشت کنی\n"
            "• به بازیکن دیگر پول انتقال بدهی\n"
            "• تاریخچه تراکنش‌ها را ببینی\n\n"
            "⚠️ انتقال پول باید فقط یک بار انجام شود؛ "
            "برای جلوگیری از دوبار پرداخت شدن، "
            "هر انتقال شناسه یکتا دارد."
        )
    },

    {
        "title": "🚗 خودرو",
        "text": (
            "سیستم خودرو یکی از بخش‌های اصلی بازیه.\n\n"
            "می‌تونی:\n"
            "🚗 خودرو بخری\n"
            "💰 خودرو بفروشی\n"
            "🎁 خودرو هدیه بدهی\n"
            "🤝 با بازیکن دیگر معامله کنی\n"
            "📢 خودرو را برای فروش آگهی کنی\n"
            "🔨 خودرو را وارد حراجی کنی\n\n"
            "هر خودرو مالک مشخص دارد و انتقال مالکیت "
            "فقط بعد از تکمیل موفق معامله انجام می‌شود."
        )
    },

    {
        "title": "🤝 معامله با بازیکنان",
        "text": (
            "برای معامله خودرو با بازیکن دیگر:\n\n"
            "1️⃣ خودرو را برای فروش پیشنهاد بده.\n"
            "2️⃣ خریدار قیمت را بررسی می‌کند.\n"
            "3️⃣ می‌تواند پیشنهاد قیمت بدهد.\n"
            "4️⃣ فروشنده قبول یا رد می‌کند.\n"
            "5️⃣ پس از تأیید، موجودی خریدار بررسی می‌شود.\n"
            "6️⃣ پول منتقل می‌شود.\n"
            "7️⃣ مالکیت خودرو تغییر می‌کند.\n\n"
            "اگر پول کافی نباشد، معامله انجام نمی‌شود."
        )
    },

    {
        "title": "💼 مشاغل",
        "text": (
            "دو شغل اصلی فعلی:\n\n"
            "💈 آرایشگری\n"
            "🔧 مکانیکی\n\n"
            "برای هر شغل رتبه جداگانه داری:\n\n"
            "کارآموز ← مبتدی ← متوسط ← ماهر ← "
            "حرفه‌ای ← استادکار\n\n"
            "با کار کردن XP می‌گیری.\n"
            "با آموزش می‌توانی مهارت خودت را سریع‌تر بالا ببری."
        )
    },

    {
        "title": "⭐ Level و XP",
        "text": (
            "XP باعث افزایش Level شخصیت می‌شود.\n\n"
            "با Level بالاتر امکانات بیشتری باز می‌شود.\n\n"
            "برای مثال بعضی تجهیزات و حملات فقط "
            "بعد از رسیدن به Level مشخص قابل استفاده‌اند.\n\n"
            "XP می‌تواند از:\n"
            "💼 کار\n"
            "🥊 مبارزه\n"
            "🎓 آموزش\n"
            "و فعالیت‌های دیگر به دست بیاید."
        )
    },

    {
        "title": "🥊 مبارزه",
        "text": (
            "برای شروع مبارزه می‌توانی به پیام بازیکن دیگر "
            "Reply کنی و بنویسی:\n\n"
            "<code>ریپ</code>\n\n"
            "بعد نوع ضربه و محل برخورد را انتخاب می‌کنی.\n\n"
            "مثلاً:\n"
            "👊 مشت به صورت\n"
            "🦵 لگد به پا\n"
            "🔪 حمله با چاقو\n\n"
            "هر قسمت بدن HP جداگانه دارد و لباس/زره "
            "می‌تواند مقدار آسیب را کاهش دهد."
        )
    },

    {
        "title": "🏥 آسیب و درمان",
        "text": (
            "در مبارزه ممکن است دچار آسیب شوی:\n\n"
            "🟣 کبودی\n"
            "🩸 زخم\n"
            "🩸 خونریزی\n"
            "🦴 شکستگی\n"
            "💥 دررفتگی\n\n"
            "برای درمان می‌توانی به بخش کلینیک بروی.\n\n"
            "آسیب‌های درمان‌نشده می‌توانند روی وضعیت "
            "بدنی شخصیت تأثیر بگذارند."
        )
    },

    {
        "title": "🎒 تجهیزات",
        "text": (
            "تجهیزات می‌توانند روی مبارزه اثر بگذارند.\n\n"
            "بعضی تجهیزات دفاعی هستند و آسیب را کم می‌کنند.\n\n"
            "بعضی تجهیزات تهاجمی‌اند و بعد از رسیدن "
            "به Level لازم باز می‌شوند.\n\n"
            "برای دیدن تجهیزات از منوی اصلی وارد بخش "
            "🎒 تجهیزات شو."
        )
    },

    {
        "title": "🏆 هدف بازی",
        "text": (
            "UNDERCITY فقط درباره پول نیست.\n\n"
            "می‌توانی مسیر خودت را انتخاب کنی:\n\n"
            "💰 تاجر\n"
            "🚗 دلال خودرو\n"
            "🔧 مکانیک\n"
            "💈 آرایشگر\n"
            "🥊 مبارز\n"
            "🏆 بازیکن همه‌فن‌حریف\n\n"
            "هدف اینه که شخصیتت رو قدم‌به‌قدم بسازی."
        )
    },
]


def help_keyboard(
    page,
    user_id
):
    total = len(HELP_PAGES)

    rows = []

    navigation = []

    if page > 0:
        navigation.append(
            InlineKeyboardButton(
                "⬅️ قبلی",
                callback_data=f"help|{page - 1}|{user_id}"
            )
        )

    if page < total - 1:
        navigation.append(
            InlineKeyboardButton(
                "بعدی ➡️",
                callback_data=f"help|{page + 1}|{user_id}"
            )
        )

    if navigation:
        rows.append(navigation)

    rows.append([
        InlineKeyboardButton(
            f"📖 {page + 1}/{total}",
            callback_data=f"helpnoop|{user_id}"
        )
    ])

    rows.append([
        InlineKeyboardButton(
            "🏠 منوی اصلی",
            callback_data=f"main|{user_id}"
        )
    ])

    return InlineKeyboardMarkup(rows)


async def show_help_page(
    update,
    context,
    page=0
):
    query = update.callback_query

    if query:
        user = query.from_user
    else:
        user = update.effective_user

    try:
        page = int(page)
    except Exception:
        page = 0

    page = max(
        0,
        min(
            page,
            len(HELP_PAGES) - 1
        )
    )

    data = HELP_PAGES[page]

    text = (
        "❓ <b>راهنمای UNDERCITY</b>\n\n"
        f"<b>{data['title']}</b>\n\n"
        f"{data['text']}"
    )

    keyboard = help_keyboard(
        page,
        user.id
    )

    if query:
        await query.edit_message_text(
            text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    else:
        await update.message.reply_text(
            text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )


async def help_command(update, context):
    await show_help_page(
        update,
        context,
        0
    )


async def help_callback(
    update,
    context,
    page
):
    query = update.callback_query

    if not query:
        return

    parts = (query.data or "").split("|")

    if len(parts) < 3:
        return

    if not callback_is_owner(
        query,
        parts[-1]
    ):
        await answer_callback(
            query,
            "❌ این راهنما متعلق به شما نیست.",
            True
        )
        return

    await answer_callback(query)

    await show_help_page(
        update,
        context,
        int(page)
    )


# ------------------------------------------------------------
# WALLET
# ------------------------------------------------------------

def wallet_keyboard(user_id):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "💵 واریز",
                callback_data=f"deposit|{user_id}"
            ),
            InlineKeyboardButton(
                "🏧 برداشت",
                callback_data=f"withdraw|{user_id}"
            )
        ],
        [
            InlineKeyboardButton(
                "💸 انتقال پول",
                callback_data=f"transfer|{user_id}"
            )
        ],
        [
            InlineKeyboardButton(
                "📜 تراکنش‌ها",
                callback_data=f"transactions|{user_id}"
            )
        ],
        [
            InlineKeyboardButton(
                "🔙 منوی اصلی",
                callback_data=f"main|{user_id}"
            )
        ]
    ])


async def show_wallet(
    update,
    context
):
    query = update.callback_query

    user = query.from_user
    player = get_player(user)

    text = (
        "💰 <b>کیف پول</b>\n\n"
        f"💵 پول نقد: <b>{player.get('cash', 0):,}</b>\n"
        f"🏦 بانک: <b>{player.get('bank_balance', 0):,}</b>\n"
        f"💳 اعتبار: <b>{player.get('credit_score', 0)}</b>\n\n"
        "عملیات موردنظر را انتخاب کن:"
    )

    await query.edit_message_text(
        text,
        reply_markup=wallet_keyboard(user.id),
        parse_mode="HTML"
    )


# ------------------------------------------------------------
# MONEY OPERATION STATE
# ------------------------------------------------------------

def set_money_state(
    context,
    action,
    user_id
):
    context.user_data["money_action"] = {
        "action": action,
        "user_id": int(user_id),
    }


def get_money_state(
    context
):
    return context.user_data.get(
        "money_action"
    )


def clear_money_state(
    context
):
    context.user_data.pop(
        "money_action",
        None
    )


async def ask_money_amount(
    update,
    context,
    action
):
    user = update.callback_query.from_user

    set_money_state(
        context,
        action,
        user.id
    )

    names = {
        "deposit": "واریز",
        "withdraw": "برداشت",
        "transfer": "انتقال",
    }

    name = names.get(
        action,
        "عملیات"
    )

    await update.callback_query.edit_message_text(
        (
            f"💰 <b>{name}</b>\n\n"
            "مبلغ را به صورت عدد ارسال کن.\n\n"
            "مثال:\n"
            "<code>500000</code>\n\n"
            "برای لغو بنویس:\n"
            "<code>لغو</code>"
        ),
        parse_mode="HTML"
    )


# ------------------------------------------------------------
# TRANSACTION HISTORY
# ------------------------------------------------------------

async def show_transactions(
    update,
    context
):
    query = update.callback_query

    user = query.from_user
    player = get_player(user)

    transactions = player.get(
        "transactions",
        []
    )

    if not transactions:
        text = (
            "📜 <b>تاریخچه تراکنش‌ها</b>\n\n"
            "هنوز تراکنشی ثبت نشده."
        )
    else:
        lines = [
            "📜 <b>آخرین تراکنش‌ها</b>",
            ""
        ]

        for item in reversed(
            transactions[-15:]
        ):
            amount = int(
                item.get("amount", 0)
            )

            direction = item.get(
                "direction",
                ""
            )

            if direction == "in":
                sign = "🟢 +"
            elif direction == "out":
                sign = "🔴 -"
            else:
                sign = "💰 "

            description = item.get(
                "description",
                "تراکنش"
            )

            lines.append(
                f"{sign}{amount:,} — {description}"
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
        ]),
        parse_mode="HTML"
    )


# ------------------------------------------------------------
# ROBUST MONEY TRANSFER
# ------------------------------------------------------------

def ensure_transfer_system(player):
    player.setdefault(
        "money_transfers",
        []
    )


def find_transfer(
    players,
    transfer_id
):
    for player in players.values():
        for transfer in player.get(
            "money_transfers",
            []
        ):
            if transfer.get("id") == transfer_id:
                return transfer

    return None


def create_transfer_id(
    sender_id,
    receiver_id,
    amount
):
    return (
        f"money:"
        f"{sender_id}:"
        f"{receiver_id}:"
        f"{amount}:"
        f"{uuid.uuid4().hex}"
    )


def execute_money_transfer(
    players,
    sender_id,
    receiver_id,
    amount
):
    sender = players.get(
        str(sender_id)
    )

    receiver = players.get(
        str(receiver_id)
    )

    if not sender:
        return False, "❌ فرستنده پیدا نشد."

    if not receiver:
        return False, "❌ گیرنده پیدا نشد."

    if sender_id == receiver_id:
        return False, "❌ نمی‌توانی به خودت پول انتقال بدهی."

    amount = int(amount)

    if amount <= 0:
        return False, "❌ مبلغ نامعتبر است."

    sender_cash = int(
        sender.get("cash", 0)
    )

    if sender_cash < amount:
        return False, "❌ موجودی نقدی کافی نیست."

    transfer_id = create_transfer_id(
        sender_id,
        receiver_id,
        amount
    )

    ensure_transfer_system(sender)
    ensure_transfer_system(receiver)

    # قفل موقت عملیات
    sender.setdefault(
        "pending_transfers",
        {}
    )

    if transfer_id in sender["pending_transfers"]:
        return False, "⚠️ این انتقال قبلاً در حال انجام است."

    sender["pending_transfers"][transfer_id] = True

    # کسر و اضافه فقط یک بار
    sender["cash"] = (
        sender_cash - amount
    )

    receiver["cash"] = (
        int(receiver.get("cash", 0))
        + amount
    )

    record = {
        "id": transfer_id,
        "from": int(sender_id),
        "to": int(receiver_id),
        "amount": amount,
        "timestamp": timestamp(),
        "status": "completed",
    }

    sender["money_transfers"].append(
        record
    )

    receiver["money_transfers"].append(
        record
    )

    sender["money_transfers"] = (
        sender["money_transfers"][-100:]
    )

    receiver["money_transfers"] = (
        receiver["money_transfers"][-100:]
    )

    sender.setdefault(
        "pending_transfers",
        {}
    ).pop(
        transfer_id,
        None
    )

    add_transaction(
        sender,
        "money_transfer_out",
        amount,
        f"انتقال پول به {receiver_id}",
        reference=transfer_id,
        direction="out"
    )

    add_transaction(
        receiver,
        "money_transfer_in",
        amount,
        f"دریافت پول از {sender_id}",
        reference=transfer_id,
        direction="in"
    )

    return True, record


# ------------------------------------------------------------
# PROCESS MONEY MESSAGE
# ------------------------------------------------------------

async def process_money_message(
    update,
    context
):
    state = get_money_state(
        context
    )

    if not state:
        return False

    user = update.effective_user

    text = normalize_digits(
        update.message.text.strip()
    )

    if text.lower() in (
        "لغو",
        "cancel"
    ):
        clear_money_state(
            context
        )

        await update.message.reply_text(
            "❌ عملیات لغو شد."
        )

        return True

    action = state.get(
        "action"
    )

    # --------------------------------------------------------
    # TRANSFER
    # --------------------------------------------------------

    if action == "transfer":
        transfer_data = context.user_data.get(
            "transfer_data"
        )

        if not transfer_data:
            # مرحله اول: دریافت آیدی
            if not text.isdigit():
                await update.message.reply_text(
                    "❌ آیدی عددی گیرنده را ارسال کن."
                )
                return True

            receiver_id = int(text)

            if receiver_id == user.id:
                await update.message.reply_text(
                    "❌ نمی‌توانی به خودت پول انتقال بدهی."
                )
                return True

            players = load_players()

            if str(receiver_id) not in players:
                await update.message.reply_text(
                    "❌ چنین بازیکنی پیدا نشد."
                )
                return True

            context.user_data["transfer_data"] = {
                "receiver_id": receiver_id
            }

            await update.message.reply_text(
                (
                    "💸 گیرنده ثبت شد.\n\n"
                    f"👤 آیدی: <code>{receiver_id}</code>\n\n"
                    "حالا مبلغ انتقال را ارسال کن."
                ),
                parse_mode="HTML"
            )

            return True
        receiver_id = int(
            transfer_data["receiver_id"]
        )

        amount = parse_amount(text)

        if amount <= 0:
            await update.message.reply_text(
                "❌ مبلغ معتبر نیست."
            )
            return True

        players = load_players()

        success, result = execute_money_transfer(
            players,
            user.id,
            receiver_id,
            amount
        )

        if not success:
            await update.message.reply_text(
                result
            )
            return True

        save_players(players)

        clear_money_state(
            context
        )

        context.user_data.pop(
            "transfer_data",
            None
        )

        await update.message.reply_text(
            (
                "✅ <b>انتقال موفق</b>\n\n"
                f"💸 مبلغ: <b>{amount:,}</b>\n"
                f"👤 گیرنده: <code>{receiver_id}</code>\n\n"
                "تراکنش با موفقیت ثبت شد."
            ),
            parse_mode="HTML"
        )

        try:
            await context.bot.send_message(
                chat_id=receiver_id,
                text=(
                    "💰 <b>پول دریافت کردی</b>\n\n"
                    f"💵 مبلغ: <b>{amount:,}</b>\n"
                    f"👤 فرستنده: <code>{user.id}</code>"
                ),
                parse_mode="HTML"
            )
        except Exception:
            pass

        return True

    # --------------------------------------------------------
    # DEPOSIT
    # --------------------------------------------------------

    amount = parse_amount(text)

    if amount <= 0:
        await update.message.reply_text(
            "❌ مبلغ معتبر وارد کن."
        )
        return True

    players = load_players()

    player = players.get(
        str(user.id)
    )

    if not player:
        clear_money_state(
            context
        )

        await update.message.reply_text(
            "❌ اطلاعات بازیکن پیدا نشد."
        )

        return True

    cash = int(
        player.get("cash", 0)
    )

    bank = int(
        player.get("bank_balance", 0)
    )

    if action == "deposit":
        if cash < amount:
            await update.message.reply_text(
                "❌ پول نقد کافی نداری."
            )
            return True

        player["cash"] = cash - amount
        player["bank_balance"] = bank + amount

        add_transaction(
            player,
            "deposit",
            amount,
            "واریز به بانک",
            reference=f"deposit:{uuid.uuid4().hex}",
            direction="out"
        )

        message = (
            "✅ <b>واریز انجام شد</b>\n\n"
            f"💵 مبلغ: <b>{amount:,}</b>\n"
            f"🏦 موجودی بانک: <b>{player['bank_balance']:,}</b>"
        )

    elif action == "withdraw":
        if bank < amount:
            await update.message.reply_text(
                "❌ موجودی بانک کافی نیست."
            )
            return True

        player["bank_balance"] = bank - amount
        player["cash"] = cash + amount

        add_transaction(
            player,
            "withdraw",
            amount,
            "برداشت از بانک",
            reference=f"withdraw:{uuid.uuid4().hex}",
            direction="in"
        )

        message = (
            "✅ <b>برداشت انجام شد</b>\n\n"
            f"💵 مبلغ: <b>{amount:,}</b>\n"
            f"💰 پول نقد: <b>{player['cash']:,}</b>"
        )

    else:
        clear_money_state(
            context
        )

        return False

    players[str(user.id)] = player

    save_players(players)

    clear_money_state(
        context
    )

    await update.message.reply_text(
        message,
        parse_mode="HTML"
    )

    return True


# ------------------------------------------------------------
# PROFILE
# ------------------------------------------------------------

async def show_profile(
    update,
    context
):
    query = update.callback_query

    user = query.from_user
    player = get_player(user)

    text = (
        "👤 <b>پروفایل</b>\n\n"
        f"🆔 ID: <code>{user.id}</code>\n"
        f"👤 نام: {player_display_name(player)}\n"
        f"⭐ Level: <b>{player.get('level', 1)}</b>\n"
        f"✨ XP: <b>{player.get('xp', 0):,}</b>\n"
        f"🏆 اعتبار: <b>{player.get('reputation', 0)}</b>\n"
        f"💳 امتیاز اعتباری: <b>{player.get('credit_score', 0)}</b>\n"
        f"💰 نقد: <b>{player.get('cash', 0):,}</b>\n"
        f"🏦 بانک: <b>{player.get('bank_balance', 0):,}</b>\n"
        f"🚗 خودروها: <b>{len(player.get('vehicles', []))}</b>"
    )

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "🔙 منوی اصلی",
                    callback_data=f"main|{user.id}"
                )
            ]
        ]),
        parse_mode="HTML"
    )


# ------------------------------------------------------------
# MAIN CALLBACK ROUTER
# ------------------------------------------------------------

async def main_callback_router(
    update,
    context
):
    query = update.callback_query

    if not query:
        return

    data = query.data or ""
    parts = data.split("|")

    action = parts[0]

    try:
        # ----------------------------------------------------
        # MAIN
        # ----------------------------------------------------

        if action == "main":
            if len(parts) < 2:
                return

            if not callback_is_owner(
                query,
                parts[-1]
            ):
                return

            await answer_callback(query)
            await show_main_menu(
                update,
                context
            )
            return

        # ----------------------------------------------------
        # HELP
        # ----------------------------------------------------

        if action == "help":
            if len(parts) < 3:
                return

            await help_callback(
                update,
                context,
                parts[1]
            )
            return

        if action == "helpnoop":
            await answer_callback(
                query
            )
            return

        # ----------------------------------------------------
        # WALLET
        # ----------------------------------------------------

        if action == "wallet":
            if not callback_is_owner(
                query,
                parts[-1]
            ):
                return

            await answer_callback(query)
            await show_wallet(
                update,
                context
            )
            return

        if action == "transactions":
            if not callback_is_owner(
                query,
                parts[-1]
            ):
                return

            await answer_callback(query)
            await show_transactions(
                update,
                context
            )
            return

        if action == "deposit":
            if not callback_is_owner(
                query,
                parts[-1]
            ):
                return

            await answer_callback(query)
            await ask_money_amount(
                update,
                context,
                "deposit"
            )
            return

        if action == "withdraw":
            if not callback_is_owner(
                query,
                parts[-1]
            ):
                return

            await answer_callback(query)
            await ask_money_amount(
                update,
                context,
                "withdraw"
            )
            return

        if action == "transfer":
            if not callback_is_owner(
                query,
                parts[-1]
            ):
                return

            await answer_callback(query)

            set_money_state(
                context,
                "transfer",
                query.from_user.id
            )

            context.user_data.pop(
                "transfer_data",
                None
            )

            await query.edit_message_text(
                (
                    "💸 <b>انتقال پول</b>\n\n"
                    "ابتدا آیدی عددی گیرنده را ارسال کن.\n\n"
                    "مثال:\n"
                    "<code>123456789</code>\n\n"
                    "برای لغو: <code>لغو</code>"
                ),
                parse_mode="HTML"
            )
            return

        # ----------------------------------------------------
        # PROFILE
        # ----------------------------------------------------

        if action == "profile":
            if not callback_is_owner(
                query,
                parts[-1]
            ):
                return

            await answer_callback(query)
            await show_profile(
                update,
                context
            )
            return

        # ----------------------------------------------------
        # JOBS
        # ----------------------------------------------------

        if action in (
            "jobs",
            "job",
            "jobunlock",
            "jobtraining",
            "jobtrainingdo",
            "work",
            "workdo",
            "jobstats",
            "jobstatsone",
        ):
            await handle_job_callback(
                update,
                context
            )
            return

        # ----------------------------------------------------
        # VEHICLES
        # ----------------------------------------------------

        if action in (
            "garage",
            "garagecar",
            "vehiclesell",
            "vehiclesellconfirm",
            "vehiclegift",
            "marketlist",
            "mymarket",
            "marketmy",
            "marketremove",
            "showroom",
            "showcar",
        ):
            await handle_vehicle_garage_callback(
                update,
                context
            )
            return

        # ----------------------------------------------------
        # COMBAT
        # ----------------------------------------------------

        if action in (
            "combat",
            "attacktype",
            "attackpart",
            "fightcancel",
            "clinic",
            "injuries",
            "treatall",
            "equipment",
        ):
            # سیستم Combat در بخش قبلی
            if "handle_combat_callback" in globals():
                await handle_combat_callback(
                    update,
                    context
                )
            return

        # ----------------------------------------------------
        # DEALS / AUCTIONS
        # ----------------------------------------------------

        if action in (
            "deals",
            "deal",
            "dealaccept",
            "dealreject",
            "dealcancel",
            "auctions",
            "auction",
            "bidquick",
            "auctioncancel",
        ):
            if "handle_direct_deal_callback" in globals():
                await handle_direct_deal_callback(
                    update,
                    context
                )

            return

        # ----------------------------------------------------
        # UNKNOWN
        # ----------------------------------------------------

        await answer_callback(
            query,
            "⚠️ این گزینه هنوز فعال نشده.",
            True
        )

    except Exception as e:
        print(
            "Main callback error:",
            repr(e)
        )

        try:
            await answer_callback(
                query,
                "❌ خطایی رخ داد.",
                True
            )
        except Exception:
            pass


# ------------------------------------------------------------
# TEXT COMMAND ALIASES
# ------------------------------------------------------------

MENU_WORDS = {
    "منو",
    "menu",
    "منوی اصلی",
    "main",
}

HELP_WORDS = {
    "راهنما",
    "help",
    "/help",
}

JOB_WORDS = {
    "کار",
    "شغل",
    "jobs",
}

VEHICLE_WORDS = {
    "ماشین",
    "خودرو",
    "ماشین ها",
    "خودروها",
    "vehicle",
    "vehicles",
}

WALLET_WORDS = {
    "کیف پول",
    "پول",
    "wallet",
}

COMBAT_WORDS = {
    "مبارزه",
    "fight",
    "combat",
}

CLINIC_WORDS = {
    "کلینیک",
    "clinic",
    "درمان",
}

EQUIPMENT_WORDS = {
    "تجهیزات",
    "equipment",
}


# ------------------------------------------------------------
# REPLY "ریپ"
# ------------------------------------------------------------

async def handle_reply_fight_text(
    update,
    context
):
    message = update.message

    if not message:
        return False

    text = normalize_digits(
        message.text.strip()
    )

    if text.lower() not in (
        "ریپ",
        "rip"
    ):
        return False

    if not message.reply_to_message:
        await message.reply_text(
            "❌ برای مبارزه باید روی پیام بازیکن موردنظر Reply کنی و «ریپ» بفرستی."
        )
        return True

    if "start_fight_from_reply" not in globals():
        await message.reply_text(
            "⚠️ سیستم مبارزه هنوز متصل نشده."
        )
        return True

    await start_fight_from_reply(
        update,
        context
    )

    return True


# ------------------------------------------------------------
# TEXT ROUTER
# ------------------------------------------------------------

async def text_router(
    update,
    context
):
    if not update.message:
        return

    if not update.message.text:
        return

    # اول عملیات‌های چندمرحله‌ای
    if await process_money_message(
        update,
        context
    ):
        return

    if await process_vehicle_gift_message(
        update,
        context
    ):
        return

    if await process_market_listing_message(
        update,
        context
    ):
        return

    # ریپ برای مبارزه
    if await handle_reply_fight_text(
        update,
        context
    ):
        return

    text = update.message.text.strip()

    normalized = normalize_digits(
        text
    ).lower()

    # منو
    if normalized in MENU_WORDS:
        await menu_command(
            update,
            context
        )
        return

    # راهنما
    if normalized in HELP_WORDS:
        await help_command(
            update,
            context
        )
        return

    # مشاغل
    if normalized in JOB_WORDS:
        await jobs_command(
            update,
            context
        )
        return

    # خودرو
    if normalized in VEHICLE_WORDS:
        await vehicle_command_menu(
            update,
            context
        )
        return

    # کیف پول
    if normalized in WALLET_WORDS:
        user = update.effective_user
        player = get_player(user)

        await update.message.reply_text(
            (
                "💰 <b>کیف پول</b>\n\n"
                f"💵 نقد: <b>{player.get('cash', 0):,}</b>\n"
                f"🏦 بانک: <b>{player.get('bank_balance', 0):,}</b>"
            ),
            reply_markup=wallet_keyboard(
                user.id
            ),
            parse_mode="HTML"
        )
        return

    # مبارزه
    if normalized in COMBAT_WORDS:
        if "combat_menu" in globals():
            await combat_menu(
                update,
                context
            )
        else:
            await update.message.reply_text(
                "🥊 سیستم مبارزه در حال آماده‌سازی است."
            )
        return

    # کلینیک
    if normalized in CLINIC_WORDS:
        if "show_clinic" in globals():
            # show_clinic در سیستم قبلی برای callback نوشته شده.
            try:
                await show_clinic(
                    update,
                    context
                )
            except Exception:
                await update.message.reply_text(
                    "🏥 کلینیک در حال آماده‌سازی است."
                )
        return

    # تجهیزات
    if normalized in EQUIPMENT_WORDS:
        if "show_equipment" in globals():
            try:
                await show_equipment(
                    update,
                    context
                )
            except Exception:
                await update.message.reply_text(
                    "🎒 تجهیزات در حال آماده‌سازی است."
                )
        return

    # --------------------------------------------------------
    # MASTER COMMANDS
    # --------------------------------------------------------

    if normalized.startswith("/"):
        await handle_master_text_command(
            update,
            context
        )
        return

    # پیام عادی
    await update.message.reply_text(
        (
            "🏙 UNDERCITY\n\n"
            "دستور موردنظر پیدا نشد.\n\n"
            "برای دیدن امکانات:\n"
            "👉 <code>منو</code>\n\n"
            "برای آموزش:\n"
            "👉 <code>/help</code>"
        ),
        parse_mode="HTML"
    )


# ------------------------------------------------------------
# MASTER COMMAND HANDLER
# ------------------------------------------------------------

async def handle_master_text_command(
    update,
    context
):
    user = update.effective_user
    text = normalize_digits(
        update.message.text.strip()
    )

    # دستورات غیر Master
    if text.startswith("/start"):
        return

    if text.startswith("/help"):
        return

    if not is_master(user.id):
        await update.message.reply_text(
            "❌ این دستور فقط برای Master است."
        )
        return

    # /panel
    if text.startswith("/panel"):
        if "show_master_panel" in globals():
            await show_master_panel(
                update,
                context
            )
        else:
            await update.message.reply_text(
                "👑 Master Panel هنوز متصل نشده."
            )
        return

    # /ban
    if text.startswith("/ban"):
        if "master_ban_command" in globals():
            await master_ban_command(
                update,
                context
            )
        return

    # /unban
    if text.startswith("/unban"):
        if "master_unban_command" in globals():
            await master_unban_command(
                update,
                context
            )
        return

    # /fine
    if text.startswith("/fine"):
        if "master_fine_command" in globals():
            await master_fine_command(
                update,
                context
            )
        return

    # /setcash
    if text.startswith("/setcash"):
        if "master_setcash_command" in globals():
            await master_setcash_command(
                update,
                context
            )
        return

    # /setbank
    if text.startswith("/setbank"):
        if "master_setbank_command" in globals():
            await master_setbank_command(
                update,
                context
            )
        return

    # /player
    if text.startswith("/player"):
        if "master_player_command" in globals():
            await master_player_command(
                update,
                context
            )
        return

    await update.message.reply_text(
        (
            "👑 <b>Master</b>\n\n"
            "دستور ناشناخته است."
        ),
        parse_mode="HTML"
    )


# ------------------------------------------------------------
# /PANEL — ONLY MASTER
# ------------------------------------------------------------

async def panel_command(
    update,
    context
):
    user = update.effective_user

    if not is_master(user.id):
        await update.message.reply_text(
            (
                "❌ <b>پنل مدیریت</b>\n\n"
                "این دستور فقط برای Master است."
            ),
            parse_mode="HTML"
        )
        return

    if "show_master_panel" in globals():
        await show_master_panel(
            update,
            context
        )
        return

    await update.message.reply_text(
        "👑 پنل Master هنوز متصل نشده."
    )


# ------------------------------------------------------------
# CALLBACK ALIASES
# ------------------------------------------------------------

async def vehicles_callback(
    update,
    context
):
    query = update.callback_query

    if not query:
        return

    user = query.from_user

    await query.answer()

    await query.edit_message_text(
        (
            "🚗 <b>خودرو</b>\n\n"
            "از گزینه‌های زیر استفاده کن:"
        ),
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "🏠 گاراژ",
                    callback_data=f"garage|{user.id}"
                ),
                InlineKeyboardButton(
                    "🏪 نمایشگاه",
                    callback_data=f"showroom|{user.id}"
                )
            ],
            [
                InlineKeyboardButton(
                    "🤝 معاملات",
                    callback_data=f"deals|{user.id}"
                ),
                InlineKeyboardButton(
                    "🔨 حراجی",
                    callback_data=f"auctions|{user.id}"
                )
            ],
            [
                InlineKeyboardButton(
                    "🔙 منوی اصلی",
                    callback_data=f"main|{user.id}"
                )
            ]
        ]),
        parse_mode="HTML"
    )


# ------------------------------------------------------------
# CALLBACK DISPATCHER
# ------------------------------------------------------------

async def universal_callback(
    update,
    context
):
    """
    این تابع نقطه ورود همه CallbackQueryهاست.
    """

    query = update.callback_query

    if not query:
        return

    data = query.data or ""

    if not data:
        return

    action = data.split("|")[0]

    # کمک
    if action in (
        "help",
        "helpnoop"
    ):
        if action == "help":
            parts = data.split("|")

            if len(parts) >= 3:
                await help_callback(
                    update,
                    context,
                    parts[1]
                )

        else:
            await answer_callback(
                query
            )

        return

    # سیستم خودرو
    if action in (
        "vehicles",
        "garage",
        "garagecar",
        "vehiclesell",
        "vehiclesellconfirm",
        "vehiclegift",
        "marketlist",
        "mymarket",
        "marketmy",
        "marketremove",
        "showroom",
        "showcar",
        "buyvehicle",
    ):
        if action == "vehicles":
            await vehicles_callback(
                update,
                context
            )
        elif action == "buyvehicle":
            parts = data.split("|")

            if len(parts) >= 3:
                await showroom_buy_callback(
                    update,
                    context,
                    parts[1]
                )
        else:
            await handle_vehicle_garage_callback(
                update,
                context
            )

        return

    # شغل
    if action in (
        "jobs",
        "job",
        "jobunlock",
        "jobtraining",
        "jobtrainingdo",
        "work",
        "workdo",
        "jobstats",
        "jobstatsone",
    ):
        await handle_job_callback(
            update,
            context
        )
        return

    # معامله / حراجی
    if action in (
        "deals",
        "deal",
        "dealaccept",
        "dealreject",
        "dealcancel",
        "auctions",
        "auction",
        "bidquick",
        "auctioncancel",
    ):
        if "handle_direct_deal_callback" in globals():
            await handle_direct_deal_callback(
                update,
                context
            )
        return

    # مبارزه
    if action in (
        "combat",
        "attacktype",
        "attackpart",
        "fightcancel",
        "clinic",
        "injuries",
        "treatall",
        "equipment",
    ):
        if "handle_combat_callback" in globals():
            await handle_combat_callback(
                update,
                context
            )
        return

    # بقیه
    await main_callback_router(
        update,
        context
            )# ============================================================
# PART 11 — FINAL INTEGRATION / HANDLERS / SAFETY FIXES
# ============================================================

# ------------------------------------------------------------
# 1. GLOBAL RUNTIME LOCK
# ------------------------------------------------------------

try:
    DATA_LOCK
except NameError:
    DATA_LOCK = threading.RLock()


# ------------------------------------------------------------
# 2. SAFE SAVE
# ------------------------------------------------------------

def safe_save_players(players):
    """
    ذخیره امن players.json
    """
    with DATA_LOCK:
        save_players(players)


# ------------------------------------------------------------
# 3. NORMALIZE OLD PLAYERS
# ------------------------------------------------------------

def migrate_player_data(player):
    """
    اطلاعات قدیمی بازیکن را با ساختار جدید هماهنگ می‌کند.
    """

    if not isinstance(player, dict):
        player = {}

    defaults = {
        "name": "Unknown",
        "username": "",
        "level": 1,
        "xp": 0,
        "cash": 0,
        "bank_balance": 0,
        "credit_score": 100,
        "reputation": 0,
        "banned": False,
        "ban_reason": "",
        "loan": 0,
        "transactions": [],
        "location": "Undercity",
        "home": None,
        "properties": [],
        "vehicles": [],
        "businesses": [],
        "body": {},
        "equipment": {},
        "jobs": {},
        "vehicle_offers": [],
        "market_listings": [],
        "auctions": [],
        "direct_deals": [],
        "transfers": [],
        "stats": {},
    }

    for key, value in defaults.items():
        if key not in player:
            if isinstance(value, list):
                player[key] = []
            elif isinstance(value, dict):
                player[key] = {}
            else:
                player[key] = value

    if not isinstance(player["transactions"], list):
        player["transactions"] = []

    if not isinstance(player["vehicles"], list):
        player["vehicles"] = []

    if not isinstance(player["body"], dict):
        player["body"] = {}

    if not isinstance(player["equipment"], dict):
        player["equipment"] = {}

    if not isinstance(player["jobs"], dict):
        player["jobs"] = {}

    if not isinstance(player["stats"], dict):
        player["stats"] = {}

    # XP / level
    try:
        player["level"] = max(1, int(player.get("level", 1)))
    except Exception:
        player["level"] = 1

    try:
        player["xp"] = max(0, int(player.get("xp", 0)))
    except Exception:
        player["xp"] = 0

    # Money
    for money_key in ("cash", "bank_balance", "loan"):
        try:
            player[money_key] = max(0, int(player.get(money_key, 0)))
        except Exception:
            player[money_key] = 0

    # Body
    try:
        ensure_body_parts(player)
    except Exception:
        pass

    return player


def migrate_all_players():
    """
    یک بار ساختار تمام بازیکنان موجود را اصلاح می‌کند.
    """

    players = load_players()

    changed = False

    for uid, player in list(players.items()):
        new_player = migrate_player_data(player)

        if new_player != player:
            players[uid] = new_player
            changed = True

    if changed:
        safe_save_players(players)

    return players


# ------------------------------------------------------------
# 4. SAFE PLAYER GET
# ------------------------------------------------------------

def get_player_safe(user_id):
    players = load_players()

    key = str(user_id)

    if key not in players:
        try:
            player = get_player(
                type(
                    "FakeUser",
                    (),
                    {
                        "id": int(user_id),
                        "first_name": "Player",
                        "last_name": "",
                        "username": "",
                    },
                )()
            )
        except Exception:
            player = migrate_player_data({})

        players = load_players()
        player = migrate_player_data(players.get(key, player))
        players[key] = player
        safe_save_players(players)

    else:
        player = migrate_player_data(players[key])
        players[key] = player
        safe_save_players(players)

    return player


# ------------------------------------------------------------
# 5. GENERIC JOB MENU
# ------------------------------------------------------------

def jobs_menu_keyboard(user_id):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "💈 آرایشگری",
                callback_data=f"job|barber|{user_id}"
            ),
            InlineKeyboardButton(
                "🔧 مکانیکی",
                callback_data=f"job|mechanic|{user_id}"
            ),
        ],
        [
            InlineKeyboardButton(
                "📊 مهارت‌های شغلی",
                callback_data=f"job_skills|{user_id}"
            )
        ],
        [
            InlineKeyboardButton(
                "🎓 آموزش و دوره‌ها",
                callback_data=f"job_training|{user_id}"
            )
        ],
        [
            InlineKeyboardButton(
                "🔙 منوی اصلی",
                callback_data=f"main|{user_id}"
            )
        ],
    ])


async def jobs_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if not user:
        return

    player = get_player_safe(user.id)

    if player.get("banned"):
        await update.message.reply_text(
            "🚫 حساب شما مسدود است."
        )
        return

    text = (
        "💼 <b>مرکز مشاغل UNDERCITY</b>\n\n"
        "در این بخش می‌توانی شغل انتخاب کنی، "
        "کار کنی و با افزایش XP رتبه شغلی خودت را بالا ببری.\n\n"
        "💈 آرایشگری\n"
        "🔧 مکانیکی\n\n"
        "هرچه مهارت بیشتر شود، مشتری و درآمد "
        "بهتری دریافت می‌کنی."
    )

    await update.message.reply_text(
        text,
        parse_mode="HTML",
        reply_markup=jobs_menu_keyboard(user.id),
    )


# ------------------------------------------------------------
# 6. VEHICLE COMMAND MENU
# ------------------------------------------------------------

async def vehicle_command_menu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    user = update.effective_user

    if not user:
        return

    player = get_player_safe(user.id)

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🏪 نمایشگاه",
                callback_data=f"vehicles_showroom|{user.id}"
            )
        ],
        [
            InlineKeyboardButton(
                "🚗 گاراژ من",
                callback_data=f"vehicles_garage|{user.id}"
            )
        ],
        [
            InlineKeyboardButton(
                "🤝 خرید و فروش بازیکنان",
                callback_data=f"vehicles_deals|{user.id}"
            )
        ],
        [
            InlineKeyboardButton(
                "🔨 مزایده‌ها",
                callback_data=f"vehicles_auctions|{user.id}"
            )
        ],
        [
            InlineKeyboardButton(
                "🔙 منوی اصلی",
                callback_data=f"main|{user.id}"
            )
        ],
    ])

    await update.message.reply_text(
        "🚘 <b>مرکز خودرو</b>\n\n"
        f"تعداد خودروهای شما: "
        f"{len(player.get('vehicles', []))}\n\n"
        "از گزینه‌های زیر استفاده کن.",
        parse_mode="HTML",
        reply_markup=keyboard,
    )


# ------------------------------------------------------------
# 7. COMBAT CALLBACK DISPATCHER
# ------------------------------------------------------------

async def handle_combat_callback(
    query,
    context: ContextTypes.DEFAULT_TYPE
):
    data = query.data or ""
    parts = data.split("|")

    action = parts[0]

    try:
        if action in (
            "fight_attack",
            "attack",
            "combat_attack",
        ):
            if "handle_attack_callback" in globals():
                return await handle_attack_callback(
                    query,
                    context
                )

        if action in (
            "fight_part",
            "attack_part",
            "combat_part",
        ):
            if "handle_attack_part_callback" in globals():
                return await handle_attack_part_callback(
                    query,
                    context
                )

        if action in (
            "fight_cancel",
            "combat_cancel",
        ):
            if "cancel_fight_callback" in globals():
                return await cancel_fight_callback(
                    query,
                    context
                )

        if action in (
            "clinic",
            "show_clinic",
        ):
            if "show_clinic_callback" in globals():
                return await show_clinic_callback(
                    query,
                    context
                )

            user_id = callback_owner_id(query)

            await query.edit_message_text(
                "🏥 <b>کلینیک</b>\n\n"
                "برای درمان آسیب‌ها از گزینه‌های زیر استفاده کن.",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton(
                            "🩹 درمان همه",
                            callback_data=f"treat_all|{user_id}"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "🔙 بازگشت",
                            callback_data=f"combat|{user_id}"
                        )
                    ],
                ])
            )
            return

        if action in (
            "treat_all",
            "clinic_treat",
        ):
            if "treat_all_callback" in globals():
                return await treat_all_callback(
                    query,
                    context
                )

        if action in (
            "injuries",
            "show_injuries",
        ):
            if "show_injuries" in globals():
                return await show_injuries(
                    query,
                    context
                )

        if action in (
            "combat",
            "combat_menu",
        ):
            if "show_combat_menu" in globals():
                return await show_combat_menu(
                    query,
                    context
                )

            user_id = callback_owner_id(query)

            await query.edit_message_text(
                "⚔️ <b>مرکز مبارزه</b>\n\n"
                "برای حمله به بازیکن دیگر باید روی پیام او "
                "ریپلای کنی و بنویسی «ریپ».",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton(
                            "🏥 کلینیک",
                            callback_data=f"clinic|{user_id}"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "🩸 آسیب‌ها",
                            callback_data=f"injuries|{user_id}"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "🔙 بازگشت",
                            callback_data=f"main|{user_id}"
                        )
                    ],
                ])
            )
            return

    except Exception as e:
        print("Combat callback error:", repr(e))

        try:
            await query.answer(
                "خطایی در بخش مبارزه رخ داد.",
                show_alert=True
            )
        except Exception:
            pass


# ------------------------------------------------------------
# 8. FIX FOR OLD COMBAT CONTEXT BUG
# ------------------------------------------------------------

async def safe_attack_part_callback(
    query,
    context: ContextTypes.DEFAULT_TYPE
):
    """
    نسخه ایمن برای callback انتخاب عضو بدن.
    اگر تابع قدیمی وجود داشته باشد آن را صدا می‌زند.
    """

    try:
        if "handle_attack_part_callback" in globals():
            return await handle_attack_part_callback(
                query,
                context
            )
    except NameError:
        pass
    except TypeError:
        pass
    except Exception as e:
        print(
            "Old attack_part_callback failed:",
            repr(e)
        )

    user_id = callback_owner_id(query)

    try:
        await query.answer(
            "این گزینه دیگر معتبر نیست.",
            show_alert=True
        )
    except Exception:
        pass


# ------------------------------------------------------------
# 9. VEHICLE GARAGE CALLBACK DISPATCHER
# ------------------------------------------------------------

async def handle_vehicle_garage_callback(
    query,
    context: ContextTypes.DEFAULT_TYPE
):
    data = query.data or ""
    parts = data.split("|")

    action = parts[0]

    user_id = callback_owner_id(query)

    player = get_player_safe(user_id)
    vehicles = player.get("vehicles", [])

    if action in (
        "vehicles_garage",
        "garage",
    ):
        if not vehicles:
            text = (
                "🚗 <b>گاراژ شما</b>\n\n"
                "گاراژ خالی است."
            )
        else:
            lines = [
                "🚗 <b>گاراژ شما</b>\n"
            ]

            for index, vehicle in enumerate(
                vehicles,
                start=1
            ):
                name = vehicle.get(
                    "name",
                    vehicle.get(
                        "model",
                        "خودرو"
                    )
                )

                price = vehicle.get(
                    "price",
                    0
                )

                vid = vehicle.get(
                    "id",
                    ""
                )

                lines.append(
                    f"{index}. {name}\n"
                    f"   💰 {price:,}\n"
                    f"   🆔 {vid}\n"
                )

            text = "\n".join(lines)

        buttons = []

        for vehicle in vehicles:
            vid = vehicle.get("id")

            if vid:
                buttons.append([
                    InlineKeyboardButton(
                        f"🚘 {vehicle.get('name', vehicle.get('model', 'خودرو'))}",
                        callback_data=(
                            f"vehicle_view|{vid}|{user_id}"
                        )
                    )
                ])

        buttons.append([
            InlineKeyboardButton(
                "🔙 خودروها",
                callback_data=f"vehicles|{user_id}"
            )
        ])

        await query.edit_message_text(
            text,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        return

    if action == "vehicle_view":
        if len(parts) < 3:
            await query.answer(
                "اطلاعات خودرو ناقص است.",
                show_alert=True
            )
            return

        vehicle_id = parts[1]

        vehicle = None

        for item in vehicles:
            if str(item.get("id")) == str(vehicle_id):
                vehicle = item
                break

        if not vehicle:
            await query.answer(
                "خودرو پیدا نشد.",
                show_alert=True
            )
            return

        try:
            name = vehicle_name(vehicle)
        except Exception:
            name = vehicle.get(
                "name",
                vehicle.get("model", "خودرو")
            )

        price = vehicle.get("price", 0)
        year = vehicle.get("year", "-")
        mileage = vehicle.get("mileage", "-")
        condition = vehicle.get("condition", "-")
        color = vehicle.get("color", "-")
        power = vehicle.get("power", "-")

        text = (
            f"🚘 <b>{name}</b>\n\n"
            f"📅 سال: {year}\n"
            f"🛣 کارکرد: {mileage}\n"
            f"🔧 وضعیت: {condition}\n"
            f"🎨 رنگ: {color}\n"
            f"⚡ قدرت: {power}\n"
            f"💰 ارزش: {price:,}\n\n"
            f"🆔 {vehicle_id}"
        )

        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "💰 فروش",
                    callback_data=(
                        f"vehicle_sell|{vehicle_id}|{user_id}"
                    )
                ),
                InlineKeyboardButton(
                    "🎁 هدیه",
                    callback_data=(
                        f"vehicle_gift|{vehicle_id}|{user_id}"
                    )
                ),
            ],
            [
                InlineKeyboardButton(
                    "🤝 پیشنهاد فروش",
                    callback_data=(
                        f"vehicle_offer|{vehicle_id}|{user_id}"
                    )
                )
            ],
            [
                InlineKeyboardButton(
                    "🔙 گاراژ",
                    callback_data=(
                        f"vehicles_garage|{user_id}"
                    )
                )
            ],
        ])

        await query.edit_message_text(
            text,
            parse_mode="HTML",
            reply_markup=keyboard
        )
        return


# ------------------------------------------------------------
# 10. JOB CALLBACK SYSTEM
# ------------------------------------------------------------

def ensure_job_data(player, job_key):
    jobs = player.setdefault("jobs", {})

    if job_key not in jobs:
        jobs[job_key] = {
            "rank": 0,
            "xp": 0,
            "sessions": 0,
            "income": 0,
            "loss": 0,
            "customers": 0,
        }

    data = jobs[job_key]

    defaults = {
        "rank": 0,
        "xp": 0,
        "sessions": 0,
        "income": 0,
        "loss": 0,
        "customers": 0,
    }

    for key, value in defaults.items():
        if key not in data:
            data[key] = value

    return data


JOB_RANKS = [
    "کارآموز",
    "مبتدی",
    "متوسط",
    "ماهر",
    "حرفه‌ای",
    "استاد",
]


def job_rank_from_xp(xp):
    xp = max(0, int(xp))

    if xp >= 5000:
        return 5

    if xp >= 2500:
        return 4

    if xp >= 1200:
        return 3

    if xp >= 500:
        return 2

    if xp >= 100:
        return 1

    return 0


def job_display_name(job_key):
    if job_key == "barber":
        return "💈 آرایشگری"

    if job_key == "mechanic":
        return "🔧 مکانیکی"

    return "💼 شغل"


def job_session(player, job_key):
    data = ensure_job_data(
        player,
        job_key
    )

    old_rank = int(data.get("rank", 0))

    rank = max(
        old_rank,
        job_rank_from_xp(
            int(data.get("xp", 0))
        )
    )

    data["rank"] = rank

    # تعداد مشتری
    base_customers = random.randint(1, 4)

    if rank >= 2:
        base_customers += random.randint(0, 2)

    if rank >= 4:
        base_customers += random.randint(1, 3)

    customers = max(1, base_customers)

    # درآمد
    if job_key == "barber":
        base_income = 45_000
        difficulty = random.randint(1, 4)
    else:
        base_income = 80_000
        difficulty = random.randint(1, 5)

    income = 0
    loss = 0
    xp_gain = 0

    for _ in range(customers):
        job_income = (
            base_income
            * random.randint(8, 16)
            // 10
        )

        difficulty_bonus = (
            difficulty * 10_000
        )

        job_income += difficulty_bonus

        # احتمال خسارت
        failure_chance = max(
            3,
            18 - (rank * 3)
        )

        if random.randint(1, 100) <= failure_chance:
            mistake = max(
                5_000,
                job_income // 4
            )

            loss += mistake
            xp_gain += max(
                5,
                difficulty * 4
            )
        else:
            income += job_income
            xp_gain += max(
                8,
                difficulty * 10
            )

    net = income - loss

    player["cash"] = max(
        0,
        int(player.get("cash", 0)) + net
    )

    data["sessions"] += 1
    data["customers"] += customers
    data["income"] += income
    data["loss"] += loss
    data["xp"] += xp_gain

    new_rank = max(
        data["rank"],
        job_rank_from_xp(
            data["xp"]
        )
    )

    data["rank"] = new_rank

    try:
        add_xp(
            player,
            xp_gain
        )
    except Exception:
        player["xp"] = (
            int(player.get("xp", 0))
            + xp_gain
        )

    return {
        "customers": customers,
        "income": income,
        "loss": loss,
        "net": net,
        "xp": xp_gain,
        "old_rank": old_rank,
        "new_rank": new_rank,
        "difficulty": difficulty,
    }


async def handle_job_callback(
    query,
    context: ContextTypes.DEFAULT_TYPE
):
    parts = (query.data or "").split("|")
    action = parts[0]

    user_id = callback_owner_id(query)

    player = get_player_safe(user_id)

    if player.get("banned"):
        await query.answer(
            "حساب شما مسدود است.",
            show_alert=True
        )
        return

    if action == "job":
        job_key = (
            parts[1]
            if len(parts) > 1
            else "barber"
        )

        data = ensure_job_data(
            player,
            job_key
        )

        rank = int(
            data.get("rank", 0)
        )

        text = (
            f"{job_display_name(job_key)}\n\n"
            f"🎖 رتبه: "
            f"{JOB_RANKS[min(rank, 5)]}\n"
            f"⭐ XP شغلی: {data.get('xp', 0):,}\n"
            f"👥 مشتری‌ها: {data.get('customers', 0):,}\n"
            f"💰 درآمد کل: {data.get('income', 0):,}\n"
            f"📉 خسارت کل: {data.get('loss', 0):,}\n"
            f"🧰 تعداد جلسات: {data.get('sessions', 0):,}"
        )

        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "▶️ شروع کار",
                    callback_data=(
                        f"job_work|{job_key}|{user_id}"
                    )
                )
            ],
            [
                InlineKeyboardButton(
                    "🎓 آموزش",
                    callback_data=(
                        f"job_training|{user_id}"
                    )
                )
            ],
            [
                InlineKeyboardButton(
                    "🔙 مشاغل",
                    callback_data=(
                        f"jobs|{user_id}"
                    )
                )
            ],
        ])

        await query.edit_message_text(
            text,
            reply_markup=keyboard
        )
        return

    if action == "job_work":
        job_key = (
            parts[1]
            if len(parts) > 1
            else "barber"
        )
        
        result = job_session(
            player,
            job_key
        )

        # ذخیره واقعی بازیکن
        players = load_players()
        players[str(user_id)] = player
        safe_save_players(players)

        rank_text = JOB_RANKS[
            min(
                result["new_rank"],
                5
            )
        ]

        promotion = ""

        if result["new_rank"] > result["old_rank"]:
            promotion = (
                "\n\n🎉 <b>تبریک!</b>\n"
                "رتبه شغلی شما ارتقا پیدا کرد."
            )

        text = (
            f"💼 <b>شیفت کاری تمام شد</b>\n\n"
            f"👥 مشتری: {result['customers']}\n"
            f"💰 درآمد: +{result['income']:,}\n"
            f"📉 خسارت: -{result['loss']:,}\n"
            f"💵 خالص: {result['net']:+,}\n"
            f"⭐ XP شغلی: +{result['xp']}\n"
            f"🎖 رتبه فعلی: {rank_text}"
            f"{promotion}"
        )

        await query.edit_message_text(
            text,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "🔄 یک شیفت دیگر",
                        callback_data=(
                            f"job_work|{job_key}|{user_id}"
                        )
                    )
                ],
                [
                    InlineKeyboardButton(
                        "🔙 شغل",
                        callback_data=(
                            f"job|{job_key}|{user_id}"
                        )
                    )
                ],
            ])
        )
        return

    if action == "job_skills":
        jobs = player.get("jobs", {})

        lines = [
            "📊 <b>مهارت‌های شغلی</b>\n"
        ]

        for job_key in (
            "barber",
            "mechanic",
        ):
            data = ensure_job_data(
                player,
                job_key
            )

            rank = min(
                int(data.get("rank", 0)),
                5
            )

            lines.append(
                f"{job_display_name(job_key)}\n"
                f"🎖 {JOB_RANKS[rank]}\n"
                f"⭐ {data.get('xp', 0):,} XP\n"
            )

        await query.edit_message_text(
            "\n".join(lines),
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "🔙 مشاغل",
                        callback_data=f"jobs|{user_id}"
                    )
                ]
            ])
        )
        return

    if action == "job_training":
        await query.edit_message_text(
            "🎓 <b>آموزش شغلی</b>\n\n"
            "فعلاً آموزش به شکل تمرین عملی انجام می‌شود.\n"
            "با انجام شیفت‌های بیشتر، رتبه و XP شما افزایش پیدا می‌کند.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "🔙 مشاغل",
                        callback_data=f"jobs|{user_id}"
                    )
                ]
            ])
        )
        return

    if action == "jobs":
        await query.edit_message_text(
            "💼 <b>مشاغل</b>\n\n"
            "یک شغل را انتخاب کن.",
            parse_mode="HTML",
            reply_markup=jobs_menu_keyboard(user_id)
        )
        return


# ------------------------------------------------------------
# 11. VEHICLE BUY CALLBACK WRAPPER
# ------------------------------------------------------------

async def showroom_buy_callback(
    query,
    context: ContextTypes.DEFAULT_TYPE
):
    """
    Wrapper برای خرید خودرو از نمایشگاه.
    """

    try:
        if "handle_showroom_buy_callback" in globals():
            return await handle_showroom_buy_callback(
                query,
                context
            )

        if "buy_vehicle_callback" in globals():
            return await buy_vehicle_callback(
                query,
                context
            )

    except Exception as e:
        print(
            "Showroom buy error:",
            repr(e)
        )

    try:
        await query.answer(
            "سیستم خرید خودرو آماده نیست.",
            show_alert=True
        )
    except Exception:
        pass


# ------------------------------------------------------------
# 12. SAFE VEHICLE GIFT MESSAGE
# ------------------------------------------------------------

async def process_vehicle_gift_message(
    update,
    context
):
    state = context.user_data.get(
        "vehicle_gift_state"
    )

    if not state:
        return False

    text = normalize_digits(
        (update.message.text or "").strip()
    )

    if text.lower() in (
        "لغو",
        "cancel",
        "انصراف",
    ):
        context.user_data.pop(
            "vehicle_gift_state",
            None
        )

        await update.message.reply_text(
            "❌ هدیه خودرو لغو شد."
        )

        return True

    if not text.isdigit():
        await update.message.reply_text(
            "❌ شناسه عددی بازیکن مقصد را وارد کن."
        )
        return True

    target_id = int(text)

    sender_id = update.effective_user.id

    if target_id == sender_id:
        await update.message.reply_text(
            "❌ نمی‌توانی خودرو را به خودت هدیه بدهی."
        )
        return True

    vehicle_id = state.get(
        "vehicle_id"
    )

    players = load_players()

    sender = players.get(
        str(sender_id)
    )

    target = players.get(
        str(target_id)
    )

    if not sender or not target:
        await update.message.reply_text(
            "❌ بازیکن پیدا نشد."
        )
        return True

    vehicle = None

    for item in sender.get("vehicles", []):
        if str(item.get("id")) == str(vehicle_id):
            vehicle = item
            break

    if not vehicle:
        await update.message.reply_text(
            "❌ این خودرو دیگر در گاراژ شما نیست."
        )
        context.user_data.pop(
            "vehicle_gift_state",
            None
        )
        return True

    sender["vehicles"] = [
        item
        for item in sender.get("vehicles", [])
        if str(item.get("id")) != str(vehicle_id)
    ]

    target.setdefault(
        "vehicles",
        []
    ).append(vehicle)

    add_transaction(
        sender,
        "vehicle_gift",
        0,
        f"هدیه خودرو {vehicle_id} به {target_id}"
    )

    add_transaction(
        target,
        "vehicle_received",
        0,
        f"دریافت خودرو {vehicle_id} از {sender_id}"
    )

    players[str(sender_id)] = sender
    players[str(target_id)] = target

    safe_save_players(players)

    context.user_data.pop(
        "vehicle_gift_state",
        None
    )

    await update.message.reply_text(
        "🎁 خودرو با موفقیت منتقل شد."
    )

    try:
        await context.bot.send_message(
            chat_id=target_id,
            text=(
                "🎁 یک خودرو به شما هدیه داده شد.\n"
                f"🆔 {vehicle_id}"
            )
        )
    except Exception:
        pass

    return True


# ------------------------------------------------------------
# 13. SAFE MARKET MESSAGE
# ------------------------------------------------------------

async def process_market_listing_message(
    update,
    context
):
    state = context.user_data.get(
        "market_listing_state"
    )

    if not state:
        return False

    text = normalize_digits(
        (update.message.text or "").strip()
    )

    if text.lower() in (
        "لغو",
        "cancel",
        "انصراف",
    ):
        context.user_data.pop(
            "market_listing_state",
            None
        )

        await update.message.reply_text(
            "❌ آگهی لغو شد."
        )

        return True

    if not text.isdigit():
        await update.message.reply_text(
            "❌ مبلغ را فقط به صورت عدد وارد کن."
        )
        return True

    price = int(text)

    if price <= 0:
        await update.message.reply_text(
            "❌ مبلغ باید بیشتر از صفر باشد."
        )
        return True

    user_id = update.effective_user.id
    vehicle_id = state.get("vehicle_id")

    players = load_players()
    player = players.get(str(user_id))

    if not player:
        return True

    vehicle = None

    for item in player.get("vehicles", []):
        if str(item.get("id")) == str(vehicle_id):
            vehicle = item
            break

    if not vehicle:
        context.user_data.pop(
            "market_listing_state",
            None
        )

        await update.message.reply_text(
            "❌ خودرو در گاراژ شما پیدا نشد."
        )

        return True

    ensure_vehicle_system(player)

    listing_id = make_id(
        "listing"
    )

    listing = {
        "id": listing_id,
        "seller_id": user_id,
        "vehicle_id": vehicle_id,
        "price": price,
        "status": "active",
        "created_at": timestamp(),
    }

    player.setdefault(
        "market_listings",
        []
    ).append(listing)

    players[str(user_id)] = player

    safe_save_players(players)

    context.user_data.pop(
        "market_listing_state",
        None
    )

    await update.message.reply_text(
        "🏷 آگهی با موفقیت ثبت شد.\n\n"
        f"🚘 خودرو: "
        f"{vehicle.get('name', vehicle.get('model', 'خودرو'))}\n"
        f"💰 قیمت: {price:,}\n"
        f"🆔 آگهی: {listing_id}"
    )

    return True


# ------------------------------------------------------------
# 14. MASTER PANEL FALLBACK
# ------------------------------------------------------------

async def show_master_panel(
    target,
    context=None
):
    """
    پنل اصلی Master.
    target می‌تواند Update یا CallbackQuery باشد.
    """

    if hasattr(target, "effective_user"):
        user = target.effective_user
    else:
        user = target.from_user

    if not user or not is_master(user.id):
        if hasattr(target, "answer"):
            try:
                await target.answer(
                    "دسترسی ندارید.",
                    show_alert=True
                )
            except Exception:
                pass
        return

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "👥 بازیکنان",
                callback_data=f"master_players|{user.id}"
            )
        ],
        [
            InlineKeyboardButton(
                "💰 اقتصاد",
                callback_data=f"master_economy|{user.id}"
            )
        ],
        [
            InlineKeyboardButton(
                "🚫 مدیریت بن",
                callback_data=f"master_ban|{user.id}"
            )
        ],
        [
            InlineKeyboardButton(
                "📊 آمار",
                callback_data=f"master_stats|{user.id}"
            )
        ],
        [
            InlineKeyboardButton(
                "🔙 منوی اصلی",
                callback_data=f"main|{user.id}"
            )
        ],
    ])

    text = (
        "👑 <b>MASTER PANEL</b>\n\n"
        "دسترسی مدیریتی فعال است."
    )

    if hasattr(target, "message") and target.message:
        await target.message.reply_text(
            text,
            parse_mode="HTML",
            reply_markup=keyboard
        )
    else:
        await target.edit_message_text(
            text,
            parse_mode="HTML",
            reply_markup=keyboard
        )


# ------------------------------------------------------------
# 15. MASTER CALLBACK
# ------------------------------------------------------------

async def handle_master_callback(
    query,
    context
):
    if not is_master(query.from_user.id):
        await query.answer(
            "دسترسی ندارید.",
            show_alert=True
        )
        return

    parts = (query.data or "").split("|")
    action = parts[0]
    master_id = query.from_user.id

    players = load_players()

    if action == "master_players":

        total = len(players)

        active = sum(
            1
            for p in players.values()
            if not p.get("banned")
        )

        banned = sum(
            1
            for p in players.values()
            if p.get("banned")
        )

        text = (
            "👥 <b>بازیکنان</b>\n\n"
            f"👤 کل: {total}\n"
            f"🟢 فعال: {active}\n"
            f"🔴 بن: {banned}"
        )

    elif action == "master_economy":

        cash_total = sum(
            int(p.get("cash", 0))
            for p in players.values()
        )

        bank_total = sum(
            int(p.get("bank_balance", 0))
            for p in players.values()
        )

        text = (
            "💰 <b>اقتصاد</b>\n\n"
            f"💵 نقدینگی: {cash_total:,}\n"
            f"🏦 بانک: {bank_total:,}"
        )

    elif action == "master_stats":

        total_vehicles = sum(
            len(p.get("vehicles", []))
            for p in players.values()
        )

        total_transactions = sum(
            len(p.get("transactions", []))
            for p in players.values()
        )

        text = (
            "📊 <b>آمار سرور</b>\n\n"
            f"👥 بازیکنان: {len(players)}\n"
            f"🚗 خودروها: {total_vehicles}\n"
            f"💳 تراکنش‌ها: {total_transactions}"
        )

    elif action == "master_ban":

        text = (
            "🚫 <b>مدیریت بن</b>\n\n"
            "برای مدیریت بازیکن از دستورات Master "
            "استفاده کن."
        )

    else:
        text = (
            "👑 <b>MASTER PANEL</b>\n\n"
            "گزینه نامعتبر است."
        )

    await query.edit_message_text(
        text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "🔙 پنل Master",
                    callback_data=f"master_panel|{master_id}"
                )
            ]
        ])
    )


# ------------------------------------------------------------
# 16. FINAL CALLBACK ROUTER
# ------------------------------------------------------------

async def final_callback_router(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query

    if not query:
        return

    data = query.data or ""

    try:
        await query.answer()
    except Exception:
        pass

    action = data.split("|")[0]

    # Master
    if action.startswith("master_"):
        return await handle_master_callback(
            query,
            context
        )

    if action == "master_panel":
        return await show_master_panel(
            query,
            context
        )

    # Combat
    combat_actions = {
        "combat",
        "combat_menu",
        "fight_attack",
        "attack",
        "combat_attack",
        "fight_part",
        "attack_part",
        "combat_part",
        "fight_cancel",
        "combat_cancel",
        "clinic",
        "show_clinic",
        "treat_all",
        "clinic_treat",
        "injuries",
        "show_injuries",
    }

    if action in combat_actions:
        return await handle_combat_callback(
            query,
            context
        )

    # Jobs
    job_actions = {
        "job",
        "job_work",
        "job_skills",
        "job_training",
        "jobs",
    }

    if action in job_actions:
        return await handle_job_callback(
            query,
            context
        )

    # Vehicles
    vehicle_actions = {
        "vehicles_garage",
        "garage",
        "vehicle_view",
        "vehicle_sell",
        "vehicle_gift",
        "vehicle_offer",
    }

    if action in vehicle_actions:
        return await handle_vehicle_garage_callback(
            query,
            context
        )

    # showroom
    if action in (
        "showroom_buy",
        "vehicle_buy",
        "buy_vehicle",
    ):
        return await showroom_buy_callback(
            query,
            context
        )

    # مستقیم معاملات
    direct_actions = {
        "deal_accept",
        "deal_reject",
        "deal_cancel",
        "direct_deal",
        "negotiation",
        "auction",
        "auction_bid",
        "auction_cancel",
    }

    if action in direct_actions:
        if "handle_direct_deal_callback" in globals():
            return await handle_direct_deal_callback(
                query,
                context
            )

    # Help
    if action == "help":
        if "help_callback" in globals():
            return await help_callback(
                query,
                context
            )

    # Main
    if action == "main":
        return await show_main_menu(
            query,
            query.from_user.id
        )

    # Wallet
    if action in (
        "wallet",
        "wallet_transactions",
        "wallet_transfer",
        "wallet_deposit",
        "wallet_withdraw",
    ):
        if "main_callback_router" in globals():
            return await main_callback_router(
                query,
                context
            )

    # fallback
    try:
        if "universal_callback" in globals():
            return await universal_callback(
                update,
                context
            )
    except Exception as e:
        print(
            "Universal callback fallback error:",
            repr(e)
        )

    try:
        await query.answer(
            "گزینه پیدا نشد.",
            show_alert=True
        )
    except Exception:
        pass


# ------------------------------------------------------------
# 17. FINAL TEXT ROUTER WRAPPER
# ------------------------------------------------------------

async def final_text_router(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    """
    تمام پیام‌های متنی از اینجا عبور می‌کنند.
    """

    if not update.message:
        return

    user = update.effective_user

    if not user:
        return

    player = get_player_safe(user.id)

    if player.get("banned"):
        await update.message.reply_text(
            "🚫 حساب شما مسدود است."
        )
        return

    text = normalize_digits(
        (update.message.text or "").strip()
    )

    # اول stateهای چندمرحله‌ای
    if await process_vehicle_gift_message(
        update,
        context
    ):
        return

    if await process_market_listing_message(
        update,
        context
    ):
        return

    # stateهای مالی
    try:
        if await process_money_message(
            update,
            context
        ):
            return
    except Exception as e:
        print(
            "Money message error:",
            repr(e)
        )

    # ریپ / مبارزه
    if text.lower() in (
        "ریپ",
        "rep",
    ):
        if update.message.reply_to_message:
            if "start_fight_from_reply" in globals():
                return await start_fight_from_reply(
                    update,
                    context
                )

        await update.message.reply_text(
            "⚔️ برای مبارزه باید روی پیام بازیکن "
            "موردنظر ریپلای کنی و «ریپ» بفرستی."
        )
        return

    # منو
    if text.lower() in (
        "منو",
        "menu",
    ):
        return await menu_command(
            update,
            context
        )

    # پنل
    if text.lower() in (
        "پنل",
        "panel",
    ):
        if is_master(user.id):
            return await panel_command(
                update,
                context
            )

        await update.message.reply_text(
            "❌ پنل مدیریتی فقط برای Master است."
        )
        return

    # مشاغل
    if text.lower() in (
        "کار",
        "شغل",
        "jobs",
    ):
        return await jobs_command(
            update,
            context
        )

    # خودرو
    if text.lower() in (
        "خودرو",
        "ماشین",
        "cars",
        "car",
    ):
        return await vehicle_command_menu(
            update,
            context
        )

    # اگر router اصلی موجود است
    if "text_router" in globals():
        try:
            return await text_router(
                update,
                context
            )
        except Exception as e:
            print(
                "Old text router error:",
                repr(e)
            )

    await update.message.reply_text(
        "دستور شناخته نشد.\n"
        "برای دیدن راهنما /help را بزن."
    )


# ------------------------------------------------------------
# 18. ERROR HANDLER
# ------------------------------------------------------------

async def global_error_handler(
    update,
    context
):
    print(
        "UNDERCITY ERROR:",
        repr(context.error)
    )

    try:
        if update and update.effective_chat:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=(
                    "⚠️ یک خطای موقت رخ داد.\n"
                    "لطفاً دوباره تلاش کن."
                )
            )
    except Exception:
        pass


# ------------------------------------------------------------
# 19. STARTUP
# ------------------------------------------------------------

def startup_database():
    try:
        migrate_all_players()
    except Exception as e:
        print(
            "Database migration error:",
            repr(e)
        )


# ------------------------------------------------------------
# 20. APPLICATION BUILDER
# ------------------------------------------------------------

def build_application():
    token = os.environ.get(
        "BOT_TOKEN",
        ""
    )

    if not token:
        raise RuntimeError(
            "BOT_TOKEN environment variable is missing."
        )

    application = (
        Application
        .builder()
        .token(token)
        .build()
    )

    # --------------------------------------------------------
    # Commands
    # --------------------------------------------------------

    application.add_handler(
        CommandHandler(
            "start",
            start_command
        )
    )

    application.add_handler(
        CommandHandler(
            "help",
            help_command
        )
    )

    application.add_handler(
        CommandHandler(
            "menu",
            menu_command
        )
    )

    application.add_handler(
        CommandHandler(
            "panel",
            panel_command
        )
    )

    application.add_handler(
        CommandHandler(
            "jobs",
            jobs_command
        )
    )

    application.add_handler(
        CommandHandler(
            "cars",
            vehicle_command_menu
        )
    )

    # --------------------------------------------------------
    # CALLBACK
    # --------------------------------------------------------

    application.add_handler(
        CallbackQueryHandler(
            final_callback_router
        )
    )

    # --------------------------------------------------------
    # TEXT
    # --------------------------------------------------------

    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            final_text_router
        )
    )

    # --------------------------------------------------------
    # ERRORS
    # --------------------------------------------------------

    application.add_error_handler(
        global_error_handler
    )

    return application


# ------------------------------------------------------------
# 21. HEALTH SERVER START
# ------------------------------------------------------------

def start_health_server():
    try:
        thread = threading.Thread(
            target=run_server,
            daemon=True
        )

        thread.start()

        print(
            f"Health server started on port {PORT}"
        )

    except Exception as e:
        print(
            "Health server failed:",
            repr(e)
        )


# ------------------------------------------------------------
# 22. MAIN
# ------------------------------------------------------------

def main():
    print("=" * 60)
    print("UNDERCITY BOT")
    print("Starting...")
    print("=" * 60)

    startup_database()

    start_health_server()

    application = build_application()

    print(
        "Bot application created successfully."
    )

    print(
        "Starting polling..."
    )

    application.run_polling(
        allowed_updates=Update.ALL_TYPES
    )


# ------------------------------------------------------------
# 23. RUN
# ------------------------------------------------------------

if __name__ == "__main__":
    main()# ============================================================
# PART 12 — VEHICLE TRANSACTION SAFETY / IDEMPOTENCY
# ============================================================

# ------------------------------------------------------------
# 1. VEHICLE SYSTEM STORAGE
# ------------------------------------------------------------

def ensure_vehicle_system(player):
    if not isinstance(player, dict):
        return player

    defaults = {
        "vehicles": [],
        "vehicle_offers": [],
        "market_listings": [],
        "auctions": [],
        "direct_deals": [],
        "vehicle_history": [],
    }

    for key, value in defaults.items():
        if key not in player:
            player[key] = list(value)

    if not isinstance(player["vehicles"], list):
        player["vehicles"] = []

    if not isinstance(player["vehicle_offers"], list):
        player["vehicle_offers"] = []

    if not isinstance(player["market_listings"], list):
        player["market_listings"] = []

    if not isinstance(player["auctions"], list):
        player["auctions"] = []

    if not isinstance(player["direct_deals"], list):
        player["direct_deals"] = []

    if not isinstance(player["vehicle_history"], list):
        player["vehicle_history"] = []

    return player


# ------------------------------------------------------------
# 2. VEHICLE OPERATION LOCK
# ------------------------------------------------------------

try:
    VEHICLE_OPERATION_LOCK
except NameError:
    VEHICLE_OPERATION_LOCK = threading.RLock()


# ------------------------------------------------------------
# 3. VEHICLE OPERATION IDS
# ------------------------------------------------------------

def vehicle_operation_id(
    operation_type,
    vehicle_id,
    actor_id,
    target_id=None
):
    raw = (
        f"{operation_type}:"
        f"{vehicle_id}:"
        f"{actor_id}:"
        f"{target_id or ''}"
    )

    import hashlib

    return hashlib.sha256(
        raw.encode("utf-8")
    ).hexdigest()[:32]


def vehicle_operation_exists(
    player,
    operation_id
):
    history = player.get(
        "vehicle_history",
        []
    )

    for item in history:
        if item.get("operation_id") == operation_id:
            return True

    return False


def add_vehicle_operation(
    player,
    operation_id,
    operation_type,
    vehicle_id,
    description=""
):
    ensure_vehicle_system(player)

    player["vehicle_history"].append({
        "operation_id": operation_id,
        "type": operation_type,
        "vehicle_id": vehicle_id,
        "description": description,
        "timestamp": timestamp(),
    })

    player["vehicle_history"] = (
        player["vehicle_history"][-200:]
    )


# ------------------------------------------------------------
# 4. VEHICLE LOOKUP
# ------------------------------------------------------------

def get_player_vehicle(
    player,
    vehicle_id
):
    ensure_vehicle_system(player)

    for vehicle in player["vehicles"]:
        if str(vehicle.get("id")) == str(vehicle_id):
            return vehicle

    return None


def player_owns_vehicle(
    player,
    vehicle_id
):
    return (
        get_player_vehicle(
            player,
            vehicle_id
        )
        is not None
    )


def remove_vehicle_from_player(
    player,
    vehicle_id
):
    ensure_vehicle_system(player)

    old_count = len(
        player["vehicles"]
    )

    player["vehicles"] = [
        vehicle
        for vehicle in player["vehicles"]
        if str(vehicle.get("id")) != str(vehicle_id)
    ]

    return len(
        player["vehicles"]
    ) < old_count


def add_vehicle_to_player(
    player,
    vehicle
):
    ensure_vehicle_system(player)

    vehicle_id = vehicle.get("id")

    if vehicle_id and player_owns_vehicle(
        player,
        vehicle_id
    ):
        return False

    player["vehicles"].append(
        vehicle
    )

    return True


# ------------------------------------------------------------
# 5. MONEY HELPERS
# ------------------------------------------------------------

def can_afford(
    player,
    amount
):
    try:
        return int(
            player.get("cash", 0)
        ) >= int(amount)
    except Exception:
        return False


def remove_cash(
    player,
    amount
):
    amount = int(amount)

    if amount < 0:
        return False

    if not can_afford(
        player,
        amount
    ):
        return False

    player["cash"] = (
        int(player.get("cash", 0))
        - amount
    )

    return True


def add_cash(
    player,
    amount
):
    amount = int(amount)

    if amount < 0:
        return False

    player["cash"] = (
        int(player.get("cash", 0))
        + amount
    )

    return True


# ------------------------------------------------------------
# 6. VEHICLE NAME / DETAILS
# ------------------------------------------------------------

def vehicle_name(vehicle):
    if not vehicle:
        return "خودرو"

    if vehicle.get("name"):
        return str(
            vehicle.get("name")
        )

    brand = vehicle.get(
        "brand",
        ""
    )

    model = vehicle.get(
        "model",
        ""
    )

    year = vehicle.get(
        "year",
        ""
    )

    result = (
        f"{brand} {model}"
    ).strip()

    if year:
        result += f" {year}"

    return result or "خودرو"


def vehicle_details_text(
    vehicle
):
    if not vehicle:
        return "خودرو پیدا نشد."

    name = vehicle_name(
        vehicle
    )

    lines = [
        f"🚘 <b>{name}</b>",
        "",
    ]

    fields = [
        ("📅 سال", "year"),
        ("🛣 کارکرد", "mileage"),
        ("🔧 وضعیت", "condition"),
        ("🎨 رنگ", "color"),
        ("⚙️ موتور", "engine"),
        ("⚡ قدرت", "power"),
        ("🔄 گیربکس", "transmission"),
        ("💰 قیمت", "price"),
    ]

    for label, key in fields:
        value = vehicle.get(
            key,
            "-"
        )

        if key == "price":
            try:
                value = f"{int(value):,}"
            except Exception:
                pass

        lines.append(
            f"{label}: {value}"
        )

    if vehicle.get("tuning"):
        lines.append(
            f"🏁 تیونینگ: "
            f"{vehicle.get('tuning')}"
        )

    lines.extend([
        "",
        f"🆔 {vehicle.get('id', '-')}",
    ])

    return "\n".join(lines)


# ------------------------------------------------------------
# 7. CREATE VEHICLE COPY
# ------------------------------------------------------------

def clone_vehicle(
    vehicle,
    new_id=None
):
    import copy

    result = copy.deepcopy(
        vehicle
    )

    if new_id:
        result["id"] = new_id

    return result


# ------------------------------------------------------------
# 8. PURCHASE LOCK
# ------------------------------------------------------------

def make_purchase_key(
    buyer_id,
    catalog_id
):
    return vehicle_operation_id(
        "purchase",
        catalog_id,
        buyer_id
    )


def purchase_vehicle_once(
    buyer_id,
    catalog_id
):
    """
    خرید خودرو از کاتالوگ.
    عملیات کاملاً idempotent طراحی شده است.
    """

    with VEHICLE_OPERATION_LOCK:

        players = load_players()

        buyer_key = str(
            buyer_id
        )

        buyer = players.get(
            buyer_key
        )

        if not buyer:
            return {
                "success": False,
                "reason": "buyer_not_found",
            }

        buyer = migrate_player_data(
            buyer
        )

        if buyer.get("banned"):
            return {
                "success": False,
                "reason": "banned",
            }

        try:
            catalog_id = int(
                catalog_id
            )
        except Exception:
            return {
                "success": False,
                "reason": "invalid_vehicle",
            }

        catalog_vehicle = None

        for vehicle in VEHICLES:
            if int(
                vehicle.get("id", -1)
            ) == catalog_id:
                catalog_vehicle = vehicle
                break

        if not catalog_vehicle:
            return {
                "success": False,
                "reason": "vehicle_not_found",
            }

        price = int(
            catalog_vehicle.get(
                "price",
                0
            )
        )

        if not can_afford(
            buyer,
            price
        ):
            return {
                "success": False,
                "reason": "not_enough_money",
                "price": price,
                "cash": int(
                    buyer.get(
                        "cash",
                        0
                    )
                ),
            }

        purchase_key = make_purchase_key(
            buyer_id,
            catalog_id
        )

        # اگر قبلاً همین خرید انجام شده
        if vehicle_operation_exists(
            buyer,
            purchase_key
        ):
            existing = None

            for vehicle in buyer.get(
                "vehicles",
                []
            ):
                if vehicle.get(
                    "purchase_key"
                ) == purchase_key:
                    existing = vehicle
                    break

            return {
                "success": True,
                "already_done": True,
                "vehicle": existing,
                "price": price,
            }

        new_vehicle_id = make_id(
            "car"
        )

        new_vehicle = clone_vehicle(
            catalog_vehicle,
            new_vehicle_id
        )

        new_vehicle["purchase_key"] = (
            purchase_key
        )

        new_vehicle["owner_id"] = (
            buyer_id
        )

        new_vehicle["purchased_at"] = (
            timestamp()
        )

        # ----------------------------------------
        # اتمیک در حافظه
        # ----------------------------------------

        if not remove_cash(
            buyer,
            price
        ):
            return {
                "success": False,
                "reason": "payment_failed",
            }

        if not add_vehicle_to_player(
            buyer,
            new_vehicle
        ):
            # rollback
            add_cash(
                buyer,
                price
            )

            return {
                "success": False,
                "reason": "vehicle_add_failed",
            }

        add_vehicle_operation(
            buyer,
            purchase_key,
            "purchase",
            new_vehicle_id,
            f"خرید {vehicle_name(new_vehicle)}"
        )

        add_transaction(
            buyer,
            "vehicle_purchase",
            price,
            f"خرید {vehicle_name(new_vehicle)}"
        )

        players[buyer_key] = buyer

        # ----------------------------------------
        # اگر Master خریدار باشد،
        # فقط یک تراکنش برای خریدار ثبت می‌شود.
        # ----------------------------------------

        safe_save_players(
            players
        )

        return {
            "success": True,
            "already_done": False,
            "vehicle": new_vehicle,
            "price": price,
        }


# ------------------------------------------------------------
# 9. PURCHASE CALLBACK
# ------------------------------------------------------------

async def buy_vehicle_callback(
    query,
    context
):
    parts = (
        query.data or ""
    ).split("|")

    user_id = query.from_user.id

    # پشتیبانی از:
    # buy_vehicle|catalog_id|user_id
    if len(parts) >= 2:
        try:
            catalog_id = int(
                parts[1]
            )
        except Exception:
            await query.answer(
                "شناسه خودرو نامعتبر است.",
                show_alert=True
            )
            return
    else:
        await query.answer(
            "شناسه خودرو مشخص نیست.",
            show_alert=True
        )
        return

    if len(parts) >= 3:
        try:
            callback_uid = int(
                parts[-1]
            )

            if callback_uid != user_id:
                await query.answer(
                    "این دکمه متعلق به شما نیست.",
                    show_alert=True
                )
                return

        except Exception:
            pass

    result = purchase_vehicle_once(
        user_id,
        catalog_id
    )

    if not result.get("success"):
        reason = result.get(
            "reason"
        )

        messages = {
            "buyer_not_found":
                "❌ بازیکن پیدا نشد.",
            "banned":
                "🚫 حساب شما مسدود است.",
            "invalid_vehicle":
                "❌ خودرو نامعتبر است.",
            "vehicle_not_found":
                "❌ خودرو پیدا نشد.",
            "not_enough_money":
                "💸 موجودی نقدی شما کافی نیست.",
            "payment_failed":
                "❌ پرداخت انجام نشد.",
            "vehicle_add_failed":
                "❌ خودرو به گاراژ اضافه نشد.",
        }

        await query.answer(
            messages.get(
                reason,
                "❌ خرید انجام نشد."
            ),
            show_alert=True
        )

        return

    vehicle = result.get(
        "vehicle"
    )

    if result.get(
        "already_done"
    ):
        await query.answer(
            "این خرید قبلاً انجام شده است.",
            show_alert=True
        )
    else:
        await query.answer(
            "✅ خرید با موفقیت انجام شد."
        )

    if vehicle:
        text = (
            "✅ <b>خرید موفق</b>\n\n"
            + vehicle_details_text(
                vehicle
            )
            + "\n\n"
            "💰 مبلغ از حساب شما کسر شد."
        )
    else:
        text = (
            "✅ خرید قبلاً انجام شده است."
        )

    await query.edit_message_text(
        text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "🚗 گاراژ",
                    callback_data=(
                        f"vehicles_garage|{user_id}"
                    )
                )
            ],
            [
                InlineKeyboardButton(
                    "🏪 نمایشگاه",
                    callback_data=(
                        f"vehicles_showroom|{user_id}"
                    )
                )
            ],
            [
                InlineKeyboardButton(
                    "🔙 خودروها",
                    callback_data=(
                        f"vehicles|{user_id}"
                    )
                )
            ],
        ])
    )


# ------------------------------------------------------------
# 10. DIRECT SALE — ATOMIC TRANSFER
# ------------------------------------------------------------

def execute_direct_sale_once(
    deal_id,
    buyer_id,
    seller_id
):
    """
    انتقال خودرو و پول در یک عملیات قفل‌شده.
    """

    with VEHICLE_OPERATION_LOCK:

        players = load_players()

        buyer_key = str(
            buyer_id
        )

        seller_key = str(
            seller_id
        )

        buyer = players.get(
            buyer_key
        )

        seller = players.get(
            seller_key
        )

        if not buyer or not seller:
            return {
                "success": False,
                "reason": "player_not_found",
            }

        migrate_player_data(
            buyer
        )

        migrate_player_data(
            seller
        )

        ensure_vehicle_system(
            buyer
        )

        ensure_vehicle_system(
            seller
        )

        deal = None

        # پیدا کردن معامله
        for item in seller.get(
            "direct_deals",
            []
        ):
            if str(
                item.get("id")
            ) == str(deal_id):
                deal = item
                break

        if not deal:

            for item in buyer.get(
                "direct_deals",
                []
            ):
                if str(
                    item.get("id")
                ) == str(deal_id):
                    deal = item
                    break

        if not deal:
            return {
                "success": False,
                "reason": "deal_not_found",
            }

        # ----------------------------------------
        # اگر قبلاً تکمیل شده
        # ----------------------------------------

        if deal.get(
            "status"
        ) == "completed":

            return {
                "success": True,
                "already_done": True,
                "deal": deal,
            }

        if deal.get(
            "status"
        ) not in (
            "pending",
            "accepted",
            "processing",
        ):
            return {
                "success": False,
                "reason": "deal_not_active",
            }

        vehicle_id = deal.get(
            "vehicle_id"
        )

        try:
            price = int(
                deal.get(
                    "price",
                    0
                )
            )
        except Exception:
            return {
                "success": False,
                "reason": "invalid_price",
            }

        # ----------------------------------------
        # عملیات کلیددار
        # ----------------------------------------

        operation_id = vehicle_operation_id(
            "direct_sale",
            vehicle_id,
            seller_id,
            buyer_id
        )

        if (
            vehicle_operation_exists(
                seller,
                operation_id
            )
            or
            vehicle_operation_exists(
                buyer,
                operation_id
            )
        ):
            deal["status"] = "completed"

            return {
                "success": True,
                "already_done": True,
                "deal": deal,
            }

        # ----------------------------------------
        # بررسی مالکیت
        # ----------------------------------------

        vehicle = get_player_vehicle(
            seller,
            vehicle_id
        )

        if not vehicle:

            # اگر قبلاً منتقل شده
            if get_player_vehicle(
                buyer,
                vehicle_id
            ):
                deal["status"] = "completed"

                return {
                    "success": True,
                    "already_done": True,
                    "deal": deal,
                }

            return {
                "success": False,
                "reason": "vehicle_not_owned",
            }

        # ----------------------------------------
        # بررسی پول
        # ----------------------------------------

        if not can_afford(
            buyer,
            price
        ):
            return {
                "success": False,
                "reason": "not_enough_money",
                "price": price,
            }

        # ----------------------------------------
        # LOCK معامله
        # ----------------------------------------

        deal["status"] = "processing"

        # ----------------------------------------
        # پرداخت
        # ----------------------------------------

        if not remove_cash(
            buyer,
            price
        ):
            deal["status"] = "pending"

            return {
                "success": False,
                "reason": "payment_failed",
            }

        # ----------------------------------------
        # انتقال خودرو
        # ----------------------------------------

        removed = remove_vehicle_from_player(
            seller,
            vehicle_id
        )

        if not removed:
            # rollback پول
            add_cash(
                buyer,
                price
            )

            deal["status"] = "pending"

            return {
                "success": False,
                "reason": "vehicle_transfer_failed",
            }

        transferred_vehicle = clone_vehicle(
            vehicle
        )

        transferred_vehicle["owner_id"] = (
            buyer_id
        )

        transferred_vehicle["transferred_at"] = (
            timestamp()
        )

        added = add_vehicle_to_player(
            buyer,
            transferred_vehicle
        )

        if not added:
            # rollback خودرو
            add_vehicle_to_player(
                seller,
                vehicle
            )

            add_cash(
                buyer,
                price
            )

            deal["status"] = "pending"

            return {
                "success": False,
                "reason": "buyer_garage_error",
            }

        # ----------------------------------------
        # پرداخت فروشنده
        # ----------------------------------------

        add_cash(
            seller,
            price
        )

        # ----------------------------------------
        # تکمیل معامله
        # ----------------------------------------

        deal["status"] = "completed"

        deal["completed_at"] = (
            timestamp()
        )

        deal["operation_id"] = (
            operation_id
        )

        add_vehicle_operation(
            seller,
            operation_id,
            "direct_sale",
            vehicle_id,
            f"فروش به {buyer_id}"
        )

        add_vehicle_operation(
            buyer,
            operation_id,
            "direct_purchase",
            vehicle_id,
            f"خرید از {seller_id}"
        )

        add_transaction(
            buyer,
            "vehicle_purchase",
            price,
            f"خرید {vehicle_name(vehicle)} از {seller_id}"
        )

        add_transaction(
            seller,
            "vehicle_sale",
            price,
            f"فروش {vehicle_name(vehicle)} به {buyer_id}"
        )

        players[buyer_key] = buyer
        players[seller_key] = seller

        safe_save_players(
            players
        )

        return {
            "success": True,
            "already_done": False,
            "deal": deal,
            "vehicle": transferred_vehicle,
            "price": price,
        }


# ------------------------------------------------------------
# 11. SAFE DIRECT DEAL ACCEPT
# ------------------------------------------------------------

async def safe_accept_direct_sale(
    query,
    context
):
    parts = (
        query.data or ""
    ).split("|")

    if len(parts) < 2:
        await query.answer(
            "شناسه معامله نامعتبر است.",
            show_alert=True
        )
        return

    deal_id = parts[1]

    buyer_id = query.from_user.id

    # پیدا کردن معامله
    players = load_players()

    deal = None

    for player in players.values():

        for item in player.get(
            "direct_deals",
            []
        ):
            if str(
                item.get("id")
            ) == str(deal_id):
                deal = item
                break

        if deal:
            break

    if not deal:
        await query.answer(
            "❌ معامله پیدا نشد.",
            show_alert=True
        )
        return

    seller_id = int(
        deal.get(
            "seller_id"
        )
    )

    # فقط خریدار مجاز
    if int(
        deal.get(
            "buyer_id"
        )
    ) != buyer_id:
        await query.answer(
            "❌ این پیشنهاد برای شما نیست.",
            show_alert=True
        )
        return

    result = execute_direct_sale_once(
        deal_id,
        buyer_id,
        seller_id
    )

    if not result.get(
        "success"
    ):
        reasons = {
            "player_not_found":
                "❌ بازیکن پیدا نشد.",
            "deal_not_found":
                "❌ معامله پیدا نشد.",
            "deal_not_active":
                "❌ معامله دیگر فعال نیست.",
            "vehicle_not_owned":
                "❌ فروشنده دیگر مالک خودرو نیست.",
            "not_enough_money":
                "💸 موجودی شما کافی نیست.",
            "payment_failed":
                "❌ پرداخت انجام نشد.",
            "vehicle_transfer_failed":
                "❌ انتقال خودرو انجام نشد.",
            "buyer_garage_error":
                "❌ گاراژ خریدار آماده دریافت خودرو نیست.",
        }

        await query.answer(
            reasons.get(
                result.get("reason"),
                "❌ معامله انجام نشد."
            ),
            show_alert=True
        )

        return

    if result.get(
        "already_done"
    ):
        await query.answer(
            "این معامله قبلاً انجام شده است.",
            show_alert=True
        )
    else:
        await query.answer(
            "✅ معامله با موفقیت انجام شد."
        )

    vehicle = result.get(
        "vehicle"
    )

    text = (
        "🤝 <b>معامله تکمیل شد</b>\n\n"
        f"🚘 {vehicle_name(vehicle) if vehicle else 'خودرو'}\n"
        f"💰 مبلغ: "
        f"{int(result.get('price', 0)):,}\n\n"
        "مالکیت خودرو به خریدار منتقل شد."
    )

    await query.edit_message_text(
        text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "🚗 گاراژ من",
                    callback_data=(
                        f"vehicles_garage|{buyer_id}"
                    )
                )
            ],
            [
                InlineKeyboardButton(
                    "🔙 خودروها",
                    callback_data=(
                        f"vehicles|{buyer_id}"
                    )
                )
            ],
        ])
    )


# ------------------------------------------------------------
# 12. PATCH OLD ACCEPT FUNCTION
# ------------------------------------------------------------

async def handle_deal_accept(
    query,
    context
):
    """
    این تابع عمداً به نسخه امن هدایت می‌شود.
    """

    return await safe_accept_direct_sale(
        query,
        context
    )


# ------------------------------------------------------------
# 13. VEHICLE SELL CONFIRMATION
# ------------------------------------------------------------

async def vehicle_sell_callback(
    query,
    context
):
    parts = (
        query.data or ""
    ).split("|")

    user_id = query.from_user.id

    if len(parts) < 2:
        await query.answer(
            "شناسه خودرو نامعتبر است.",
            show_alert=True
        )
        return

    vehicle_id = parts[1]

    player = get_player_safe(
        user_id
    )

    vehicle = get_player_vehicle(
        player,
        vehicle_id
    )

    if not vehicle:
        await query.answer(
            "❌ خودرو در گاراژ شما نیست.",
            show_alert=True
        )
        return

    price = int(
        vehicle.get(
            "price",
            0
        )
    )

    sale_price = max(
        1,
        price
    )

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                f"💰 فروش فوری {sale_price:,}",
                callback_data=(
                    f"vehicle_sell_confirm|"
                    f"{vehicle_id}|{user_id}"
                )
            )
        ],
        [
            InlineKeyboardButton(
                "🤝 فروش به بازیکن",
                callback_data=(
                    f"vehicle_offer|"
                    f"{vehicle_id}|{user_id}"
                )
            )
        ],
        [
            InlineKeyboardButton(
                "❌ لغو",
                callback_data=(
                    f"vehicle_view|"
                    f"{vehicle_id}|{user_id}"
                )
            )
        ],
    ])

    await query.edit_message_text(
        "💰 <b>فروش خودرو</b>\n\n"
        f"🚘 {vehicle_name(vehicle)}\n"
        f"💵 قیمت پیشنهادی فروش فوری: "
        f"{sale_price:,}\n\n"
        "آیا مطمئنی؟",
        parse_mode="HTML",
        reply_markup=keyboard
    )


# ------------------------------------------------------------
# 14. INSTANT SALE
# ------------------------------------------------------------

def instant_sell_vehicle_once(
    seller_id,
    vehicle_id
):
    with VEHICLE_OPERATION_LOCK:

        players = load_players()

        seller = players.get(
            str(seller_id)
        )

        if not seller:
            return {
                "success": False,
                "reason": "seller_not_found",
            }

        ensure_vehicle_system(
            seller
        )

        vehicle = get_player_vehicle(
            seller,
            vehicle_id
        )

        if not vehicle:
            return {
                "success": False,
                "reason": "vehicle_not_found",
            }

        operation_id = vehicle_operation_id(
            "instant_sale",
            vehicle_id,
            seller_id
        )

        if vehicle_operation_exists(
            seller,
            operation_id
        ):
            return {
                "success": True,
                "already_done": True,
            }

        price = int(
            vehicle.get(
                "price",
                0
            )
        )

        if price <= 0:
            return {
                "success": False,
                "reason": "invalid_price",
            }

        if not remove_vehicle_from_player(
            seller,
            vehicle_id
        ):
            return {
                "success": False,
                "reason": "remove_failed",
            }

        # فروش فوری با قیمت کاتالوگ
        add_cash(
            seller,
            price
        )

        add_vehicle_operation(
            seller,
            operation_id,
            "instant_sale",
            vehicle_id,
            "فروش فوری خودرو"
        )

        add_transaction(
            seller,
            "vehicle_sale",
            price,
            f"فروش فوری {vehicle_name(vehicle)}"
        )

        players[str(seller_id)] = seller

        safe_save_players(
            players
        )

        return {
            "success": True,
            "already_done": False,
            "price": price,
            "vehicle": vehicle,
        }

# ------------------------------------------------------------
# 15. INSTANT SELL CALLBACK
# ------------------------------------------------------------

async def vehicle_sell_confirm_callback(
    query,
    context
):
    parts = (
        query.data or ""
    ).split("|")

    user_id = query.from_user.id

    if len(parts) < 2:
        await query.answer(
            "شناسه خودرو نامعتبر است.",
            show_alert=True
        )
        return

    vehicle_id = parts[1]

    result = instant_sell_vehicle_once(
        user_id,
        vehicle_id
    )

    if not result.get(
        "success"
    ):
        reasons = {
            "seller_not_found":
                "❌ بازیکن پیدا نشد.",
            "vehicle_not_found":
                "❌ خودرو در گاراژ نیست.",
            "invalid_price":
                "❌ قیمت خودرو نامعتبر است.",
            "remove_failed":
                "❌ فروش خودرو انجام نشد.",
        }

        await query.answer(
            reasons.get(
                result.get("reason"),
                "❌ فروش انجام نشد."
            ),
            show_alert=True
        )

        return

    if result.get(
        "already_done"
    ):
        await query.answer(
            "این فروش قبلاً انجام شده است.",
            show_alert=True
        )
    else:
        await query.answer(
            "✅ خودرو فروخته شد."
        )

    price = int(
        result.get(
            "price",
            0
        )
    )

    await query.edit_message_text(
        "✅ <b>فروش موفق</b>\n\n"
        f"💰 مبلغ دریافت‌شده: {price:,}\n"
        "🚘 خودرو از گاراژ حذف شد.",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "🚗 گاراژ",
                    callback_data=(
                        f"vehicles_garage|{user_id}"
                    )
                )
            ],
            [
                InlineKeyboardButton(
                    "🔙 خودروها",
                    callback_data=(
                        f"vehicles|{user_id}"
                    )
                )
            ],
        ])
    )


# ------------------------------------------------------------
# 16. PATCH VEHICLE CALLBACK DISPATCHER
# ------------------------------------------------------------

async def vehicle_transaction_callback(
    query,
    context
):
    action = (
        query.data or ""
    ).split("|")[0]

    if action == "vehicle_sell":
        return await vehicle_sell_callback(
            query,
            context
        )

    if action == "vehicle_sell_confirm":
        return await vehicle_sell_confirm_callback(
            query,
            context
        )

    if action in (
        "deal_accept",
        "vehicle_offer_accept",
    ):
        return await safe_accept_direct_sale(
            query,
            context
        )

    return None


# ------------------------------------------------------------
# 17. FINAL VEHICLE CALLBACK OVERRIDE
# ------------------------------------------------------------

_previous_handle_vehicle_garage_callback = (
    handle_vehicle_garage_callback
)


async def handle_vehicle_garage_callback(
    query,
    context
):
    action = (
        query.data or ""
    ).split("|")[0]

    if action in (
        "vehicle_sell",
        "vehicle_sell_confirm",
        "deal_accept",
        "vehicle_offer_accept",
    ):
        return await vehicle_transaction_callback(
            query,
            context
        )

    return await _previous_handle_vehicle_garage_callback(
        query,
        context
    )


# ------------------------------------------------------------
# 18. DIRECT DEAL CALLBACK PATCH
# ------------------------------------------------------------

_previous_handle_direct_deal_callback = (
    globals().get(
        "handle_direct_deal_callback"
    )
)


async def patched_direct_deal_callback(
    query,
    context
):
    action = (
        query.data or ""
    ).split("|")[0]

    if action in (
        "deal_accept",
        "vehicle_offer_accept",
    ):
        return await safe_accept_direct_sale(
            query,
            context
        )

    if _previous_handle_direct_deal_callback:
        return await _previous_handle_direct_deal_callback(
            query,
            context
        )

    await query.answer(
        "عملیات معامله پیدا نشد.",
        show_alert=True
    )


handle_direct_deal_callback = (
    patched_direct_deal_callback
)


# ------------------------------------------------------------
# 19. FINAL CALLBACK ROUTER PATCH
# ------------------------------------------------------------

_previous_final_callback_router = (
    final_callback_router
)


async def final_callback_router(
    update,
    context
):
    query = update.callback_query

    if not query:
        return

    action = (
        query.data or ""
    ).split("|")[0]

    # عملیات‌های حساس خودرو
    if action in (
        "vehicle_sell",
        "vehicle_sell_confirm",
        "deal_accept",
        "vehicle_offer_accept",
    ):
        try:
            await query.answer()
        except Exception:
            pass

        return await vehicle_transaction_callback(
            query,
            context
        )

    return await _previous_final_callback_router(
        update,
        context
    )


# ------------------------------------------------------------
# 20. CLEAN DUPLICATE TRANSACTIONS
# ------------------------------------------------------------

def clean_duplicate_vehicle_transactions():
    """
    فقط تراکنش‌های کاملاً تکراری خودرو را پاک می‌کند.
    تراکنش‌های متفاوت دست‌نخورده می‌مانند.
    """

    players = load_players()
    changed = False

    for uid, player in players.items():

        transactions = player.get(
            "transactions",
            []
        )

        if not isinstance(
            transactions,
            list
        ):
            continue

        seen = set()
        cleaned = []

        for tx in transactions:

            tx_type = tx.get(
                "type",
                ""
            )

            description = tx.get(
                "description",
                ""
            )

            amount = tx.get(
                "amount",
                0
            )

            # فقط تراکنش‌های خودرو
            is_vehicle_tx = (
                "vehicle"
                in str(tx_type).lower()
                or
                "خودرو"
                in str(description)
                or
                "فروش"
                in str(description)
                or
                "خرید"
                in str(description)
            )

            if not is_vehicle_tx:
                cleaned.append(tx)
                continue

            signature = (
                str(tx_type),
                str(amount),
                str(description),
            )

            if signature in seen:
                changed = True
                continue

            seen.add(signature)
            cleaned.append(tx)

        player["transactions"] = (
            cleaned[-100:]
        )

        players[uid] = player

    if changed:
        safe_save_players(
            players
        )

    return changed


# ------------------------------------------------------------
# 21. FINAL VEHICLE MIGRATION
# ------------------------------------------------------------

def migrate_vehicle_data():
    players = load_players()

    changed = False

    for uid, player in players.items():

        before = repr(
            player.get(
                "vehicles",
                []
            )
        )

        ensure_vehicle_system(
            player
        )

        for vehicle in player.get(
            "vehicles",
            []
        ):
            if not vehicle.get(
                "id"
            ):
                vehicle["id"] = make_id(
                    "car"
                )

            if not vehicle.get(
                "owner_id"
            ):
                vehicle["owner_id"] = int(
                    uid
                )

        after = repr(
            player.get(
                "vehicles",
                []
            )
        )

        if before != after:
            changed = True

        players[uid] = player

    if changed:
        safe_save_players(
            players
        )


# ------------------------------------------------------------
# 22. RUN VEHICLE MIGRATION AT STARTUP
# ------------------------------------------------------------

try:
    _old_startup_database = startup_database
except NameError:
    _old_startup_database = None


def startup_database():
    if _old_startup_database:
        try:
            _old_startup_database()
        except Exception as e:
            print(
                "Base startup migration error:",
                repr(e)
            )

    try:
        migrate_vehicle_data()
    except Exception as e:
        print(
            "Vehicle migration error:",
            repr(e)
        )

    try:
        clean_duplicate_vehicle_transactions()
    except Exception as e:
        print(
            "Duplicate transaction cleanup error:",
            repr(e)
        )

    print(
        "Vehicle system migration completed."
    )


# ============================================================
# END OF PART 12
# ============================================================# ============================================================
# PART 13 — FINAL PATCH / INTEGRITY CHECK / RUNTIME SAFETY
# ============================================================

# ------------------------------------------------------------
# 1. RUNTIME STATE
# ------------------------------------------------------------

try:
    RUNTIME_STATE
except NameError:
    RUNTIME_STATE = {
        "started": False,
        "startup_checked": False,
        "errors": [],
    }


# ------------------------------------------------------------
# 2. SAFE INTEGER
# ------------------------------------------------------------

def safe_int(value, default=0):
    try:
        return int(value)
    except Exception:
        return default


# ------------------------------------------------------------
# 3. SAFE TEXT
# ------------------------------------------------------------

def safe_text(value, default=""):
    if value is None:
        return default

    try:
        return str(value)
    except Exception:
        return default


# ------------------------------------------------------------
# 4. PLAYER STRUCTURE CHECK
# ------------------------------------------------------------

def validate_player_structure(
    user_id,
    player
):
    errors = []

    if not isinstance(player, dict):
        return [
            "player_not_dict"
        ]

    required_lists = [
        "vehicles",
        "transactions",
        "properties",
        "businesses",
        "vehicle_offers",
        "market_listings",
        "auctions",
        "direct_deals",
        "vehicle_history",
    ]

    for key in required_lists:
        if not isinstance(
            player.get(key),
            list
        ):
            errors.append(
                f"{key}_not_list"
            )

    required_dicts = [
        "body",
        "equipment",
        "jobs",
        "stats",
    ]

    for key in required_dicts:
        if not isinstance(
            player.get(key),
            dict
        ):
            errors.append(
                f"{key}_not_dict"
            )

    for key in (
        "level",
        "xp",
        "cash",
        "bank_balance",
        "credit_score",
        "reputation",
        "loan",
    ):
        try:
            int(
                player.get(
                    key,
                    0
                )
            )
        except Exception:
            errors.append(
                f"{key}_invalid"
            )

    return errors


# ------------------------------------------------------------
# 5. VEHICLE STRUCTURE CHECK
# ------------------------------------------------------------

def validate_vehicle(
    vehicle
):
    errors = []

    if not isinstance(
        vehicle,
        dict
    ):
        return [
            "vehicle_not_dict"
        ]

    if not vehicle.get("id"):
        errors.append(
            "missing_vehicle_id"
        )

    if not (
        vehicle.get("name")
        or
        vehicle.get("model")
    ):
        errors.append(
            "missing_vehicle_name"
        )

    try:
        int(
            vehicle.get(
                "price",
                0
            )
        )
    except Exception:
        errors.append(
            "invalid_vehicle_price"
        )

    return errors


# ------------------------------------------------------------
# 6. COMPLETE DATABASE CHECK
# ------------------------------------------------------------

def validate_database():
    players = load_players()

    report = {
        "players": 0,
        "vehicles": 0,
        "errors": [],
    }

    if not isinstance(
        players,
        dict
    ):
        report["errors"].append(
            "players_database_not_dict"
        )

        return report

    for uid, player in players.items():

        report["players"] += 1

        player_errors = (
            validate_player_structure(
                uid,
                player
            )
        )

        for error in player_errors:
            report["errors"].append(
                f"{uid}:{error}"
            )

        for vehicle in player.get(
            "vehicles",
            []
        ):

            report["vehicles"] += 1

            vehicle_errors = (
                validate_vehicle(
                    vehicle
                )
            )

            for error in vehicle_errors:
                report["errors"].append(
                    f"{uid}:vehicle:{error}"
                )

    return report


# ------------------------------------------------------------
# 7. AUTOMATIC DATABASE REPAIR
# ------------------------------------------------------------

def repair_database():
    players = load_players()

    if not isinstance(
        players,
        dict
    ):
        players = {}

    changed = False

    for uid, player in list(
        players.items()
    ):

        original = repr(
            player
        )

        player = migrate_player_data(
            player
        )

        ensure_vehicle_system(
            player
        )

        # ----------------------------------------
        # Repair vehicles
        # ----------------------------------------

        cleaned_vehicles = []

        seen_vehicle_ids = set()

        for vehicle in player.get(
            "vehicles",
            []
        ):

            if not isinstance(
                vehicle,
                dict
            ):
                changed = True
                continue

            if not vehicle.get("id"):
                vehicle["id"] = make_id(
                    "car"
                )
                changed = True

            vehicle_id = str(
                vehicle.get("id")
            )

            # جلوگیری از دو مالک برای
            # یک خودرو در یک گاراژ
            if vehicle_id in seen_vehicle_ids:
                changed = True
                continue

            seen_vehicle_ids.add(
                vehicle_id
            )

            vehicle["owner_id"] = safe_int(
                vehicle.get(
                    "owner_id",
                    uid
                ),
                safe_int(uid)
            )

            if "price" not in vehicle:
                vehicle["price"] = 0
                changed = True

            cleaned_vehicles.append(
                vehicle
            )

        player["vehicles"] = (
            cleaned_vehicles
        )

        # ----------------------------------------
        # Repair transactions
        # ----------------------------------------

        if not isinstance(
            player.get("transactions"),
            list
        ):
            player["transactions"] = []
            changed = True

        player["transactions"] = (
            player["transactions"][-100:]
        )

        # ----------------------------------------
        # Repair history
        # ----------------------------------------

        if not isinstance(
            player.get("vehicle_history"),
            list
        ):
            player["vehicle_history"] = []
            changed = True

        player["vehicle_history"] = (
            player["vehicle_history"][-200:]
        )

        new_repr = repr(
            player
        )

        if original != new_repr:
            changed = True

        players[uid] = player

    if changed:
        safe_save_players(
            players
        )

    return changed


# ------------------------------------------------------------
# 8. FIND VEHICLE OWNER
# ------------------------------------------------------------

def find_vehicle_owner(
    vehicle_id,
    players=None
):
    if players is None:
        players = load_players()

    for uid, player in players.items():

        for vehicle in player.get(
            "vehicles",
            []
        ):

            if str(
                vehicle.get("id")
            ) == str(vehicle_id):

                return int(uid)

    return None


# ------------------------------------------------------------
# 9. CHECK VEHICLE OWNERSHIP UNIQUENESS
# ------------------------------------------------------------

def validate_vehicle_ownership():
    players = load_players()

    owners = {}
    duplicates = []

    for uid, player in players.items():

        for vehicle in player.get(
            "vehicles",
            []
        ):

            vehicle_id = str(
                vehicle.get("id")
            )

            if not vehicle_id:
                continue

            if vehicle_id in owners:
                duplicates.append({
                    "vehicle_id": vehicle_id,
                    "owner_1": owners[vehicle_id],
                    "owner_2": uid,
                })
            else:
                owners[vehicle_id] = uid

    return duplicates


# ------------------------------------------------------------
# 10. TRANSACTION DUPLICATE SIGNATURE
# ------------------------------------------------------------

def transaction_signature(
    transaction
):
    return (
        safe_text(
            transaction.get("type")
        ),
        safe_int(
            transaction.get("amount")
        ),
        safe_text(
            transaction.get(
                "description"
            )
        ),
    )

# ------------------------------------------------------------
# 11. REMOVE EXACT DUPLICATE TRANSACTIONS
# ------------------------------------------------------------

def repair_exact_duplicate_transactions():
    players = load_players()

    changed = False

    for uid, player in players.items():

        transactions = player.get(
            "transactions",
            []
        )

        if not isinstance(
            transactions,
            list
        ):
            player["transactions"] = []
            changed = True
            continue

        seen = set()
        cleaned = []

        for tx in transactions:

            if not isinstance(
                tx,
                dict
            ):
                changed = True
                continue

            signature = (
                transaction_signature(
                    tx
                )
            )

            # فقط موارد کاملاً یکسان
            if signature in seen:
                changed = True
                continue

            seen.add(
                signature
            )

            cleaned.append(
                tx
            )

        player["transactions"] = (
            cleaned[-100:]
        )

        players[uid] = player

    if changed:
        safe_save_players(
            players
        )

    return changed


# ------------------------------------------------------------
# 12. CALLBACK OWNER SAFETY
# ------------------------------------------------------------

def callback_user_is_requester(
    query,
    expected_user_id
):
    try:
        return int(
            query.from_user.id
        ) == int(
            expected_user_id
        )
    except Exception:
        return False


# ------------------------------------------------------------
# 13. SAFE CALLBACK ANSWER
# ------------------------------------------------------------

async def safe_query_answer(
    query,
    text=None,
    show_alert=False
):
    try:
        if text:
            await query.answer(
                text,
                show_alert=show_alert
            )
        else:
            await query.answer()
    except Exception:
        pass


# ------------------------------------------------------------
# 14. BANNED PLAYER CALLBACK PROTECTION
# ------------------------------------------------------------

async def callback_player_allowed(
    query
):
    try:
        player = get_player_safe(
            query.from_user.id
        )

        if player.get("banned"):
            await safe_query_answer(
                query,
                "🚫 حساب شما مسدود است.",
                True
            )
            return False

        return True

    except Exception:
        await safe_query_answer(
            query,
            "خطا در بررسی حساب.",
            True
        )
        return False


# ------------------------------------------------------------
# 15. CALLBACK WRAPPER
# ------------------------------------------------------------

_previous_final_callback_router_v2 = (
    final_callback_router
)


async def final_callback_router(
    update,
    context
):
    query = update.callback_query

    if not query:
        return

    if not await callback_player_allowed(
        query
    ):
        return

    try:
        return await (
            _previous_final_callback_router_v2(
                update,
                context
            )
        )

    except Exception as e:

        print(
            "FINAL CALLBACK ERROR:",
            repr(e)
        )

        RUNTIME_STATE.setdefault(
            "errors",
            []
        ).append({
            "type": "callback",
            "error": repr(e),
            "time": timestamp(),
        })

        try:
            await query.answer(
                "⚠️ خطایی رخ داد.",
                show_alert=True
            )
        except Exception:
            pass


# ------------------------------------------------------------
# 16. TEXT ROUTER PROTECTION
# ------------------------------------------------------------

_previous_final_text_router_v2 = (
    final_text_router
)


async def final_text_router(
    update,
    context
):
    try:
        return await (
            _previous_final_text_router_v2(
                update,
                context
            )
        )

    except Exception as e:

        print(
            "FINAL TEXT ERROR:",
            repr(e)
        )

        RUNTIME_STATE.setdefault(
            "errors",
            []
        ).append({
            "type": "text",
            "error": repr(e),
            "time": timestamp(),
        })

        try:
            await update.message.reply_text(
                "⚠️ خطایی رخ داد.\n"
                "لطفاً دوباره تلاش کن."
            )
        except Exception:
            pass


# ------------------------------------------------------------
# 17. DATABASE BACKUP
# ------------------------------------------------------------

def create_database_backup():
    """
    یک backup ساده از players.json
    در همان پوشه ایجاد می‌کند.
    """

    if not os.path.exists(
        PLAYERS_FILE
    ):
        return False

    try:
        import shutil

        backup_name = (
            "players_backup_"
            + str(
                int(
                    time.time()
                )
            )
            + ".json"
        )

        shutil.copy2(
            PLAYERS_FILE,
            backup_name
        )

        return True

    except Exception as e:
        print(
            "Backup error:",
            repr(e)
        )

        return False


# ------------------------------------------------------------
# 18. STARTUP INTEGRITY CHECK
# ------------------------------------------------------------

def run_integrity_check():
    print(
        "Running UNDERCITY integrity check..."
    )

    # ----------------------------------------
    # Repair
    # ----------------------------------------

    try:
        repair_database()
        print(
            "✓ Database repair"
        )
    except Exception as e:
        print(
            "✗ Database repair:",
            repr(e)
        )

    # ----------------------------------------
    # Vehicle migration
    # ----------------------------------------

    try:
        migrate_vehicle_data()
        print(
            "✓ Vehicle migration"
        )
    except Exception as e:
        print(
            "✗ Vehicle migration:",
            repr(e)
        )

    # ----------------------------------------
    # Exact duplicate transactions
    # ----------------------------------------

    try:
        repair_exact_duplicate_transactions()
        print(
            "✓ Transaction cleanup"
        )
    except Exception as e:
        print(
            "✗ Transaction cleanup:",
            repr(e)
        )

    # ----------------------------------------
    # Validate database
    # ----------------------------------------

    try:
        report = validate_database()

        print(
            "Players:",
            report["players"]
        )

        print(
            "Vehicles:",
            report["vehicles"]
        )

        if report["errors"]:
            print(
                "Database warnings:",
                len(
                    report["errors"]
                )
            )
        else:
            print(
                "✓ Database validation"
            )

    except Exception as e:
        print(
            "✗ Database validation:",
            repr(e)
        )

    # ----------------------------------------
    # Ownership
    # ----------------------------------------

    try:
        duplicates = (
            validate_vehicle_ownership()
        )

        if duplicates:
            print(
                "⚠ Duplicate vehicle ownership:",
                len(duplicates)
            )
        else:
            print(
                "✓ Vehicle ownership"
            )

    except Exception as e:
        print(
            "✗ Ownership check:",
            repr(e)
        )

    RUNTIME_STATE[
        "startup_checked"
    ] = True

    print(
        "Integrity check completed."
    )


# ------------------------------------------------------------
# 19. FINAL STARTUP PATCH
# ------------------------------------------------------------

_previous_startup_database_v2 = (
    startup_database
)


def startup_database():
    """
    نسخه نهایی startup.
    """

    try:
        _previous_startup_database_v2()
    except Exception as e:
        print(
            "Previous startup warning:",
            repr(e)
        )

    try:
        create_database_backup()
    except Exception as e:
        print(
            "Backup warning:",
            repr(e)
        )

    try:
        run_integrity_check()
    except Exception as e:
        print(
            "Integrity check warning:",
            repr(e)
        )


# ------------------------------------------------------------
# 20. FINAL APPLICATION BUILDER PATCH
# ------------------------------------------------------------

def build_application():
    token = os.environ.get(
        "BOT_TOKEN",
        ""
    )

    if not token:
        raise RuntimeError(
            "BOT_TOKEN environment variable is missing."
        )

    application = (
        Application
        .builder()
        .token(token)
        .build()
    )

    # ----------------------------------------
    # Commands
    # ----------------------------------------

    application.add_handler(
        CommandHandler(
            "start",
            start_command
        )
    )

    application.add_handler(
        CommandHandler(
            "help",
            help_command
        )
    )

    application.add_handler(
        CommandHandler(
            "menu",
            menu_command
        )
    )

    application.add_handler(
        CommandHandler(
            "panel",
            panel_command
        )
    )

    application.add_handler(
        CommandHandler(
            "jobs",
            jobs_command
        )
    )

    application.add_handler(
        CommandHandler(
            "cars",
            vehicle_command_menu
        )
    )

    # ----------------------------------------
    # ONE CALLBACK ROUTER
    # ----------------------------------------

    application.add_handler(
        CallbackQueryHandler(
            final_callback_router
        )
    )

    # ----------------------------------------
    # ONE TEXT ROUTER
    # ----------------------------------------

    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            final_text_router
        )
    )

    # ----------------------------------------
    # ERROR HANDLER
    # ----------------------------------------

    application.add_error_handler(
        global_error_handler
    )

    return application


# ------------------------------------------------------------
# 21. FINAL MAIN PATCH
# ------------------------------------------------------------

def main():
    print("=" * 60)
    print("UNDERCITY")
    print("Starting final build...")
    print("=" * 60)

    if RUNTIME_STATE.get(
        "started"
    ):
        print(
            "WARNING: main() called twice."
        )

    RUNTIME_STATE[
        "started"
    ] = True

    # ----------------------------------------
    # Database
    # ----------------------------------------

    startup_database()

    # ----------------------------------------
    # Health server
    # ----------------------------------------

    start_health_server()

    # ----------------------------------------
    # Telegram
    # ----------------------------------------

    application = build_application()

    print(
        "✓ Telegram application ready."
    )

    print(
        "✓ Health server ready."
    )

    print(
        "✓ Database ready."
    )

    print(
        "✓ UNDERCITY is starting..."
    )

    application.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=False,
    )


# ------------------------------------------------------------
# 22. FINAL EXECUTION
# ------------------------------------------------------------

if __name__ == "__main__":
    main()


# ============================================================
# END OF PART 13
# ============================================================
