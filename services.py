import os
import re
import shutil
import yt_dlp
import img2pdf
import pytesseract
import instaloader
from PIL import Image
from urllib.parse import urlparse
from deep_translator import GoogleTranslator

# --- الإعدادات ---
tesseract_path = shutil.which("tesseract") or '/usr/bin/tesseract'
pytesseract.pytesseract.tesseract_cmd = tesseract_path
L = instaloader.Instaloader(download_videos=True, download_pictures=True, save_metadata=False)

# --- وظائف الأمان ---
def get_safe_filename(name):
    """تأمين اسم الملف ومنع التنقل بين المجلدات"""
    return re.sub(r'[^a-zA-Z0-9_\.]', '', str(name))

def is_safe_url(url):
    """التحقق من صحة الرابط"""
    parsed = urlparse(url)
    return parsed.scheme in ('http', 'https')

# --- الخدمات ---

def download_video_service(url, file_path):
    if not is_safe_url(url):
        raise ValueError("رابط غير آمن!")
    
    # تأمين المسار: التأكد أن الملف يُحفظ في المجلد الحالي فقط
    safe_name = get_safe_filename(os.path.basename(file_path))
    final_path = os.path.join(os.getcwd(), safe_name)
    
    ydl_opts = {
        'format': 'best',
        'outtmpl': final_path,
        'noplaylist': True,
        'max_filesize': 50 * 1024 * 1024, # حماية الذاكرة
        'quiet': True
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    return final_path

def extract_text_from_image(image_path):
    # حماية: التأكد من وجود الملف قبل المعالجة
    if not os.path.exists(image_path): return "الملف غير موجود."
    try:
        with Image.open(image_path) as img:
            return pytesseract.image_to_string(img, lang='ara+eng').strip()
    except Exception as e:
        return f"خطأ: {str(e)}"

def translate_text(text, dest_lang='ar'):
    try:
        return GoogleTranslator(source='auto', target=dest_lang).translate(text[:2000]) # تحديد الطول للحماية
    except Exception as e:
        return "خطأ في الترجمة."

def convert_to_pdf(image_path, pdf_path):
    if not os.path.exists(image_path): return
    safe_pdf = get_safe_filename(pdf_path)
    with open(safe_pdf, "wb") as f:
        f.write(img2pdf.convert(image_path))
