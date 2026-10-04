import os
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🌃 به UNDERCITY خوش آمدی!\n\n"
        "اینجا شهریه که می‌تونی ثروت بسازی، "
        "ملک بخری، ماشین جمع کنی، کسب‌وکار راه بندازی "
        "و امپراتوری خودت رو بسازی.\n\n"
        "🚧 بازی در حال ساخت است..."
    )


def main():
    token = os.environ["BOT_TOKEN"]

    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", start))

    print("UNDERCITY is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
