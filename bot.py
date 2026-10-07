
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UNDERCITY — Professional Telegram Role-Playing Game Bot
نسخهٔ تمیز، ایمن و یکپارچه
"""

from __future__ import annotations

import os
import json
import re
import threading
import uuid
import random
import time
import hashlib
import copy
import logging
import traceback
import html as html_module
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Any, Optional

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, User
from telegram.error import BadRequest, NetworkError, TimedOut, Forbidden
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ══════════════════════════════════════════════════════════════
# LOGGING
# ══════════════════════════════════════════════════════════════

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)

# جلوگیری از نمایش URLهای Telegram API و BOT_TOKEN در لاگ
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

logger = logging.getLogger("UNDERCITY")
# ══════════════════════════════════════════════════════════════
# CONFIG
# ══════════════════════════════════════════════════════════════

PORT = int(os.environ.get("PORT", 10000))
PLAYERS_FILE = os.environ.get("PLAYERS_FILE", "players.json")
MASTER_USER_ID = int(os.environ.get("MASTER_USER_ID", "5750241558"))
MASTER_CASH = 10_000_000_000_000
MASTER_BANK = 10_000_000_000_000
STARTING_CASH = 50_000
DATA_LOCK = threading.RLock()

# ══════════════════════════════════════════════════════════════
# VEHICLE CATALOG
# ══════════════════════════════════════════════════════════════

VEHICLE_CATALOG: dict[str, dict] = {
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

# ══════════════════════════════════════════════════════════════
# BODY / COMBAT
# ══════════════════════════════════════════════════════════════

BODY_PARTS: dict[str, dict] = {
    "head": {"name": "🧠 سر", "max_hp": 80, "multiplier": 1.5},
    "face": {"name": "😶 صورت", "max_hp": 70, "multiplier": 1.4},
    "chest": {"name": "🫁 سینه", "max_hp": 120, "multiplier": 1.1},
    "abdomen": {"name": "🫃 شکم", "max_hp": 110, "multiplier": 1.0},
    "right_arm": {"name": "💪 دست راست", "max_hp": 90, "multiplier": 0.85},
    "left_arm": {"name": "💪 دست چپ", "max_hp": 90, "multiplier": 0.85},
    "right_shoulder": {"name": "🔹 شانه راست", "max_hp": 90, "multiplier": 0.9},
    "left_shoulder": {"name": "🔹 شانه چپ", "max_hp": 90, "multiplier": 0.9},
    "right_leg": {"name": "🦵 پای راست", "max_hp": 100, "multiplier": 0.9},
    "left_leg": {"name": "🦵 پای چپ", "max_hp": 100, "multiplier": 0.9},
}

ATTACKS: dict[str, dict] = {
    "fist": {
        "name": "👊 مشت",
        "min": 6,
        "max": 14,
        "accuracy": 85,
        "xp": 5,
        "level": 1,
    },
    "kick": {
        "name": "🦵 لگد",
        "min": 8,
        "max": 18,
        "accuracy": 75,
        "xp": 7,
        "level": 1,
    },
    "heavy": {
        "name": "💥 ضربه سنگین",
        "min": 12,
        "max": 22,
        "accuracy": 65,
        "xp": 10,
        "level": 3,
    },
    "knife": {
        "name": "🔪 چاقو",
        "min": 16,
        "max": 28,
        "accuracy": 70,
        "xp": 14,
        "level": 5,
    },
}

INJURY_TYPES: dict[str, dict] = {
    "bruise": {"name": "کبودی", "severity": 1, "cost": 8_000, "heal_sec": 60},
    "wound": {"name": "زخم", "severity": 2, "cost": 25_000, "heal_sec": 180},
    "bleeding": {"name": "خونریزی", "severity": 3, "cost": 55_000, "heal_sec": 300},
    "dislocation": {"name": "دررفتگی", "severity": 4, "cost": 95_000, "heal_sec": 480},
    "fracture": {"name": "شکستگی", "severity": 5, "cost": 180_000, "heal_sec": 900},
}

# ══════════════════════════════════════════════════════════════
# JOBS
# ══════════════════════════════════════════════════════════════

JOBS: dict[str, dict] = {
    "barber": {
        "name": "💈 آرایشگری",
        "ranks": ["کارآموز", "مبتدی", "متوسط", "ماهر", "حرفه‌ای", "استاد"],
        "base_income": 55_000,
        "base_xp": 12,
        "duration": 15,
    },
    "mechanic": {
        "name": "🔧 مکانیکی",
        "ranks": ["کارآموز", "مبتدی", "متوسط", "ماهر", "حرفه‌ای", "استاد"],
        "base_income": 95_000,
        "base_xp": 18,
        "duration": 20,
    },
}

JOB_RANK_THRESHOLDS = [0, 100, 500, 1200, 2500, 5000]

# ══════════════════════════════════════════════════════════════
# EQUIPMENT
# ══════════════════════════════════════════════════════════════

EQUIPMENT: dict[str, dict] = {
    "normal_clothes": {
        "name": "👕 لباس معمولی",
        "price": 0,
        "level": 1,
        "protection": {"head": 0, "chest": 0, "arms": 0, "legs": 0},
    },
    "leather_jacket": {
        "name": "🧥 کت چرمی",
        "price": 2_500_000,
        "level": 2,
        "protection": {"head": 0, "chest": 10, "arms": 6, "legs": 0},
    },
    "body_armor": {
        "name": "🦺 جلیقه محافظ",
        "price": 18_000_000,
        "level": 4,
        "protection": {"head": 0, "chest": 35, "arms": 15, "legs": 8},
    },
    "helmet": {
        "name": "⛑️ کلاه محافظ",
        "price": 9_000_000,
        "level": 3,
        "protection": {"head": 40, "chest": 0, "arms": 0, "legs": 0},
    },
    "knife": {
        "name": "🔪 چاقو",
        "price": 12_000_000,
        "level": 5,
        "weapon": True,
    },
}

# ══════════════════════════════════════════════════════════════
# DISTRICTS (مناطق شهر)
# ══════════════════════════════════════════════════════════════

DISTRICTS: dict[str, dict] = {
    "downtown": {
        "name": "🏙️ مرکز شهر",
        "desc": "پررونق، امن‌تر، اجاره بالاتر",
        "rent_mult": 1.4,
        "crime": 0.2,
        "move_cost": 500_000,
    },
    "south": {
        "name": "🌆 پایین‌شهر",
        "desc": "شروع بازی، ارزان، جرم بیشتر",
        "rent_mult": 1.0,
        "crime": 0.55,
        "move_cost": 0,
    },
    "industrial": {
        "name": "🏭 منطقه صنعتی",
        "desc": "کارخانه و مکانیکی، درآمد شغلی بهتر",
        "rent_mult": 0.9,
        "crime": 0.4,
        "move_cost": 300_000,
    },
    "port": {
        "name": "⚓ بندر",
        "desc": "قاچاق و تجارت دریایی (فاز بعد)",
        "rent_mult": 1.1,
        "crime": 0.5,
        "move_cost": 800_000,
    },
    "north": {
        "name": "🏡 شمال شهر",
        "desc": "لوکس و آرام، برای پولدارها",
        "rent_mult": 2.0,
        "crime": 0.1,
        "move_cost": 2_000_000,
    },
}

# ══════════════════════════════════════════════════════════════
# PROPERTIES (املاک)
# ══════════════════════════════════════════════════════════════

PROPERTY_CATALOG: dict[str, dict] = {
    "room_south": {
        "name": "🛏️ اتاق اجاره‌ای پایین‌شهر",
        "district": "south",
        "type": "rent",
        "price": 0,
        "rent": 150_000,
        "level": 1,
    },
    "apt_south": {
        "name": "🏢 آپارتمان کوچک پایین‌شهر",
        "district": "south",
        "type": "buy",
        "price": 25_000_000,
        "rent": 0,
        "level": 1,
    },
    "apt_downtown": {
        "name": "🏢 آپارتمان مرکز شهر",
        "district": "downtown",
        "type": "buy",
        "price": 80_000_000,
        "rent": 0,
        "level": 3,
    },
    "house_north": {
        "name": "🏠 ویلای شمال شهر",
        "district": "north",
        "type": "buy",
        "price": 350_000_000,
        "rent": 0,
        "level": 8,
    },
    "shop_industrial": {
        "name": "🏪 مغازه منطقه صنعتی",
        "district": "industrial",
        "type": "buy",
        "price": 120_000_000,
        "rent": 0,
        "level": 5,
        "income": 400_000,
    },
    "warehouse_port": {
        "name": "📦 انبار بندر",
        "district": "port",
        "type": "buy",
        "price": 200_000_000,
        "rent": 0,
        "level": 6,
        "income": 600_000,
    },
}

# ══════════════════════════════════════════════════════════════
# TRAINING COURSES (دوره‌ها)
# ══════════════════════════════════════════════════════════════

COURSES: dict[str, dict] = {
    "barber_basic": {
        "name": "💈 دوره پایه آرایشگری",
        "job": "barber",
        "xp": 80,
        "cost": 2_000_000,
        "level": 1,
    },
    "barber_pro": {
        "name": "💈 دوره حرفه‌ای آرایشگری",
        "job": "barber",
        "xp": 250,
        "cost": 8_000_000,
        "level": 3,
    },
    "mech_basic": {
        "name": "🔧 دوره پایه مکانیکی",
        "job": "mechanic",
        "xp": 100,
        "cost": 3_000_000,
        "level": 1,
    },
    "mech_pro": {
        "name": "🔧 دوره پیشرفته مکانیکی",
        "job": "mechanic",
        "xp": 300,
        "cost": 12_000_000,
        "level": 4,
    },
    "combat_basic": {
        "name": "⚔️ دوره دفاع شخصی",
        "job": None,
        "xp_player": 40,
        "cost": 5_000_000,
        "level": 2,
    },
}

# ══════════════════════════════════════════════════════════════
# HELP PAGES
# ══════════════════════════════════════════════════════════════

HELP_PAGES = [
    {
        "title": "🏙️ UNDERCITY چیست؟",
        "text": (
            "UNDERCITY یک بازی نقش‌آفرینی شهری و اقتصادی است.\n\n"
            "تو یک شخصیت داری و می‌توانی پول دربیاوری، شغل داشته باشی، "
            "خودرو بخری، با دیگران مبارزه کنی و پیشرفت کنی.\n\n"
            "دستورهای اصلی:\n"
            "• منو / menu\n"
            "• /help — راهنما\n"
            "• /jobs — مشاغل\n"
            "• /cars — خودروها"
        ),
    },
    {
        "title": "💰 پول و بانک",
        "text": (
            "💵 پول نقد و 🏦 حساب بانکی داری.\n\n"
            "دستورات:\n"
            "• واریز 1000000\n"
            "• برداشت 500000\n"
            "• انتقال پول 2500000\n"
            "• انتقال پول 10000000 به @username\n\n"
            "مبلغ سقف ثابت ندارد؛ هر عددی تا موجودی بانک.\n\n"
            "برای انتقال با ریپلای روی پیام شخص بزن و بنویس:\n"
            "انتقال پول 2500000"
        ),
    },
    {
        "title": "🚗 خودرو",
        "text": (
            "از نمایشگاه خودرو بخر، در گاراژ نگه‌دار، "
            "در بازار بفروش یا به بازیکن دیگر هدیه بده.\n\n"
            "هر خودرو شناسه یکتا دارد."
        ),
    },
    {
        "title": "⚔️ مبارزه",
        "text": (
            "روی پیام بازیکن ریپلای کن و بنویس:\n"
            "حمله\n\n"
            "سپس نوع حمله و قسمت بدن را انتخاب کن.\n"
            "آسیب می‌تواند کبودی، زخم، خونریزی، دررفتگی یا شکستگی ایجاد کند."
        ),
    },
    {
        "title": "💼 شغل",
        "text": (
            "آرایشگری و مکانیکی در دسترس است.\n"
            "با کار کردن XP شغلی می‌گیری و رتبه بالاتر می‌روی.\n"
            "رتبه بالاتر = مشتری و درآمد بیشتر."
        ),
    },
    {
        "title": "📈 XP و Level",
        "text": (
            "کار، مبارزه و بعضی فعالیت‌ها XP می‌دهند.\n"
            "با افزایش Level امکانات و تجهیزات جدید باز می‌شود."
        ),
    },
]

# ══════════════════════════════════════════════════════════════
# HEALTH SERVER
# ══════════════════════════════════════════════════════════════


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(b"UNDERCITY is alive")

    def log_message(self, format, *args):
        return


def run_health_server():
    server = HTTPServer(("0.0.0.0", PORT), HealthHandler)
    server.serve_forever()


# ══════════════════════════════════════════════════════════════
# DATABASE
# ══════════════════════════════════════════════════════════════


def load_players() -> dict:
    with DATA_LOCK:
        try:
            with open(PLAYERS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            pass
        return {}


def save_players(players: dict) -> None:
    with DATA_LOCK:
        tmp = PLAYERS_FILE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(players, f, ensure_ascii=False, indent=2)
        os.replace(tmp, PLAYERS_FILE)


# ══════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════


def normalize_digits(text: str) -> str:
    if not text:
        return ""
    table = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")
    return str(text).translate(table)


def parse_amount(value) -> int:
    try:
        value = normalize_digits(str(value))
        value = value.replace(",", "").replace("_", "").replace("٬", "").strip()
        return max(0, int(value))
    except Exception:
        return 0


def is_master(user_id) -> bool:
    try:
        return int(user_id) == MASTER_USER_ID
    except Exception:
        return False


def actor_name(user_id: int, fallback: str = "بازیکن") -> str:
    if is_master(user_id):
        return "Master"
    return fallback or "بازیکن"


def resolve_player_identifier(identifier: str, players: dict):
    identifier = str(identifier).strip()

    if identifier.startswith("@"):
        key, player = find_player_by_username(players, identifier)
        return key, player

    if identifier.isdigit():
        key = str(int(identifier))
        return (key, players[key]) if key in players else (None, None)

    key, player = find_player_by_username(players, identifier)
    return key, player


def make_id(prefix: str = "ID") -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12].upper()}"


def timestamp() -> int:
    return int(time.time())


def cooldown_remaining(player: dict, action: str, cooldown: int) -> int:
    now = timestamp()
    last = int(player.get("last_actions", {}).get(action, 0))

    remaining = cooldown - (now - last)

    if remaining > 0:
        return remaining

    return 0


def start_cooldown(player: dict, action: str) -> None:
    player.setdefault("last_actions", {})
    player["last_actions"][action] = timestamp()


def update_player_life(player: dict) -> None:
    if not player.get("dead"):
        return

    if timestamp() < int(player.get("dead_until", 0)):
        return

    player["dead"] = False
    player["dead_until"] = 0

    body = player.setdefault("body", default_body())

    body["hp"] = body.get("max_hp", 100)

    for part_id, part_data in body.get("parts", {}).items():
        if isinstance(part_data, dict):
            part_data["hp"] = part_data.get("max_hp", 0)


def xp_required(level: int) -> int:

            
    return 100 + (max(1, level) - 1) * 75


def format_num(n) -> str:
    try:
        return f"{int(n):,}"
    except Exception:
        return str(n)


def esc(text) -> str:
    """Escape text for Telegram HTML parse_mode."""
    if text is None:
        return ""
    return html_module.escape(str(text))


async def safe_edit_message(query, text: str, **kwargs):
    """edit_message_text without crashing on 'Message is not modified'."""
    try:
        await query.edit_message_text(text, **kwargs)
    except BadRequest as e:
        msg = str(e).lower()
        if "message is not modified" in msg:
            try:
                await query.answer()
            except Exception:
                pass
            return
        if "message to edit not found" in msg or "message can't be edited" in msg:
            try:
                await query.message.reply_text(text, **kwargs)
            except Exception:
                pass
            return
        raise
    except Forbidden:
        pass


# ══════════════════════════════════════════════════════════════
# PLAYER SYSTEM
# ══════════════════════════════════════════════════════════════


def default_body() -> dict:
    parts = {}
    for pid, data in BODY_PARTS.items():
        parts[pid] = {
            "hp": data["max_hp"],
            "max_hp": data["max_hp"],
        }
    return {
        "hp": 100,
        "max_hp": 100,
        "parts": parts,
        "injuries": [],
    }


def create_player(user: User) -> dict:
    master = is_master(user.id)
    return {
        "user_id": int(user.id),
        "name": user.first_name or "Player",
        "username": user.username or "",
        "level": 1,
        "xp": 0,
        "cash": MASTER_CASH if master else STARTING_CASH,
        "bank_balance": MASTER_BANK if master else 0,
        "credit_score": 500,
        "reputation": 0,
        "banned": False,
        "ban_reason": "",
        "loan": 0,
        "location": "south",
        "transactions": [],
        "vehicles": [],
        "properties": [],
        "businesses": [],
        "courses_done": [],
        "body": default_body(),
        "equipment": {
            "clothes": "normal_clothes",
            "armor": None,
            "weapons": [],
        },
        "jobs": {},
        "vehicle_offers": [],
        "market_listings": [],
        "direct_deals": [],
        "vehicle_history": [],
        "stats": {
            "fights": 0,
            "hits": 0,
            "wins": 0,
            "losses": 0,
            "damage_dealt": 0,
            "damage_received": 0,
            "vehicles_bought": 0,
            "vehicles_sold": 0,
            "jobs_done": 0,
        },
        "pending": None,
        "last_actions": {},
        "dead": False,
        "dead_until": 0,
        "created_at": timestamp(),
    }


def normalize_player(player: dict, user: Optional[User] = None) -> dict:
    if not isinstance(player, dict):
        player = {}

    if user:
        player["name"] = user.first_name or player.get("name") or "Player"
        player["username"] = user.username or player.get("username") or ""
        player["user_id"] = int(user.id)

    defaults = {
        "name": "Player",
        "username": "",
        "level": 1,
        "xp": 0,
        "cash": STARTING_CASH,
        "bank_balance": 0,
        "credit_score": 500,
        "reputation": 0,
        "banned": False,
        "ban_reason": "",
        "loan": 0,
        "location": "south",
        "transactions": [],
        "vehicles": [],
        "properties": [],
        "businesses": [],
        "courses_done": [],
        "body": {},
        "equipment": {},
        "jobs": {},
        "vehicle_offers": [],
        "market_listings": [],
        "direct_deals": [],
        "vehicle_history": [],
        "stats": {},
        "pending": None,
        "last_actions": {},
        "dead": False,
        "dead_until": 0,
    }

    for k, v in defaults.items():
        if k not in player:
            player[k] = copy.deepcopy(v) if isinstance(v, (list, dict)) else v

    for key in (
        "transactions",
        "vehicles",
        "properties",
        "businesses",
        "vehicle_offers",
        "market_listings",
        "direct_deals",
        "vehicle_history",
        "courses_done",
    ):
        if not isinstance(player.get(key), list):
            player[key] = []

    # مهاجرت نام قدیمی منطقه
    if player.get("location") in ("پایین‌شهر", "Undercity", ""):
        player["location"] = "south"
    if player.get("location") not in DISTRICTS:
        player["location"] = "south"

    for key in ("body", "equipment", "jobs", "stats", "last_actions"):
        if not isinstance(player.get(key), dict):
            player[key] = {}

    if not player["body"].get("parts"):
        player["body"] = default_body()
    else:
        player["body"].setdefault("hp", 100)
        player["body"].setdefault("max_hp", 100)
        player["body"].setdefault("injuries", [])
        for pid, data in BODY_PARTS.items():
            if pid not in player["body"]["parts"]:
                player["body"]["parts"][pid] = {
                    "hp": data["max_hp"],
                    "max_hp": data["max_hp"],
                }

    player["equipment"].setdefault("clothes", "normal_clothes")
    player["equipment"].setdefault("armor", None)
    player["equipment"].setdefault("weapons", [])

    for job_id in JOBS:
        if not isinstance(player["jobs"].get(job_id), dict):
            player["jobs"][job_id] = {
                "xp": 0,
                "rank": 0,
                "sessions": 0,
                "income": 0,
                "loss": 0,
                "customers": 0,
            }

    for sk in (
        "fights",
        "hits",
        "wins",
        "losses",
        "damage_dealt",
        "damage_received",
        "vehicles_bought",
        "vehicles_sold",
        "jobs_done",
    ):
        player["stats"].setdefault(sk, 0)

    try:
        player["level"] = max(1, int(player.get("level", 1)))
        player["xp"] = max(0, int(player.get("xp", 0)))
        player["cash"] = max(0, int(player.get("cash", 0)))
        player["bank_balance"] = max(0, int(player.get("bank_balance", 0)))
    except Exception:
        player["level"] = 1
        player["xp"] = 0
        player["cash"] = STARTING_CASH
        player["bank_balance"] = 0

    if is_master(player.get("user_id")):
        player["name"] = "Master"
        player["level"] = 99
        player["xp"] = 0
        player["cash"] = MASTER_CASH
        player["bank_balance"] = MASTER_BANK
        player["banned"] = False
        player["ban_reason"] = ""

    return player


def get_player(user: User) -> dict:
    """بارگذاری یا ساخت بازیکن + ذخیره خودکار"""
    players = load_players()
    key = str(user.id)

    if key not in players:
        player = create_player(user)
        players[key] = player
        save_players(players)
        return player

    player = normalize_player(players[key], user)
    players[key] = player
    save_players(players)
    return player


def get_player_by_id(user_id: int) -> Optional[dict]:
    players = load_players()
    key = str(user_id)
    if key not in players:
        return None
    return normalize_player(players[key])


def save_player(user_id: int, player: dict) -> None:
    players = load_players()
    players[str(user_id)] = normalize_player(player)
    save_players(players)


def add_xp(player: dict, amount: int) -> int:
    amount = max(0, int(amount))
    player["xp"] = player.get("xp", 0) + amount
    level_ups = 0
    while player["xp"] >= xp_required(player.get("level", 1)):
        req = xp_required(player.get("level", 1))
        player["xp"] -= req
        player["level"] = player.get("level", 1) + 1
        level_ups += 1
    return level_ups


def add_transaction(
    player: dict,
    tx_type: str,
    amount: int,
    description: str,
    tx_id: Optional[str] = None,
    direction: Optional[str] = None,
    reference_id: Optional[str] = None,
) -> bool:
    player.setdefault("transactions", [])
    tx_id = tx_id or make_id("TX")

    for old in player["transactions"]:
        if old.get("id") == tx_id:
            return False
        if reference_id and old.get("reference_id") == reference_id:
            return False

    if direction is None:
        incoming = {
            "transfer_received",
            "deposit",
            "sale_received",
            "vehicle_received",
            "job_income",
            "fine_received",
            "vehicle_sale",
            "vehicle_sale_player",
            "vehicle_market_sale",
            "vehicle_gift_received",
        }
        direction = "in" if tx_type in incoming else "out"

    entry = {
        "id": tx_id,
        "type": tx_type,
        "amount": int(amount),
        "description": description,
        "direction": direction,
        "time": timestamp(),
    }
    if reference_id:
        entry["reference_id"] = reference_id

    player["transactions"].append(entry)
    player["transactions"] = player["transactions"][-100:]
    return True


# ══════════════════════════════════════════════════════════════
# MONEY HELPERS
# ══════════════════════════════════════════════════════════════


def can_spend(player: dict, amount: int, source: str = "bank") -> bool:
    amount = int(amount)
    if amount <= 0:
        return False
    if source == "cash":
        return player.get("cash", 0) >= amount
    return player.get("bank_balance", 0) >= amount


def spend_money(player: dict, amount: int, source: str = "bank") -> bool:
    amount = int(amount)
    if not can_spend(player, amount, source):
        return False
    if source == "cash":
        player["cash"] -= amount
    else:
        player["bank_balance"] -= amount
    return True


def add_money(player: dict, amount: int, dest: str = "bank") -> bool:
    amount = int(amount)
    if amount <= 0:
        return False
    if dest == "cash":
        player["cash"] = player.get("cash", 0) + amount
    else:
        player["bank_balance"] = player.get("bank_balance", 0) + amount
    return True


def execute_money_transfer(
    sender_id: int, receiver_id: int, amount: int
) -> tuple[bool, Any]:
    amount = int(amount)

    if amount <= 0:
        return False, "مبلغ نامعتبر است."

    if int(sender_id) == int(receiver_id):
        return False, "نمی‌توانی به خودت پول انتقال بدهی."

    with DATA_LOCK:
        players = load_players()
        s_key = str(sender_id)
        r_key = str(receiver_id)

        if s_key not in players:
            return False, "حساب فرستنده پیدا نشد."

        if r_key not in players:
            return False, "حساب گیرنده پیدا نشد."

        sender = normalize_player(players[s_key])
        receiver = normalize_player(players[r_key])

        bank = int(sender.get("bank_balance", 0))
        cash = int(sender.get("cash", 0))

        if bank + cash < amount:
            return False, "موجودی کافی نیست. بانک و نقد با هم کم می‌شود."

        from_bank = min(bank, amount)
        from_cash = amount - from_bank

        sender["bank_balance"] = bank - from_bank
        sender["cash"] = cash - from_cash

        receiver["bank_balance"] = (
            int(receiver.get("bank_balance", 0)) + amount
        )

        transfer_id = make_id("TRF")

        add_transaction(
            sender,
            "transfer_sent",
            amount,
            f"انتقال به {actor_name(receiver_id, receiver.get('name', 'بازیکن'))}",
            direction="out",
            reference_id=transfer_id,
        )

        players[s_key] = sender
        players[r_key] = receiver
        save_players(players)

        return True, {
            "transfer_id": transfer_id,
            "amount": amount,
            "sender": sender,
            "receiver": receiver,
        }


# ══════════════════════════════════════════════════════════════
# VEHICLE HELPERS
# ══════════════════════════════════════════════════════════════


def vehicle_name(vehicle: dict) -> str:
    if not vehicle:
        return "خودرو"
    if vehicle.get("name"):
        return str(vehicle["name"])
    brand = vehicle.get("brand", "")
    model = vehicle.get("model", "")
    year = vehicle.get("year", "")
    result = f"{brand} {model}".strip()
    if year:
        result += f" {year}"
    return result or "خودرو"


def vehicle_details_text(vehicle: dict) -> str:
    if not vehicle:
        return "خودرو پیدا نشد."
    name = esc(vehicle_name(vehicle))
    lines = [
        f"🚘 <b>{name}</b>",
        "",
        f"📅 سال: {esc(vehicle.get('year', '-'))}",
        f"🛣 کارکرد: {format_num(vehicle.get('mileage', 0))} km",
        f"🔧 وضعیت: {esc(vehicle.get('condition', '-'))}",
        f"🎨 رنگ: {esc(vehicle.get('color', '-'))}",
        f"⚙️ موتور: {esc(vehicle.get('engine', '-'))}",
        f"⚡ قدرت: {esc(vehicle.get('power', '-'))}",
        f"🔄 گیربکس: {esc(vehicle.get('transmission', '-'))}",
        f"🏁 تیونینگ: {esc(vehicle.get('tuning', 'فابریک'))}",
        f"💰 قیمت: {format_num(vehicle.get('price', 0))}",
        "",
        f"🆔 {esc(vehicle.get('id', '-'))}",
    ]
    return "\n".join(lines)


def create_vehicle_from_catalog(catalog_id: str, owner_id: int) -> dict:
    catalog = VEHICLE_CATALOG.get(str(catalog_id))
    if not catalog:
        raise ValueError("catalog not found")
    vehicle = copy.deepcopy(catalog)
    vehicle["id"] = make_id("CAR")
    vehicle["owner_id"] = int(owner_id)
    vehicle["purchased_at"] = timestamp()
    vehicle["catalog_id"] = str(catalog_id)
    return vehicle


def get_vehicle_by_id(player: dict, vehicle_id: str) -> Optional[dict]:
    for v in player.get("vehicles", []):
        if str(v.get("id")) == str(vehicle_id):
            return v
    return None


def remove_vehicle(player: dict, vehicle_id: str) -> bool:
    before = len(player.get("vehicles", []))
    player["vehicles"] = [
        v for v in player.get("vehicles", []) if str(v.get("id")) != str(vehicle_id)
    ]
    return len(player["vehicles"]) < before


def find_player_by_username(players: dict, username: str) -> tuple[Optional[str], Optional[dict]]:
    username = username.lstrip("@").lower()
    for key, p in players.items():
        saved = str(p.get("username", "")).lstrip("@").lower()
        if saved and saved == username:
            return key, p
    return None, None


# ══════════════════════════════════════════════════════════════
# KEYBOARDS
# ══════════════════════════════════════════════════════════════


def main_menu_keyboard(user_id: int, master: bool = False) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton("👤 پروفایل", callback_data=f"profile|{user_id}"),
            InlineKeyboardButton("💰 کیف پول", callback_data=f"wallet|{user_id}"),
        ],
        [
            InlineKeyboardButton("🚗 خودروها", callback_data=f"vehicles|{user_id}"),
            InlineKeyboardButton("💼 مشاغل", callback_data=f"jobs|{user_id}"),
        ],
        [
            InlineKeyboardButton("🏠 املاک", callback_data=f"properties|{user_id}"),
            InlineKeyboardButton("🗺️ مناطق", callback_data=f"districts|{user_id}"),
        ],
        [
            InlineKeyboardButton("🎓 دوره‌ها", callback_data=f"courses|{user_id}"),
            InlineKeyboardButton("⚔️ مبارزه", callback_data=f"combat|{user_id}"),
        ],
        [
            InlineKeyboardButton("🏥 کلینیک", callback_data=f"clinic|{user_id}"),
            InlineKeyboardButton("📖 راهنما", callback_data=f"help|0|{user_id}"),
        ],
        [
            InlineKeyboardButton(
                "💸 راهنمای انتقال پول",
                callback_data=f"transfer_help|{user_id}",
            ),
        ],
    ]
    if master:
        rows.append(
            [InlineKeyboardButton("👑 پنل Master", callback_data=f"master_panel|{user_id}")]
        )
    return InlineKeyboardMarkup(rows)


def back_button(user_id: int, target: str = "main") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("🔙 بازگشت", callback_data=f"{target}|{user_id}")]]
    )


def wallet_menu(user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("📜 تراکنش‌ها", callback_data=f"transactions|{user_id}"),
            ],
            [
                InlineKeyboardButton("🔙 منوی اصلی", callback_data=f"main|{user_id}"),
            ],
        ]
    )


def help_keyboard(user_id: int, page: int) -> InlineKeyboardMarkup:
    total = len(HELP_PAGES)
    nav = []
    if page > 0:
        nav.append(
            InlineKeyboardButton("⬅️ قبلی", callback_data=f"help|{page - 1}|{user_id}")
        )
    nav.append(
        InlineKeyboardButton(f"📖 {page + 1}/{total}", callback_data=f"help|noop|{user_id}")
    )
    if page < total - 1:
        nav.append(
            InlineKeyboardButton("بعدی ➡️", callback_data=f"help|{page + 1}|{user_id}")
        )
    return InlineKeyboardMarkup(
        [nav, [InlineKeyboardButton("🏙️ منوی اصلی", callback_data=f"main|{user_id}")]]
    )


def vehicles_menu(user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("🏪 نمایشگاه", callback_data=f"showroom|{user_id}"),
                InlineKeyboardButton("🚗 گاراژ", callback_data=f"garage|{user_id}"),
            ],
            [
                InlineKeyboardButton("🤝 بازار بازیکنان", callback_data=f"carmarket|{user_id}"),
            ],
            [
                InlineKeyboardButton("🔙 منوی اصلی", callback_data=f"main|{user_id}"),
            ],
        ]
    )


def jobs_menu(user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("💈 آرایشگری", callback_data=f"job|barber|{user_id}"),
                InlineKeyboardButton("🔧 مکانیکی", callback_data=f"job|mechanic|{user_id}"),
            ],
            [
                InlineKeyboardButton("📊 مهارت‌ها", callback_data=f"job_skills|{user_id}"),
            ],
            [
                InlineKeyboardButton("🔙 منوی اصلی", callback_data=f"main|{user_id}"),
            ],
        ]
    )


def combat_menu(user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("🏥 کلینیک", callback_data=f"clinic|{user_id}"),
                InlineKeyboardButton("🩸 آسیب‌ها", callback_data=f"injuries|{user_id}"),
            ],
            [
                InlineKeyboardButton("🔙 منوی اصلی", callback_data=f"main|{user_id}"),
            ],
        ]
    )


# ══════════════════════════════════════════════════════════════
# TEXT BUILDERS
# ══════════════════════════════════════════════════════════════


def profile_text(player: dict) -> str:
    name = esc(player.get("name", "بازیکن"))
    username = player.get("username") or "ندارد"

    if username != "ندارد" and not username.startswith("@"):
        username = f"@{username}"

    username = esc(username)

    user_id = player.get("user_id", "نامشخص")
    level = player.get("level", 1)
    xp = player.get("xp", 0)

    next_xp = xp_required(level)

    body = player.get("body", {})
    hp = body.get("hp", 100)
    max_hp = body.get("max_hp", 100)

    loc_key = player.get("location", "south")
    loc_name = DISTRICTS.get(loc_key, {}).get("name", loc_key)

    return (
        "👤 <b>پروفایل شخصیت</b>\n\n"
        f"🆔 ID عددی: <code>{user_id}</code>\n"
        f"🪪 نام: {name}\n"
        f"🔹 Username: {username}\n\n"
        f"⭐ Level: {level}\n"
        f"📈 XP: {format_num(xp)} / {format_num(next_xp)}\n\n"
        f"❤️ سلامت: {hp} / {max_hp}\n"
        f"🗺️ منطقه: {loc_name}\n"
        f"💵 پول نقد: {format_num(player.get('cash', 0))}\n"
        f"🏦 بانک: {format_num(player.get('bank_balance', 0))}\n"
        f"💳 اعتبار: {player.get('credit_score', 0)}\n"
        f"⭐ شهرت: {player.get('reputation', 0)}\n"
        f"🚫 بن: {'بله' if player.get('banned') else 'خیر'}\n\n"
        f"🚗 خودروها: {len(player.get('vehicles', []))}\n"
        f"🏠 املاک: {len(player.get('properties', []))}\n"
        f"🏪 کسب‌وکارها: {len(player.get('businesses', []))}\n"
        f"💼 مشاغل: {len(player.get('jobs', {}))}\n"
        f"📜 تراکنش‌ها: {len(player.get('transactions', []))}"
    )


def wallet_text(player: dict) -> str:
    cash = player.get("cash", 0)
    bank = player.get("bank_balance", 0)
    return (
        "💰 <b>کیف پول</b>\n\n"
        f"💵 پول نقد:\n{format_num(cash)}\n\n"
        f"🏦 موجودی بانک:\n{format_num(bank)}\n\n"
        f"💎 دارایی نقدی:\n{format_num(cash + bank)}\n\n"
        "برای واریز/برداشت بنویس:\n"
        "واریز 1000000\n"
        "برداشت 500000"
    )


def transaction_text(player: dict, limit: int = 12) -> str:
    txs = player.get("transactions", [])
    if not txs:
        return "📜 <b>تاریخچه تراکنش‌ها</b>\n\nهنوز تراکنشی ثبت نشده."
    lines = ["📜 <b>تاریخچه تراکنش‌ها</b>", ""]
    for tx in reversed(txs[-limit:]):
        direction = tx.get("direction", "info")
        amount = tx.get("amount", 0)
        if direction == "in":
            icon, amt = "🟢", f"+{format_num(amount)}"
        elif direction == "out":
            icon, amt = "🔴", f"-{format_num(amount)}"
        else:
            icon, amt = "⚪", format_num(amount)
        lines.append(f"{icon} {amt}")
        if tx.get("description"):
            lines.append(f"   {tx['description']}")
        lines.append("")
    return "\n".join(lines)


def help_page_text(page: int) -> str:
    data = HELP_PAGES[page]
    return (
        f"{data['title']}\n\n"
        f"{data['text']}\n\n"
        "━━━━━━━━━━━━━━\n"
        f"صفحه {page + 1} از {len(HELP_PAGES)}"
    )


# ══════════════════════════════════════════════════════════════
# CALLBACK SAFETY
# ══════════════════════════════════════════════════════════════


def callback_owner_id(data: str) -> Optional[int]:
    if not data:
        return None
    parts = data.split("|")
    try:
        return int(parts[-1])
    except Exception:
        return None


def is_owner(query) -> bool:
    owner = callback_owner_id(query.data or "")
    if owner is None or not query.from_user:
        return False
    return int(owner) == int(query.from_user.id)


async def safe_answer(query, text: Optional[str] = None, alert: bool = False):
    try:
        if text:
            await query.answer(text, show_alert=alert)
        else:
            await query.answer()
    except Exception:
        pass


# ══════════════════════════════════════════════════════════════
# COMMANDS
# ══════════════════════════════════════════════════════════════


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user:
        return
    player = get_player(user)
    if player.get("banned"):
        await update.message.reply_text(
            f"🚫 حساب شما مسدود است.\n\nدلیل: {player.get('ban_reason', 'بدون توضیح')}"
        )
        return

    name = player.get("name", user.first_name or "بازیکن")
    master_line = "\n👑 دسترسی MASTER فعال است.\n" if is_master(user.id) else ""
    text = (
        f"درود {name} 👋{master_line}\n"
        "🌃 به UNDERCITY خوش آمدی\n\n"
        "یک شهر زنده و بی‌رحم که در آن می‌توانی از هیچ شروع کنی "
        "و به قدرتمندترین فرد شهر تبدیل شوی.\n\n"
        "💰 پول دربیاور\n"
        "با کار، تجارت، سرمایه‌گذاری، خرید و فروش و فرصت‌های مختلف ثروت بساز.\n\n"
        "🏠 املاک و دارایی\n"
        "خانه، آپارتمان، زمین، ساختمان و دارایی‌های ارزشمند بخر و مدیریت کن.\n\n"
        "🏢 کسب‌وکار و صنعت\n"
        "کسب‌وکار راه بینداز، کارخانه بساز، پروژه اجرا کن و از اقتصاد شهر سود ببر.\n\n"
        "📈 خرید، فروش و دلالی\n"
        "در بازار شهر معامله کن، قیمت‌ها را دنبال کن، کالا و دارایی بخر و بفروش "
        "و از اختلاف قیمت‌ها سود ببر.\n\n"
        "🚗 وسایل نقلیه زمینی\n"
        "از خودروهای شهری و اسپرت گرفته تا خودروهای سنگین، زرهی، موتورسیکلت "
        "و وسایل نقلیه ویژه را خریداری، فروش و ارتقا بده.\n\n"
        "🚤 وسایل نقلیه آبی\n"
        "قایق، کشتی و دیگر وسایل نقلیه دریایی را به دست بیاور "
        "و در آب‌های UNDERCITY از آن‌ها استفاده کن.\n\n"
        "✈️ وسایل نقلیه هوایی\n"
        "هلیکوپتر، هواپیما، جت و دیگر وسایل پرنده را تهیه کن "
        "و آسمان شهر را زیر سلطه خودت دربیاور.\n\n"
        "🌊🚙 وسایل نقلیه آبی‌خاکی\n"
        "وسایل نقلیه مخصوص خشکی و آب را به دست بیاور "
        "و به مناطقی دسترسی پیدا کن که دیگران نمی‌توانند.\n\n"
        "🕶️ دنیای زیرزمینی\n"
        "وارد فعالیت‌های خلافکارانه شو؛ از معاملات غیرقانونی و سرقت گرفته "
        "تا مأموریت‌های خطرناک و عملیات گروهی.\n\n"
        "🔫 درگیری و نبرد\n"
        "در نبردهای بازی شرکت کن و از تجهیزات مختلف استفاده کن؛ "
        "از سلاح‌های سبک و سنگین گرفته تا خودروهای زرهی، تانک، "
        "هلیکوپتر، جنگنده، ناو و دیگر تجهیزات نظامی.\n\n"
        "🤝 باند و اتحاد\n"
        "گروه خودت را تشکیل بده، متحد پیدا کن، قلمرو و نفوذ به دست بیاور "
        "و با گروه‌های رقیب رقابت کن.\n\n"
        "🏥 درمانگاه و مراقبت پزشکی\n"
        "برای آسیب‌ها و وضعیت جسمانی شخصیتت به مراکز درمانی شهر مراجعه کن "
        "و شرایط خودت را مدیریت کن.\n\n"
        "💊 داروخانه\n"
        "اقلام و داروهای موردنیاز شخصیتت را از داروخانه‌های شهر تهیه کن "
        "و برای شرایط مختلف آماده باش.\n\n"
        "🌆 شهر را بشناس\n"
        "مناطق مختلف شهر، بازارها، مراکز صنعتی، مناطق ثروتمند، "
        "محله‌های خطرناک و مکان‌های مخفی را کشف کن.\n\n"
        "👑 هدف نهایی\n"
        "ثروت، قدرت، نفوذ و اعتبار خودت را افزایش بده و امپراتوری خودت را بساز.\n\n"
        "⚠️ UNDERCITY هنوز در حال توسعه است...\n\n"
        "هر انتخابی که می‌کنی، می‌تواند مسیر بازی تو را تغییر دهد.\n\n"
        "🏙️ شهر منتظر توست.\n\n"
        "━━━━━━━━━━━━━━\n"
        "💡 منوی اصلی: منو\n"
        "📖 راهنما: /help"
    )
    await update.message.reply_text(text)


async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user:
        return
    player = get_player(user)
    if player.get("banned"):
        await update.message.reply_text("🚫 حساب شما مسدود است.")
        return
    await update.message.reply_text(
        "🏙️ <b>منوی اصلی UNDERCITY</b>\n\nیکی از بخش‌ها را انتخاب کن:",
        parse_mode="HTML",
        reply_markup=main_menu_keyboard(user.id, is_master(user.id)),
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user:
        return
    player = get_player(user)
    if player.get("banned"):
        await update.message.reply_text("🚫 حساب شما مسدود است.")
        return
    await update.message.reply_text(
        help_page_text(0),
        reply_markup=help_keyboard(user.id, 0),
    )


async def jobs_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user:
        return
    player = get_player(user)
    if player.get("banned"):
        await update.message.reply_text("🚫 حساب شما مسدود است.")
        return
    await update.message.reply_text(
        "💼 <b>مرکز مشاغل</b>\n\nیک شغل انتخاب کن و کار کن.",
        parse_mode="HTML",
        reply_markup=jobs_menu(user.id),
    )


async def cars_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user:
        return
    player = get_player(user)
    if player.get("banned"):
        await update.message.reply_text("🚫 حساب شما مسدود است.")
        return
    await update.message.reply_text(
        f"🚘 <b>مرکز خودرو</b>\n\nتعداد خودروهای شما: {len(player.get('vehicles', []))}",
        parse_mode="HTML",
        reply_markup=vehicles_menu(user.id),
    )


async def panel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user or not is_master(user.id):
        await update.message.reply_text("❌ این دستور فقط برای Master است.")
        return
    await show_master_panel(update, context)


# ══════════════════════════════════════════════════════════════
# SHOW HELPERS (callback + message)
# ══════════════════════════════════════════════════════════════


async def show_main_menu(query, user_id: int):
    await safe_edit_message(
        query,
        "🏙️ <b>منوی اصلی UNDERCITY</b>\n\nیکی از بخش‌ها را انتخاب کن:",
        parse_mode="HTML",
        reply_markup=main_menu_keyboard(user_id, is_master(user_id)),
    )


async def show_profile(query, user_id: int):
    player = get_player_by_id(user_id) or get_player(query.from_user)
    await safe_edit_message(
        query,
        profile_text(player),
        parse_mode="HTML",
        reply_markup=back_button(user_id, "main"),
    )


async def show_wallet(query, user_id: int):
    player = get_player_by_id(user_id) or get_player(query.from_user)
    await safe_edit_message(
        query,
        wallet_text(player),
        parse_mode="HTML",
        reply_markup=wallet_menu(user_id),
    )


async def show_transactions(query, user_id: int):
    player = get_player_by_id(user_id) or get_player(query.from_user)
    await safe_edit_message(
        query,
        transaction_text(player),
        parse_mode="HTML",
        reply_markup=back_button(user_id, "wallet"),
    )


# ══════════════════════════════════════════════════════════════
# VEHICLE ACTIONS
# ══════════════════════════════════════════════════════════════


async def show_showroom(query, user_id: int):
    rows = []
    for cid, v in VEHICLE_CATALOG.items():
        name = f"{v.get('brand', '')} {v.get('model', '')}"
        rows.append(
            [
                InlineKeyboardButton(
                    f"🚗 {name} — {format_num(v.get('price', 0))}",
                    callback_data=f"showcar|{cid}|{user_id}",
                )
            ]
        )
    rows.append([InlineKeyboardButton("🔙 خودروها", callback_data=f"vehicles|{user_id}")])
    await query.edit_message_text(
        "🏢 <b>نمایشگاه خودرو</b>\n\nخودروی موردنظر را انتخاب کن:",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(rows),
    )


async def show_catalog_vehicle(query, catalog_id: str, user_id: int):
    catalog = VEHICLE_CATALOG.get(str(catalog_id))
    if not catalog:
        await safe_answer(query, "خودرو پیدا نشد.", True)
        return
    text = vehicle_details_text({**catalog, "id": f"catalog-{catalog_id}"})
    kb = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "💳 خرید خودرو",
                    callback_data=f"buycar|{catalog_id}|{user_id}",
                )
            ],
            [
                InlineKeyboardButton("🔙 نمایشگاه", callback_data=f"showroom|{user_id}"),
                InlineKeyboardButton("🚗 خودروها", callback_data=f"vehicles|{user_id}"),
            ],
        ]
    )
    await query.edit_message_text(text, parse_mode="HTML", reply_markup=kb)


def execute_vehicle_purchase(buyer_id: int, catalog_id: str) -> tuple[bool, Any]:
    with DATA_LOCK:
        players = load_players()
        key = str(buyer_id)
        if key not in players:
            return False, "حساب پیدا نشد."

        buyer = normalize_player(players[key])
        if buyer.get("banned"):
            return False, "حساب شما مسدود است."

        catalog = VEHICLE_CATALOG.get(str(catalog_id))
        if not catalog:
            return False, "خودرو پیدا نشد."

        price = int(catalog.get("price", 0))
        if price <= 0:
            return False, "قیمت نامعتبر است."
        if buyer.get("bank_balance", 0) < price:
            return False, "موجودی بانک کافی نیست."

        ref = make_id("PUR")
        # جلوگیری از خرید تکراری با همان reference (idempotency ساده)
        for tx in buyer.get("transactions", []):
            if tx.get("reference_id") == ref:
                return False, "این خرید قبلاً انجام شده."

        buyer["bank_balance"] -= price
        vehicle = create_vehicle_from_catalog(catalog_id, buyer_id)
        vehicle["purchase_price"] = price
        vehicle["purchase_reference"] = ref
        buyer.setdefault("vehicles", []).append(vehicle)
        buyer["stats"]["vehicles_bought"] = buyer["stats"].get("vehicles_bought", 0) + 1

        add_transaction(
            buyer,
            "vehicle_purchase",
            price,
            f"خرید {vehicle_name(vehicle)}",
            direction="out",
            reference_id=ref,
        )

        # فروش به Master (اگر خریدار Master نباشد)
        if int(buyer_id) != MASTER_USER_ID:
            m_key = str(MASTER_USER_ID)
            if m_key not in players:
                # ساخت حساب master ساده
                players[m_key] = {
                    "name": "Master",
                    "username": "",
                    "level": 99,
                    "xp": 0,
                    "cash": MASTER_CASH,
                    "bank_balance": MASTER_BANK,
                    "transactions": [],
                    "vehicles": [],
                    "banned": False,
                    "stats": {},
                    "body": default_body(),
                    "equipment": {},
                    "jobs": {},
                }
            master = normalize_player(players[m_key])
            master["bank_balance"] = master.get("bank_balance", 0) + price
            add_transaction(
                master,
                "vehicle_sale",
                price,
                f"فروش {vehicle_name(vehicle)} به {buyer_id}",
                direction="in",
                reference_id=ref,
            )
            players[m_key] = master

        players[key] = buyer
        save_players(players)
        return True, {"vehicle": vehicle, "price": price, "buyer": buyer}


async def buy_vehicle(query, catalog_id: str, user_id: int):
    success, result = execute_vehicle_purchase(user_id, catalog_id)
    if not success:
        await safe_answer(query, str(result), True)
        return
    vehicle = result["vehicle"]
    price = result["price"]
    await safe_answer(query, "✅ خودرو خریداری شد.")
    await query.edit_message_text(
        "✅ <b>خرید موفق</b>\n\n"
        f"🚗 {vehicle_name(vehicle)}\n"
        f"💰 قیمت: {format_num(price)}\n"
        f"🆔 {vehicle.get('id')}\n\n"
        "خودرو به گاراژ شما اضافه شد.",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("🚗 گاراژ من", callback_data=f"garage|{user_id}")],
                [InlineKeyboardButton("🏙️ منوی اصلی", callback_data=f"main|{user_id}")],
            ]
        ),
    )


async def show_garage(query, user_id: int):
    player = get_player_by_id(user_id) or get_player(query.from_user)
    vehicles = player.get("vehicles", [])
    if not vehicles:
        await query.edit_message_text(
            "🚗 <b>گاراژ من</b>\n\nگاراژ شما خالی است.\nاز نمایشگاه می‌توانی خودرو بخری.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("🏪 نمایشگاه", callback_data=f"showroom|{user_id}")],
                    [InlineKeyboardButton("🔙 خودروها", callback_data=f"vehicles|{user_id}")],
                ]
            ),
        )
        return

    lines = [f"🚗 <b>گاراژ من</b>\n\nتعداد: {len(vehicles)}\n"]
    rows = []
    for i, v in enumerate(vehicles, 1):
        lines.append(
            f"{i}. {vehicle_name(v)}\n   🆔 {v.get('id')}\n   💰 {format_num(v.get('price', 0))}\n"
        )
        rows.append(
            [
                InlineKeyboardButton(
                    f"🚘 {vehicle_name(v)[:28]}",
                    callback_data=f"mycar|{v.get('id')}|{user_id}",
                )
            ]
        )
    rows.append([InlineKeyboardButton("🔙 خودروها", callback_data=f"vehicles|{user_id}")])
    await query.edit_message_text(
        "\n".join(lines),
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(rows),
    )


async def show_my_vehicle(query, vehicle_id: str, user_id: int):
    player = get_player_by_id(user_id) or get_player(query.from_user)
    vehicle = get_vehicle_by_id(player, vehicle_id)
    if not vehicle:
        await safe_answer(query, "این خودرو در گاراژ شما نیست.", True)
        return
    text = vehicle_details_text(vehicle) + "\n\n📌 وضعیت: متعلق به شما"
    kb = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "💰 فروش فوری",
                    callback_data=f"sellcar|{vehicle_id}|{user_id}",
                ),
                InlineKeyboardButton(
                    "🏷 آگهی بازار",
                    callback_data=f"listcar|{vehicle_id}|{user_id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    "🎁 انتقال / هدیه",
                    callback_data=f"giftcar|{vehicle_id}|{user_id}",
                ),
            ],
            [InlineKeyboardButton("🔙 گاراژ", callback_data=f"garage|{user_id}")],
        ]
    )
    await query.edit_message_text(text, parse_mode="HTML", reply_markup=kb)


def execute_instant_sell(seller_id: int, vehicle_id: str) -> tuple[bool, Any]:
    with DATA_LOCK:
        players = load_players()
        key = str(seller_id)
        if key not in players:
            return False, "حساب پیدا نشد."
        seller = normalize_player(players[key])
        vehicle = get_vehicle_by_id(seller, vehicle_id)
        if not vehicle:
            return False, "خودرو در گاراژ نیست."
        price = int(vehicle.get("price", 0))
        if price <= 0:
            return False, "قیمت نامعتبر است."

        op_id = hashlib.sha256(
            f"instant_sale:{vehicle_id}:{seller_id}".encode()
        ).hexdigest()[:24]
        for h in seller.get("vehicle_history", []):
            if h.get("operation_id") == op_id:
                return True, {"already_done": True, "price": price}

        if not remove_vehicle(seller, vehicle_id):
            return False, "حذف خودرو ناموفق بود."

        # فروش فوری با ۸۰٪ قیمت
        sale_price = max(1, int(price * 0.8))
        seller["bank_balance"] = seller.get("bank_balance", 0) + sale_price
        seller["stats"]["vehicles_sold"] = seller["stats"].get("vehicles_sold", 0) + 1

        seller.setdefault("vehicle_history", []).append(
            {
                "operation_id": op_id,
                "type": "instant_sale",
                "vehicle_id": vehicle_id,
                "timestamp": timestamp(),
            }
        )
        seller["vehicle_history"] = seller["vehicle_history"][-200:]

        add_transaction(
            seller,
            "vehicle_sale",
            sale_price,
            f"فروش فوری {vehicle_name(vehicle)}",
            direction="in",
            reference_id=op_id,
        )
        players[key] = seller
        save_players(players)
        return True, {"price": sale_price, "vehicle": vehicle, "already_done": False}


async def sell_car_instant(query, vehicle_id: str, user_id: int):
    success, result = execute_instant_sell(user_id, vehicle_id)
    if not success:
        await safe_answer(query, str(result), True)
        return
    if result.get("already_done"):
        await safe_answer(query, "این فروش قبلاً انجام شده.", True)
        return
    await safe_answer(query, "✅ فروخته شد.")
    await query.edit_message_text(
        f"✅ <b>فروش موفق</b>\n\n💰 مبلغ: {format_num(result['price'])}\n"
        "خودرو از گاراژ حذف شد.",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("🚗 گاراژ", callback_data=f"garage|{user_id}")],
                [InlineKeyboardButton("🔙 خودروها", callback_data=f"vehicles|{user_id}")],
            ]
        ),
    )


async def prepare_list_car(query, vehicle_id: str, user_id: int):
    player = get_player_by_id(user_id) or get_player(query.from_user)
    vehicle = get_vehicle_by_id(player, vehicle_id)
    if not vehicle:
        await safe_answer(query, "خودرو پیدا نشد.", True)
        return
    player["pending"] = {
        "type": "list_vehicle",
        "vehicle_id": vehicle_id,
        "created_at": time.time(),
    }
    save_player(user_id, player)
    await query.edit_message_text(
        f"🏷 <b>ثبت آگهی</b>\n\n"
        f"🚗 {vehicle_name(vehicle)}\n\n"
        "قیمت فروش را ارسال کن.\n\n"
        "مثال:\nفروش خودرو 500000000\n\n"
        "برای لغو: لغو",
        parse_mode="HTML",
    )


async def prepare_gift_car(query, vehicle_id: str, user_id: int):
    player = get_player_by_id(user_id) or get_player(query.from_user)
    vehicle = get_vehicle_by_id(player, vehicle_id)
    if not vehicle:
        await safe_answer(query, "خودرو پیدا نشد.", True)
        return
    player["pending"] = {
        "type": "gift_vehicle",
        "vehicle_id": vehicle_id,
        "created_at": time.time(),
    }
    save_player(user_id, player)
    await query.edit_message_text(
        f"🎁 <b>انتقال خودرو</b>\n\n"
        f"🚗 {vehicle_name(vehicle)}\n\n"
        "شناسه عددی یا @username گیرنده را ارسال کن.\n\n"
        "مثال:\nانتقال خودرو به 123456789\n"
        "یا:\nانتقال خودرو به @username\n\n"
        "برای لغو: لغو",
        parse_mode="HTML",
    )


# ══════════════════════════════════════════════════════════════
# JOB SYSTEM
# ══════════════════════════════════════════════════════════════


def job_rank_from_xp(xp: int) -> int:
    xp = max(0, int(xp))
    rank = 0
    for i, thr in enumerate(JOB_RANK_THRESHOLDS):
        if xp >= thr:
            rank = i
    return min(rank, 5)


def ensure_job(player: dict, job_key: str) -> dict:
    jobs = player.setdefault("jobs", {})
    if job_key not in jobs or not isinstance(jobs[job_key], dict):
        jobs[job_key] = {
            "xp": 0,
            "rank": 0,
            "sessions": 0,
            "income": 0,
            "loss": 0,
            "customers": 0,
        }
    data = jobs[job_key]
    for k in ("xp", "rank", "sessions", "income", "loss", "customers"):
        data.setdefault(k, 0)
    return data


def run_job_session(player: dict, job_key: str) -> dict:
    job = JOBS[job_key]
    data = ensure_job(player, job_key)
    old_rank = int(data.get("rank", 0))
    rank = max(old_rank, job_rank_from_xp(data.get("xp", 0)))
    data["rank"] = rank

    customers = random.randint(1, 3) + (rank // 2)
    income = 0
    loss = 0
    xp_gain = 0
    base = job["base_income"]

    for _ in range(customers):
        job_income = int(base * random.uniform(0.85, 1.35))
        fail_chance = max(3, 16 - rank * 2)
        if random.randint(1, 100) <= fail_chance:
            mistake = max(5_000, job_income // 5)
            loss += mistake
            xp_gain += max(4, job["base_xp"] // 2)
        else:
            income += job_income
            xp_gain += job["base_xp"] + rank * 3

    net = income - loss
    player["cash"] = max(0, int(player.get("cash", 0)) + net)
    data["sessions"] += 1
    data["customers"] += customers
    data["income"] += income
    data["loss"] += loss
    data["xp"] += xp_gain
    data["rank"] = max(data["rank"], job_rank_from_xp(data["xp"]))
    player["stats"]["jobs_done"] = player["stats"].get("jobs_done", 0) + 1
    add_xp(player, xp_gain // 2)
    add_transaction(
        player,
        "job_income",
        max(0, net),
        f"درآمد {job['name']} ({customers} مشتری)",
        direction="in" if net >= 0 else "out",
    )
    return {
        "customers": customers,
        "income": income,
        "loss": loss,
        "net": net,
        "xp": xp_gain,
        "old_rank": old_rank,
        "new_rank": data["rank"],
    }


async def handle_job_action(query, parts: list):
    user_id = int(parts[-1])
    if not is_owner(query):
        await safe_answer(query, "دسترسی ندارید.", True)
        return
    player = get_player(query.from_user)
    action = parts[0]

    if action == "jobs":
        await query.edit_message_text(
            "💼 <b>مشاغل</b>\n\nیک شغل انتخاب کن.",
            parse_mode="HTML",
            reply_markup=jobs_menu(user_id),
        )
        return

    if action == "job_skills":
        lines = ["📊 <b>مهارت‌های شغلی</b>\n"]
        for jkey, jdata in JOBS.items():
            d = ensure_job(player, jkey)
            rank = min(int(d.get("rank", 0)), 5)
            lines.append(
                f"{jdata['name']}\n"
                f"🎖 {jdata['ranks'][rank]}\n"
                f"⭐ {format_num(d.get('xp', 0))} XP\n"
            )
        await query.edit_message_text(
            "\n".join(lines),
            parse_mode="HTML",
            reply_markup=back_button(user_id, "jobs"),
        )
        return

    if action == "job":
        job_key = parts[1] if len(parts) > 2 else "barber"
        if job_key not in JOBS:
            job_key = "barber"
        data = ensure_job(player, job_key)
        rank = min(int(data.get("rank", 0)), 5)
        j = JOBS[job_key]
        text = (
            f"{j['name']}\n\n"
            f"🎖 رتبه: {j['ranks'][rank]}\n"
            f"⭐ XP شغلی: {format_num(data.get('xp', 0))}\n"
            f"👥 مشتری‌ها: {format_num(data.get('customers', 0))}\n"
            f"💰 درآمد کل: {format_num(data.get('income', 0))}\n"
            f"📉 خسارت کل: {format_num(data.get('loss', 0))}\n"
            f"🧰 جلسات: {format_num(data.get('sessions', 0))}"
        )
        kb = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "▶️ شروع کار",
                        callback_data=f"job_work|{job_key}|{user_id}",
                    )
                ],
                [InlineKeyboardButton("🔙 مشاغل", callback_data=f"jobs|{user_id}")],
            ]
        )
        await query.edit_message_text(text, reply_markup=kb)
        return

    if action == "job_work":
        job_key = parts[1] if len(parts) > 2 else "barber"
        if job_key not in JOBS:
            await safe_answer(query, "شغل نامعتبر.", True)
            return
        result = run_job_session(player, job_key)
        save_player(user_id, player)
        rank_name = JOBS[job_key]["ranks"][min(result["new_rank"], 5)]
        promo = ""
        if result["new_rank"] > result["old_rank"]:
            promo = "\n\n🎉 <b>تبریک!</b> رتبه شغلی ارتقا یافت."
        text = (
            f"💼 <b>شیفت کاری تمام شد</b>\n\n"
            f"👥 مشتری: {result['customers']}\n"
            f"💰 درآمد: +{format_num(result['income'])}\n"
            f"📉 خسارت: -{format_num(result['loss'])}\n"
            f"💵 خالص: {result['net']:+,}\n"
            f"⭐ XP شغلی: +{result['xp']}\n"
            f"🎖 رتبه: {rank_name}"
            f"{promo}"
        )
        await query.edit_message_text(
            text,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "🔄 یک شیفت دیگر",
                            callback_data=f"job_work|{job_key}|{user_id}",
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "🔙 شغل",
                            callback_data=f"job|{job_key}|{user_id}",
                        )
                    ],
                ]
            ),
        )


# ══════════════════════════════════════════════════════════════
# COMBAT
# ══════════════════════════════════════════════════════════════


def body_status_text(player: dict) -> str:
    body = player.get("body", default_body())
    lines = [
        "⚔️ <b>وضعیت بدن</b>",
        "",
        f"❤️ HP کلی: {body.get('hp', 100)}/{body.get('max_hp', 100)}",
        "",
        "🩸 آسیب‌ها:",
    ]
    injuries = body.get("injuries", [])
    if not injuries:
        lines.append("هیچ آسیب فعالی نداری.")
    else:
        for inj in injuries:
            itype = INJURY_TYPES.get(inj.get("type", "bruise"), {})
            part = BODY_PARTS.get(inj.get("part", ""), {}).get("name", inj.get("part"))
            lines.append(f"• {itype.get('name', '?')} در {part}")
    return "\n".join(lines)


async def start_fight_from_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    msg = update.message
    if not user or not msg or not msg.reply_to_message:
        return
    target = msg.reply_to_message.from_user
    if not target:
        await msg.reply_text("❌ صاحب پیام شناسایی نشد.")
        return
    if target.id == user.id:
        await msg.reply_text("❌ نمی‌توانی با خودت مبارزه کنی.")
        return
    if target.is_bot:
        await msg.reply_text("❌ نمی‌توانی با ربات مبارزه کنی.")
        return

    attacker = get_player(user)
    if attacker.get("banned"):
        await msg.reply_text("🚫 حساب شما مسدود است.")
        return
    # اطمینان از وجود حساب هدف
    get_player(target)

    rows = []
    for aid, atk in ATTACKS.items():
        if attacker.get("level", 1) >= atk.get("level", 1):
            rows.append(
                [
                    InlineKeyboardButton(
                        f"{atk['name']} (Lv.{atk.get('level', 1)})",
                        callback_data=f"attacktype|{aid}|{target.id}|{user.id}",
                    )
                ]
            )
    rows.append(
        [InlineKeyboardButton("❌ لغو", callback_data=f"fightcancel|{user.id}")]
    )
    await msg.reply_text(
        f"⚔️ مبارزه با {target.first_name or 'بازیکن'}\n\nنوع حمله را انتخاب کن:",
        reply_markup=InlineKeyboardMarkup(rows),
    )


async def handle_attack_type(query, attack_id: str, target_id: int, attacker_id: int):
    if int(query.from_user.id) != int(attacker_id):
        await safe_answer(query, "این دکمه متعلق به شما نیست.", True)
        return
    if attack_id not in ATTACKS:
        await safe_answer(query, "حمله نامعتبر.", True)
        return
    rows = []
    current = []
    for pid, pdata in BODY_PARTS.items():
        current.append(
            InlineKeyboardButton(
                pdata["name"],
                callback_data=f"attackpart|{attack_id}|{pid}|{target_id}|{attacker_id}",
            )
        )
        if len(current) == 2:
            rows.append(current)
            current = []
    if current:
        rows.append(current)
    rows.append(
        [InlineKeyboardButton("❌ لغو", callback_data=f"fightcancel|{attacker_id}")]
    )
    await query.edit_message_text(
        f"{ATTACKS[attack_id]['name']}\n\nقسمت بدن را انتخاب کن:",
        reply_markup=InlineKeyboardMarkup(rows),
    )


async def handle_attack_part(
    query, attack_id: str, part_id: str, target_id: int, attacker_id: int, context
):
    if int(query.from_user.id) != int(attacker_id):
        await safe_answer(query, "دسترسی ندارید.", True)
        return
    if attack_id not in ATTACKS or part_id not in BODY_PARTS:
        await safe_answer(query, "داده نامعتبر.", True)
        return

    with DATA_LOCK:
        players = load_players()
        a_key, t_key = str(attacker_id), str(target_id)
        if a_key not in players or t_key not in players:
            await safe_answer(query, "بازیکن پیدا نشد.", True)
            return
        attacker = normalize_player(players[a_key])
        target = normalize_player(players[t_key])

        atk = ATTACKS[attack_id]
        if attacker.get("level", 1) < atk.get("level", 1):
            await safe_answer(query, "سطح شما کافی نیست.", True)
            return

        # دقت
        if random.randint(1, 100) > atk["accuracy"]:
            await query.edit_message_text(
                f"💨 حمله {atk['name']} به خطا رفت!",
                reply_markup=back_button(attacker_id, "combat"),
            )
            return

        base_dmg = random.randint(atk["min"], atk["max"])
        mult = BODY_PARTS[part_id]["multiplier"]
        damage = max(1, int(base_dmg * mult))

        # اعمال آسیب
        body = target.setdefault("body", default_body())
        parts = body.setdefault("parts", {})
        if part_id not in parts:
            parts[part_id] = {
                "hp": BODY_PARTS[part_id]["max_hp"],
                "max_hp": BODY_PARTS[part_id]["max_hp"],
            }
        parts[part_id]["hp"] = max(0, parts[part_id]["hp"] - damage)
        body["hp"] = max(0, body.get("hp", 100) - max(1, damage // 3))

        # احتمال آسیب
        injury = None
        roll = random.randint(1, 100)
        if roll <= 8 and damage >= 18:
            injury = "fracture"
        elif roll <= 18 and damage >= 14:
            injury = "dislocation"
        elif roll <= 30 and damage >= 12:
            injury = "bleeding"
        elif roll <= 50 and damage >= 8:
            injury = "wound"
        elif roll <= 70:
            injury = "bruise"

        if injury:
            body.setdefault("injuries", []).append(
                {
                    "type": injury,
                    "part": part_id,
                    "created_at": timestamp(),
                }
            )
            body["injuries"] = body["injuries"][-20:]

        attacker["stats"]["fights"] = attacker["stats"].get("fights", 0) + 1
        attacker["stats"]["hits"] = attacker["stats"].get("hits", 0) + 1
        attacker["stats"]["damage_dealt"] = (
            attacker["stats"].get("damage_dealt", 0) + damage
        )
        target["stats"]["damage_received"] = (
            target["stats"].get("damage_received", 0) + damage
        )
        add_xp(attacker, atk["xp"])

        players[a_key] = attacker
        players[t_key] = target
        save_players(players)

    part_name = BODY_PARTS[part_id]["name"]
    inj_text = ""
    if injury:
        inj_text = f"\n🩸 آسیب: {INJURY_TYPES[injury]['name']}"

    await query.edit_message_text(
        f"⚔️ <b>حمله موفق</b>\n\n"
        f"{atk['name']} به {part_name}\n"
        f"💥 آسیب: {damage}{inj_text}",
        parse_mode="HTML",
        reply_markup=back_button(attacker_id, "combat"),
    )

    try:
        await context.bot.send_message(
            chat_id=target_id,
            text=(
                f"⚠️ به شما حمله شد!\n\n"
                f"👤 مهاجم: {query.from_user.first_name or 'بازیکن'}\n"
                f"{atk['name']} به {part_name}\n"
                f"💥 آسیب: {damage}{inj_text}"
            ),
        )
    except Exception:
        pass


async def show_clinic(query, user_id: int):
    player = get_player_by_id(user_id) or get_player(query.from_user)
    body = player.get("body", default_body())
    injuries = body.get("injuries", [])
    if not injuries:
        text = "🏥 <b>کلینیک</b>\n\nآسیب فعالی نداری. سلامت کامل!"
        kb = back_button(user_id, "combat")
    else:
        total_cost = 0
        lines = ["🏥 <b>کلینیک</b>\n\nآسیب‌های فعال:\n"]
        for inj in injuries:
            itype = INJURY_TYPES.get(inj.get("type", "bruise"), {})
            part = BODY_PARTS.get(inj.get("part", ""), {}).get("name", "?")
            cost = itype.get("cost", 10000)
            total_cost += cost
            lines.append(f"• {itype.get('name')} در {part} — {format_num(cost)}")
        lines.append(f"\n💰 هزینه درمان همه: {format_num(total_cost)}")
        text = "\n".join(lines)
        kb = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "🩹 درمان همه",
                        callback_data=f"treat_all|{user_id}",
                    )
                ],
                [InlineKeyboardButton("🔙 مبارزه", callback_data=f"combat|{user_id}")],
            ]
        )
    await query.edit_message_text(text, parse_mode="HTML", reply_markup=kb)


async def treat_all(query, user_id: int):
    with DATA_LOCK:
        players = load_players()
        key = str(user_id)
        if key not in players:
            await safe_answer(query, "حساب پیدا نشد.", True)
            return
        player = normalize_player(players[key])
        body = player.get("body", default_body())
        injuries = body.get("injuries", [])
        if not injuries:
            await safe_answer(query, "آسیبی برای درمان نیست.")
            return
        total = 0
        for inj in injuries:
            total += INJURY_TYPES.get(inj.get("type", "bruise"), {}).get("cost", 10000)
        if player.get("bank_balance", 0) < total and player.get("cash", 0) < total:
            await safe_answer(query, "پول کافی نیست.", True)
            return
        if player.get("bank_balance", 0) >= total:
            player["bank_balance"] -= total
        else:
            player["cash"] -= total

        # درمان
        body["injuries"] = []
        body["hp"] = body.get("max_hp", 100)
        for pid, pdata in BODY_PARTS.items():
            if pid in body.get("parts", {}):
                body["parts"][pid]["hp"] = pdata["max_hp"]
        player["body"] = body
        add_transaction(
            player,
            "clinic",
            total,
            "درمان کامل در کلینیک",
            direction="out",
        )
        players[key] = player
        save_players(players)

    await query.edit_message_text(
        f"✅ درمان کامل انجام شد.\n💰 هزینه: {format_num(total)}",
        reply_markup=back_button(user_id, "combat"),
    )


# ══════════════════════════════════════════════════════════════
# DISTRICTS / PROPERTIES / COURSES
# ══════════════════════════════════════════════════════════════


async def show_districts(query, user_id: int):
    player = get_player_by_id(user_id) or get_player(query.from_user)
    current = player.get("location", "south")
    lines = [
        "🗺️ <b>مناطق شهر</b>\n",
        f"📍 محل فعلی: {DISTRICTS.get(current, {}).get('name', current)}\n",
    ]
    rows = []
    for did, d in DISTRICTS.items():
        mark = " ✅" if did == current else ""
        lines.append(
            f"{d['name']}{mark}\n"
            f"   {d['desc']}\n"
            f"   💸 هزینه جابه‌جایی: {format_num(d['move_cost'])}\n"
        )
        if did != current:
            rows.append(
                [
                    InlineKeyboardButton(
                        f"رفتن به {d['name']}",
                        callback_data=f"move|{did}|{user_id}",
                    )
                ]
            )
    rows.append([InlineKeyboardButton("🔙 منوی اصلی", callback_data=f"main|{user_id}")])
    await safe_edit_message(
        query,
        "\n".join(lines),
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(rows),
    )


async def move_district(query, district_id: str, user_id: int):
    if district_id not in DISTRICTS:
        await safe_answer(query, "منطقه نامعتبر.", True)
        return
    with DATA_LOCK:
        players = load_players()
        key = str(user_id)
        if key not in players:
            await safe_answer(query, "حساب پیدا نشد.", True)
            return
        player = normalize_player(players[key])
        if player.get("location") == district_id:
            await safe_answer(query, "همین‌جا هستی.")
            return
        cost = int(DISTRICTS[district_id]["move_cost"])
        if cost > 0:
            if player.get("bank_balance", 0) >= cost:
                player["bank_balance"] -= cost
            elif player.get("cash", 0) >= cost:
                player["cash"] -= cost
            else:
                await safe_answer(query, "پول کافی برای جابه‌جایی نیست.", True)
                return
            add_transaction(
                player,
                "move",
                cost,
                f"جابه‌جایی به {DISTRICTS[district_id]['name']}",
                direction="out",
            )
        player["location"] = district_id
        players[key] = player
        save_players(players)

    await safe_edit_message(
        query,
        f"✅ به {DISTRICTS[district_id]['name']} نقل‌مکان کردی."
        + (f"\n💰 هزینه: {format_num(cost)}" if cost else ""),
        reply_markup=back_button(user_id, "districts"),
    )


async def show_properties(query, user_id: int):
    player = get_player_by_id(user_id) or get_player(query.from_user)
    owned = player.get("properties", [])
    lines = ["🏠 <b>املاک</b>\n"]
    if owned:
        lines.append("<b>املاک شما:</b>")
        for p in owned:
            lines.append(f"• {esc(p.get('name', 'ملک'))} ({p.get('id', '')})")
        lines.append("")
    else:
        lines.append("هنوز ملکی نداری.\n")

    lines.append("<b>بازار املاک:</b>")
    rows = []
    for pid, prop in PROPERTY_CATALOG.items():
        already = any(o.get("catalog_id") == pid for o in owned)
        dtype = "اجاره" if prop["type"] == "rent" else "خرید"
        price = prop.get("rent") if prop["type"] == "rent" else prop.get("price")
        label = f"{prop['name']} — {dtype} {format_num(price)}"
        lines.append(f"• {prop['name']} | {dtype}: {format_num(price)}")
        if not already:
            rows.append(
                [
                    InlineKeyboardButton(
                        label[:60],
                        callback_data=f"buyprop|{pid}|{user_id}",
                    )
                ]
            )
    rows.append([InlineKeyboardButton("🔙 منوی اصلی", callback_data=f"main|{user_id}")])
    await safe_edit_message(
        query,
        "\n".join(lines),
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(rows),
    )


async def buy_property(query, prop_id: str, user_id: int):
    catalog = PROPERTY_CATALOG.get(prop_id)
    if not catalog:
        await safe_answer(query, "ملک پیدا نشد.", True)
        return
    with DATA_LOCK:
        players = load_players()
        key = str(user_id)
        if key not in players:
            await safe_answer(query, "حساب پیدا نشد.", True)
            return
        player = normalize_player(players[key])
        if player.get("level", 1) < catalog.get("level", 1):
            await safe_answer(
                query,
                f"حداقل Level {catalog['level']} لازم است.",
                True,
            )
            return
        if any(p.get("catalog_id") == prop_id for p in player.get("properties", [])):
            await safe_answer(query, "این ملک را داری.", True)
            return

        if catalog["type"] == "rent":
            cost = int(catalog.get("rent", 0))
            # اجاره ماهانه از بانک
            if not spend_money(player, cost, "bank") and not spend_money(
                player, cost, "cash"
            ):
                await safe_answer(query, "پول کافی برای اجاره نیست.", True)
                return
            tx_type = "rent"
            desc = f"اجاره {catalog['name']}"
        else:
            cost = int(catalog.get("price", 0))
            if not spend_money(player, cost, "bank") and not spend_money(
                player, cost, "cash"
            ):
                await safe_answer(query, "موجودی کافی نیست.", True)
                return
            tx_type = "property_buy"
            desc = f"خرید {catalog['name']}"

        prop = {
            "id": make_id("PROP"),
            "catalog_id": prop_id,
            "name": catalog["name"],
            "district": catalog["district"],
            "type": catalog["type"],
            "price": catalog.get("price", 0),
            "rent": catalog.get("rent", 0),
            "income": catalog.get("income", 0),
            "bought_at": timestamp(),
        }
        player.setdefault("properties", []).append(prop)
        # اگر ملک در منطقه دیگر است، اختیاری مکان را عوض نکن مگر خرید خانه
        if catalog["type"] == "buy" and catalog["district"]:
            player["location"] = catalog["district"]

        add_transaction(player, tx_type, cost, desc, direction="out")
        players[key] = player
        save_players(players)

    await safe_edit_message(
        query,
        f"✅ {catalog['name']}\n💰 مبلغ: {format_num(cost)}\nثبت شد.",
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("🏠 املاک", callback_data=f"properties|{user_id}")],
                [InlineKeyboardButton("🔙 منو", callback_data=f"main|{user_id}")],
            ]
        ),
    )


async def show_courses(query, user_id: int):
    player = get_player_by_id(user_id) or get_player(query.from_user)
    done = set(player.get("courses_done", []))
    lines = ["🎓 <b>دوره‌های آموزشی</b>\n"]
    rows = []
    for cid, c in COURSES.items():
        status = " ✅ گذرانده" if cid in done else ""
        lines.append(
            f"• {c['name']}{status}\n"
            f"   💰 {format_num(c['cost'])} | Lv.{c.get('level', 1)}\n"
        )
        if cid not in done:
            rows.append(
                [
                    InlineKeyboardButton(
                        f"شرکت در {c['name'][:28]}",
                        callback_data=f"takecourse|{cid}|{user_id}",
                    )
                ]
            )
    rows.append([InlineKeyboardButton("🔙 منوی اصلی", callback_data=f"main|{user_id}")])
    await safe_edit_message(
        query,
        "\n".join(lines),
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(rows),
    )


async def take_course(query, course_id: str, user_id: int):
    course = COURSES.get(course_id)
    if not course:
        await safe_answer(query, "دوره پیدا نشد.", True)
        return
    with DATA_LOCK:
        players = load_players()
        key = str(user_id)
        if key not in players:
            await safe_answer(query, "حساب پیدا نشد.", True)
            return
        player = normalize_player(players[key])
        if course_id in player.get("courses_done", []):
            await safe_answer(query, "این دوره را قبلاً گذراندی.", True)
            return
        if player.get("level", 1) < course.get("level", 1):
            await safe_answer(
                query,
                f"حداقل Level {course['level']} لازم است.",
                True,
            )
            return
        cost = int(course["cost"])
        if not spend_money(player, cost, "bank") and not spend_money(
            player, cost, "cash"
        ):
            await safe_answer(query, "پول کافی نیست.", True)
            return

        player.setdefault("courses_done", []).append(course_id)
        job_key = course.get("job")
        if job_key and job_key in JOBS:
            data = ensure_job(player, job_key)
            data["xp"] = data.get("xp", 0) + int(course.get("xp", 0))
            data["rank"] = max(data.get("rank", 0), job_rank_from_xp(data["xp"]))
        if course.get("xp_player"):
            add_xp(player, int(course["xp_player"]))
        add_transaction(
            player,
            "course",
            cost,
            f"دوره: {course['name']}",
            direction="out",
        )
        players[key] = player
        save_players(players)

    await safe_edit_message(
        query,
        f"✅ دوره «{course['name']}» با موفقیت گذرانده شد.\n"
        f"💰 هزینه: {format_num(cost)}",
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("🎓 دوره‌ها", callback_data=f"courses|{user_id}")],
                [InlineKeyboardButton("💼 مشاغل", callback_data=f"jobs|{user_id}")],
            ]
        ),
    )


async def show_transfer_help(query, user_id: int):
    text = (
        "💸 <b>راهنمای انتقال پول</b>\n\n"
        "روش ۱ — ریپلای:\n"
        "روی پیام بازیکن ریپلای کن و بنویس:\n"
        "<code>انتقال پول 2500000</code>\n\n"
        "روش ۲ — یوزرنیم:\n"
        "<code>انتقال پول 10000000 به @username</code>\n\n"
        "مبلغ محدودیت ثابت ندارد.\n"
        "⚠️ پول از <b>حساب بانکی</b> کم می‌شود.\n"
        "اگر بانک خالی است اول واریز کن:\n"
        "<code>واریز 1000000</code>\n\n"
        "⚔️ مبارزه: روی پیام شخص ریپلای کن و بنویس:\n"
        "<code>ریپ</code>"
    )
    await safe_edit_message(
        query,
        text,
        parse_mode="HTML",
        reply_markup=back_button(user_id, "main"),
    )


# ══════════════════════════════════════════════════════════════
# MASTER PANEL
# ══════════════════════════════════════════════════════════════


async def show_master_panel(target, context=None):
    if hasattr(target, "effective_user"):
        user = target.effective_user
        send = target.message.reply_text
    else:
        user = target.from_user
        send = target.edit_message_text

    if not user or not is_master(user.id):
        return

    players = load_players()
    total = len(players)
    banned = sum(1 for p in players.values() if p.get("banned"))
    cash_total = sum(int(p.get("cash", 0)) for p in players.values())
    bank_total = sum(int(p.get("bank_balance", 0)) for p in players.values())

    text = (
        "👑 <b>MASTER PANEL</b>\n\n"
        f"👥 بازیکنان: {total}\n"
        f"🔴 بن: {banned}\n"
        f"💵 نقدینگی کل: {format_num(cash_total)}\n"
        f"🏦 بانک کل: {format_num(bank_total)}\n\n"
        "دستورات:\n"
        "/ban &lt;user_id&gt; [دلیل]\n"
        "/unban &lt;user_id&gt;\n"
        "/setcash &lt;user_id&gt; &lt;amount&gt;\n"
        "/setbank &lt;user_id&gt; &lt;amount&gt;\n"
        "/player &lt;user_id&gt;"
    )
    kb = InlineKeyboardMarkup(
        [[InlineKeyboardButton("🔙 منوی اصلی", callback_data=f"main|{user.id}")]]
    )
    await send(text, parse_mode="HTML", reply_markup=kb)


# ══════════════════════════════════════════════════════════════
# TEXT MESSAGE HANDLERS
# ══════════════════════════════════════════════════════════════


async def handle_deposit(update: Update, amount: int):
    user = update.effective_user
    player = get_player(user)
    if amount <= 0:
        await update.message.reply_text("❌ مبلغ باید بیشتر از صفر باشد.")
        return
    if player.get("cash", 0) < amount:
        await update.message.reply_text("❌ پول نقد کافی نیست.")
        return
    player["cash"] -= amount
    player["bank_balance"] = player.get("bank_balance", 0) + amount
    add_transaction(player, "deposit", amount, "واریز پول نقد به بانک", direction="in")
    save_player(user.id, player)
    await update.message.reply_text(
        f"✅ واریز انجام شد.\n💵 مبلغ: {format_num(amount)}\n"
        f"🏦 موجودی بانک: {format_num(player['bank_balance'])}"
    )


async def handle_withdraw(update: Update, amount: int):
    user = update.effective_user
    player = get_player(user)
    if amount <= 0:
        await update.message.reply_text("❌ مبلغ باید بیشتر از صفر باشد.")
        return
    if player.get("bank_balance", 0) < amount:
        await update.message.reply_text("❌ موجودی بانک کافی نیست.")
        return
    player["bank_balance"] -= amount
    player["cash"] = player.get("cash", 0) + amount
    add_transaction(player, "withdraw", amount, "برداشت پول از بانک", direction="out")
    save_player(user.id, player)
    await update.message.reply_text(
        f"✅ برداشت انجام شد.\n💵 مبلغ: {format_num(amount)}\n"
        f"💵 پول نقد: {format_num(player['cash'])}\n"
        f"🏦 بانک: {format_num(player['bank_balance'])}"
    )


async def handle_transfer(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    user = update.effective_user
    if not user:
        return
    text = normalize_digits(text.strip())
    pattern = re.compile(
        r"^انتقال\s+پول\s+([\d,]+)(?:\s+به\s+@?([A-Za-z0-9_]+))?$",
        re.IGNORECASE,
    )
    match = pattern.match(text)
    if not match:
        await update.message.reply_text(
            "❌ فرمت صحیح:\n"
            "انتقال پول 2500000\n"
            "یا:\nانتقال پول 10000000 به @username\n\n"
            "مبلغ سقف ثابت ندارد.\n"
            "یا روی پیام شخص ریپلای کن و بنویس:\nانتقال پول 2500000"
        )
        return

    amount = parse_amount(match.group(1))
    username = match.group(2)
    if amount <= 0:
        await update.message.reply_text("❌ مبلغ نامعتبر.")
        return

    target_id = None
    if username:
        players = load_players()
        key, _ = find_player_by_username(players, username)
        if not key:
            await update.message.reply_text("❌ بازیکنی با این Username پیدا نشد.")
            return
        target_id = int(key)
    elif update.message.reply_to_message and update.message.reply_to_message.from_user:
        target = update.message.reply_to_message.from_user
        if target.id == user.id:
            await update.message.reply_text("❌ نمی‌توانی به خودت پول بدهی.")
            return
        get_player(target)  # ساخت حساب در صورت نیاز
        target_id = target.id
    else:
        await update.message.reply_text(
            "❌ گیرنده مشخص نیست.\nریپلای کن یا @username بنویس."
        )
        return

    success, result = execute_money_transfer(user.id, target_id, amount)
    if not success:
        await update.message.reply_text(f"❌ انتقال انجام نشد.\n{result}")
        return

    sender = result["sender"]
    receiver = result["receiver"]
    await update.message.reply_text(
        f"✅ انتقال موفق.\n"
        f"👤 گیرنده: {receiver.get('name', target_id)}\n"
        f"💸 مبلغ: {format_num(amount)}\n"
        f"🏦 موجودی شما: {format_num(sender.get('bank_balance', 0))}"
    )
    try:
        await context.bot.send_message(
            chat_id=target_id,
            text=(
                f"💰 دریافت وجه\n\n"
                f"👤 فرستنده: {user.first_name or 'بازیکن'}\n"
                f"💵 مبلغ: {format_num(amount)}\n"
                f"🏦 موجودی بانک: {format_num(receiver.get('bank_balance', 0))}"
            ),
        )
    except Exception:
        pass


async def process_pending(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str) -> bool:
    """پردازش حالت‌های چندمرحله‌ای (آگهی، هدیه و ...)"""
    user = update.effective_user
    if not user:
        return False
    player = get_player(user)
    pending = player.get("pending")
    if not pending or not isinstance(pending, dict):
        return False

    # انقضا (۱۰ دقیقه)
    if time.time() - pending.get("created_at", 0) > 600:
        player["pending"] = None
        save_player(user.id, player)
        return False

    low = text.lower().strip()
    if low in ("لغو", "cancel", "انصراف"):
        player["pending"] = None
        save_player(user.id, player)
        await update.message.reply_text("❌ عملیات لغو شد.")
        return True

    ptype = pending.get("type")

    if ptype == "list_vehicle":
        # استخراج مبلغ
        amount = None
        m = re.match(r"^(?:فروش\s+خودرو\s+)?([\d,]+)$", normalize_digits(text), re.I)
        if m:
            amount = parse_amount(m.group(1))
        if not amount or amount <= 0:
            await update.message.reply_text("❌ مبلغ را به صورت عدد وارد کن.")
            return True
        vehicle_id = pending.get("vehicle_id")
        vehicle = get_vehicle_by_id(player, vehicle_id)
        if not vehicle:
            player["pending"] = None
            save_player(user.id, player)
            await update.message.reply_text("❌ خودرو پیدا نشد.")
            return True
        listing_id = make_id("LST")
        listing = {
            "id": listing_id,
            "seller_id": user.id,
            "vehicle_id": vehicle_id,
            "price": amount,
            "status": "active",
            "created_at": timestamp(),
        }
        player.setdefault("market_listings", []).append(listing)
        player["pending"] = None
        save_player(user.id, player)
        await update.message.reply_text(
            f"✅ آگهی ثبت شد.\n🚗 {vehicle_name(vehicle)}\n💰 قیمت: {format_num(amount)}"
        )
        return True

    if ptype == "gift_vehicle":
        # استخراج شناسه یا یوزرنیم
        identifier = text
        m = re.match(
            r"^(?:انتقال\s+خودرو\s+به\s+)?@?([A-Za-z0-9_]+|\d+)$",
            normalize_digits(text),
            re.I,
        )
        if m:
            identifier = m.group(1)
        players = load_players()
        receiver_key = None
        if identifier.isdigit():
            if str(identifier) in players:
                receiver_key = str(identifier)
        else:
            receiver_key, _ = find_player_by_username(players, identifier)

        if not receiver_key:
            await update.message.reply_text("❌ گیرنده پیدا نشد.")
            return True
        if int(receiver_key) == user.id:
            await update.message.reply_text("❌ نمی‌توانی به خودت هدیه بدهی.")
            return True

        vehicle_id = pending.get("vehicle_id")
        with DATA_LOCK:
            players = load_players()
            sender = normalize_player(players[str(user.id)])
            receiver = normalize_player(players[receiver_key])
            vehicle = get_vehicle_by_id(sender, vehicle_id)
            if not vehicle:
                player["pending"] = None
                save_player(user.id, player)
                await update.message.reply_text("❌ خودرو دیگر در گاراژ نیست.")
                return True
            remove_vehicle(sender, vehicle_id)
            gifted = copy.deepcopy(vehicle)
            gifted["owner_id"] = int(receiver_key)
            gifted["gifted_at"] = timestamp()
            receiver.setdefault("vehicles", []).append(gifted)
            ref = make_id("GFT")
            add_transaction(
                sender,
                "vehicle_gift_sent",
                0,
                f"هدیه {vehicle_name(vehicle)} به {receiver_key}",
                direction="out",
                reference_id=ref,
            )
            add_transaction(
                receiver,
                "vehicle_gift_received",
                0,
                f"دریافت هدیه {vehicle_name(vehicle)} از {user.id}",
                direction="in",
                reference_id=ref,
            )
            sender["pending"] = None
            players[str(user.id)] = sender
            players[receiver_key] = receiver
            save_players(players)

        await update.message.reply_text(
            f"🎁 خودرو منتقل شد.\n🚗 {vehicle_name(vehicle)}\n"
            f"👤 گیرنده: {receiver.get('name', receiver_key)}"
        )
        try:
            await context.bot.send_message(
                chat_id=int(receiver_key),
                text=(
                    f"🎁 یک خودرو به شما هدیه داده شد.\n"
                    f"🚗 {vehicle_name(vehicle)}\n"
                    f"👤 از: {user.first_name or 'بازیکن'}"
                ),
            )
        except Exception:
            pass
        return True

    return False


async def text_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    user = update.effective_user
    if not user:
        return

    try:
        player = get_player(user)
    except Exception as e:
        logger.exception("get_player failed: %s", e)
        await update.message.reply_text("⚠️ خطا در بارگذاری حساب. دوباره /start بزن.")
        return

    if player.get("banned"):
        await update.message.reply_text("🚫 حساب شما مسدود است.")
        return

    text = normalize_digits(update.message.text.strip())
    low = text.lower()

    # حالت‌های pending
    if await process_pending(update, context, text):
        return

    # منو
    if low in ("منو", "menu"):
        await menu_command(update, context)
        return

    # مبارزه: Reply روی پیام بازیکن + کلمه حمله
    fight_words = {
        "حمله",
        "ضربه",
        "نبرد",
        "دعوا",
        "fight",
        "attack",
    }
    if low in fight_words or text in fight_words:
        if update.message.reply_to_message:
            await start_fight_from_reply(update, context)
        else:
            await update.message.reply_text(
                "⚔️ برای حمله:\n"
                "۱) روی پیام بازیکن مقابل Reply بزن\n"
                "۲) بنویس: حمله\n\n"
                "⚠️ در گروه: BotFather → /setprivacy → Disable"
            )
        return

    # مشاغل / خودرو
    if low in ("کار", "شغل", "jobs"):
        await jobs_command(update, context)
        return
    if low in ("خودرو", "ماشین", "cars", "car"):
        await cars_command(update, context)
        return

    # پنل
    if low in ("پنل", "panel"):
        if is_master(user.id):
            await panel_command(update, context)
        else:
            await update.message.reply_text("❌ فقط برای Master.")
        return

    # واریز / برداشت
    m = re.match(r"^(?:واریز|deposit)\s+([\d,]+)$", text, re.I)
    if m:
        await handle_deposit(update, parse_amount(m.group(1)))
        return
    m = re.match(r"^(?:برداشت|withdraw)\s+([\d,]+)$", text, re.I)
    if m:
        await handle_withdraw(update, parse_amount(m.group(1)))
        return

    # انتقال پول
    if text.startswith("انتقال پول"):
        await handle_transfer(update, context, text)
        return

    await update.message.reply_text(
        "دستور شناخته نشد.\nبرای منو بنویس: منو\nبرای راهنما: /help"
    )


async def _require_master(update: Update) -> bool:
    user = update.effective_user
    if not user or not is_master(user.id):
        if update.message:
            await update.message.reply_text("❌ فقط برای Master.")
        return False
    return True


async def master_ban_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _require_master(update):
        return
    args = context.args or []
    if len(args) < 1:
        await update.message.reply_text("فرمت: /ban USER_ID [دلیل]")
        return
    try:
        uid = int(args[0])
        reason = " ".join(args[1:]) or "بدون توضیح"
        players = load_players()
        if str(uid) not in players:
            await update.message.reply_text("بازیکن پیدا نشد.")
            return
        players[str(uid)]["banned"] = True
        players[str(uid)]["ban_reason"] = reason
        save_players(players)
        await update.message.reply_text(f"✅ کاربر {uid} بن شد.\nدلیل: {reason}")
    except Exception as e:
        await update.message.reply_text(f"خطا: {e}")


async def master_unban_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _require_master(update):
        return
    args = context.args or []
    if len(args) < 1:
        await update.message.reply_text("فرمت: /unban USER_ID")
        return
    try:
        uid = int(args[0])
        players = load_players()
        if str(uid) not in players:
            await update.message.reply_text("بازیکن پیدا نشد.")
            return
        players[str(uid)]["banned"] = False
        players[str(uid)]["ban_reason"] = ""
        save_players(players)
        await update.message.reply_text(f"✅ کاربر {uid} آنبن شد.")
    except Exception as e:
        await update.message.reply_text(f"خطا: {e}")


async def master_setcash_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _require_master(update):
        return
    args = context.args or []
    if len(args) < 2:
        await update.message.reply_text("فرمت: /setcash USER_ID AMOUNT")
        return
    try:
        uid = int(args[0])
        amount = parse_amount(args[1])
        players = load_players()
        if str(uid) not in players:
            await update.message.reply_text("بازیکن پیدا نشد.")
            return
        players[str(uid)]["cash"] = amount
        save_players(players)
        await update.message.reply_text(f"✅ cash کاربر {uid} = {format_num(amount)}")
    except Exception as e:
        await update.message.reply_text(f"خطا: {e}")


async def master_setbank_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _require_master(update):
        return
    args = context.args or []
    if len(args) < 2:
        await update.message.reply_text("فرمت: /setbank USER_ID AMOUNT")
        return
    try:
        uid = int(args[0])
        amount = parse_amount(args[1])
        players = load_players()
        if str(uid) not in players:
            await update.message.reply_text("بازیکن پیدا نشد.")
            return
        players[str(uid)]["bank_balance"] = amount
        save_players(players)
        await update.message.reply_text(f"✅ bank کاربر {uid} = {format_num(amount)}")
    except Exception as e:
        await update.message.reply_text(f"خطا: {e}")


async def master_setlevel_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _require_master(update):
        return

    args = context.args or []

    if len(args) < 2:
        await update.message.reply_text(
            "فرمت: /setlevel USER_ID_OR_USERNAME LEVEL"
        )
        return

    try:
        players = load_players()
        key, player = resolve_player_identifier(args[0], players)

        if not key or not player:
            await update.message.reply_text("❌ بازیکن پیدا نشد.")
            return

        level = max(1, int(args[1]))

        player = normalize_player(player)
        player["level"] = level

        players[key] = player
        save_players(players)

        await update.message.reply_text(
            f"✅ Level بازیکن {key} شد {level}"
        )

    except Exception as e:
        await update.message.reply_text(f"❌ خطا: {e}")


async def master_setxp_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _require_master(update):
        return

    args = context.args or []

    if len(args) < 2:
        await update.message.reply_text(
            "فرمت: /setxp USER_ID_OR_USERNAME XP"
        )
        return

    try:
        players = load_players()
        key, player = resolve_player_identifier(args[0], players)

        if not key or not player:
            await update.message.reply_text("❌ بازیکن پیدا نشد.")
            return

        player = normalize_player(player)
        player["xp"] = max(0, int(args[1]))

        players[key] = player
        save_players(players)

        await update.message.reply_text(
            f"✅ XP بازیکن تنظیم شد: {format_num(player['xp'])}"
        )

    except Exception as e:
        await update.message.reply_text(f"❌ خطا: {e}")


async def master_setrep_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _require_master(update):
        return

    args = context.args or []

    if len(args) < 2:
        await update.message.reply_text(
            "فرمت: /setrep USER_ID_OR_USERNAME VALUE"
        )
        return

    try:
        players = load_players()
        key, player = resolve_player_identifier(args[0], players)

        if not key or not player:
            await update.message.reply_text("❌ بازیکن پیدا نشد.")
            return

        player = normalize_player(player)
        player["reputation"] = int(args[1])

        players[key] = player
        save_players(players)

        await update.message.reply_text("✅ شهرت تغییر کرد.")

    except Exception as e:
        await update.message.reply_text(f"❌ خطا: {e}")


async def master_player_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _require_master(update):
        return

    args = context.args or []

    if len(args) < 1:
        await update.message.reply_text(
            "فرمت:\n"
            "/player USER_ID\n"
            "یا:\n"
            "/player @username"
        )
        return

    try:
        identifier = args[0]
        players = load_players()

        key, p = resolve_player_identifier(identifier, players)

        if not key or not p:
            await update.message.reply_text("❌ بازیکن پیدا نشد.")
            return

        p = normalize_player(p)

        await update.message.reply_text(
            profile_text(p),
            parse_mode="HTML",
        )

    except Exception as e:
        logger.exception("Master player lookup failed")
        await update.message.reply_text(f"❌ خطا: {e}")


# ══════════════════════════════════════════════════════════════
# CALLBACK ROUTER
# ══════════════════════════════════════════════════════════════


async def callback_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return
    data = query.data or ""
    parts = data.split("|")
    action = parts[0]

    try:
        await query.answer()
    except Exception:
        pass

    # مالکیت
    if action not in ("noop",) and not is_owner(query):
        # بعضی اکشن‌ها owner چک نمی‌خواهند، اما اکثریت می‌خواهند
        if action not in ("attacktype", "attackpart"):  # این‌ها خودشان چک می‌کنند
            owner = callback_owner_id(data)
            if owner is not None and int(owner) != int(query.from_user.id):
                await safe_answer(query, "❌ این منو متعلق به شما نیست.", True)
                return

    user_id = query.from_user.id
    player = get_player(query.from_user)
    if player.get("banned"):
        await safe_answer(query, "حساب شما مسدود است.", True)
        return

    try:
        if action == "main":
            await show_main_menu(query, user_id)
        elif action == "profile":
            await show_profile(query, user_id)
        elif action == "wallet":
            await show_wallet(query, user_id)
        elif action == "transactions":
            await show_transactions(query, user_id)
        elif action == "help":
            if len(parts) >= 2 and parts[1] != "noop":
                page = int(parts[1])
                page = max(0, min(page, len(HELP_PAGES) - 1))
                await query.edit_message_text(
                    help_page_text(page),
                    reply_markup=help_keyboard(user_id, page),
                )
        elif action == "vehicles":
            await query.edit_message_text(
                "🚗 <b>خودرو</b>\n\nاز گزینه‌های زیر استفاده کن:",
                parse_mode="HTML",
                reply_markup=vehicles_menu(user_id),
            )
        elif action == "showroom":
            await show_showroom(query, user_id)
        elif action == "showcar" and len(parts) >= 2:
            await show_catalog_vehicle(query, parts[1], user_id)
        elif action == "buycar" and len(parts) >= 2:
            await buy_vehicle(query, parts[1], user_id)
        elif action == "garage":
            await show_garage(query, user_id)
        elif action == "mycar" and len(parts) >= 2:
            await show_my_vehicle(query, parts[1], user_id)
        elif action == "sellcar" and len(parts) >= 2:
            await sell_car_instant(query, parts[1], user_id)
        elif action == "listcar" and len(parts) >= 2:
            await prepare_list_car(query, parts[1], user_id)
        elif action == "giftcar" and len(parts) >= 2:
            await prepare_gift_car(query, parts[1], user_id)
        elif action == "carmarket":
            await query.edit_message_text(
                "🏪 <b>بازار خودرو</b>\n\nفعلاً آگهی‌ها از طریق «آگهی بازار» در گاراژ ثبت می‌شوند.\n"
                "نسخه کامل بازار به‌زودی تکمیل می‌شود.",
                parse_mode="HTML",
                reply_markup=back_button(user_id, "vehicles"),
            )
        elif action in ("jobs", "job", "job_work", "job_skills"):
            await handle_job_action(query, parts)
        elif action == "districts":
            await show_districts(query, user_id)
        elif action == "move" and len(parts) >= 2:
            await move_district(query, parts[1], user_id)
        elif action == "properties":
            await show_properties(query, user_id)
        elif action == "buyprop" and len(parts) >= 2:
            await buy_property(query, parts[1], user_id)
        elif action == "courses":
            await show_courses(query, user_id)
        elif action == "takecourse" and len(parts) >= 2:
            await take_course(query, parts[1], user_id)
        elif action == "transfer_help":
            await show_transfer_help(query, user_id)
        elif action == "combat":
            await safe_edit_message(
                query,
                "⚔️ <b>مرکز مبارزه</b>\n\n"
                "برای حمله روی پیام بازیکن <b>ریپلای</b> کن و بنویس:\n"
                "<code>حمله</code>\n\n"
                "بعد نوع حمله و قسمت بدن را انتخاب کن.",
                parse_mode="HTML",
                reply_markup=combat_menu(user_id),
            )
        elif action == "clinic":
            await show_clinic(query, user_id)
        elif action == "injuries":
            await query.edit_message_text(
                body_status_text(player),
                parse_mode="HTML",
                reply_markup=back_button(user_id, "combat"),
            )
        elif action == "treat_all":
            await treat_all(query, user_id)
        elif action == "attacktype" and len(parts) >= 4:
            await handle_attack_type(query, parts[1], int(parts[2]), int(parts[3]))
        elif action == "attackpart" and len(parts) >= 5:
            await handle_attack_part(
                query, parts[1], parts[2], int(parts[3]), int(parts[4]), context
            )
        elif action == "fightcancel":
            await query.edit_message_text(
                "❌ مبارزه لغو شد.",
                reply_markup=back_button(user_id, "combat"),
            )
        elif action == "master_panel":
            if is_master(user_id):
                await show_master_panel(query, context)
            else:
                await safe_answer(query, "دسترسی ندارید.", True)
        else:
            await safe_answer(query, "گزینه پیدا نشد.", True)
    except Exception as e:
        logger.exception("Callback error: %s", e)
        try:
            await query.answer("⚠️ خطایی رخ داد.", show_alert=True)
        except Exception:
            pass


# ══════════════════════════════════════════════════════════════
# ERROR HANDLER
# ══════════════════════════════════════════════════════════════


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    err = context.error
    # خطاهای بی‌ضرر شبکه / پیام تغییرنیافته را فقط لاگ سبک کن
    if isinstance(err, BadRequest):
        msg = str(err).lower()
        if "message is not modified" in msg:
            logger.debug("Ignored: message is not modified")
            return
        if "query is too old" in msg or "query id is invalid" in msg:
            logger.debug("Ignored: expired callback query")
            return
    if isinstance(err, (NetworkError, TimedOut)):
        logger.warning("Network issue: %s", err)
        return
    if isinstance(err, Forbidden):
        logger.warning("Forbidden (user blocked bot?): %s", err)
        return

    logger.error(
        "Exception while handling update:\n%s",
        "".join(
            traceback.format_exception(type(err), err, err.__traceback__)
        )
        if err
        else "unknown",
    )

    try:
        if update is None:
            return
        # فقط یک بار به کاربر اطلاع بده
        if hasattr(update, "callback_query") and update.callback_query:
            try:
                await update.callback_query.answer(
                    "⚠️ خطای موقت. دوباره تلاش کن.",
                    show_alert=False,
                )
            except Exception:
                pass
            return
        if hasattr(update, "effective_message") and update.effective_message:
            await update.effective_message.reply_text(
                "⚠️ یک خطای موقت رخ داد. لطفاً دوباره تلاش کن."
            )
    except Exception:
        pass


# ══════════════════════════════════════════════════════════════
# STARTUP / MAIN
# ══════════════════════════════════════════════════════════════


def startup():
    # اطمینان از وجود فایل دیتابیس
    if not os.path.exists(PLAYERS_FILE):
        save_players({})
    players = load_players()
    for uid, p in list(players.items()):
        players[uid] = normalize_player(p)
    save_players(players)
    logger.info("Database ready. Players: %d", len(players))


def build_application() -> Application:
    token = os.environ.get("BOT_TOKEN", "").strip()
    if not token:
        raise RuntimeError(
            "BOT_TOKEN environment variable is missing.\n"
            "مثال: export BOT_TOKEN='123456:ABC-DEF...'"
        )

    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("menu", menu_command))
    app.add_handler(CommandHandler("jobs", jobs_command))
    app.add_handler(CommandHandler("cars", cars_command))
    app.add_handler(CommandHandler("panel", panel_command))
    # Master slash commands
    app.add_handler(CommandHandler("ban", master_ban_cmd))
    app.add_handler(CommandHandler("unban", master_unban_cmd))
    app.add_handler(CommandHandler("setcash", master_setcash_cmd))
    app.add_handler(CommandHandler("setbank", master_setbank_cmd))
    app.add_handler(CommandHandler("player", master_player_cmd))
    app.add_handler(CommandHandler("setlevel", master_setlevel_cmd))
    app.add_handler(CommandHandler("setxp", master_setxp_cmd))
    app.add_handler(CommandHandler("setrep", master_setrep_cmd))
    
    app.add_handler(CallbackQueryHandler(callback_router))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_router))

    app.add_error_handler(error_handler)
    return app


def main():
    print("=" * 60)
    print("UNDERCITY — Professional Build")
    print("=" * 60)

    startup()

    try:
        t = threading.Thread(
            target=run_health_server,
            daemon=True,
            name="health-server",
        )
        t.start()
        logger.info("Health server started on port %s", PORT)
    except Exception:
        logger.exception("Health server failed to start")

    app = build_application()
    logger.info("Starting polling...")

    try:
        app.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True,
        )
    except Exception:
        logger.exception("BOT STOPPED UNEXPECTEDLY")
        raise
    finally:
        logger.info("Bot process is shutting down.")


if __name__ == "__main__":
    main()
