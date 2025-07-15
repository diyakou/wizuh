import asyncio
import logging
import platform
import signal
import traceback
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ConversationHandler, PicklePersistence
from telegram import Update
from config.settings import TELEGRAM_BOT_TOKEN
from database.db import init_db
from bot.handlers.user import (
    start_handler, handle_main_menu, handle_buy_menu, handle_configs_menu,
    handle_wallet_menu, handle_help_menu, handle_profile_menu, handle_back_to_main
)
from bot.handlers.admin import admin_panel, admin_backup, admin_broadcast, handle_admin_message
from bot.handlers.callback import callback_handler
from bot.handlers.server_management import start_server_add, cancel_server_add
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

async def error_handler(update, context):
    logger.error(f"Update {update} caused error {context.error}", exc_info=True)

async def main():
    logger.info("Initializing bot...")
    init_db()

    persistence = PicklePersistence(filepath="bot_persistence")
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).persistence(persistence).build()

    # Add all handlers
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(MessageHandler(filters.Regex("^(🛒 خرید اشتراک|📱 کانفیگ های من|💰 کیف پول|❓ راهنما|👤 پروفایل)$"), handle_main_menu))
    app.add_handler(MessageHandler(filters.Regex("^🔙 بازگشت به منوی اصلی$"), handle_back_to_main))
    app.add_handler(MessageHandler(filters.Regex("^(💳 افزایش موجودی|📊 تراکنش ها)$"), handle_wallet_menu))
    app.add_handler(MessageHandler(filters.Regex("^(📝 ویرایش نام|📞 ویرایش شماره)$"), handle_profile_menu))
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CommandHandler("backup", admin_backup))
    app.add_handler(CommandHandler("broadcast", admin_broadcast))
    app.add_handler(CallbackQueryHandler(callback_handler))

    server_conv = ConversationHandler(
        entry_points=[CommandHandler("add_server", start_server_add)],
        states={},
        fallbacks=[CallbackQueryHandler(cancel_server_add, pattern="^cancel_server_add$")]
    )
    app.add_handler(server_conv)

    for h in get_category_management_handlers():
        app.add_handler(h)
    for h in get_plan_management_handlers():
        app.add_handler(h)
    for h in get_settings_management_handlers():
        app.add_handler(h)

    app.add_handler(MessageHandler(filters.Regex('^🎛 پنل مدیریت$'), admin_panel))
    app.add_handler(MessageHandler(
        filters.Regex('^(🛠 تنظیمات درگاه‌های پرداخت|📢 تنظیمات کانال|📁 مدیریت دسته‌بندی‌ها|💰 مدیریت پلن‌ها|🖥 مدیریت سرورها|📊 گزارش‌ها|📨 ارسال پیام همگانی|💾 پشتیبان‌گیری|👥 مدیریت کاربران|🔙 بازگشت به منوی اصلی)$'),
        handle_admin_message
    ))

    app.add_error_handler(error_handler)

    await app.initialize()
    logger.info("Bot is running... Press Ctrl+C to stop")

    try:
        await app.start()
        await app.run_polling(allowed_updates=Update.ALL_TYPES)
    finally:
        logger.info("Shutting down application...")
        await app.shutdown()
        logger.info("Shutdown complete.")

def handle_shutdown(loop, app):
    logger.info("Received SIGINT, initiating shutdown...")
    tasks = [task for task in asyncio.all_tasks(loop) if task is not asyncio.current_task()]
    for task in tasks:
        task.cancel()
    loop.run_until_complete(app.shutdown())
    loop.run_until_complete(loop.shutdown_asyncgens())
    loop.close()
    logger.info("Event loop closed.")

if __name__ == "__main__":
    if platform.system() == "Windows":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    loop = asyncio.get_event_loop()
    app = None  # Will be initialized in main()
    try:
        app = asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        handle_shutdown(loop, app)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)