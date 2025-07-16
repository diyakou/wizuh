import telebot
import logging
from config.settings import TELEGRAM_BOT_TOKEN
from database.db import init_db
from bot.handlers.user import (
    start_handler, handle_main_menu, handle_buy_menu, handle_configs_menu,
    handle_wallet_menu, handle_help_menu, handle_profile_menu, handle_back_to_main
)
from bot.handlers.admin import admin_panel, admin_backup, admin_broadcast, handle_admin_message
from bot.handlers.callback import callback_handler
from bot.handlers.category_management import get_category_management_handlers
from bot.handlers.plan_management import get_plan_management_handlers
from bot.handlers.settings_management import get_settings_management_handlers

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

init_db()

@bot.message_handler(commands=['start'])
def start(message):
    start_handler(bot, message)

@bot.message_handler(regexp="^(🛒 خرید اشتراک|📱 کانفیگ های من|💰 کیف پول|❓ راهنما|👤 پروفایل)$")
def main_menu(message):
    handle_main_menu(bot, message)

@bot.message_handler(regexp="^🔙 بازگشت به منوی اصلی$")
def back_to_main(message):
    handle_back_to_main(bot, message)

@bot.message_handler(regexp="^(💳 افزایش موجودی|📊 تراکنش ها)$")
def wallet_menu(message):
    handle_wallet_menu(bot, message)

@bot.message_handler(regexp="^(📝 ویرایش نام|📞 ویرایش شماره)$")
def profile_menu(message):
    handle_profile_menu(bot, message)

@bot.message_handler(commands=['admin'])
def admin(message):
    admin_panel(bot, message)

@bot.message_handler(commands=['backup'])
def backup(message):
    admin_backup(bot, message)

@bot.message_handler(commands=['broadcast'])
def broadcast(message):
    admin_broadcast(bot, message)

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    callback_handler(bot, call)

# These handlers are more complex and will be handled in their respective files
# for handler in get_category_management_handlers():
#     bot.add_message_handler(handler)

# for handler in get_plan_management_handlers():
#     bot.add_message_handler(handler)

# for handler in get_settings_management_handlers():
#     bot.add_message_handler(handler)

@bot.message_handler(regexp='^🎛 پنل مدیریت$')
def admin_panel_message(message):
    admin_panel(bot, message)
    
@bot.message_handler(regexp='^(🛠 تنظیمات درگاه‌های پرداخت|📢 تنظیمات کانال|📁 مدیریت دسته‌بندی‌ها|💰 مدیریت پلن‌ها|🖥 مدیریت سرورها|📊 گزارش‌ها|📨 ارسال پیام همگانی|💾 پشتیبان‌گیری|👥 مدیریت کاربران|🔙 بازگشت به منوی اصلی)$')
def admin_message(message):
    handle_admin_message(bot, message)

def main():
    logger.info("Bot is running... Press Ctrl+C to stop")
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
    finally:
        logger.info("Bot stopped.")

if __name__ == "__main__":
    main()
