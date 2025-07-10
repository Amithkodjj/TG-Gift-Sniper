# 🐧 TelegramGiftsBot - Linux Setup Guide
# دليل تثبيت بوت هدايا التيليجرام على نظام لينكس

## 🎯 **نظرة عامة**
هذا الدليل يشرح كيفية تثبيت وتشغيل بوت هدايا التيليجرام على خوادم لينكس بطريقة آمنة ومستقرة.

---

## 🔧 **متطلبات النظام**

### **الحد الأدنى:**
- Ubuntu 20.04+ / CentOS 8+ / Debian 11+
- Python 3.8+
- 512MB RAM
- 1GB مساحة فارغة
- اتصال انترنت مستقر

### **موصى به:**
- Ubuntu 22.04 LTS
- Python 3.11+
- 1GB RAM
- 2GB مساحة فارغة

---

## 📥 **التثبيت السريع (Ubuntu/Debian)**

### **1. تحديث النظام:**
```bash
sudo apt update && sudo apt upgrade -y
```

### **2. تثبيت Python و pip:**
```bash
sudo apt install python3 python3-pip python3-venv git -y
```

### **3. إنشاء مستخدم للبوت (أمان إضافي):**
```bash
sudo adduser --disabled-login --gecos "" telegrambot
sudo su - telegrambot
```

### **4. استنساخ المشروع:**
```bash
cd /home/telegrambot
git clone <repository-url> TelegramGiftsBot
cd TelegramGiftsBot
```

### **5. إنشاء بيئة افتراضية:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### **6. تثبيت المتطلبات:**
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### **7. إعداد متغيرات البيئة:**
```bash
cp sample.env .env
nano .env
```

**أضف البيانات التالية:**
```env
TELEGRAM_BOT_TOKEN="your_bot_token_here"
TELEGRAM_USER_ID="your_user_id_here"
```

### **8. اختبار البوت:**
```bash
python main.py
```

---

## 🎛️ **إعداد كخدمة نظام (Systemd)**

### **1. إنشاء ملف خدمة:**
```bash
sudo nano /etc/systemd/system/telegrambot.service
```

**محتوى الملف:**
```ini
[Unit]
Description=Telegram Gifts Bot
After=network.target

[Service]
Type=simple
User=telegrambot
Group=telegrambot
WorkingDirectory=/home/telegrambot/TelegramGiftsBot
Environment=PATH=/home/telegrambot/TelegramGiftsBot/venv/bin
ExecStart=/home/telegrambot/TelegramGiftsBot/venv/bin/python main.py
Restart=always
RestartSec=3

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/home/telegrambot/TelegramGiftsBot

[Install]
WantedBy=multi-user.target
```

### **2. تفعيل وبدء الخدمة:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable telegrambot.service
sudo systemctl start telegrambot.service
```

### **3. فحص حالة الخدمة:**
```bash
sudo systemctl status telegrambot.service
```

---

## 📊 **مراقبة وإدارة البوت**

### **أوامر إدارة الخدمة:**
```bash
# إيقاف البوت
sudo systemctl stop telegrambot.service

# إعادة تشغيل البوت
sudo systemctl restart telegrambot.service

# فحص السجلات
sudo journalctl -u telegrambot.service -f

# فحص آخر 50 رسالة سجل
sudo journalctl -u telegrambot.service -n 50
```

### **مراقبة أداء البوت:**
```bash
# فحص استهلاك الذاكرة والمعالج
top -p $(pgrep -f "python main.py")

# فحص حجم الملفات
du -sh /home/telegrambot/TelegramGiftsBot
```

---

## 🔥 **تثبيت على CentOS/RHEL/Rocky Linux**

### **1. تحديث النظام:**
```bash
sudo dnf update -y
```

### **2. تثبيت المتطلبات:**
```bash
sudo dnf install python3 python3-pip python3-devel git -y
```

### **3. متابعة باقي الخطوات كما في Ubuntu**
(نفس الخطوات من 3 إلى 8)

---

## 🛡️ **إعدادات الأمان**

### **1. جدار الحماية (UFW):**
```bash
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow from <your-ip> to any port 22
```

### **2. تحديث دوري:**
```bash
# إضافة cron job للتحديث التلقائي
sudo crontab -e

