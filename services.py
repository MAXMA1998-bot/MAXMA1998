import os
import re
import shutil
import yt_dlp
import img2pdf
import pytesseract
from PIL import Image
from urllib.parse import urlparse
from deep_translator import GoogleTranslator
from PIL import Image, ImageEnhance, ImageFilter

# --- الإعدادات والمصادر ---
tesseract_path = shutil.which("tesseract") or '/usr/bin/tesseract'
pytesseract.pytesseract.tesseract_cmd = tesseract_path

def get_safe_filename(name):
    """تأمين اسم الملف ومنع التنقل بين المجلدات"""
    return re.sub(r'[^a-zA-Z0-9_\.]', '', str(name))

def is_safe_url(url):
    """التحقق من صحة الرابط قبل تحميله"""
    parsed = urlparse(url)
    return parsed.scheme in ('http', 'https')

# --- الخدمات الأساسية ---

def download_video_service(url, file_path):
    if not is_safe_url(url):
        raise ValueError("الرابط المرسل غير آمن!")
    
    safe_name = get_safe_filename(os.path.basename(file_path))
    final_path = os.path.join(os.getcwd(), safe_name)
    
    ydl_opts = {
        'format': 'best',
        'outtmpl': final_path,
        'noplaylist': True,
        'max_filesize': 50 * 1024 * 1024,  # حد أقصى للحماية: 50 ميجابايت
        'quiet': True
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    return final_path

def extract_text_from_image(image_path):
    if not os.path.exists(image_path): 
        return ""
    try:
        with Image.open(image_path) as img:
            return pytesseract.image_to_string(img, lang='ara+eng').strip()
    except Exception:
        return ""

def translate_text(text, dest_lang='ar'):
    if not text.strip():
        return "لا يوجد نص صالح للترجمة."
    try:
        return GoogleTranslator(source='auto', target=dest_lang).translate(text[:2000])
    except Exception:
        return "خطأ أثناء عملية الترجمة."

def convert_to_pdf(image_path, pdf_path):
    if not os.path.exists(image_path): 
        return
    safe_pdf = get_safe_filename(pdf_path)
    with open(safe_pdf, "wb") as f:
        f.write(img2pdf.convert(image_path))


def enhance_image(input_path, output_path):
    if not os.path.exists(input_path):
        raise Exception("الصورة غير موجودة")
    with Image.open(input_path) as img:
        img = img.convert("RGB")
        width, height = img.size
        img = img.resize((width * 2, height * 2), Image.LANCZOS)
        img = img.filter(ImageFilter.SHARPEN)
        contrast = ImageEnhance.Contrast(img)
        img = contrast.enhance(1.3)
        sharpness = ImageEnhance.Sharpness(img)
        img = sharpness.enhance(2.0)
        img.save(output_path, quality=100)


def get_image_metadata(image_path):
    with Image.open(image_path) as img:
        width, height = img.size
        result = {
            "format": img.format,
            "width": width,
            "height": height,
            "mode": img.mode,
            "camera": "غير معروف",
            "date": "غير متوفر",
            "software": "غير معروف",
            "gps": False
        }
        exif = img.getexif()
        if exif:
            readable = {}
            for tag_id, value in exif.items():
                tag = TAGS.get(tag_id, str(tag_id))
                try:
                    readable[tag] = str(value)
                except:
                    pass
            if "Model" in readable:
                result["camera"] = readable["Model"]
            if "DateTime" in readable:
                result["date"] = readable["DateTime"]
            if "Software" in readable:
                result["software"] = readable["Software"]
            if "GPSInfo" in readable:
                result["gps"] = True
        return result
        
