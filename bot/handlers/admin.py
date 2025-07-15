from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes, ConversationHandler, CallbackQueryHandler, MessageHandler, filters
from database.models import User, Config, Plan, Transaction, Server, UserRole, Setting, SettingType, ServerCategory, ServerPlan, XUIServer, XUIConfig, ServerProtocol
from database.db import session
from config.settings import ADMIN_IDS
from api.xui import XUIClient
import logging
import json
from datetime import datetime, timedelta
from sqlalchemy import select
from bot.keyboards.admin import (
    get_admin_main_menu,
    get_server_management_menu,
    get_user_management_menu,
    get_plan_management_menu,
    get_settings_menu,
    get_reports_menu
)

logger = logging.getLogger(__name__)

# Admin panel states
(
    ADMIN_START,
    ADMIN_GATEWAYS,
    ADMIN_CHANNELS,
    ADMIN_CATEGORIES,
    ADMIN_PLANS,
    ADMIN_SERVERS,
    ADMIN_REPORTS,
    ADMIN_BROADCAST,
    ADMIN_BACKUP,
    ADMIN_USERS,
    WAITING_SERVER_INFO,
    WAITING_PLAN_INFO,
    WAITING_USER_SEARCH,
    WAITING_BOT_TEXT,
    WAITING_NOTIFICATION_SETTINGS,
    WAITING_GATEWAY_INFO,
    WAITING_CATEGORY_INFO,
    WAITING_PLAN_NAME,
    WAITING_PLAN_PRICE,
    WAITING_PLAN_DURATION,
    WAITING_PLAN_DESCRIPTION,
    WAITING_USER_TO_BLOCK,
    WAITING_USER_TO_UNBLOCK,
    CONFIRM_USER_BLOCK,
    CONFIRM_USER_UNBLOCK
) = range(25)

# Add new states for X-UI server management
(
    WAITING_XUI_SERVER_NAME,
    WAITING_XUI_SERVER_URL,
    WAITING_XUI_SERVER_CREDENTIALS,
    CONFIRM_XUI_SERVER,
    WAITING_XUI_SERVER_EDIT,
    CONFIRM_XUI_SERVER_DELETE
) = range(25, 31)

