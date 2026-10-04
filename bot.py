import os
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)


PORT = int(os.environ.get("PORT", 10000))
PLAYERS_FILE = "players.json"


# -------------------------
# Render Web Server
# -------------------------

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


# -------------------------
# Player Database
# -------------------------

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
            indent=4
        )


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

    return players[user_id]


# -------------------------
# Main Menu
# -------------------------

def main_menu():

    keyboard = [

        [
            InlineKeyboardButton(
                "👤 پروفایل",
                callback_data="profile"
            ),
            InlineKeyboardButton(
                "💰 کیف پول",
                callback_data="wallet"
            )
        ],

        [
            InlineKeyboardButton(
                "🏙️ شهر",
                callback_data="city"
            ),
            InlineKeyboardButton(
                "🏠 املاک",
                callback_data="properties"
            )
        ],

        [
            InlineKeyboardButton(
                "🚗 وسایل نقلیه",
                callback_data="vehicles"
            ),
            InlineKeyboardButton(
                "🏢 کسب‌وکارها",
                callback_data="businesses"
            )
        ],

        [
            InlineKeyboardButton(
                "📈 بازار",
                callback_data="market"
            ),
            InlineKeyboardButton(
                "🕶️ دنیای زیرزمینی",
                callback_data="underground"
            )
        ],

        [
            InlineKeyboardButton(
                "🤝 باند و اتحاد",
                callback_data="gang"
            )
        ],

        [
            InlineKeyboardButton(
                "🏥 درمانگاه",
                callback_data="clinic"
            ),
            InlineKeyboardButton(
                "💊 داروخانه",
                callback_data="pharmacy"
            )
        ],

        [
            InlineKeyboardButton(
                "⚙️ تنظیمات",
                callback_data="settings"
            )
        ]
    ]

    return InlineKeyboardMarkup(keyboard)


# -------------------------
# Start
# -------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    get_player(update.effective_user)

    await update.message.reply_text(

        "🌃 به UNDERCITY خوش آمدی\n\n"

        "یک شهر زنده و بی‌رحم که در آن می‌توانی از هیچ شروع کنی "
        "و به قدرتمندترین فرد شهر تبدیل شوی.\n\n"

        "💰 پول دربیاور\n"
        "با کار، تجارت، سرمایه‌گذاری، خرید و فروش و فرصت‌های مختلف "
        "ثروت بساز.\n\n"

        "🏠 املاک و دارایی\n"
        "خانه، آپارتمان، زمین، ساختمان و دارایی‌های ارزشمند بخر "
        "و مدیریت کن.\n\n"

        "🏢 کسب‌وکار و صنعت\n"
        "کسب‌وکار راه بینداز، کارخانه بساز، پروژه اجرا کن "
        "و از اقتصاد شهر سود ببر.\n\n"

        "📈 خرید، فروش و دلالی\n"
        "در بازار شهر معامله کن و از اختلاف قیمت‌ها سود ببر.\n\n"

        "🚗 وسایل نقلیه زمینی\n"
        "خودرو، موتورسیکلت، خودروهای سنگین، زرهی و وسایل نقلیه ویژه.\n\n"

        "🚤 وسایل نقلیه آبی\n"
        "قایق، کشتی و دیگر وسایل نقلیه دریایی.\n\n"

        "✈️ وسایل نقلیه هوایی\n"
        "هلیکوپتر، هواپیما، جت و دیگر وسایل پرنده.\n\n"

        "🌊🚙 وسایل نقلیه آبی‌خاکی\n"
        "وسایل نقلیه مخصوص خشکی و آب.\n\n"

        "🕶️ دنیای زیرزمینی\n"
        "فعالیت‌های خلافکارانه، معاملات غیرقانونی، سرقت و مأموریت‌های خطرناک.\n\n"

        "🔫 درگیری و نبرد\n"
        "نبردهای بازی با تجهیزات مختلف؛ از سلاح‌های سبک و سنگین "
        "تا خودروهای زرهی، تانک، هلیکوپتر، جنگنده و ناو.\n\n"

        "🤝 باند و اتحاد\n"
        "گروه خودت را تشکیل بده، متحد پیدا کن و قلمرو و نفوذ به دست بیاور.\n\n"

        "🏥 درمانگاه و 💊 داروخانه\n"
        "وضعیت شخصیتت را مدیریت کن و برای شرایط مختلف آماده باش.\n\n"

        "🌆 شهر را کشف کن و امپراتوری خودت را بساز.\n\n"

        "👇 از منوی زیر شروع کن:",

        reply_markup=main_menu()
    )


