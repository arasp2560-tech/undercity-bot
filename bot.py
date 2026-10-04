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
        "🌃 به UNDERCITY خوش آمدی!\n\n"
        "اینجا شهریه که می‌تونی ثروت بسازی، "
        "ملک بخری، کسب‌وکار راه بندازی "
        "و امپراتوری خودت رو بسازی.\n\n"
        "🚧 بازی در حال ساخت است..."
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
