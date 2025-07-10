# 🔧 Environment Setup Guide - دليل إعداد البيئة

## 📋 ملف `.env` المطلوب

### 🔑 **المتغيرات الأساسية (مطلوبة):**

```env
# التوكن الخاص بالبوت من @BotFather
TELEGRAM_BOT_TOKEN="123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"

# الـ ID الخاص بك كمالك البوت (من @userinfobot)
TELEGRAM_USER_ID="123456789"
```

### ⚙️ **المتغيرات الاختيارية (يمكن إضافتها):**

```env
# نسبة العمولة (1% إلى 20%) - افتراضي: 5%
COMMISSION_RATE="0.05"

# وضع التطوير للاختبار - افتراضي: false
DEV_MODE="false"

# الحد الأقصى لعدد الملفات لكل مستخدم - افتراضي: 3
MAX_PROFILES="3"

# فترة التأخير بين المشتريات - افتراضي: 0.3 ثانية
PURCHASE_COOLDOWN="0.3"
```

---

## 🚀 **خطوات الإعداد السريع:**

### **1. إنشاء ملف `.env`:**
```bash
# في مجلد البوت
touch .env
```

### **2. إضافة المتغيرات الأساسية:**
```env
TELEGRAM_BOT_TOKEN="ضع_التوكن_هنا"
TELEGRAM_USER_ID="ضع_الايدي_هنا"
```

### **3. (اختياري) إضافة إعدادات متقدمة:**
```env
# لتغيير نسبة العمولة لـ 3%
COMMISSION_RATE="0.03"

# لزيادة عدد الملفات لـ 5
MAX_PROFILES="5"
```

---

## 🔍 **الفرق عن النسخة السابقة:**

| **المتغير** | **النسخة القديمة** | **النسخة الجديدة v2.0** |
|-------------|-------------------|------------------------|
| `TELEGRAM_BOT_TOKEN` | ✅ مطلوب | ✅ مطلوب (نفسه) |
| `TELEGRAM_USER_ID` | ✅ مطلوب | ✅ مطلوب (نفسه) |
| `COMMISSION_RATE` | ❌ غير موجود | ✅ جديد (اختياري) |
| `DEV_MODE` | ❌ غير موجود | ✅ جديد (اختياري) |
| `MAX_PROFILES` | ❌ غير موجود | ✅ جديد (اختياري) |

---

## ⚡ **إعداد سريع (Copy & Paste):**

```env
# ========================================
# TelegramGiftsBot v2.0.0 Configuration
# ========================================

# 🔑 REQUIRED - مطلوبة
TELEGRAM_BOT_TOKEN="YOUR_BOT_TOKEN_HERE"
TELEGRAM_USER_ID="YOUR_USER_ID_HERE"

# ⚙️ OPTIONAL - اختيارية (احذف # لتفعيلها)
# COMMISSION_RATE="0.05"
# DEV_MODE="false"
# MAX_PROFILES="3"
# PURCHASE_COOLDOWN="0.3"
```

---

## 💡 **نصائح مهمة:**

### **✅ ما تحتاجه بالضرورة:**
- فقط `TELEGRAM_BOT_TOKEN` و `TELEGRAM_USER_ID`
- باقي المتغيرات اختيارية ولها قيم افتراضية

### **⚠️ تحذيرات:**
- **لا تشارك** ملف `.env` مع أحد
- **احتفظ بنسخة احتياطية** من التوكن
- **لا تضع** ملف `.env` في Git

### **🔧 استكشاف الأخطاء:**
```bash
# إذا لم يعمل البوت، تحقق من:
cat .env  # للتأكد من وجود الملف
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(os.getenv('TELEGRAM_BOT_TOKEN'))"
```

---

## 🎯 **خلاصة:**

**نعم، ملف `.env` سيبقى بسيط جداً!** 

المطلوب فقط:
```env
TELEGRAM_BOT_TOKEN="your_token"
TELEGRAM_USER_ID="your_id"
```

والباقي اختياري لمن يريد تخصيصات متقدمة. 🚀 