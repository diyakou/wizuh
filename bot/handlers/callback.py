from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup
from database.models import User, Config, Plan, Transaction, Server
from database.db import session
from bot.keyboards.admin import (
    get_admin_main_menu,
    get_server_management_menu,
    get_user_management_menu,
    get_plan_management_menu,
    get_settings_menu,
    get_reports_menu
)
from bot.keyboards.user import (
    get_main_menu,
    get_plans_menu,
    get_payment_methods_menu,
    get_config_menu,
    get_wallet_menu,
    get_support_menu
)
from api.payment import create_payment_link
from api.qr import generate_qr_code
from config.settings import ADMIN_IDS
import logging
from datetime import datetime, timedelta
import uuid

logger = logging.getLogger(__name__)

def callback_handler(bot, call):
    """Handle callback queries."""
    try:
        query = call
        
        # Get user and check if admin
        user_id = query.from_user.id
        is_admin = user_id in ADMIN_IDS
        
        # Handle server management callbacks
        if query.data.startswith("server_") or query.data.startswith("edit_server_") or query.data.startswith("delete_server_") or query.data.startswith("confirm_delete_") or query.data == "back_to_server_menu" or query.data == "cancel_server_add":
            from bot.handlers.server_management import handle_server_callback
            handle_server_callback(bot, query)
            return

        # Handle admin callbacks
        if query.data.startswith("admin_") and is_admin:
            handle_admin_callback(bot, query)
            return
            
        # Handle user callbacks
        handle_user_callback(bot, query)
            
    except Exception as e:
        logger.error(f"Error in callback handler: {e}")
        bot.edit_message_text(
            "متأسفانه خطایی رخ داد. لطفاً دوباره تلاش کنید.",
            query.message.chat.id,
            query.message.message_id,
            reply_markup=get_main_menu() if not is_admin else get_admin_main_menu()
        )

def handle_admin_callback(bot, query) -> None:
    """Handle admin-specific callbacks."""
    callback_data = query.data
    
    if callback_data == "back_to_admin":
        bot.edit_message_text(
            "🔰 به پنل مدیریت خوش آمدید.\n"
            "لطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
            query.message.chat.id,
            query.message.message_id,
            reply_markup=get_admin_main_menu()
        )
        return

    # Admin main menu options
    if callback_data == "admin_users":
        bot.edit_message_text(
            "مدیریت کاربران - لطفاً یک گزینه را انتخاب کنید:",
            query.message.chat.id,
            query.message.message_id,
            reply_markup=get_user_management_menu()
        )
    
    elif callback_data == "admin_plans":
        bot.edit_message_text(
            "مدیریت پلن‌ها - لطفاً یک گزینه را انتخاب کنید:",
            query.message.chat.id,
            query.message.message_id,
            reply_markup=get_plan_management_menu()
        )
    
    elif callback_data == "admin_reports":
        bot.edit_message_text(
            "گزارش‌ها - لطفاً یک گزینه را انتخاب کنید:",
            query.message.chat.id,
            query.message.message_id,
            reply_markup=get_reports_menu()
        )
    
    elif callback_data == "admin_settings":
        bot.edit_message_text(
            "تنظیمات ربات - لطفاً یک گزینه را انتخاب کنید:",
            query.message.chat.id,
            query.message.message_id,
            reply_markup=get_settings_menu()
        )
    
    # Server management
    elif callback_data == "add_server":
        from bot.handlers.server_management import start_server_add
        start_server_add(bot, query.message)
    
    elif callback_data == "list_servers":
        servers = Server.get_all()
        if not servers:
            bot.edit_message_text(
                "هیچ سروری یافت نشد.",
                query.message.chat.id,
                query.message.message_id,
                reply_markup=get_server_management_menu()
            )
            return
        
        message = "لیست سرورها:\n\n"
        for server in servers:
            status = "فعال" if server.is_active else "غیرفعال"
            message += f"🖥 {server.ip}:{server.port} - {server.type} - {status}\n"
        
        bot.edit_message_text(
            message,
            query.message.chat.id,
            query.message.message_id,
            reply_markup=get_server_management_menu()
        )
    
    # Add more admin callback handlers...

