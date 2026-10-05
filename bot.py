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
       
