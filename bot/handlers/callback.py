from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
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

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle callback queries."""
    try:
        query = update.callback_query
        await query.answer()  # Answer the callback query to stop loading animation
        
        # Get user and check if admin
        user_id = update.effective_user.id
        is_admin = user_id in ADMIN_IDS
        
        # Handle admin callbacks
        if query.data.startswith("admin_") and is_admin:
            await handle_admin_callback(update, context)
            return
            
        # Handle user callbacks
        await handle_user_callback(update, context)
            
    except Exception as e:
        logger.error(f"Error in callback handler: {e}")
        await query.edit_message_text(
            "متأسفانه خطایی رخ داد. لطفاً دوباره تلاش کنید.",
            reply_markup=get_main_menu() if not is_admin else get_admin_main_menu()
        )

async def handle_admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle admin-specific callbacks."""
    query = update.callback_query
    callback_data = query.data
    
    # Admin main menu options
    if callback_data == "admin_servers":
        await query.edit_message_text(
            "مدیریت سرورها - لطفاً یک گزینه را انتخاب کنید:",
            reply_markup=get_server_management_menu()
        )
    
    elif callback_data == "admin_users":
        await query.edit_message_text(
            "مدیریت کاربران - لطفاً یک گزینه را انتخاب کنید:",
            reply_markup=get_user_management_menu()
        )
    
    elif callback_data == "admin_plans":
        await query.edit_message_text(
            "مدیریت پلن‌ها - لطفاً یک گزینه را انتخاب کنید:",
            reply_markup=get_plan_management_menu()
        )
    
    elif callback_data == "admin_reports":
        await query.edit_message_text(
            "گزارش‌ها - لطفاً یک گزینه را انتخاب کنید:",
            reply_markup=get_reports_menu()
        )
    
    elif callback_data == "admin_settings":
        await query.edit_message_text(
            "تنظیمات ربات - لطفاً یک گزینه را انتخاب کنید:",
            reply_markup=get_settings_menu()
        )
    
    # Server management
    elif callback_data == "add_server":
        context.user_data["state"] = "waiting_server_info"
        await query.edit_message_text(
            "لطفاً اطلاعات سرور را در قالب زیر وارد کنید:\n"
            "IP|PORT|USERNAME|PASSWORD|TYPE\n"
            "مثال:\n"
            "1.2.3.4|8080|admin|pass123|xui"
        )
    
    elif callback_data == "list_servers":
        servers = Server.get_all()
        if not servers:
            await query.edit_message_text(
                "هیچ سروری یافت نشد.",
                reply_markup=get_server_management_menu()
            )
            return
        
        message = "لیست سرورها:\n\n"
        for server in servers:
            status = "فعال" if server.is_active else "غیرفعال"
            message += f"🖥 {server.ip}:{server.port} - {server.type} - {status}\n"
        
        await query.edit_message_text(
            message,
            reply_markup=get_server_management_menu()
        )
    
    # Add more admin callback handlers...

async def handle_user_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle user-specific callbacks."""
    query = update.callback_query
    callback_data = query.data
    
    if callback_data == "start":
        await query.edit_message_text(
            "منوی اصلی - لطفاً یک گزینه را انتخاب کنید:",
            reply_markup=get_main_menu()
        )
    
    elif callback_data == "buy":
        plans = Plan.get_active_plans()
        await query.edit_message_text(
            "لطفاً یک پلن را انتخاب کنید:",
            reply_markup=get_plans_menu(plans)
        )
    
    elif callback_data.startswith("buy_plan_"):
        plan_id = int(callback_data.split("_")[2])
        plan = Plan.get_by_id(plan_id)
        if not plan:
            await query.edit_message_text(
                "پلن مورد نظر یافت نشد.",
                reply_markup=get_main_menu()
            )
            return
        
        await query.edit_message_text(
            f"پلن انتخابی:\n"
            f"نام: {plan.name}\n"
            f"حجم: {plan.volume} GB\n"
            f"مدت: {plan.duration} روز\n"
            f"قیمت: {plan.price:,} تومان\n\n"
            "لطفاً روش پرداخت را انتخاب کنید:",
            reply_markup=get_payment_methods_menu(plan.price, plan.id)
        )
    
    elif callback_data.startswith("pay_"):
        _, method, plan_id, amount = callback_data.split("_")
        plan_id = int(plan_id)
        amount = int(amount)
        
        if method == "wallet":
            user = User.get_by_telegram_id(update.effective_user.id)
            if user.balance < amount:
                await query.edit_message_text(
                    "موجودی کیف پول شما کافی نیست.",
                    reply_markup=get_wallet_menu(user.balance)
                )
                return
            
            # Process wallet payment
            success = await process_wallet_payment(user, amount, plan_id)
            if success:
                await query.edit_message_text(
                    "پرداخت با موفقیت انجام شد. سرویس شما در حال فعال‌سازی است...",
                    reply_markup=get_main_menu()
                )
            else:
                await query.edit_message_text(
                    "خطا در پردازش پرداخت. لطفاً مجدداً تلاش کنید.",
                    reply_markup=get_main_menu()
                )
        else:
            # Generate payment link for other methods
            payment_link = create_payment_link(method, amount, plan_id, update.effective_user.id)
            await query.edit_message_text(
                "لطفاً روی لینک زیر کلیک کنید تا به درگاه پرداخت منتقل شوید:",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("پرداخت", url=payment_link),
                    InlineKeyboardButton("بازگشت", callback_data="buy")
                ]])
            )
    
    elif callback_data == "configs":
        configs = Config.get_user_configs(update.effective_user.id)
        if not configs:
            await query.edit_message_text(
                "شما هیچ سرویس فعالی ندارید.",
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
        
        await query.edit_message_text(
            message,
            reply_markup=get_main_menu()
        )
    
    # Add more user callback handlers...

async def process_wallet_payment(user: User, amount: int, plan_id: int) -> bool:
    # Implementation of process_wallet_payment method
    pass