def is_admin(user_id: int) -> bool:
    """Check if user is an admin."""
    return user_id in ADMIN_IDS

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show admin panel with keyboard buttons."""
    user = update.effective_user
    
    # Check if user is admin
    admin = User.get_by_telegram_id(user.id)
    if not admin or not admin.is_admin:
        await update.message.reply_text("⛔️ شما دسترسی به پنل ادمین را ندارید.")
        return
    
    # Create keyboard with admin options
    keyboard = [
        [KeyboardButton("🛠 تنظیمات درگاه‌های پرداخت"), KeyboardButton("📢 تنظیمات کانال")],
        [KeyboardButton("📁 مدیریت دسته‌بندی‌ها"), KeyboardButton("💰 مدیریت پلن‌ها")],
        [KeyboardButton("🖥 مدیریت سرورها"), KeyboardButton("📊 گزارش‌ها")],
        [KeyboardButton("📨 ارسال پیام همگانی"), KeyboardButton("💾 پشتیبان‌گیری")],
        [KeyboardButton("👥 مدیریت کاربران"), KeyboardButton("🔙 بازگشت به منوی اصلی")]
    ]
    
    reply_markup = ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        one_time_keyboard=False
    )
    
    await update.message.reply_text(
        "🔰 به پنل مدیریت خوش آمدید.\n"
        "لطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
        reply_markup=reply_markup
    )
    return ADMIN_START

async def handle_admin_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle admin panel messages."""
    message = update.message.text
    
    # Check if user is admin
    user = update.effective_user
    admin = User.get_by_telegram_id(user.id)
    if not admin or not admin.is_admin:
        return
    
    if message == "🛠 تنظیمات درگاه‌های پرداخت":
        keyboard = [
            [InlineKeyboardButton("💳 درگاه‌های فعال", callback_data="gateways_active")],
            [InlineKeyboardButton("➕ افزودن درگاه جدید", callback_data="gateway_add")],
            [InlineKeyboardButton("✏️ ویرایش درگاه", callback_data="gateway_edit")],
            [InlineKeyboardButton("❌ حذف درگاه", callback_data="gateway_delete")],
            [InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_admin")]
        ]
        
        await update.message.reply_text(
            "🛠 مدیریت درگاه‌های پرداخت\n"
            "لطفاً یک گزینه را انتخاب کنید:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return ADMIN_GATEWAYS
        
    elif message == "📢 تنظیمات کانال":
        keyboard = [
            [InlineKeyboardButton("📢 کانال‌های فعال", callback_data="channels_active")],
            [InlineKeyboardButton("➕ افزودن کانال جدید", callback_data="channel_add")],
            [InlineKeyboardButton("✏️ ویرایش کانال", callback_data="channel_edit")],
            [InlineKeyboardButton("❌ حذف کانال", callback_data="channel_delete")],
            [InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_admin")]
        ]
        
        await update.message.reply_text(
            "📢 مدیریت کانال‌ها\n"
            "لطفاً یک گزینه را انتخاب کنید:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return ADMIN_CHANNELS
        
    elif message == "📁 مدیریت دسته‌بندی‌ها":
        keyboard = [
            [InlineKeyboardButton("📁 دسته‌بندی‌های موجود", callback_data="categories_list")],
            [InlineKeyboardButton("➕ افزودن دسته‌بندی", callback_data="category_add")],
            [InlineKeyboardButton("✏️ ویرایش دسته‌بندی", callback_data="category_edit")],
            [InlineKeyboardButton("❌ حذف دسته‌بندی", callback_data="category_delete")],
            [InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_admin")]
        ]
        
        await update.message.reply_text(
            "📁 مدیریت دسته‌بندی‌ها\n"
            "لطفاً یک گزینه را انتخاب کنید:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return ADMIN_CATEGORIES
        
    elif message == "💰 مدیریت پلن‌ها":
        keyboard = [
            [InlineKeyboardButton("💰 پلن‌های موجود", callback_data="plans_list")],
            [InlineKeyboardButton("➕ افزودن پلن", callback_data="plan_add")],
            [InlineKeyboardButton("✏️ ویرایش پلن", callback_data="plan_edit")],
            [InlineKeyboardButton("❌ حذف پلن", callback_data="plan_delete")],
            [InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_admin")]
        ]
        
        await update.message.reply_text(
            "💰 مدیریت پلن‌ها\n"
            "لطفاً یک گزینه را انتخاب کنید:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return ADMIN_PLANS
        
    elif message == "🖥 مدیریت سرورها":
        keyboard = [
            [InlineKeyboardButton("🖥 سرورهای موجود", callback_data="servers_list")],
            [InlineKeyboardButton("➕ افزودن سرور", callback_data="server_add")],
            [InlineKeyboardButton("✏️ ویرایش سرور", callback_data="server_edit")],
            [InlineKeyboardButton("❌ حذف سرور", callback_data="server_delete")],
            [InlineKeyboardButton("📊 وضعیت سرورها", callback_data="server_status")],
            [InlineKeyboardButton("🔄 همگام‌سازی", callback_data="server_sync")],
            [InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_admin")]
        ]
        
        await update.message.reply_text(
            "🖥 مدیریت سرورها\n"
            "لطفاً یک گزینه را انتخاب کنید:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return ADMIN_SERVERS
        
    elif message == "📊 گزارش‌ها":
        await admin_reports(update, context)
        return ADMIN_REPORTS
        
    elif message == "📨 ارسال پیام همگانی":
        await admin_broadcast(update, context)
        return ADMIN_BROADCAST
        
    elif message == "💾 پشتیبان‌گیری":
        await admin_backup(update, context)
        return ADMIN_BACKUP
        
    elif message == "👥 مدیریت کاربران":
        await admin_users(update, context)
        return ADMIN_USERS
        
    elif message == "🔙 بازگشت به منوی اصلی":
        # Return to main menu
        keyboard = [
            [KeyboardButton("🛍 خرید اشتراک"), KeyboardButton("👤 حساب کاربری")],
            [KeyboardButton("📱 پیکربندی‌های من"), KeyboardButton("💰 شارژ کیف پول")],
            [KeyboardButton("📞 پشتیبانی"), KeyboardButton("ℹ️ راهنما")]
        ]
        
        if admin and admin.is_admin:
            keyboard.insert(0, [KeyboardButton("🎛 پنل مدیریت")])
        
        reply_markup = ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True,
            one_time_keyboard=False
        )
        
        await update.message.reply_text(
            "🏠 به منوی اصلی بازگشتید.\n"
            "لطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
            reply_markup=reply_markup
        )
        return ConversationHandler.END

async def admin_reports(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle admin reports."""
    keyboard = [
        [
            InlineKeyboardButton("📊 گزارش درآمد", callback_data="report_income"),
            InlineKeyboardButton("📊 گزارش کاربران", callback_data="report_users")
        ],
        [
            InlineKeyboardButton("📊 گزارش سرورها", callback_data="report_servers"),
            InlineKeyboardButton("📊 گزارش تراکنش‌ها", callback_data="report_transactions")
        ],
        [
            InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_admin")
        ]
    ]
    
    await update.message.reply_text(
        "📊 گزارش‌ها\n"
        "لطفاً نوع گزارش را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def admin_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle broadcast message to all users."""
    keyboard = [
        [
            InlineKeyboardButton("📨 ارسال به همه", callback_data="broadcast_all"),
            InlineKeyboardButton("📨 ارسال به کاربران فعال", callback_data="broadcast_active")
        ],
        [
            InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_admin")
        ]
    ]
    
    await update.message.reply_text(
        "📨 ارسال پیام همگانی\n"
        "لطفاً نوع ارسال را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def admin_backup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle database backup."""
    keyboard = [
        [
            InlineKeyboardButton("💾 پشتیبان‌گیری کامل", callback_data="backup_full"),
            InlineKeyboardButton("💾 پشتیبان‌گیری تنظیمات", callback_data="backup_settings")
        ],
        [
            InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_admin")
        ]
    ]
    
    await update.message.reply_text(
        "💾 پشتیبان‌گیری\n"
        "لطفاً نوع پشتیبان‌گیری را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def admin_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle user management."""
    keyboard = [
        [
            InlineKeyboardButton("➕ افزودن ادمین", callback_data="user_add_admin"),
            InlineKeyboardButton("➖ حذف ادمین", callback_data="user_remove_admin")
        ],
        [
            InlineKeyboardButton("🚫 مسدود کردن کاربر", callback_data="user_block"),
            InlineKeyboardButton("✅ رفع مسدودی کاربر", callback_data="user_unblock")
        ],
        [
            InlineKeyboardButton("👥 لیست کاربران", callback_data="user_list"),
            InlineKeyboardButton("👥 لیست ادمین‌ها", callback_data="admin_list")
        ],
        [
            InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_admin")
        ]
    ]
    
    await update.message.reply_text(
        "👥 مدیریت کاربران\n"
        "لطفاً عملیات مورد نظر را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle_server_management(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle server management section."""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "مدیریت سرورها - لطفاً یک گزینه را انتخاب کنید:",
        reply_markup=get_server_management_menu()
    )

async def add_server(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the add server conversation."""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "لطفاً اطلاعات سرور را در قالب زیر وارد کنید:\n"
        "IP|PORT|USERNAME|PASSWORD|TYPE\n"
        "مثال:\n"
        "1.2.3.4|8080|admin|pass123|xui"
    )
    return WAITING_SERVER_INFO

async def handle_server_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process server information and add to database."""
    try:
        ip, port, username, password, server_type = update.message.text.split("|")
        server = Server(
            ip=ip.strip(),
            port=int(port.strip()),
            username=username.strip(),
            password=password.strip(),
            type=server_type.strip()
        )
        # Add server to database
        server.save()
        await update.message.reply_text(
            "سرور با موفقیت اضافه شد.",
            reply_markup=get_server_management_menu()
        )
    except Exception as e:
        logger.error(f"Error adding server: {e}")
        await update.message.reply_text(
            "خطا در افزودن سرور. لطفاً مجدداً تلاش کنید.",
            reply_markup=get_server_management_menu()
        )
    return ConversationHandler.END

async def list_servers(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """List all servers."""
    query = update.callback_query
    await query.answer()
    
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

async def generate_daily_report(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Generate and send daily report."""
    query = update.callback_query
    await query.answer()
    
    today = datetime.now()
    yesterday = today - timedelta(days=1)
    
    # Get statistics
    new_users = User.count_new_users(yesterday)
    active_configs = Config.count_active()
    daily_income = Transaction.get_daily_income(yesterday)
    
    report = (
        "📊 گزارش روزانه\n\n"
        f"📅 تاریخ: {yesterday.strftime('%Y-%m-%d')}\n"
        f"👥 کاربران جدید: {new_users}\n"
        f"🔰 سرویس‌های فعال: {active_configs}\n"
        f"💰 درآمد روزانه: {daily_income:,} تومان\n"
    )
    
    await query.edit_message_text(
        report,
        reply_markup=get_reports_menu()
    )

async def handle_bot_settings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle bot settings section."""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "تنظیمات ربات - لطفاً یک گزینه را انتخاب کنید:",
        reply_markup=get_settings_menu()
    )

async def handle_gateway_management(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle payment gateway management section."""
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("💳 درگاه‌های فعال", callback_data="gateways_list")],
        [InlineKeyboardButton("➕ افزودن درگاه", callback_data="gateway_add")],
        [InlineKeyboardButton("✏️ ویرایش درگاه", callback_data="gateway_edit")],
        [InlineKeyboardButton("❌ حذف درگاه", callback_data="gateway_delete")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_admin")]
    ]
    
    await query.edit_message_text(
        "🛠 مدیریت درگاه‌های پرداخت\n"
        "لطفاً یک گزینه را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def add_gateway(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the add gateway conversation."""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "لطفاً اطلاعات درگاه پرداخت را در قالب زیر وارد کنید:\n"
        "NAME|API_KEY|TYPE\n"
        "مثال:\n"
        "ZarinPal|your-api-key-here|zarinpal"
    )
    return WAITING_GATEWAY_INFO

async def handle_gateway_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process gateway information and add to database."""
    try:
        name, api_key, gateway_type = update.message.text.split("|")
        Setting.create_payment_gateway(
            name=name.strip(),
            gateway_type=gateway_type.strip(),
            api_key=api_key.strip()
        )
        await update.message.reply_text(
            "درگاه پرداخت با موفقیت اضافه شد.",
            reply_markup=get_admin_main_menu()
        )
    except Exception as e:
        logger.error(f"Error adding gateway: {e}")
        await update.message.reply_text(
            "خطا در افزودن درگاه پرداخت. لطفاً مجدداً تلاش کنید.",
            reply_markup=get_admin_main_menu()
        )
    return ConversationHandler.END

async def handle_category_management(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle category management section."""
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("📁 دسته‌بندی‌های موجود", callback_data="categories_list")],
        [InlineKeyboardButton("➕ افزودن دسته‌بندی", callback_data="category_add")],
        [InlineKeyboardButton("✏️ ویرایش دسته‌بندی", callback_data="category_edit")],
        [InlineKeyboardButton("❌ حذف دسته‌بندی", callback_data="category_delete")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_admin")]
    ]
    
    await query.edit_message_text(
        "📁 مدیریت دسته‌بندی‌ها\n"
        "لطفاً یک گزینه را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def add_category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the add category conversation."""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "لطفاً نام و توضیحات دسته‌بندی را در قالب زیر وارد کنید:\n"
        "NAME|DESCRIPTION\n"
        "مثال:\n"
        "VIP|سرویس‌های ویژه با سرعت بالا"
    )
    return WAITING_CATEGORY_INFO

async def handle_category_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process category information and add to database."""
    try:
        name, description = update.message.text.split("|")
        category = ServerCategory(
            title=name.strip(),
            remark=description.strip(),
            server_ids=[]  # Empty list initially, servers can be added later
        )
        category.save()
        await update.message.reply_text(
            "دسته‌بندی با موفقیت اضافه شد.",
            reply_markup=get_admin_main_menu()
        )
    except Exception as e:
        logger.error(f"Error adding category: {e}")
        await update.message.reply_text(
            "خطا در افزودن دسته‌بندی. لطفاً مجدداً تلاش کنید.",
            reply_markup=get_admin_main_menu()
        )
    return ConversationHandler.END

async def handle_plan_management(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle plan management section."""
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("💰 پلن‌های موجود", callback_data="plans_list")],
        [InlineKeyboardButton("➕ افزودن پلن", callback_data="plan_add")],
        [InlineKeyboardButton("✏️ ویرایش پلن", callback_data="plan_edit")],
        [InlineKeyboardButton("❌ حذف پلن", callback_data="plan_delete")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_admin")]
    ]
    
    await query.edit_message_text(
        "💰 مدیریت پلن‌ها\n"
        "لطفاً یک گزینه را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def add_plan(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the add plan conversation."""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "لطفاً نام پلن را وارد کنید:"
    )
    return WAITING_PLAN_NAME

async def handle_plan_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle plan name input and ask for price."""
    context.user_data['plan_name'] = update.message.text
    
    await update.message.reply_text(
        "لطفاً قیمت پلن را به تومان وارد کنید:"
    )
    return WAITING_PLAN_PRICE

async def handle_plan_price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle plan price input and ask for duration."""
    try:
        context.user_data['plan_price'] = int(update.message.text)
        await update.message.reply_text(
            "لطفاً مدت زمان پلن را به روز وارد کنید:"
        )
        return WAITING_PLAN_DURATION
    except ValueError:
        await update.message.reply_text(
            "لطفاً یک عدد صحیح وارد کنید."
        )
        return WAITING_PLAN_PRICE

async def handle_plan_duration(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle plan duration input and ask for description."""
    try:
        context.user_data['plan_duration'] = int(update.message.text)
        await update.message.reply_text(
            "لطفاً توضیحات پلن را وارد کنید:"
        )
        return WAITING_PLAN_DESCRIPTION
    except ValueError:
        await update.message.reply_text(
            "لطفاً یک عدد صحیح وارد کنید."
        )
        return WAITING_PLAN_DURATION

async def handle_plan_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process all plan information and add to database."""
    try:
        plan = Plan(
            name=context.user_data['plan_name'],
            price=context.user_data['plan_price'],
            duration=context.user_data['plan_duration'],
            description=update.message.text
        )
        plan.save()
        
        # Clear user data
        context.user_data.clear()
        
        await update.message.reply_text(
            "پلن با موفقیت اضافه شد.",
            reply_markup=get_admin_main_menu()
        )
    except Exception as e:
        logger.error(f"Error adding plan: {e}")
        await update.message.reply_text(
            "خطا در افزودن پلن. لطفاً مجدداً تلاش کنید.",
            reply_markup=get_admin_main_menu()
        )
    return ConversationHandler.END

async def handle_user_management(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle user management section."""
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [
            InlineKeyboardButton("🚫 مسدود کردن کاربر", callback_data="user_block"),
            InlineKeyboardButton("✅ آزاد کردن کاربر", callback_data="user_unblock")
        ],
        [InlineKeyboardButton("👥 لیست کاربران", callback_data="user_list")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_admin")]
    ]
    
    await query.edit_message_text(
        "👥 مدیریت کاربران\n"
        "لطفاً یک گزینه را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def start_block_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the block user process."""
    query = update.callback_query
    await query.answer()
    
    # Get list of active users
    users = session.query(User).filter(User.is_banned == False).all()
    keyboard = []
    
    # Create buttons for each user
    for user in users:
        # Get username safely
        username_value = session.query(User.username).filter(User.telegram_id == user.telegram_id).scalar()
        username = str(username_value) if username_value is not None else f"ID: {user.telegram_id}"
        
        # Get first and last name safely
        first_name = session.query(User.first_name).filter(User.telegram_id == user.telegram_id).scalar() or ''
        last_name = session.query(User.last_name).filter(User.telegram_id == user.telegram_id).scalar() or ''
        
        button = InlineKeyboardButton(
            f"{username} - {first_name} {last_name}".strip(),
            callback_data=f"block_user_{user.telegram_id}"
        )
        keyboard.append([button])
    
    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_user_management")])
    
    await query.edit_message_text(
        "لطفاً کاربر مورد نظر را برای مسدود کردن انتخاب کنید یا ID تلگرام کاربر را وارد کنید:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return WAITING_USER_TO_BLOCK

async def handle_block_user_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle user input for blocking - either from button or manual ID."""
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        user_id = int(query.data.split('_')[2])
    else:
        try:
            user_id = int(update.message.text)
        except ValueError:
            await update.message.reply_text(
                "لطفاً یک ID معتبر وارد کنید.",
                reply_markup=get_user_management_menu()
            )
            return WAITING_USER_TO_BLOCK
    
    # Get user from database
    user = User.get_by_telegram_id(user_id)
    if not user:
        message = "کاربر با این ID یافت نشد. لطفاً دوباره امتحان کنید."
        if update.callback_query:
            await query.edit_message_text(message, reply_markup=get_user_management_menu())
        else:
            await update.message.reply_text(message, reply_markup=get_user_management_menu())
        return WAITING_USER_TO_BLOCK
    
    # Check if user is already banned using SQLAlchemy comparison
    is_banned = session.query(User.is_banned).filter(User.telegram_id == user_id).scalar()
    if is_banned:
        message = "این کاربر قبلاً مسدود شده است."
        if update.callback_query:
            await query.edit_message_text(message, reply_markup=get_user_management_menu())
        else:
            await update.message.reply_text(message, reply_markup=get_user_management_menu())
        return WAITING_USER_TO_BLOCK
    
    # Store user ID in context for confirmation
    context.user_data['block_user_id'] = user_id
    
    # Show user info and ask for confirmation
    keyboard = [
        [
            InlineKeyboardButton("✅ تأیید", callback_data="confirm_block"),
            InlineKeyboardButton("❌ لغو", callback_data="cancel_block")
        ]
    ]
    
    message = (
        f"اطلاعات کاربر:\n"
        f"ID تلگرام: {user.telegram_id}\n"
        f"نام: {str(user.username or 'تنظیم نشده')}\n"
        f"نام کامل: {str(user.first_name or '')} {str(user.last_name or '')}\n"
        f"وضعیت: {'مسدود' if session.query(User.is_banned).filter(User.telegram_id == user_id).scalar() else 'فعال'}\n\n"
        f"آیا می‌خواهید این کاربر را مسدود کنید؟"
    )
    
    if update.callback_query:
        await query.edit_message_text(message, reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.message.reply_text(message, reply_markup=InlineKeyboardMarkup(keyboard))
    
    return CONFIRM_USER_BLOCK

async def confirm_block_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle confirmation of user block."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "cancel_block":
        await query.edit_message_text(
            "عملیات مسدود کردن کاربر لغو شد.",
            reply_markup=get_user_management_menu()
        )
        return ConversationHandler.END
    
    user_id = context.user_data.get('block_user_id')
    if not user_id:
        await query.edit_message_text(
            "خطا در فرآیند مسدود کردن. لطفاً دوباره تلاش کنید.",
            reply_markup=get_user_management_menu()
        )
        return ConversationHandler.END
    
    try:
        # Update user status using SQLAlchemy update
        session.query(User).filter(User.telegram_id == user_id).update(
            {
                User.is_banned: True,
                User.banned_at: datetime.utcnow()
            }
        )
        session.commit()
        
        # Try to notify the user
        try:
            await context.bot.send_message(
                user_id,
                "دسترسی شما به ربات به دلیل نقض قوانین مسدود شد. برای اطلاعات بیشتر با پشتیبانی تماس بگیرید."
            )
        except Exception as e:
            logger.error(f"Failed to notify user {user_id} about ban: {e}")
        
        await query.edit_message_text(
            f"کاربر با ID {user_id} با موفقیت مسدود شد!",
            reply_markup=get_user_management_menu()
        )
    except Exception as e:
        logger.error(f"Error blocking user {user_id}: {e}")
        await query.edit_message_text(
            "خطا در مسدود کردن کاربر. لطفاً دوباره تلاش کنید.",
            reply_markup=get_user_management_menu()
        )
    
    return ConversationHandler.END

async def start_unblock_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the unblock user process."""
    query = update.callback_query
    await query.answer()
    
    # Get list of banned users
    users = session.query(User).filter(User.is_banned == True).all()
    keyboard = []
    
    # Create buttons for each banned user
    for user in users:
        # Get username safely
        username_value = session.query(User.username).filter(User.telegram_id == user.telegram_id).scalar()
        username = str(username_value) if username_value is not None else f"ID: {user.telegram_id}"
        
        # Get first and last name safely
        first_name = session.query(User.first_name).filter(User.telegram_id == user.telegram_id).scalar() or ''
        last_name = session.query(User.last_name).filter(User.telegram_id == user.telegram_id).scalar() or ''
        
        button = InlineKeyboardButton(
            f"{username} - {first_name} {last_name}".strip(),
            callback_data=f"unblock_user_{user.telegram_id}"
        )
        keyboard.append([button])
    
    if not users:
        keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_user_management")]]
        await query.edit_message_text(
            "هیچ کاربر مسدودی وجود ندارد.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return ConversationHandler.END
    
    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_user_management")])
    
    await query.edit_message_text(
        "لطفاً کاربر مورد نظر را برای آزاد کردن انتخاب کنید یا ID تلگرام کاربر را وارد کنید:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return WAITING_USER_TO_UNBLOCK

async def handle_unblock_user_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle user input for unblocking - either from button or manual ID."""
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        user_id = int(query.data.split('_')[2])
    else:
        try:
            user_id = int(update.message.text)
        except ValueError:
            await update.message.reply_text(
                "لطفاً یک ID معتبر وارد کنید.",
                reply_markup=get_user_management_menu()
            )
            return WAITING_USER_TO_UNBLOCK
    
    # Get user from database
    user = User.get_by_telegram_id(user_id)
    if not user:
        message = "کاربر با این ID یافت نشد. لطفاً دوباره امتحان کنید."
        if update.callback_query:
            await query.edit_message_text(message, reply_markup=get_user_management_menu())
        else:
            await update.message.reply_text(message, reply_markup=get_user_management_menu())
        return WAITING_USER_TO_UNBLOCK
    
    # Check if user is banned using SQLAlchemy comparison
    is_banned = session.query(User.is_banned).filter(User.telegram_id == user_id).scalar()
    if not is_banned:
        message = "این کاربر مسدود نیست!"
        if update.callback_query:
            await query.edit_message_text(message, reply_markup=get_user_management_menu())
        else:
            await update.message.reply_text(message, reply_markup=get_user_management_menu())
        return WAITING_USER_TO_UNBLOCK
    
    # Store user ID in context for confirmation
    context.user_data['unblock_user_id'] = user_id
    
    # Show user info and ask for confirmation
    keyboard = [
        [
            InlineKeyboardButton("✅ تأیید", callback_data="confirm_unblock"),
            InlineKeyboardButton("❌ لغو", callback_data="cancel_unblock")
        ]
    ]
    
    message = (
        f"اطلاعات کاربر:\n"
        f"ID تلگرام: {user.telegram_id}\n"
        f"نام: {str(user.username or 'تنظیم نشده')}\n"
        f"نام کامل: {str(user.first_name or '')} {str(user.last_name or '')}\n"
        f"وضعیت: مسدود\n\n"
        f"آیا می‌خواهید این کاربر را آزاد کنید؟"
    )
    
    if update.callback_query:
        await query.edit_message_text(message, reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.message.reply_text(message, reply_markup=InlineKeyboardMarkup(keyboard))
    
    return CONFIRM_USER_UNBLOCK

async def confirm_unblock_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle confirmation of user unblock."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "cancel_unblock":
        await query.edit_message_text(
            "عملیات آزاد کردن کاربر لغو شد.",
            reply_markup=get_user_management_menu()
        )
        return ConversationHandler.END
    
    user_id = context.user_data.get('unblock_user_id')
    if not user_id:
        await query.edit_message_text(
            "خطا در فرآیند آزاد کردن. لطفاً دوباره تلاش کنید.",
            reply_markup=get_user_management_menu()
        )
        return ConversationHandler.END
    
    try:
        # Update user status using SQLAlchemy update
        session.query(User).filter(User.telegram_id == user_id).update(
            {
                User.is_banned: False,
                User.unbanned_at: datetime.utcnow()
            }
        )
        session.commit()
        
        # Try to notify the user
        try:
            await context.bot.send_message(
                user_id,
                "دسترسی شما به ربات دوباره فعال شد. اکنون می‌توانید از خدمات استفاده کنید."
            )
        except Exception as e:
            logger.error(f"Failed to notify user {user_id} about unban: {e}")
        
        await query.edit_message_text(
            f"کاربر با ID {user_id} با موفقیت آزاد شد!",
            reply_markup=get_user_management_menu()
        )
    except Exception as e:
        logger.error(f"Error unblocking user {user_id}: {e}")
        await query.edit_message_text(
            "خطا در آزاد کردن کاربر. لطفاً دوباره تلاش کنید.",
            reply_markup=get_user_management_menu()
        )
    
    return ConversationHandler.END

async def handle_xui_server_management(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle X-UI server management section."""
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("🖥 سرورهای موجود", callback_data="xui_servers_list")],
        [InlineKeyboardButton("➕ افزودن سرور", callback_data="xui_server_add")],
        [InlineKeyboardButton("✏️ ویرایش سرور", callback_data="xui_server_edit")],
        [InlineKeyboardButton("❌ حذف سرور", callback_data="xui_server_delete")],
        [InlineKeyboardButton("🔄 همگام‌سازی", callback_data="xui_server_sync")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_admin")]
    ]
    
    await query.edit_message_text(
        "🖥 مدیریت سرورهای X-UI\n"
        "لطفاً یک گزینه را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def list_xui_servers(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """List all X-UI servers."""
    query = update.callback_query
    await query.answer()
    
    servers = XUIServer.get_active_servers()
    if not servers:
        await query.edit_message_text(
            "هیچ سرور X-UI یافت نشد.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_xui_management")]
            ])
        )
        return
    
    message = "📋 لیست سرورهای X-UI:\n\n"
    for server in servers:
        status = "✅ فعال" if session.scalar(select(server.status)) else "❌ غیرفعال"
        server_name = session.scalar(select(server.name))
        server_url = session.scalar(select(server.url))
        message += f"🖥 {server_name}\n"
        message += f"🌐 {server_url}\n"
        message += f"📊 {status}\n"
        message += "➖➖➖➖➖➖➖➖\n"
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_xui_management")]
        ])
    )

async def start_add_xui_server(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the add X-UI server process."""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "لطفاً نام سرور را وارد کنید (مثال: سرور ایران):",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 لغو", callback_data="cancel_xui_server")]
        ])
    )
    return WAITING_XUI_SERVER_NAME

async def handle_xui_server_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle X-UI server name input."""
    # Store server name in context
    context.user_data['xui_server_name'] = update.message.text
    
    await update.message.reply_text(
        "لطفاً آدرس پنل X-UI را وارد کنید (مثال: http://example.com:54321):",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 لغو", callback_data="cancel_xui_server")]
        ])
    )
    return WAITING_XUI_SERVER_URL

async def handle_xui_server_url(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle X-UI server URL input."""
    # Store server URL in context
    context.user_data['xui_server_url'] = update.message.text
    
    await update.message.reply_text(
        "لطفاً نام کاربری و رمز عبور یا توکن امنیتی را در قالب زیر وارد کنید:\n"
        "username|password\n"
        "یا\n"
        "token",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 لغو", callback_data="cancel_xui_server")]
        ])
    )
    return WAITING_XUI_SERVER_CREDENTIALS

async def handle_xui_server_credentials(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle X-UI server credentials input."""
    credentials = update.message.text.strip()
    
    if "|" in credentials:
        username, password = credentials.split("|")
        context.user_data['xui_server_username'] = username.strip()
        context.user_data['xui_server_password'] = password.strip()
        context.user_data['xui_server_token'] = None
    else:
        context.user_data['xui_server_username'] = None
        context.user_data['xui_server_password'] = None
        context.user_data['xui_server_token'] = credentials.strip()
    
    # Test connection
    client = XUIClient(
        url=context.user_data['xui_server_url'],
        username=context.user_data['xui_server_username'],
        password=context.user_data['xui_server_password'],
        token=context.user_data['xui_server_token']
    )
    
    if not client.check_connection():
        await update.message.reply_text(
            "❌ خطا در اتصال به سرور X-UI. لطفاً اطلاعات را بررسی کرده و دوباره تلاش کنید.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 تلاش مجدد", callback_data="xui_server_add")],
                [InlineKeyboardButton("🔙 لغو", callback_data="cancel_xui_server")]
            ])
        )
        return ConversationHandler.END
    
    # Show confirmation
    message = (
        "📋 اطلاعات سرور X-UI:\n\n"
        f"نام: {context.user_data['xui_server_name']}\n"
        f"آدرس: {context.user_data['xui_server_url']}\n"
        f"احراز هویت: {'نام کاربری و رمز عبور' if context.user_data['xui_server_username'] else 'توکن'}\n\n"
        "آیا اطلاعات فوق را تأیید می‌کنید؟"
    )
    
    await update.message.reply_text(
        message,
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ تأیید", callback_data="confirm_xui_server"),
                InlineKeyboardButton("❌ لغو", callback_data="cancel_xui_server")
            ]
        ])
    )
    return CONFIRM_XUI_SERVER

async def confirm_add_xui_server(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle X-UI server addition confirmation."""
    query = update.callback_query
    await query.answer()
    
    try:
        # Create new server
        server = XUIServer(
            name=context.user_data['xui_server_name'],
            url=context.user_data['xui_server_url'],
            username=context.user_data['xui_server_username'],
            password=context.user_data['xui_server_password'],
            token=context.user_data['xui_server_token'],
            status=True
        )
        session.add(server)
        session.commit()
        
        # Clear context data
        context.user_data.clear()
        
        await query.edit_message_text(
            "✅ سرور X-UI با موفقیت اضافه شد!",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_xui_management")]
            ])
        )
    except Exception as e:
        logger.error(f"Error adding X-UI server: {e}")
        await query.edit_message_text(
            "❌ خطا در افزودن سرور X-UI. لطفاً دوباره تلاش کنید.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_xui_management")]
            ])
        )
    
    return ConversationHandler.END

async def start_edit_xui_server(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the edit X-UI server process."""
    query = update.callback_query
    await query.answer()
    
    servers = XUIServer.get_active_servers()
    if not servers:
        await query.edit_message_text(
            "هیچ سرور X-UI برای ویرایش یافت نشد.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_xui_management")]
            ])
        )
        return ConversationHandler.END
    
    keyboard = []
    for server in servers:
        server_name = session.scalar(select(server.name))
        keyboard.append([
            InlineKeyboardButton(
                f"🖥 {server_name}",
                callback_data=f"edit_xui_server_{server.id}"
            )
        ])
    
    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_xui_management")])
    
    await query.edit_message_text(
        "لطفاً سرور مورد نظر برای ویرایش را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return WAITING_XUI_SERVER_EDIT

async def handle_edit_xui_server(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle X-UI server edit selection."""
    query = update.callback_query
    await query.answer()
    
    server_id = int(query.data.split("_")[-1])
    server = session.get(XUIServer, server_id)
    
    if not server:
        await query.edit_message_text(
            "❌ سرور مورد نظر یافت نشد.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_xui_management")]
            ])
        )
        return ConversationHandler.END
    
    # Store server ID in context
    context.user_data['edit_xui_server_id'] = server_id
    
    # Pre-fill context with current values
    server_name = session.scalar(select(server.name))
    server_url = session.scalar(select(server.url))
    server_username = session.scalar(select(server.username))
    server_password = session.scalar(select(server.password))
    server_token = session.scalar(select(server.token))
    
    context.user_data['xui_server_name'] = server_name
    context.user_data['xui_server_url'] = server_url
    context.user_data['xui_server_username'] = server_username
    context.user_data['xui_server_password'] = server_password
    context.user_data['xui_server_token'] = server_token
    
    await query.edit_message_text(
        f"ویرایش سرور: {server_name}\n"
        "لطفاً نام جدید سرور را وارد کنید:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 لغو", callback_data="cancel_xui_server")]
        ])
    )
    return WAITING_XUI_SERVER_NAME

