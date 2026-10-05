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

    amount = int(amount)

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

    player["bank_balance"] -= amount

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
        reply_markup=help_keyboa(
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
# ============================================================
