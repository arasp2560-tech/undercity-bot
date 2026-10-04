import os
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


# -------------------------
# Server for Render
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
# Main Menu
# -------------------------

def main_menu():
    keyboard = [
        [
            InlineKeyboardButton("👤 پروفایل", callback_data="profile"),
            InlineKeyboardButton("💰 کیف پول", callback_data="wallet"),
        ],
        [
            InlineKeyboardButton("🏙️ شهر", callback_data="city"),
            InlineKeyboardButton("🏠 املاک", callback_data="properties"),
        ],
        [
            InlineKeyboardButton("🚗 وسایل نقلیه", callback_data="vehicles"),
            InlineKeyboardButton("🏢 کسب‌وکارها", callback_data="businesses"),
        ],
        [
            InlineKeyboardButton("📈 بازار", callback_data="market"),
            InlineKeyboardButton("🕶️ دنیای زیرزمینی", callback_data="underground"),
        ],
        [
            InlineKeyboardButton("🤝 باند و اتحاد", callback_data="gang"),
        ],
        [
            InlineKeyboardButton("🏥 درمانگاه", callback_data="clinic"),
            InlineKeyboardButton("💊 داروخانه", callback_data="pharmacy"),
        ],
        [
            InlineKeyboardButton("⚙️ تنظیمات", callback_data="settings"),
        ],
    ]

    return InlineKeyboardMarkup(keyboard)


# -------------------------
# Start
# -------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

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

        "⚠️ UNDERCITY هنوز در حال توسعه است...\n\n"

        "👇 از منوی زیر شروع کن:",
        reply_markup=main_menu()
    )


# -------------------------
# Button Handler
# -------------------------

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    if query.data == "profile":
        text = (
            "👤 پروفایل\n\n"
            "🚧 این بخش در حال ساخت است.\n\n"
            "به‌زودی اطلاعات شخصیت، سطح، تجربه، اعتبار، "
            "دارایی‌ها و وضعیت بازیکن اینجا نمایش داده می‌شود."
        )

    elif query.data == "wallet":
        text = "💰 کیف پول\n\n🚧 این بخش در حال ساخت است."

    elif query.data == "city":
        text = "🏙️ شهر\n\n🚧 نقشه و مناطق شهر در حال ساخت است."

    elif query.data == "properties":
        text = "🏠 املاک\n\n🚧 سیستم خرید و مدیریت املاک در حال ساخت است."

    elif query.data == "vehicles":
        text = "🚗 وسایل نقلیه\n\n🚧 سیستم وسایل نقلیه در حال ساخت است."

    elif query.data == "businesses":
        text = "🏢 کسب‌وکارها\n\n🚧 سیستم کسب‌وکار و کارخانه‌ها در حال ساخت است."

    elif query.data == "market":
        text = "📈 بازار\n\n🚧 بازار پویا و سیستم خرید و فروش در حال ساخت است."

    elif query.data == "underground":
        text = "🕶️ دنیای زیرزمینی\n\n🚧 این بخش در حال ساخت است."

    elif query.data == "gang":
        text = "🤝 باند و اتحاد\n\n🚧 سیستم باندها و اتحادها در حال ساخت است."

    elif query.data == "clinic":
        text = "🏥 درمانگاه\n\n🚧 سیستم درمان و وضعیت جسمانی در حال ساخت است."

    elif query.data == "pharmacy":
        text = "💊 داروخانه\n\n🚧 سیستم داروخانه در حال ساخت است."

    elif query.data == "settings":
        text = "⚙️ تنظیمات\n\n🚧 تنظیمات بازی در حال ساخت است."

    else:
        text = "❌ گزینه نامعتبر است."

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="main_menu")]
        ])
    )


# -------------------------
# Back to Main Menu
# -------------------------

async def back_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        "🌃 **UNDERCITY**\n\n"
        "👇 از منوی اصلی انتخاب کن:",
        reply_markup=main_menu(),
        parse_mode="Markdown"
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

    app.add_handler(CommandHandler("start", start))

    app.add_handler(
        CallbackQueryHandler(
            back_to_menu,
            pattern="^main_menu$"
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            button_handler
        )
    )

    print("UNDERCITY is running...")

    app.run_polling()


if __name__ == "__main__":
    main()
