import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes


PORT = int(os.environ.get("PORT", 10000))


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


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🌃 به UNDERCITY خوش آمدی\n\n"
        "یک شهر زنده و بی‌رحم که در آن می‌توانی از هیچ شروع کنی "
        "و به قدرتمندترین فرد شهر تبدیل شوی.\n\n"

        "💰 پول دربیاور\n"
        "با کار، تجارت، سرمایه‌گذاری، خرید و فروش و فرصت‌های مختلف "
        "ثروت بساز.\n\n"

        "🏠 املاک و دارایی\n"
        "خانه، آپارتمان، زمین، ساختمان و دارایی‌های ارزشمند بخر و مدیریت کن.\n\n"

        "🏢 کسب‌وکار و صنعت\n"
        "کسب‌وکار راه بینداز، کارخانه بساز، پروژه اجرا کن و از اقتصاد شهر سود ببر.\n\n"

        "📈 خرید، فروش و دلالی\n"
        "در بازار شهر معامله کن، قیمت‌ها را دنبال کن، کالا و دارایی بخر و بفروش "
        "و از اختلاف قیمت‌ها سود ببر.\n\n"

        "🕶️ دنیای زیرزمینی\n"
        "وارد فعالیت‌های خلافکارانه شو؛ از معاملات غیرقانونی و سرقت "
        "گرفته تا مأموریت‌های خطرناک و عملیات گروهی.\n\n"

        "🔫 درگیری و نبرد\n"
        "در نبردهای بازی شرکت کن و از تجهیزات مختلف استفاده کن؛ "
        "از سلاح‌های سبک و سنگین گرفته تا خودروهای زرهی، تانک، "
        "هلیکوپتر، جنگنده، ناو و دیگر تجهیزات نظامی.\n\n"

        "🤝 باند و اتحاد\n"
        "گروه خودت را تشکیل بده، متحد پیدا کن، قلمرو و نفوذ به دست بیاور "
        "و با گروه‌های رقیب رقابت کن.\n\n"

        "🌆 شهر را بشناس\n"
        "مناطق مختلف شهر، بازارها، مراکز صنعتی، مناطق ثروتمند، "
        "محله‌های خطرناک و مکان‌های مخفی را کشف کن.\n\n"

        "👑 هدف نهایی\n"
        "ثروت، قدرت، نفوذ و اعتبار خودت را افزایش بده "
        "و امپراتوری خودت را بساز.\n\n"

        "⚠️ UNDERCITY هنوز در حال توسعه است...\n\n"
        "هر انتخابی که می‌کنی، می‌تواند مسیر بازی تو را تغییر دهد.\n\n"
        "🏙️ شهر منتظر توست."
    )
    def main():
    token = os.environ["BOT_TOKEN"]

    threading.Thread(target=run_server, daemon=True).start()

    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))

    print("UNDERCITY is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
