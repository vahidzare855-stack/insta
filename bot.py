import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN = "8237709094:AAGxjI5sllNVu3rEE70TGb1SQ3Sloy7OruE"
MAX_DOWNLOADS_PER_DAY = 5
user_limits = {}
import time
RESET_TIME = 24*60*60

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"سلام! لینک اینستاگرام بده تا دانلود کنم.\nروزانه حداکثر {MAX_DOWNLOADS_PER_DAY} دانلود.")

def check_limit(user_id):
    now = time.time()
    if user_id not in user_limits or now > user_limits[user_id]["reset"]:
        user_limits[user_id] = {"count":0, "reset": now+RESET_TIME}
    if user_limits[user_id]["count"]>=MAX_DOWNLOADS_PER_DAY:
        return False
    user_limits[user_id]["count"] += 1
    return True

async def download_instagram(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    user_id = update.message.from_user.id

    if "instagram.com" not in url:
        await update.message.reply_text("لطفا لینک معتبر اینستاگرام بده 😅")
        return

    if not check_limit(user_id):
        await update.message.reply_text("❌ سقف دانلود روزانه پر شد! فردا دوباره امتحان کن.")
        return

    msg = await update.message.reply_text("⏳ در حال آماده سازی فایل...")

    try:
        # استفاده از API savefrom
        api_url = f"https://api.savefrom.net/api/convert?url={url}&format=mp4"
        response = requests.get(api_url).json()

        if "url" not in response:
            await msg.edit_text("❌ خطا: فایل پیدا نشد یا لینک نامعتبر است.")
            return

        file_url = response["url"]
        file_name = file_url.split("/")[-1]

        r = requests.get(file_url)
        if len(r.content)/(1024*1024) > 200:
            await msg.edit_text("❌ فایل خیلی بزرگ است (بیشتر از 200MB).")
            return

        with open(file_name,"wb") as f:
            f.write(r.content)

        with open(file_name,"rb") as f:
            await update.message.reply_document(f)

        os.remove(file_name)
        await msg.edit_text("✅ دانلود و ارسال شد!")

    except Exception as e:
        await msg.edit_text(f"❌ خطا در دانلود: {e}")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_instagram))
    print("🚀 ربات اجرا شد...")
    app.run_polling()

if __name__ == "__main__":
    main()