# -------------------------
# Profile
# -------------------------

async def show_profile(query, user):

    player = get_player(user)

    properties_count = len(player["properties"])
    vehicles_count = len(player["vehicles"])
    businesses_count = len(player["businesses"])

    home = player["home"]

    profile_text = (

        "👤 پروفایل بازیکن\n\n"

        f"👤 نام: {player['name']}\n"
        f"🆔 شناسه: {user.id}\n\n"

        f"⭐ سطح: {player['level']}\n"
        f"✨ تجربه: {player['xp']}/100\n\n"

        f"💰 موجودی: ${player['money']:,}\n"
        f"🏆 اعتبار: {player['reputation']}\n\n"

        f"🏙️ منطقه: {player['location']}\n\n"

        f"🏠 محل سکونت: {home['name']}\n"
        f"💵 اجاره: ${home['rent']:,}\n\n"

        f"🏢 املاک خریداری‌شده: {properties_count}\n"
        f"🚗 وسایل نقلیه: {vehicles_count}\n"
        f"🏢 کسب‌وکارها: {businesses_count}"
    )

    keyboard = [

        [
            InlineKeyboardButton(
                "🔙 منوی اصلی",
                callback_data="main_menu"
            )
        ]

    ]

    await query.edit_message_text(
        profile_text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# -------------------------
# Button Handler
# -------------------------

async def button_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    user = update.effective_user

    # Profile
    if query.data == "profile":

        await show_profile(query, user)
        return

    # Main menu
    if query.data == "main_menu":

        await query.edit_message_text(

            "🌃 UNDERCITY\n\n"
            "👇 از منوی اصلی انتخاب کن:",

            reply_markup=main_menu()
        )

        return

    # Other sections
    sections = {

        "wallet":
            "💰 کیف پول\n\n"
            "🚧 سیستم کیف پول در حال ساخت است.",

        "city":
            "🏙️ شهر\n\n"
            "🚧 نقشه و مناطق شهر در حال ساخت است.",

        "properties":
            "🏠 املاک\n\n"
            "🚧 سیستم خرید و مدیریت املاک در حال ساخت است.",

        "vehicles":
            "🚗 وسایل نقلیه\n\n"
            "🚧 سیستم وسایل نقلیه در حال ساخت است.",

        "businesses":
            "🏢 کسب‌وکارها\n\n"
            "🚧 سیستم کسب‌وکار و کارخانه‌ها در حال ساخت است.",

        "market":
            "📈 بازار\n\n"
            "🚧 بازار پویا و سیستم خرید و فروش در حال ساخت است.",

        "underground":
            "🕶️ دنیای زیرزمینی\n\n"
            "🚧 این بخش در حال ساخت است.",

        "gang":
            "🤝 باند و اتحاد\n\n"
            "🚧 سیستم باندها و اتحادها در حال ساخت است.",

        "clinic":
            "🏥 درمانگاه\n\n"
            "🚧 سیستم درمان و وضعیت جسمانی در حال ساخت است.",

        "pharmacy":
            "💊 داروخانه\n\n"
            "🚧 سیستم داروخانه در حال ساخت است.",

        "settings":
            "⚙️ تنظیمات\n\n"
            "🚧 تنظیمات بازی در حال ساخت است."
    }

    text = sections.get(
        query.data,
        "❌ گزینه نامعتبر است."
    )

    keyboard = [

        [
            InlineKeyboardButton(
                "🔙 بازگشت به منوی اصلی",
                callback_data="main_menu"
            )
        ]

    ]

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# -------------------------
# Main
# -------------------------

def main():

    token = os.environ["BOT_TOKEN"]

    threading.Thread(
        target=run_server,
        daemon=True
    ).start()

    app = Application.builder().token(token).build()

    app.add_handler(
        CommandHandler("start", start)
    )

    app.add_handler(
        CallbackQueryHandler(button_handler)
    )

    print("UNDERCITY is running...")

    app.run_polling()


if __name__ == "__main__":
    main()
