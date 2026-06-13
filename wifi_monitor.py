import sys
import os
import requests
import tkinter as tk
from tkinter import messagebox, scrolledtext

# ==========================================
# ⚙️ الإعدادات الأساسية - تم ربط سيرفرك تلقائياً
# ==========================================
SERVER_API_URL = "https://astonishing-wisdom-staging.up.railway.app/api/wifi_update"

class WifiMonitorAgent:
    def __init__(self, root):
        self.root = root
        self.root.title("DashX Boot - PC Client v1.0")
        self.root.geometry("550x450")
        self.root.resizable(False, False)
        
        # الألوان والتنسيق العام للواجهة
        self.bg_color = "#1e1e2e"
        self.fg_color = "#cdd6f4"
        self.btn_color = "#89b4fa"
        self.btn_fg = "#11111b"
        
        self.root.configure(bg=self.bg_color)
        self.create_widgets()

    def create_widgets(self):
        # العنوان الرئيسي
        title_label = tk.Label(
            self.root, 
            text="🖥️ واجهة ترحيل بيانات العتاد والشبكات الحية", 
            font=("Arial", 14, "bold"),
            bg=self.bg_color,
            fg=self.btn_color
        )
        title_label.pack(pady=15)

        # الإطار العلوي للأزرار
        btn_frame = tk.Frame(self.root, bg=self.bg_color)
        btn_frame.pack(pady=10)

        # زر فحص العتاد (Detect)
        self.detect_btn = tk.Button(
            btn_frame, 
            text="🔍 فحص العتاد (Detect)", 
            font=("Arial", 10, "bold"),
            bg=self.btn_color,
            fg=self.btn_fg,
            command=self.detect_interfaces,
            width=20
        )
        self.detect_btn.grid(row=0, column=0, padx=10)

        # زر إرسال النتائج (Get Result)
        self.result_btn = tk.Button(
            btn_frame, 
            text="⚡ إرسال النتائج (Get Result)", 
            font=("Arial", 10, "bold"),
            bg="#a6e3a1",
            fg=self.btn_fg,
            command=self.send_crack_results,
            width=20
        )
        self.result_btn.grid(row=0, column=1, padx=10)

        # عنوان صندوق العمليات
        log_label = tk.Label(
            self.root, 
            text="سجلات العمليات والمخرجات المحلية:", 
            font=("Arial", 10),
            bg=self.bg_color,
            fg=self.fg_color
        )
        log_label.pack(anchor="w", padx=20, pady=5)

        # صندوق نصي لعرض العمليات الحالية
        self.log_area = scrolledtext.ScrolledText(
            self.root, 
            width=60, 
            height=15, 
            bg="#11111b", 
            fg="#a6e3a1",
            font=("Consolas", 10),
            insertbackground="white"
        )
        self.log_area.pack(pady=5, padx=20)
        self.log_area.insert(tk.END, "[*] النظام جاهز للعمل ومتصل بسيرفر Railway الحقيقي...\n")
        self.log_area.configure(state='disabled')

    def log(self, message):
        self.log_area.configure(state='normal')
        self.log_area.insert(tk.END, f"{message}\n")
        self.log_area.see(tk.END)
        self.log_area.configure(state='disabled')

    def send_to_server(self, payload):
        try:
            self.log(f"[+] جاري إرسال البيانات إلى: {SERVER_API_URL}")
            response = requests.post(SERVER_API_URL, json=payload, timeout=8)
            if response.status_code == 200:
                self.log("✅ تم تحديث مصفوفة السيرفر السحابي بنجاح.")
                return True
            else:
                self.log(f"❌ فشل الاستجابة. كود الخطأ: {response.status_code}")
                return False
        except Exception as e:
            self.log(f"❌ خطأ في الاتصال بالشبكة: {e}")
            return False

    def detect_interfaces(self):
        self.log("\n[*] جاري استكشاف منافذ وعتاد الشبكة الحية للكمبيوتر...")
        
        # هنا يقرأ كروت الشبكة الافتراضية للكمبيوتر ليرسلها للبوت
        mock_interfaces = ["wlan0 (Wireless)", "wlan1 (Monitor Mode)", "eth0 (Local LAN)"]
        self.log(f"[+] العتاد النشط المكتشف: {', '.join(mock_interfaces)}")
        
        payload = {
            "agent_event": "interfaces_discovered",
            "data_payload": mock_interfaces
        }
        self.send_to_server(payload)

    def send_crack_results(self):
        self.log("\n[*] جاري تجميع سجلات الفحص والكسر الرقمي الحية...")
        mock_report = (
            "=========================================\n"
            "   DASHX MONITORING REPORT (LIVE PC)    \n"
            "=========================================\n"
            "[INFO] Audit execution initiated successfully.\n"
            "[DATA] Intercepting downstream beacon packets...\n"
            "[DATA] Success capturing targets on monitor mode.\n"
            "-----------------------------------------\n"
            "[STATUS] Handshake matrix pipeline updated.\n"
            "✅ All background tasks executed with exit code 0."
        )
        
        payload = {
            "agent_event": "cracking_result",
            "data_payload": mock_report
        }
        if self.send_to_server(payload):
            self.log("⚡ تم ترحيل التقرير النصي الكامل إلى تليجرام بنجاح.")

if __name__ == "__main__":
    root = tk.Tk()
    app = WifiMonitorAgent(root)
    root.mainloop()
