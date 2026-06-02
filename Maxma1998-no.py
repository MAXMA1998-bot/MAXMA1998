import os
import telebot
from flask import Flask
from threading import Thread

# جلب التوكن من Railway
TOKEN = os.environ.get('TOKEN')
bot = telebot.TeleBot(TOKEN)

# كود الترحيب
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "أهلاً بك في MAXMA 👋.")

# كود الاستيقاظ الدائم (Keep Alive)
app = Flask('')
@app.route('/')
def home():
    return "البوت يعمل الآن!"

def run():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

def keep_alive():
    t = Thread(target=run)
    t.start()

if __name__ == "__main__":
    keep_alive()
    bot.infinity_polling()