# أضف هذا السطر للتحديث يومياً الساعة 3 صباحاً
0 3 * * * apt update && apt upgrade -y
```

### **3. نسخ احتياطية:**
```bash
# إنشاء نسخة احتياطية يومية
sudo crontab -e

# أضف للنسخ الاحتياطي الساعة 2 صباحاً
0 2 * * * tar -czf /backup/telegrambot-$(date +\%Y\%m\%d).tar.gz /home/telegrambot/TelegramGiftsBot
```

---

## 📱 **الإعداد للاستخدام المتقدم**

### **استخدام Nginx كـ Reverse Proxy (اختياري):**
```bash
sudo apt install nginx -y

# إنشاء ملف تكوين Nginx
sudo nano /etc/nginx/sites-available/telegrambot

# محتوى الملف:
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

# تفعيل الموقع
sudo ln -s /etc/nginx/sites-available/telegrambot /etc/nginx/sites-enabled/
sudo systemctl restart nginx
```

---

## 🔧 **استكشاف الأخطاء الشائعة**

### **خطأ: `ModuleNotFoundError`**
```bash
# تأكد من تفعيل البيئة الافتراضية
source venv/bin/activate
pip install -r requirements.txt
```

### **خطأ: `Permission denied`**
```bash
# تصحيح الأذونات
sudo chown -R telegrambot:telegrambot /home/telegrambot/TelegramGiftsBot
sudo chmod +x /home/telegrambot/TelegramGiftsBot/main.py
```

### **خطأ: البوت لا يستجيب**
```bash
# فحص الاتصال
ping api.telegram.org

# فحص متغيرات البيئة
python3 -c "import os; from dotenv import load_dotenv; load_dotenv(); print('Token:', bool(os.getenv('TELEGRAM_BOT_TOKEN')))"
```

---

## 🚀 **نصائح للأداء**

### **1. تحسين استهلاك الذاكرة:**
```bash
# إضافة swap file
sudo fallocate -l 1G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

### **2. مراقبة مستمرة:**
```bash
# تثبيت htop لمراقبة أفضل
sudo apt install htop -y

# مراقبة البوت
watch -n 5 'systemctl status telegrambot.service'
```

---

## 📋 **قائمة فحص ما بعد التثبيت**

- [ ] البوت يعمل بدون أخطاء
- [ ] الخدمة تبدأ تلقائياً مع النظام
- [ ] السجلات تعمل بشكل صحيح
- [ ] النسخ الاحتياطية مُعدة
- [ ] جدار الحماية مُفعل
- [ ] مراقبة النظام تعمل

---

## 🆘 **الدعم والمساعدة**

### **فحص السجلات:**
```bash
# سجلات النظام
sudo journalctl -u telegrambot.service --since "1 hour ago"

# سجلات البوت (إن وجدت)
tail -f /home/telegrambot/TelegramGiftsBot/logs/*.log
```

### **إعادة تعيين كاملة:**
```bash
# إيقاف البوت
sudo systemctl stop telegrambot.service

# حذف البيانات القديمة
rm -rf /home/telegrambot/TelegramGiftsBot/users/*
rm -rf /home/telegrambot/TelegramGiftsBot/logs/*

# إعادة التشغيل
sudo systemctl start telegrambot.service
```

---

## ✅ **تم الانتهاء!**

بوتك أصبح جاهزاً للعمل على لينكس بشكل مستقر وآمن! 🎉

للتحديثات والمساعدة، تابع السجلات بانتظام واعمل نسخ احتياطية دورية. 