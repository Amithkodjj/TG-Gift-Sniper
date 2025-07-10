#!/bin/bash

# =============================================================================
# TelegramGiftsBot v2.0 - Linux Auto Installer
# بوت هدايا التيليجرام - مثبت تلقائي للينكس
# =============================================================================

set -e  # خروج عند أي خطأ

# ألوان النص
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # بدون لون

# دالة طباعة رسائل ملونة
print_message() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================${NC}"
}

# فحص النظام
check_system() {
    print_header "فحص النظام"
    
    # فحص نظام التشغيل
    if [[ -f /etc/os-release ]]; then
        source /etc/os-release
        print_message "نظام التشغيل: $PRETTY_NAME"
    else
        print_error "لا يمكن تحديد نظام التشغيل"
        exit 1
    fi
    
    # فحص Python
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version | cut -d ' ' -f 2)
        print_message "Python متوفر: $PYTHON_VERSION"
    else
        print_warning "Python غير مثبت، سيتم تثبيته"
    fi
    
    # فحص Git
    if command -v git &> /dev/null; then
        print_message "Git متوفر"
    else
        print_warning "Git غير مثبت، سيتم تثبيته"
    fi
}

# تثبيت المتطلبات
install_requirements() {
    print_header "تثبيت المتطلبات"
    
    # تحديد مدير الحزم
    if command -v apt &> /dev/null; then
        PKG_MANAGER="apt"
        UPDATE_CMD="apt update && apt upgrade -y"
        INSTALL_CMD="apt install -y"
    elif command -v dnf &> /dev/null; then
        PKG_MANAGER="dnf"
        UPDATE_CMD="dnf update -y"
        INSTALL_CMD="dnf install -y"
    elif command -v yum &> /dev/null; then
        PKG_MANAGER="yum"
        UPDATE_CMD="yum update -y"
        INSTALL_CMD="yum install -y"
    else
        print_error "مدير الحزم غير مدعوم"
        exit 1
    fi
    
    print_message "مدير الحزم المستخدم: $PKG_MANAGER"
    
    # تحديث النظام
    print_message "تحديث النظام..."
    sudo $UPDATE_CMD
    
    # تثبيت Python و Git
    print_message "تثبيت Python و Git..."
    if [[ $PKG_MANAGER == "apt" ]]; then
        sudo $INSTALL_CMD python3 python3-pip python3-venv git curl wget
    else
        sudo $INSTALL_CMD python3 python3-pip python3-devel git curl wget
    fi
}

# إنشاء مستخدم البوت
create_bot_user() {
    print_header "إعداد مستخدم البوت"
    
    # فحص وجود المستخدم
    if id "telegrambot" &>/dev/null; then
        print_warning "المستخدم telegrambot موجود بالفعل"
        read -p "هل تريد المتابعة؟ (y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    else
        print_message "إنشاء مستخدم telegrambot..."
        sudo adduser --disabled-login --gecos "" telegrambot
    fi
    
    # إنشاء مجلد البوت
    BOT_DIR="/home/telegrambot/TelegramGiftsBot"
    sudo mkdir -p $BOT_DIR
    sudo chown telegrambot:telegrambot $BOT_DIR
}

# تنزيل وإعداد البوت
setup_bot() {
    print_header "إعداد البوت"
    
    # نسخ الملفات للمستخدم الجديد
    print_message "نسخ ملفات البوت..."
    sudo -u telegrambot cp -r . $BOT_DIR/
    
    # الانتقال لمجلد البوت
    cd $BOT_DIR
    
    # إنشاء البيئة الافتراضية
    print_message "إنشاء البيئة الافتراضية..."
    sudo -u telegrambot python3 -m venv venv
    
    # تثبيت المتطلبات
    print_message "تثبيت متطلبات Python..."
    sudo -u telegrambot $BOT_DIR/venv/bin/pip install --upgrade pip
    sudo -u telegrambot $BOT_DIR/venv/bin/pip install -r requirements.txt
    
    # إنشاء ملف .env
    if [[ ! -f $BOT_DIR/.env ]]; then
        print_message "إنشاء ملف .env..."
        sudo -u telegrambot cp $BOT_DIR/sample.env $BOT_DIR/.env
        print_warning "تحرير ملف .env وإضافة التوكن و ID المطلوبين:"
        echo "  - TELEGRAM_BOT_TOKEN"
        echo "  - TELEGRAM_USER_ID"
    fi
}

