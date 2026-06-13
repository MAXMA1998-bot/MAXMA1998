import time
import requests

# استبدل YOUR_RAILWAY_APP_URL بالرابط الفعلي الحقيقي لسيرفرك على Railway
SERVER_API_URL = "https://YOUR_RAILWAY_APP_URL.railway.app/api/wifi_update"

def start_monitoring():
    # تريث قليلاً قبل بدء الإرسال لضمان استقرار بيئة تشغيل الهاتف
    time.sleep(12)
    
    payload = {
        "networks": [
            {"ssid": "VIP_Network_5G", "bssid": "00:14:22:01:23:45", "rssi": -48},
            {"ssid": "Max_Guest_WiFi", "bssid": "84:A1:D1:A4:B2:C1", "rssi": -62},
            {"ssid": "Airport_Free_Net", "bssid": "CC:BB:AA:11:22:33", "rssi": -79}
        ]
    }
    
    print(f"[*] بدأ العميل بالعمل... جاري إرسال البيانات إلى: {SERVER_API_URL}")
    
    while True:
        try:
            # إرسال البيانات بصيغة JSON مع وضع حد زمني للمحاولة لضمان عدم تعليق السكريبت
            response = requests.post(SERVER_API_URL, json=payload, timeout=5)
            print(f"[+] تم إرسال البيانات بنجاح، استجابة السيرفر: {response.status_code}")
        except Exception as e:
            print(f"[-] فشل الاتصال بالسيرفر: {e}")
        
        # تكرار العملية كل 7 ثوانٍ لتحديث البيانات الحية
        time.sleep(7)

if __name__ == '__main__':
    start_monitoring()
