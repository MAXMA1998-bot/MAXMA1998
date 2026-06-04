import os
import requests
import telebot
from telebot import types
from flask import Flask
from threading import Thread
import re
import instaloader
import yt_dlp
import io
import time
from PIL import Image
from rembg import remove

# إعداد الـ Token من متغيرات البيئة في Railway
TOKEN = os.environ.get('TOKEN')
bot = telebot.TeleBot(TOKEN)

# --- حماية المستوى الأول (Rate Limiting) ---
user_last_action = {}
def is_spaming(user_id):
    current_time = time.time()
    last_time = user_last_action.get(user_id, 0)
    if current_time - last_time < 2: # منع أي طلبين في أقل من ثانيتين
        return True
    user_last_action[user_id] = current_time
    return False
# --- حماية المستوى الثاني (Validation & Sanitization) ---

def is_valid_url(url):
    # قائمة بالنطاقات المسموح بها فقط
    allowed_domains = ['youtube.com', 'youtu.be', 'instagram.com']
    return any(domain in url for domain in allowed_domains)

def clean_text(text):
    # إزالة أي رموز قد تُستخدم في هجمات الحقن البرمجي (Injection)
    # نسمح فقط بالحروف والأرقام والرموز الأساسية للروابط
    return re.sub(r'[^\w\s/:.?=&]', '', text)


# تهيئة انستالودر
L = instaloader.Instaloader(download_videos=True, download_pictures=True, save_metadata=False)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("الاشتراك المجاني", callback_data='free_sub'),
               types.InlineKeyboardButton("اشتراك ماكس ✨", callback_data='max_sub'))
    bot.send_message(message.chat.id, "أهلاً بك في ✨ 𝓜𝓐𝓧 𝓑𝓞𝓞𝓣 ✨", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    # تطبيق الحماية في بداية كل استجابة
    if is_spaming(call.from_user.id):
        bot.answer_callback_query(call.id, "⚠️ تريث قليلاً! لا تضغط بسرعة.")
        return

    # قسم الاشتراكات المجانية
    if call.data == 'free_sub':
        my_free_names = ["تحميل ستوري ", "تحميل أي فيديو🎥", "تحويل الفيديو الى صوت🔊 ", " تحويل الصورة الى pdf📄 "]
        markup = types.InlineKeyboardMarkup(row_width=2)
        buttons = [types.InlineKeyboardButton(my_free_names[i], callback_data=f'f{i+1}') for i in range(4)]
        markup.add(*buttons)
        bot.edit_message_text("اختر الخدمة المجانية:", call.message.chat.id, call.message.message_id, reply_markup=markup)

    elif call.data == 'f1':
        msg = bot.send_message(call.message.chat.id, "أرسل الآن يوزر (معرف) الحساب الذي تريد تحميل الستوري الخاص به:")
        bot.register_next_step_handler(msg, process_insta_username)
        
    elif call.data == 'f2': 
        msg = bot.send_message(call.message.chat.id, "أرسل رابط الفيديو (إنستا/فيس/يوتيوب):")
        bot.register_next_step_handler(msg, process_universal_video)

  
    elif call.data == 'f3':
        msg = bot.send_message(call.message.chat.id, "أرسل رابط الفيديو الذي تريد استخراج الصوت منه:")
        bot.register_next_step_handler(msg, process_audio_conversion)

    elif call.data == 'f4':
        msg = bot.send_message(call.message.chat.id, "📄 أرسل الصورة التي تريد تحويلها إلى PDF:")
        bot.register_next_step_handler(msg, process_to_pdf)

    # قسم اشتراك ماكس
    elif call.data == 'max_sub':
        my_names = [" 💀واتساب 🟡 ", "يوزرات تلي مميزة👑 ", "كود حظر واتس⚡️ ", "اختراق كاميرا📷 ", "معرفة موقع الضحية ","دعس حساب تيكتوك☠️ ", "أرقام فيك ✅ ", "فتح انستا برايفت👀 ", "فك حظر سافيوم994+ ", "كود حظر واتس",
                    "مزايا انستا ✨", "تلغيم رابط🌎 ", "ببجي🎮 ", "رشق انستا✅ ", "تفعيل التطبيقات برو ",
                    " 📱بليلردو لانهائي8 ", "اداة تيكتوك ترول ", "ازالة الاعلانات📢 ", "ارقام مفعلة حقيقيه✅", "تطبيقات ايفون برو "]
        markup = types.InlineKeyboardMarkup(row_width=2)
        buttons = [types.InlineKeyboardButton(my_names[i], callback_data=f'max_{i+1}') for i in range(20)]
        markup.add(*buttons)
        bot.edit_message_text("اختر خدمة ماكس المطلوبة:", call.message.chat.id, call.message.message_id, reply_markup=markup)
    
    elif call.data.startswith('max_'):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("تفعيل ماكس ✨", callback_data='activate_max'))
        bot.edit_message_text("عذراً، أنت غير مشترك في خطة ماكس ✨", call.message.chat.id, call.message.message_id, reply_markup=markup)

    elif call.data == 'activate_max':
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(types.InlineKeyboardButton("🔴 Asiacell", callback_data='provider_asia'),
                   types.InlineKeyboardButton("🔵 Zain", callback_data='provider_zain'))
        bot.edit_message_text("اختر مزود الخدمة:", call.message.chat.id, call.message.message_id, reply_markup=markup)

    elif call.data.startswith('provider_'):
        provider = "آسياسيل" if call.data == 'provider_asia' else "زين"
        msg = bot.send_message(call.message.chat.id, f"تم اختيار {provider}.\nيرجى إرسال رقم البطاقة (16 رقماً فقط):")
        bot.register_next_step_handler(msg, lambda m: get_card_number(m, provider))

