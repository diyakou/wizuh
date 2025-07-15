import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Telegram Bot Settings
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CHANNEL_ID = os.getenv('CHANNEL_ID', '@WizWizCh')

# Database Settings
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
DB_NAME = os.getenv('DB_NAME', 'wizwiz_db')
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"

# X-UI Panel Settings
XUI_API_URL = os.getenv('XUI_API_URL')
XUI_API_TOKEN = os.getenv('XUI_API_TOKEN')

# Payment Gateway Settings
ZARINPAL_API_KEY = os.getenv('ZARINPAL_API_KEY')
NEXTPAY_API_KEY = os.getenv('NEXTPAY_API_KEY')
NOWPAYMENTS_API_KEY = os.getenv('NOWPAYMENTS_API_KEY')

# Bot Settings
DEFAULT_LANGUAGE = 'fa'  # Persian/Farsi
ADMIN_IDS = [int(id) for id in os.getenv('ADMIN_IDS', '').split(',') if id]
CHANNEL_LOCK_ENABLED = os.getenv('CHANNEL_LOCK_ENABLED', 'true').lower() == 'true'

# Payment Settings
CURRENCY = 'IRR'  # Iranian Rial
MIN_DEPOSIT = 100000  # Minimum deposit amount in IRR 