async def start_delete_xui_server(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the delete X-UI server process."""
    query = update.callback_query
    await query.answer()
    
    servers = XUIServer.get_active_servers()
    if not servers:
        await query.edit_message_text(
            "هیچ سرور X-UI برای حذف یافت نشد.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_xui_management")]
            ])
        )
        return ConversationHandler.END
    
    keyboard = []
    for server in servers:
        server_name = session.scalar(select(server.name))
        keyboard.append([
            InlineKeyboardButton(
                f"🖥 {server_name}",
                callback_data=f"delete_xui_server_{server.id}"
            )
        ])
    
    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_xui_management")])
    
    await query.edit_message_text(
        "⚠️ لطفاً سرور مورد نظر برای حذف را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return CONFIRM_XUI_SERVER_DELETE

async def confirm_delete_xui_server(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle X-UI server deletion confirmation."""
    query = update.callback_query
    await query.answer()
    
    server_id = int(query.data.split("_")[-1])
    server = session.get(XUIServer, server_id)
    
    if not server:
        await query.edit_message_text(
            "❌ سرور مورد نظر یافت نشد.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_xui_management")]
            ])
        )
        return ConversationHandler.END
    
    try:
        # Check if server has active configs
        active_configs = XUIConfig.get_active_configs()
        server_configs = [c for c in active_configs if session.scalar(select(c.server_id)) == server_id]
        
        if server_configs:
            server_name = session.scalar(select(server.name))
            await query.edit_message_text(
                f"❌ امکان حذف سرور {server_name} وجود ندارد.\n"
                f"این سرور دارای {len(server_configs)} کانفیگ فعال است.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_xui_management")]
                ])
            )
            return ConversationHandler.END
        
        # Delete server
        session.delete(server)
        session.commit()
        
        server_name = session.scalar(select(server.name))
        await query.edit_message_text(
            f"✅ سرور {server_name} با موفقیت حذف شد!",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_xui_management")]
            ])
        )
    except Exception as e:
        logger.error(f"Error deleting X-UI server: {e}")
        await query.edit_message_text(
            "❌ خطا در حذف سرور X-UI. لطفاً دوباره تلاش کنید.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_xui_management")]
            ])
        )
    
    return ConversationHandler.END

