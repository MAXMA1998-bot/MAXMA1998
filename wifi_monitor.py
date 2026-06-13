import time
import requests

SERVER_API_URL = "https://astonishing-wisdom-production.up.railway.app/api/wifi_update"

def start_monitoring():
    time.sleep(10)
    while True:
        try:
            payload = {
                "networks": [
                    {"ssid": "VIP_Network_5G", "bssid": "00:14:22:01:23:45", "rssi": -48},
                    {"ssid": "Max_Guest_WiFi", "bssid": "84:A1:D1:A4:B2:C1", "rssi": -62},
                    {"filename": "Airport_Free_Net", "bssid": "CC:BB:AA:11:22:33", "rssi": -79}
                ]
            }
            requests.post(SERVER_API_URL, json=payload, timeout=5)
        except Exception as e:
            pass
            
        time.sleep(5)