def handle_user_callback(bot, query) -> None:
    """Handle user-specific callbacks."""
    callback_data = query.data
    
    if callback_data == "start":
        bot.edit_message_text(
            "منوی اصلی - لطفاً یک گزینه را انتخاب کنید:",
            query.message.chat.id,
            query.message.message_id,
            reply_markup=get_main_menu()
        )
    
    elif callback_data == "buy":
        plans = Plan.get_active_plans()
        bot.edit_message_text(
            "لطفاً یک پلن را انتخاب کنید:",
            query.message.chat.id,
            query.message.message_id,
            reply_markup=get_plans_menu(plans)
        )
    
    elif callback_data.startswith("buy_plan_"):
        plan_id = int(callback_data.split("_")[2])
        plan = Plan.get_by_id(plan_id)
        if not plan:
            bot.edit_message_text(
                "پلن مورد نظر یافت نشد.",
                query.message.chat.id,
                query.message.message_id,
                reply_markup=get_main_menu()
            )
            return
        
        bot.edit_message_text(
            f"پلن انتخابی:\n"
            f"نام: {plan.name}\n"
            f"حجم: {plan.volume} GB\n"
            f"مدت: {plan.duration} روز\n"
            f"قیمت: {plan.price:,} تومان\n\n"
            "لطفاً روش پرداخت را انتخاب کنید:",
            query.message.chat.id,
            query.message.message_id,
            reply_markup=get_payment_methods_menu(plan.price, plan.id)
        )
    
    elif callback_data.startswith("pay_"):
        _, method, plan_id, amount = callback_data.split("_")
        plan_id = int(plan_id)
        amount = int(amount)
        
        if method == "wallet":
            user = User.get_by_telegram_id(query.from_user.id)
            if user.balance < amount:
                bot.edit_message_text(
                    "موجودی کیف پول شما کافی نیست.",
                    query.message.chat.id,
                    query.message.message_id,
                    reply_markup=get_wallet_menu(user.balance)
                )
                return
            
            # Process wallet payment
            success = process_wallet_payment(user, amount, plan_id)
            if success:
                bot.edit_message_text(
                    "پرداخت با موفقیت انجام شد. سرویس شما در حال فعال‌سازی است...",
                    query.message.chat.id,
                    query.message.message_id,
                    reply_markup=get_main_menu()
                )
            else:
                bot.edit_message_text(
                    "خطا در پردازش پرداخت. لطفاً مجدداً تلاش کنید.",
                    query.message.chat.id,
                    query.message.message_id,
                    reply_markup=get_main_menu()
                )
        else:
            # Generate payment link for other methods
            payment_link = create_payment_link(method, amount, plan_id, query.from_user.id)
            bot.edit_message_text(
                "لطفاً روی لینک زیر کلیک کنید تا به درگاه پرداخت منتقل شوید:",
                query.message.chat.id,
                query.message.message_id,
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("پرداخت", url=payment_link),
                    InlineKeyboardButton("بازگشت", callback_data="buy")
                ]])
            )
    
    elif callback_data == "configs":
        configs = Config.get_user_configs(query.from_user.id)
        if not configs:
            bot.edit_message_text(
                "شما هیچ سرویس فعالی ندارید.",
                query.message.chat.id,
                query.message.message_id,
                reply_markup=get_main_menu()
            )
            return
        
        message = "سرویس‌های شما:\n\n"
        for config in configs:
            message += (
                f"🔰 {config.name}\n"
                f"حجم باقیمانده: {config.remaining_volume} GB\n"
                f"زمان باقیمانده: {config.remaining_days} روز\n"
                f"وضعیت: {'فعال' if config.is_active else 'غیرفعال'}\n\n"
            )
        
        bot.edit_message_text(
            message,
            query.message.chat.id,
            query.message.message_id,
            reply_markup=get_main_menu()
        )
    
    # Add more user callback handlers...

def process_wallet_payment(user: User, amount: int, plan_id: int) -> bool:
    # Implementation of process_wallet_payment method
    pass