# إنشاء خدمة النظام
create_systemd_service() {
    print_header "إنشاء خدمة النظام"
    
    SERVICE_FILE="/etc/systemd/system/telegrambot.service"
    
    print_message "إنشاء ملف خدمة systemd..."
    
    sudo tee $SERVICE_FILE > /dev/null <<EOF
[Unit]
Description=Telegram Gifts Bot
After=network.target

[Service]
Type=simple
User=telegrambot
Group=telegrambot
WorkingDirectory=$BOT_DIR
Environment=PATH=$BOT_DIR/venv/bin
ExecStart=$BOT_DIR/venv/bin/python main.py
Restart=always
RestartSec=3

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$BOT_DIR

[Install]
WantedBy=multi-user.target
EOF

    # تحديث systemd
    sudo systemctl daemon-reload
    sudo systemctl enable telegrambot.service
    
    print_message "تم إنشاء الخدمة بنجاح!"
}

# إعداد جدار الحماية الأساسي
setup_firewall() {
    print_header "إعداد جدار الحماية"
    
    if command -v ufw &> /dev/null; then
        print_message "إعداد UFW..."
        sudo ufw --force enable
        sudo ufw allow ssh
        print_message "تم تفعيل جدار الحماية UFW"
    elif command -v firewall-cmd &> /dev/null; then
        print_message "إعداد firewalld..."
        sudo systemctl enable firewalld
        sudo systemctl start firewalld
        sudo firewall-cmd --permanent --add-service=ssh
        sudo firewall-cmd --reload
        print_message "تم تفعيل جدار الحماية firewalld"
    else
        print_warning "لم يتم العثور على جدار حماية، تأكد من الأمان يدوياً"
    fi
}

# إنشاء سكريبت مراقبة
create_monitoring_script() {
    print_header "إنشاء سكريبت المراقبة"
    
    MONITOR_SCRIPT="/home/telegrambot/monitor_bot.sh"
    
    sudo -u telegrambot tee $MONITOR_SCRIPT > /dev/null <<'EOF'
#!/bin/bash

# سكريبت مراقبة بوت التيليجرام

echo "=== حالة خدمة البوت ==="
systemctl status telegrambot.service --no-pager

echo -e "\n=== آخر 20 رسالة سجل ==="
journalctl -u telegrambot.service -n 20 --no-pager

echo -e "\n=== استهلاك الموارد ==="
top -bn1 -p $(pgrep -f "python main.py") | head -n 20

echo -e "\n=== مساحة القرص ==="
df -h /home/telegrambot/TelegramGiftsBot

echo -e "\n=== حجم ملفات البوت ==="
du -sh /home/telegrambot/TelegramGiftsBot
EOF

    sudo chmod +x $MONITOR_SCRIPT
    sudo chown telegrambot:telegrambot $MONITOR_SCRIPT
    
    print_message "تم إنشاء سكريبت المراقبة: $MONITOR_SCRIPT"
}

# عرض الخلاصة النهائية
show_summary() {
    print_header "ملخص التثبيت"
    
    echo -e "${GREEN}✅ تم التثبيت بنجاح!${NC}"
    echo
    echo -e "${YELLOW}الخطوات المطلوبة لإكمال الإعداد:${NC}"
    echo "1. تحرير ملف .env وإضافة البيانات المطلوبة:"
    echo -e "   ${BLUE}sudo nano $BOT_DIR/.env${NC}"
    echo
    echo "2. بدء البوت:"
    echo -e "   ${BLUE}sudo systemctl start telegrambot.service${NC}"
    echo
    echo "3. فحص حالة البوت:"
    echo -e "   ${BLUE}sudo systemctl status telegrambot.service${NC}"
    echo
    echo -e "${YELLOW}أوامر مفيدة:${NC}"
    echo -e "• مراقبة البوت: ${BLUE}/home/telegrambot/monitor_bot.sh${NC}"
    echo -e "• إيقاف البوت: ${BLUE}sudo systemctl stop telegrambot.service${NC}"
    echo -e "• إعادة تشغيل: ${BLUE}sudo systemctl restart telegrambot.service${NC}"
    echo -e "• السجلات: ${BLUE}sudo journalctl -u telegrambot.service -f${NC}"
    echo
    echo -e "${GREEN}🎉 مبروك! البوت جاهز للاستخدام${NC}"
}

# الدالة الرئيسية
main() {
    clear
    print_header "🤖 مثبت بوت هدايا التيليجرام للينكس"
    echo -e "${BLUE}هذا السكريبت سيقوم بتثبيت وإعداد البوت تلقائياً${NC}"
    echo
    
    # طلب تأكيد من المستخدم
    read -p "هل تريد المتابعة؟ (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_message "تم إلغاء التثبيت"
        exit 0
    fi
    
    # بدء عملية التثبيت
    check_system
    install_requirements
    create_bot_user
    setup_bot
    create_systemd_service
    setup_firewall
    create_monitoring_script
    show_summary
}

# تشغيل السكريبت
main "$@" 