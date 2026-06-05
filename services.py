import instaloader
import yt_dlp
import img2pdf
import pytesseract
from deep_translator import GoogleTranslator
import os
import shutil
import pytesseract
import os
from PIL import Image  # هذه ضرورية جداً

# إعداد مسار tesseract
tesseract_path = shutil.which("tesseract") or '/usr/bin/tesseract'
pytesseract.pytesseract.tesseract_cmd = tesseract_path

def extract_text_from_image(image_path):
    try:
        # تأكد من أن ملف الصورة يفتح بشكل صحيح
        img = Image.open(image_path)
        text = pytesseract.image_to_string(img, lang='ara+eng')
        return text
    except Exception as e:
        return f"خطأ في استخراج النص: {str(e)}"


# تهيئة انستالودر
L = instaloader.Instaloader(download_videos=True, download_pictures=True, save_metadata=False)


def get_insta_media(username):
    url = f"https://www.instagram.com/stories/{username}/"
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'format': 'best',
        'outtmpl': 'story_%(id)s.mp4',
        # إضافة هذه السطور لتقليل احتمالية طلب تسجيل الدخول
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=True)
            return info.get('requested_downloads', [])
        except Exception as e:
            # إذا فشل التحميل، هذا يعني أن الحساب برايفت أو يتطلب تسجيل دخول إجباري
            print(f"فشل التحميل: {e}")
            return []


def download_video_service(url, chat_id):
    # اجعل الاسم بسيطاً جداً
    file_path = f"{chat_id}.mp4" 
    
    ydl_opts = {
        'format': 'best', 
        'outtmpl': file_path, 
        'noplaylist': True
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    
    return file_path



def convert_to_pdf(image_path, pdf_path):
    with open(pdf_path, "wb") as f:
        f.write(img2pdf.convert(image_path))



def extract_text_from_image(image_path):
    try:
        # تأكد من أن ملف الصورة يفتح بشكل صحيح
        img = Image.open(image_path)
        text = pytesseract.image_to_string(img, lang='ara+eng')
        return text
    except Exception as e:
        return f"خطأ في استخراج النص: {str(e)}"



def translate_text(text, dest_lang='ar'):
    # استخدام deep-translator بدلاً من googletrans
    translator = GoogleTranslator(source='auto', target=dest_lang)
    return translator.translate(text)