# Update the conversation handler
admin_conv_handler = ConversationHandler(
    entry_points=[MessageHandler(filters.Regex("^🎛 پنل مدیریت$"), admin_panel)],
    states={
        ADMIN_START: [
            MessageHandler(filters.Regex("^🛠 تنظیمات درگاه‌های پرداخت$"), handle_gateway_management),
            MessageHandler(filters.Regex("^📁 مدیریت دسته‌بندی‌ها$"), handle_category_management),
            MessageHandler(filters.Regex("^💰 مدیریت پلن‌ها$"), handle_plan_management),
            MessageHandler(filters.Regex("^🖥 مدیریت سرورها$"), handle_server_management),
            MessageHandler(filters.Regex("^👥 مدیریت کاربران$"), handle_user_management),
            MessageHandler(filters.Regex("^🔙 بازگشت به منوی اصلی$"), handle_admin_message),
            CallbackQueryHandler(start_block_user, pattern="^user_block$"),
            CallbackQueryHandler(start_unblock_user, pattern="^user_unblock$"),
        ],
        WAITING_GATEWAY_INFO: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_gateway_info)],
        WAITING_CATEGORY_INFO: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_category_info)],
        WAITING_SERVER_INFO: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_server_info)],
        WAITING_PLAN_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_plan_name)],
        WAITING_PLAN_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_plan_price)],
        WAITING_PLAN_DURATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_plan_duration)],
        WAITING_PLAN_DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_plan_description)],
        WAITING_USER_TO_BLOCK: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_block_user_input),
            CallbackQueryHandler(handle_block_user_input, pattern="^block_user_"),
            CallbackQueryHandler(handle_user_management, pattern="^back_to_user_management$"),
        ],
        CONFIRM_USER_BLOCK: [
            CallbackQueryHandler(confirm_block_user, pattern="^confirm_block$"),
            CallbackQueryHandler(handle_user_management, pattern="^cancel_block$"),
        ],
        WAITING_USER_TO_UNBLOCK: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_unblock_user_input),
            CallbackQueryHandler(handle_unblock_user_input, pattern="^unblock_user_"),
            CallbackQueryHandler(handle_user_management, pattern="^back_to_user_management$"),
        ],
        CONFIRM_USER_UNBLOCK: [
            CallbackQueryHandler(confirm_unblock_user, pattern="^confirm_unblock$"),
            CallbackQueryHandler(handle_user_management, pattern="^cancel_unblock$"),
        ],
        WAITING_XUI_SERVER_NAME: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_xui_server_name),
            CallbackQueryHandler(handle_xui_server_management, pattern="^cancel_xui_server$")
        ],
        WAITING_XUI_SERVER_URL: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_xui_server_url),
            CallbackQueryHandler(handle_xui_server_management, pattern="^cancel_xui_server$")
        ],
        WAITING_XUI_SERVER_CREDENTIALS: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_xui_server_credentials),
            CallbackQueryHandler(handle_xui_server_management, pattern="^cancel_xui_server$")
        ],
        CONFIRM_XUI_SERVER: [
            CallbackQueryHandler(confirm_add_xui_server, pattern="^confirm_xui_server$"),
            CallbackQueryHandler(handle_xui_server_management, pattern="^cancel_xui_server$")
        ],
        WAITING_XUI_SERVER_EDIT: [
            CallbackQueryHandler(handle_edit_xui_server, pattern="^edit_xui_server_"),
            CallbackQueryHandler(handle_xui_server_management, pattern="^back_to_xui_management$")
        ],
        CONFIRM_XUI_SERVER_DELETE: [
            CallbackQueryHandler(confirm_delete_xui_server, pattern="^delete_xui_server_"),
            CallbackQueryHandler(handle_xui_server_management, pattern="^back_to_xui_management$")
        ]
    },
    fallbacks=[MessageHandler(filters.Regex("^🔙 بازگشت به منوی اصلی$"), handle_admin_message)]
) 