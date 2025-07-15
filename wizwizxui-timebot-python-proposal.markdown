# پیشنهاد پروژه: پیاده‌سازی ربات wizwizxui-timebot در پایتون

## مقدمه
این سند پیشنهاد پروژه‌ای جامع برای توسعه یک ربات تلگرامی مشابه wizwizxui-timebot ([مخزن GitHub اصلی](https://github.com/wizwizdev/wizwizxui-timebot)) است که با پایتون پیاده‌سازی خواهد شد. ربات اصلی در PHP نوشته شده و برای مدیریت پنل‌های x-ui (پنل‌های کنترلی وب برای سرورهای VPN/پروکسی مانند V2Ray) طراحی شده است. این ربات ویژگی‌های گسترده‌ای مانند پردازش پرداخت، مدیریت پیکربندی‌های VPN، و ابزارهای مدیریتی ارائه می‌دهد و به‌ویژه برای بازار ایران با پشتیبانی از درگاه‌های پرداخت محلی مانند زرین‌پال و نکست‌پی بهینه شده است. این پیشنهاد پروژه یک نقشه راه دقیق برای توسعه‌دهنده فراهم می‌کند تا رباتی مشابه را با پایتون، با معماری ماژولار، قابلیت مقیاس‌پذیری، و مستندات جامع پیاده‌سازی کند.

## توصیف پروژه
ربات پیشنهادی یک ربات تلگرامی است که با API تلگرام و API پنل‌های x-ui (مانند Marzban، Sanaei، Vaxilu) تعامل می‌کند تا امکان مدیریت اشتراک‌های VPN، پردازش پرداخت‌ها، و عملیات سرور را فراهم کند. این ربات برای دو گروه اصلی طراحی شده است:
- **کاربران**: برای خرید، تمدید، و مدیریت پیکربندی‌های VPN (مانند vless، vmess، trojan) با قابلیت‌هایی مانند تولید کد QR، مشاهده اطلاعات پیکربندی، و مدیریت کیف پول.
- **مدیران**: برای مدیریت سرورها، کاربران، و گزارش‌های مالی، از جمله پشتیبان‌گیری، ردیابی کاربران، و مدیریت کدهای تخفیف.

پروژه با پایتون 3.10+ توسعه داده خواهد شد و از کتابخانه‌های استاندارد مانند `python-telegram-bot` (نسخه 20.7) برای تعامل با تلگرام، `requests` برای فراخوانی‌های API، `SQLAlchemy` برای مدیریت پایگاه داده، و `APScheduler` برای زمان‌بندی وظایف استفاده می‌کند. ربات باید با چندین نسخه پنل x-ui سازگار باشد و از پروتکل‌های مختلف (xtls، tls، reality، Grpc، ws، tcp) پشتیبانی کند.

## ویژگی‌های کلیدی
ویژگی‌های ربات پیشنهادی مشابه نسخه اصلی است و به دسته‌های زیر تقسیم می‌شود:

| **دسته‌بندی**              | **ویژگی‌ها**                                                                 |
|-----------------------------|------------------------------------------------------------------------------|
| **پردازش پرداخت**          | ادغام با درگاه‌های زرین‌پال، نکست‌پی، و nowpayments؛ پشتیبانی از پرداخت با ارز ریال؛ اعتبارسنجی تراکنش‌ها و مدیریت کیف پول کاربران. |
| **پشتیبانی از پروتکل‌ها**  | پشتیبانی از پروتکل‌های xtls، tls، reality، Grpc، ws، tcp و پیکربندی‌های vless، vmess، trojan؛ سازگاری با پنل‌های Marzban، Sanaei، Niduka Akalanka، Alireza، و Vaxilu. |
| **مدیریت کاربران**         | - تمدید سرویس (افزودن زمان/حجم)<br>- نمایش پروفایل پیکربندی<br>- جستجوی پیکربندی‌های خریداری‌شده<br>- مشاهده اطلاعات پیکربندی در وب (لینک/QR)<br>- تولید کد QR برای پیکربندی<br>- حذف پیکربندی توسط کاربر<br>- مدیریت کیف پول (شارژ، انتقال موجودی)<br>- احراز هویت کاربر (مانند تأیید شماره تلفن یا عضویت در کانال). |
| **مدیریت پیکربندی**        | - افزودن حجم/زمان به پیکربندی<br>- قطع/اتصال مجدد با UUID جدید<br>- به‌روزرسانی اتصالات<br>- تغییر نام پیکربندی (تصادفی یا سفارشی)<br>- اشتراک هوشمند (فیلتر بر اساس پروتکل/سرور)<br>- جابجایی خودکار پیکربندی بین سرورها. |
| **ابزارهای مدیریتی**      | - پشتیبان‌گیری از پنل x-ui (دیتابیس و تنظیمات)<br>- مدیریت زیرکمیسیون/کمیسیون برای نمایندگان<br>- ایجاد کدهای تخفیف/هدیه<br>- ردیابی کاربران (فعالیت، خریدها)<br>- مدیریت سرورها، دسته‌بندی‌ها، و طرح‌ها<br>- مسدود/آزادسازی کاربران<br>- افزودن/حذف مدیر<br>- نمایش موجودی سرور (مانند تعداد کاربران فعال). |
| **گزارش‌دهی و اعلان‌ها**   | - گزارش درآمد به کانال‌های تلگرامی<br>- پیام‌رسانی عمومی/خصوصی به کاربران<br>- اعلان ورود اعضای جدید<br>- هشدار پایان حجم/زمان اشتراک<br>- اعلان خرید/تمدید به مدیران. |
| **ویژگی‌های اضافی**       | - قفل اجباری کانال (اجبار به عضویت در کانال)<br>- نمایش جزئیات لینک پیکربندی<br>- فعال/غیرفعال کردن ویژگی‌ها<br>- تست حساب (بررسی اتصال پیکربندی)<br>- عملکرد کارت به کارت<br>- پشتیبانی از سفارش طراحی سفارشی (مانند رابط کاربری اختصاصی). |

## معماری پیشنهادی
معماری ربات به صورت ماژولار طراحی می‌شود تا قابلیت نگهداری، تست، و مقیاس‌پذیری را بهبود بخشد. اجزای اصلی شامل موارد زیر هستند:

1. **لایه ربات تلگرام**:
   - استفاده از `python-telegram-bot` برای مدیریت دستورات، پیام‌ها، و callbackهای تلگرامی.
   - پیاده‌سازی سیستم نقش‌ها (کاربر، مدیر، نماینده) با استفاده از پایگاه داده.
   - دستورات تلگرامی شامل `/start`، `/buy`، `/configs`، `/balance` برای کاربران و `/backup`، `/report`، `/block` برای مدیران.

2. **لایه تعامل با پنل x-ui**:
   - استفاده از `requests` برای فراخوانی‌های API به پنل‌های x-ui.
   - فرض می‌شود پنل‌های x-ui (مانند Marzban یا Sanaei) APIهای RESTful برای مدیریت کاربران، پیکربندی‌ها، و سرورها ارائه می‌دهند. توسعه‌دهنده باید مستندات API پنل‌ها را بررسی کند.
   - مدیریت خطاها و زمان‌بندی مجدد برای فراخوانی‌های API.

3. **لایه پایگاه داده**:
   - استفاده از `SQLAlchemy` با MySQL (یا SQLite برای تست) برای ذخیره اطلاعات کاربران، پیکربندی‌ها، تراکنش‌ها، و سرورها.
   - مدل‌های داده شامل `User`، `Config`، `Payment`، `Server`، `Admin`، و `DiscountCode`.

4. **لایه پرداخت**:
   - ادغام با APIهای درگاه‌های پرداخت (زرین‌پال، نکست‌پی، nowpayments).
   - مدیریت تراکنش‌ها، اعتبارسنجی پرداخت، و به‌روزرسانی موجودی کیف پول.

5. **لایه اعلان‌ها و زمان‌بندی**:
   - ارسال اعلان‌ها به کانال‌ها یا کاربران از طریق API تلگرام.
   - استفاده از `APScheduler` برای زمان‌بندی وظایف مانند هشدار پایان اشتراک یا گزارش‌های دوره‌ای.

6. **لایه سیستم**:
   - اسکریپت‌های پایتون برای وظایف سیستمی مانند پشتیبان‌گیری دیتابیس و به‌روزرسانی ربات.
   - استفاده از `subprocess` برای اجرای دستورات سیستمی (مانند پشتیبان‌گیری از دیتابیس MySQL).

### ساختار دایرکتوری پروژه
ساختار پیشنهادی دایرکتوری به صورت زیر است:

```
wizwizxui-timebot-python/
├── bot/
│   ├── __init__.py
│   ├── main.py              # نقطه ورود ربات
│   ├── handlers.py          # مدیریت دستورات و پیام‌های تلگرامی
│   ├── config_manager.py    # مدیریت پیکربندی‌های VPN
│   ├── payment.py           # ادغام با درگاه‌های پرداخت
│   ├── notifications.py     # مدیریت اعلان‌ها و پیام‌ها
│   └── auth.py             # احراز هویت کاربران (مانند قفل کانال)
├── database/
│   ├── __init__.py
│   ├── models.py            # مدل‌های پایگاه داده (SQLAlchemy)
│   ├── db.py                # تنظیمات و اتصال پایگاه داده
│   └── migrations/          # اسکریپت‌های مهاجرت دیتابیس
├── api/
│   ├── __init__.py
│   ├── xui_api.py           # تعامل با API پنل‌های x-ui
│   ├── payment_api.py       # تعامل با API درگاه‌های پرداخت
│   └── qr_code.py           # تولید کدهای QR برای پیکربندی‌ها
├── scripts/
│   ├── backup.py            # اسکریپت پشتیبان‌گیری دیتابیس
│   ├── update.py            # اسکریپت به‌روزرسانی ربات
│   └── install.py           # اسکریپت نصب وابستگی‌ها و تنظیمات
├── config/
│   ├── settings.py          # تنظیمات پروژه (کلیدهای API، دامنه‌ها)
│   ├── logging.conf         # تنظیمات لاگ‌گیری
│   └── .env.example         # نمونه فایل محیطی
├── tests/
│   ├── __init__.py
│   ├── test_handlers.py     # تست‌های واحد برای هندلرها
│   └── test_api.py          # تست‌های واحد برای APIها
├── requirements.txt          # وابستگی‌های پروژه
├── README.md                # مستندات پروژه
└── LICENSE                  # لایسنس پروژه (MIT پیشنهاد می‌شود)
```

## وابستگی‌ها
وابستگی‌های پروژه در فایل `requirements.txt` گنجانده می‌شوند:

```text
python-telegram-bot==20.7
requests==2.31.0
SQLAlchemy==2.0.23
pymysql==1.1.0
APScheduler==3.10.4
python-dotenv==1.0.0
qrcode==7.4.2
pillow==10.0.1  # برای تولید کدهای QR
pytest==7.4.0   # برای تست‌های واحد
```

## نمونه کدهای پیشرفته
برای کمک به توسعه‌دهنده، نمونه کدهای پیشرفته برای بخش‌های کلیدی ارائه شده است.

### 1. نقطه ورود ربات (`bot/main.py`)
```python
import logging
import asyncio
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from bot.handlers import start, buy_config, view_configs, admin_panel
from config.settings import TELEGRAM_BOT_TOKEN

# تنظیم لاگ‌گیری
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

async def main():
    # راه‌اندازی ربات
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # افزودن هندلرها
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("buy", buy_config))
    application.add_handler(CommandHandler("configs", view_configs))
    application.add_handler(CommandHandler("admin", admin_panel, filters=filters.User(is_admin=True)))
    
    # هندلر خطاها
    async def error_handler(update, context):
        logger.error(f"Update {update} caused error {context.error}")
    application.add_error_handler(error_handler)
    
    # اجرای ربات
    logger.info("Starting bot...")
    await application.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
```

### 2. مدیریت دستورات تلگرامی (`bot/handlers.py`)
```python
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database.models import User, Config
from api.xui_api import XUIAPI
from bot.auth import check_channel_membership

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    # بررسی عضویت در کانال (در صورت فعال بودن قفل کانال)
    if not await check_channel_membership(user.id, context):
        await update.message.reply_text("لطفاً ابتدا در کانال ما عضو شوید: @WizWizCh")
        return
    
    # دریافت یا ایجاد کاربر
    db_user = User.get_or_create(telegram_id=user.id, username=user.username)
    await update.message.reply_text(
        f"خوش آمدید {user.first_name}!\n"
        "دستورات موجود:\n/buy - خرید اشتراک\n/configs - مشاهده پیکربندی‌ها\n/balance - مشاهده موجودی"
    )

async def buy_config(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # دریافت لیست طرح‌ها از پنل x-ui
    xui_api = XUIAPI()
    plans = xui_api.get_plans()
    
    # ایجاد دکمه‌های انتخاب طرح
    keyboard = [
        [InlineKeyboardButton(plan["name"], callback_data=f"plan_{plan['id']}")]
        for plan in plans
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("لطفاً طرح مورد نظر خود را انتخاب کنید:", reply_markup=reply_markup)

async def view_configs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    configs = Config.get_user_configs(user.id)
    if not configs:
        await update.message.reply_text("شما هیچ پیکربندی فعالی ندارید.")
        return
    
    response = "پیکربندی‌های شما:\n"
    for config in configs:
        response += f"- {config.name}: {config.status} (حجم: {config.volume} GB, زمان: {config.expiry})\n"
    await update.message.reply_text(response)
```

### 3. مدل‌های پایگاه داده (`database/models.py`)
```python
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True)
    username = Column(String)
    balance = Column(Float, default=0.0)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    configs = relationship("Config", back_populates="user")
    
    @classmethod
    def get_or_create(cls, telegram_id, username):
        from database.db import session
        user = session.query(cls).filter_by(telegram_id=telegram_id).first()
        if not user:
            user = cls(telegram_id=telegram_id, username=username)
            session.add(user)
            session.commit()
        return user

class Config(Base):
    __tablename__ = 'configs'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    name = Column(String)
    status = Column(String)
    volume = Column(Float)
    expiry = Column(DateTime)
    uuid = Column(String, unique=True)
    user = relationship("User", back_populates="configs")
    
    @classmethod
    def get_user_configs(cls, telegram_id):
        from database.db import session
        return session.query(cls).join(User).filter(User.telegram_id == telegram_id).all()
```

### 4. تعامل با API پنل x-ui (`api/xui_api.py`)
```python
import requests
from config.settings import XUI_API_URL, XUI_API_TOKEN
from requests.exceptions import RequestException

class XUIAPI:
    def __init__(self):
        self.base_url = XUI_API_URL
        self.headers = {"Authorization": f"Bearer {XUI_API_TOKEN}"}
    
    def get_plans(self):
        try:
            response = requests.get(f"{self.base_url}/plans", headers=self.headers)
            response.raise_for_status()
            return response.json()
        except RequestException as e:
            raise Exception(f"Failed to fetch plans: {e}")
    
    def create_config(self, user_id, plan_id):
        try:
            payload = {"user_id": user_id, "plan_id": plan_id}
            response = requests.post(f"{self.base_url}/configs", json=payload, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except RequestException as e:
            raise Exception(f"Failed to create config: {e}")
    
    def get_config_qr(self, config_id):
        try:
            response = requests.get(f"{self.base_url}/configs/{config_id}/qr", headers=self.headers)
            response.raise_for_status()
            return response.json()
        except RequestException as e:
            raise Exception(f"Failed to get QR code: {e}")
```

### 5. ادغام پرداخت (`api/payment_api.py`)
```python
import requests
from config.settings import ZARINPAL_API_KEY

class ZarinpalAPI:
    def __init__(self):
        self.api_key = ZARINPAL_API_KEY
        self.base_url = "https://api.zarinpal.com/pg/v4/payment"
    
    def create_payment(self, amount, user_id, description="خرید اشتراک VPN"):
        payload = {
            "merchant_id": self.api_key,
            "amount": amount,
            "description": description,
            "callback_url": "https://your-domain.com/callback",
            "metadata": {"user_id": user_id}
        }
        try:
            response = requests.post(f"{self.base_url}/request.json", json=payload)
            response.raise_for_status()
            return response.json()
        except RequestException as e:
            raise Exception(f"Failed to create payment: {e}")
    
    def verify_payment(self, authority, amount):
        payload = {
            "merchant_id": self.api_key,
            "authority": authority,
            "amount": amount
        }
        try:
            response = requests.post(f"{self.base_url}/verify.json", json=payload)
            response.raise_for_status()
            return response.json()
        except RequestException as e:
            raise Exception(f"Failed to verify payment: {e}")
```

### 6. تولید کد QR (`api/qr_code.py`)
```python
import qrcode
from io import BytesIO
from telegram import InputFile

def generate_qr_code(data):
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return InputFile(buffer, filename="config_qr.png")
```

### 7. اسکریپت پشتیبان‌گیری (`scripts/backup.py`)
```python
import subprocess
import logging
from datetime import datetime
from config.settings import DB_HOST, DB_USER, DB_PASSWORD, DB_NAME

logger = logging.getLogger(__name__)

def backup_database():
    backup_file = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
    command = f"mysqldump -h {DB_HOST} -u {DB_USER} -p{DB_PASSWORD} {DB_NAME} > {backup_file}"
    try:
        subprocess.run(command, shell=True, check=True)
        logger.info(f"Backup created: {backup_file}")
        return backup_file
    except subprocess.CalledProcessError as e:
        logger.error(f"Backup failed: {e}")
        raise
```

## نصب و استقرار
### پیش‌نیازها
- سرور لینوکس (Ubuntu 20.04+ پیشنهاد می‌شود)
- پایتون 3.10+
- MySQL 8.0+ (یا SQLite برای تست)
- دسترسی به API پنل x-ui (مستندات API مورد نیاز است)
- کلیدهای API برای درگاه‌های پرداخت (زرین‌پال، نکست‌پی، nowpayments)
- توکن ربات تلگرام از BotFather

### مراحل نصب
1. **کلون کردن مخزن**:
   ```bash
   git clone https://github.com/your-repo/wizwizxui-timebot-python.git
   cd wizwizxui-timebot-python
   ```

2. **نصب وابستگی‌ها**:
   ```bash
   pip install -r requirements.txt
   ```

3. **تنظیم متغیرهای محیطی**:
   فایل `.env` را از `.env.example` کپی کرده و مقادیر زیر را تنظیم کنید:
   ```env
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token
   XUI_API_URL=https://your-xui-panel.com/api
   XUI_API_TOKEN=your_xui_api_token
   ZARINPAL_API_KEY=your_zarinpal_api_key
   DB_HOST=localhost
   DB_USER=your_db_user
   DB_PASSWORD=your_db_password
   DB_NAME=wizwiz_db
   CHANNEL_ID=@WizWizCh
   ```

4. **راه‌اندازی پایگاه داده**:
   - دیتابیس MySQL را ایجاد کنید:
     ```sql
     CREATE DATABASE wizwiz_db;
     ```
   - مهاجرت‌های دیتابیس را اجرا کنید (با استفاده از ابزارهایی مانند `alembic`).

5. **اجرای ربات**:
   ```bash
   python bot/main.py
   ```

6. **تنظیم وب‌هوک (اختیاری)**:
   برای مقیاس‌پذیری، می‌توانید وب‌هوک را به جای polling تنظیم کنید:
   ```python
   application.run_webhook(listen='0.0.0.0', port=8443, url_path='/webhook', webhook_url='https://your-domain.com/webhook')
   ```

### استقرار در سرور
- از سرورهای وب مانند Nginx یا Gunicorn برای استقرار استفاده کنید.
- برای پایداری، ربات را با `systemd` اجرا کنید:
  ```ini
  [Unit]
  Description=WizWizXUI TimeBot
  After=network.target
  
  [Service]
  User=your_user
  WorkingDirectory=/path/to/wizwizxui-timebot-python
  ExecStart=/usr/bin/python3 bot/main.py
  Restart=always
  
  [Install]
  WantedBy=multi-user.target
  ```

## ملاحظات امنیتی
- **کلیدهای API**: کلیدهای API (تلگرام، x-ui، درگاه‌های پرداخت) را در فایل `.env` ذخیره کنید و از دسترسی غیرمجاز محافظت کنید.
- **احراز هویت**: برای دستورات مدیریتی، بررسی نقش مدیر را پیاده‌سازی کنید.
- **محدودیت نرخ**: برای جلوگیری از سوءاستفاده، محدودیت نرخ برای فراخوانی‌های API اعمال کنید.
- **رمزنگاری**: از HTTPS برای تمام فراخوانی‌های API استفاده کنید.
- **لاگ‌گیری**: لاگ‌های حساس (مانند اطلاعات پرداخت) را رمزنگاری یا حذف کنید.

## مستندات برای توسعه‌دهنده
- **مستندات API پنل x-ui**: توسعه‌دهنده باید مستندات API پنل‌های x-ui (مانند Marzban یا Sanaei) را بررسی کند تا متدهای مورد نیاز (مانند ایجاد پیکربندی، دریافت موجودی سرور) را شناسایی کند.
- **تست‌ها**: تست‌های واحد برای هندلرها و APIها در دایرکتوری `tests/` پیاده‌سازی شوند.
- **مانیتورینگ**: از ابزارهایی مانند Prometheus یا Sentry برای مانیتورینگ عملکرد و خطاها استفاده کنید.
- **پشتیبان‌گیری**: اسکریپت‌های پشتیبان‌گیری را به صورت دوره‌ای با استفاده از `APScheduler` اجرا کنید.
- **به‌روزرسانی**: اسکریپت `update.py` را برای به‌روزرسانی کد و وابستگی‌ها پیاده‌سازی کنید.

## پشتیبانی و جامعه
- **کانال تلگرامی**: راه‌اندازی کانال تلگرامی (مانند @WizWizCh) برای اعلان‌ها و پشتیبانی.
- **گروه تلگرامی**: ایجاد گروهی (مانند @WizWizDev) برای پشتیبانی کاربران و دریافت بازخورد.
- **کمک مالی**: افزودن گزینه کمک مالی با ارزهای دیجیتال (مانند Tron، Bitcoin) در ربات و مستندات.

## نتیجه‌گیری
این پیشنهاد پروژه یک نقشه راه جامع برای پیاده‌سازی ربات wizwizxui-timebot در پایتون ارائه می‌دهد. با استفاده از معماری ماژولار، کتابخانه‌های استاندارد پایتون، و مستندات دقیق، توسعه‌دهنده می‌تواند رباتی با قابلیت‌های مشابه نسخه اصلی (پشتیبانی از پرداخت، مدیریت پیکربندی، و ابزارهای مدیریتی) ایجاد کند. این ربات برای بازار ایران بهینه شده است اما با پشتیبانی از پروتکل‌های جهانی و پنل‌های مختلف، قابلیت استفاده بین‌المللی دارد. توسعه‌دهنده باید مستندات API پنل‌های x-ui را بررسی کند و تست‌های واحد را برای اطمینان از پایداری پیاده‌سازی کند.