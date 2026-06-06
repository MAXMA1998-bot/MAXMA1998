import os
import time
import telebot
import shutil
import glob
import services
from apscheduler.schedulers.background import BackgroundScheduler

# --- 1. الإعدادات الأساسية ---
TOKEN = os.getenv('TOKEN')
OWNER_ID = int(os.getenv('OWNER_ID', 0))
bot = telebot.TeleBot(TOKEN)
user_last_message_time = {}

# --- 2. نظام الحماية والتريث (المنطق) ---
def is_allowed(message_or_callback):
    """التحقق من التريث ومن صلاحية المالك"""
    user_id = message_or_callback.from_user.id
    if user_id == OWNER_ID: return True
    
    current_time = time.time()
    last_time = user_last_message_time.get(user_id, 0)
    
    if current_time - last_time < 1:
        return False
    
    user_last_message_time[user_id] = current_time
    return True

# --- 3. نظام التنظيف التلقائي ---
def auto_cleanup_job():
    patterns = ["video_*.mp4", "*.tmp", "*.txt", "*.jpg", "*.jpeg", "*.pdf"]
    for pattern in patterns:
        for f in glob.glob(pattern):
            try: os.remove(f)
            except: pass

scheduler = BackgroundScheduler()
scheduler.add_job(auto_cleanup_job, 'interval', minutes=1)
scheduler.start()

# --- 4. الدوال (Handlers) ---

@bot.message_handler(commands=['start'])
def send_welcome(message):
    if not is_allowed(message): return
    bot.reply_to(message, "مرحباً بك في✨ 𝓜𝓐𝓧 𝓑𝓞𝓞𝓣 ✨")

@bot.message_handler(commands=['clean'])
def clean_server(message):
    if message.from_user.id != OWNER_ID: return
    # كود التنظيف الخاص بك هنا
    bot.reply_to(message, "🧹 تم التنظيف.")

@bot.message_handler(commands=['storage'])
def check_storage(message):
    if message.from_user.id != OWNER_ID: return
    # كود الفحص الخاص بك هنا
    bot.reply_to(message, "📊 المساحة جيدة.")

@bot.message_handler(func=lambda message: message.text.startswith('/'))
def restrict_commands(message):
    if message.from_user.id == OWNER_ID: return
    bot.reply_to(message, "⚠️ نعتذر، أنت تستخدم نصوص غير مصرح بها.")

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    if not is_allowed(message):
        bot.reply_to(message, "⏳ تريث قليلاً!")
        return
    # كود معالجة الروابط والتحميل هنا
    bot.send_message(message.chat.id, "جاري المعالجة...")

# --- 5. التشغيل ---
if __name__ == "__main__":
    print("🚀 البوت يعمل الآن بكفاءة.")
    bot.infinity_polling()
