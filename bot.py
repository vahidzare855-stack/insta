import os
import subprocess
import tempfile
import time
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN = "8237709094:AAGxjI5sllNVu3rEE70TGb1SQ3Sloy7OruE"

# محدودیت روزانه
user_limits = {}
MAX_DOWNLOADS_PER_DAY = 5
RESET_TIME = 24 * 60 * 60  # ۲۴ ساعت

# استارت
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "سلام! لینک اینستاگرام بده تا دانلود کنم 📥\n"
        f"روزانه حداکثر {MAX_DOWNLOADS_PER_DAY} دانلود برای هر کاربر."
    )

# بررسی محدودیت
def check_limit(user_id):
    now = time.time()
    if user_id not in user_limits or now > user_limits[user_id]["reset"]:
        user_limits[user_id] = {"count": 0, "reset": now + RESET_TIME}
    if user_limits[user_id]["count"] >= MAX_DOWNLOADS_PER_DAY:
        return False
    user_limits[user_id]["count"] += 1
    return True

# دانلود و ارسال فایل
async def download_instagram(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    user_id = update.message.from_user.id

    if "instagram.com" not in url:
        await update.message.reply_text("لطفا لینک معتبر اینستاگرام بده 😅")
        return

    if not check_limit(user_id):
        await update.message.reply_text("❌ سقف دانلود روزانه پر شد! فردا دوباره امتحان کن.")
        return

    msg = await update.message.reply_text("⏳ در حال دانلود... لطفا صبر کن")

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            out_template = os.path.join(tmpdir, "%(id)s.%(ext)s")
            cmd = ["yt-dlp", "-f", "best", "-o", out_template, url]
            subprocess.run(cmd, check=True, capture_output=True)

            # فقط فایل‌های قابل ارسال به تلگرام
            files = [f for f in os.listdir(tmpdir) if f.endswith((".mp4", ".jpg", ".png"))]
            if not files:
                await msg.edit_text("❌ فایل قابل ارسال پیدا نشد.")
                return

            filepath = os.path.join(tmpdir, files[0])
            size_mb = os.path.getsize(filepath) / (1024 * 1024)
            if size_mb > 200:
                await msg.edit_text("❌ فایل خیلی بزرگ است (بیشتر از 200MB).")
                return

            # ارسال فایل با with
            with open(filepath, "rb") as f:
                await update.message.reply_document(f)
            await msg.edit_text("✅ دانلود و ارسال شد!")

    except subprocess.CalledProcessError:
        await msg.edit_text("❌ خطا در دانلود. لینک ممکن است نامعتبر باشد.")
    except Exception as e:
        await msg.edit_text(f"❌ خطای دیگر: {e}")

# اجرای ربات
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_instagram))
    print("🚀 ربات اجرا شد...")
    app.run_polling()

if __name__ == "__main__":
    main()
