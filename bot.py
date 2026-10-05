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
        reply_markup=help_keyboa
    # ============================================================
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
            :

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

    # --------------------
    # ============================================================
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
      