# --- الدوال الأصلية ---
def process_insta_username(message):
    if is_spaming(message.from_user.id): return
    username = message.text.replace('@', '').strip()
    wait_msg = bot.send_message(message.chat.id, f"🔍 جاري البحث عن ستوري {username}...")
    try:
        L.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        profile = instaloader.Profile.from_username(L.context, username)
        stories = L.get_stories(userids=[profile.userid])
        count = 0
        for story in stories:
            for item in story.get_items():
                count += 1
                if item.is_video: bot.send_video(message.chat.id, item.video_url)
                else: bot.send_photo(message.chat.id, item.url)
        if count == 0: bot.send_message(message.chat.id, "لم يتم العثور على أي ستوري.")
        bot.delete_message(message.chat.id, wait_msg.message_id)
    except Exception as e:
        print(f"Error: {e}")
        bot.send_message(message.chat.id, "⚠️ حدث خطأ: تأكد أن الحساب عام.")

def get_card_number(message, provider):
    if message.text.isdigit() and len(message.text) == 16:
        bot.reply_to(message, "جاري التفعيل.. انتظر قليلاً.")
        try: bot.send_message(438077185, f"طلب جديد:\nالمزود: {provider}\nالرقم: {message.text}")
        except: pass
    else:
        msg = bot.reply_to(message, "خطأ: يرجى إرسال 16 رقماً فقط.")
        bot.register_next_step_handler(msg, lambda m: get_card_number(m, provider))



def process_to_pdf(message):
    if is_spaming(message.from_user.id): return
    try:
        bot.send_message(message.chat.id, "⏳ جاري التحويل...")
        file_id = message.photo[-1].file_id
        file_info = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        image = Image.open(io.BytesIO(downloaded_file))
        pdf_buffer = io.BytesIO()
        image.save(pdf_buffer, "PDF", resolution=100.0)
        pdf_buffer.seek(0)
        bot.send_document(message.chat.id, pdf_buffer, visible_file_name="image.pdf")
        bot.send_message(message.chat.id, "✅ تم التحويل بنجاح!")
    except Exception as e:
        bot.send_message(message.chat.id, f"⚠️ حدث خطأ: {str(e)}")


# دالة التحقق من صحة الرابط (فلترة الروابط الملغمة)
def is_safe_link(url):
    # يسمح فقط بروابط إنستجرام وفيسبوك ويوتيوب
    allowed_domains = ['instagram.com', 'facebook.com', 'fb.watch', 'youtube.com', 'youtu.be']
    return any(domain in url for domain in allowed_domains)

def process_universal_video(message):
    if is_spaming(message.from_user.id): return
    
    url = message.text.strip()
    
    # حماية المستوى الثاني: منع الروابط غير المعروفة
    if not is_safe_link(url):
        bot.send_message(message.chat.id, "⚠️ الرابط غير مدعوم أو غير آمن. يرجى إرسال رابط إنستجرام أو فيسبوك أو يوتيوب فقط.")
        return
        
    wait_msg = bot.send_message(message.chat.id, "⏳ جاري المعالجة والتحميل...")
    
    try:
        # استخدام Cobalt API لأنه يدعم إنستا وفيسبوك ويوتيوب بكفاءة عالية
        api_url = "https://api.cobalt.tools/api/json"
        payload = {"url": url, "vCodec": "h264"}
        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        
        response = requests.post(api_url, json=payload, headers=headers).json()
        
        if response.get("status") == "success":
            video_url = response.get("url")
            bot.send_video(message.chat.id, video_url, caption="✅ تم التحميل بنجاح بواسطة ✨ 𝓜𝓐𝓧 𝓑𝓞𝓞𝓣 ✨")
            bot.delete_message(message.chat.id, wait_msg.message_id)
        else:
            bot.send_message(message.chat.id, "⚠️ فشل التحميل: تأكد أن الحساب عام (Public) والرابط صحيح.")
            bot.delete_message(message.chat.id, wait_msg.message_id)
            
    except Exception as e:
        bot.send_message(message.chat.id, f"⚠️ خطأ تقني: {str(e)}")
        bot.delete_message(message.chat.id, wait_msg.message_id)


app = Flask('')
@app.route('/')
def home(): return "البوت يعمل!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    Thread(target=lambda: app.run(host='0.0.0.0', port=port)).start()
    bot.infinity_polling()
