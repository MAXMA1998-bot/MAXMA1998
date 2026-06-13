# -*- coding: utf-8 -*-
import time
import requests

# رابط السيرفر الخاص بك المستخرج تلقائياً
SERVER_API_URL = "https://astonishing-wisdom-production.up.railway.app/api/wifi_update"

def scan_iphone_airspace():
    # مصفوفة البيانات التجريبية الحية
    return [
        {"ssid": "VIP_Network_5G", "bssid": "00:14:22:01:23:45", "rssi": -48},
        {"ssid": "Max_Guest_WiFi", "bssid": "84:A1:D1:A4:B2:C1", "rssi": -62},
        {"ssid": "Airport_Free_Net", "bssid": "CC:BB:AA:11:22:33", "rssi": -79}
    ]

print("[*] بدأ العميل بالعمل... جاري بث الشبكات إلى السيرفر كل 5 ثوانٍ.")

# تشغيل البث المباشر المستمر
while True:
    try:
        current_networks = scan_iphone_airspace()
        payload = {"networks": current_networks}
        
        print("[*] جاري إرسال حزمة البيانات المحدثة...")
        response = requests.post(SERVER_API_URL, json=payload, timeout=5)
        
        print(f"[+] استجابة السيرفر: {response.status_code}")
    except Exception as e:
        print(f"[-] خطأ أثناء الاتصال بالسيرفر: {e}")
        
    time.sleep(5)
