from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
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

user_states = {}

def is_admin(user_id: int) -> bool:
    """Check if user is an admin."""
    return user_id in ADMIN_IDS

def admin_panel(bot, message):
    """Show admin panel with keyboard buttons."""
    user = message.from_user
    
    # Check if user is admin
    admin = User.get_by_telegram_id(user.id)
    if not admin or not admin.is_admin:
        bot.send_message(message.chat.id, "⛔️ شما دسترسی به پنل ادمین را ندارید.")
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
    
    bot.send_message(
        message.chat.id,
        "🔰 به پنل مدیریت خوش آمدید.\n"
        "لطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
        reply_markup=reply_markup
    )

def handle_admin_message(bot, message):
    """Handle admin panel messages."""
    text = message.text
    user = message.from_user

    # Check if user is admin
    admin = User.get_by_telegram_id(user.id)
    if not admin or not admin.is_admin:
        return

    # Map commands to functions
    command_handlers = {
        "🛠 تنظیمات درگاه‌های پرداخت": handle_gateway_management,
        "📁 مدیریت دسته‌بندی‌ها": handle_category_management,
        "💰 مدیریت پلن‌ها": handle_plan_management,
        "🖥 مدیریت سرورها": handle_server_management,
        "👥 مدیریت کاربران": handle_user_management,
        "📊 گزارش‌ها": admin_reports,
        "📨 ارسال پیام همگانی": admin_broadcast,
        "💾 پشتیبان‌گیری": admin_backup,
    }

    handler = command_handlers.get(text)
    if handler:
        handler(bot, message)
    elif text == "🔙 بازگشت به منوی اصلی":
        from bot.handlers.user import get_main_keyboard
        bot.send_message(
            message.chat.id,
            "🏠 به منوی اصلی بازگشتید.\n"
            "لطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
            reply_markup=get_main_keyboard()
        )
    else:
        state = user_states.get(message.chat.id)
        if state == 'WAITING_GATEWAY_INFO':
            handle_gateway_info(bot, message)
        elif state == 'WAITING_CATEGORY_INFO':
            handle_category_info(bot, message)
        elif state == 'WAITING_SERVER_INFO':
            handle_server_info(bot, message)
        elif state == 'WAITING_PLAN_NAME':
            handle_plan_name(bot, message)
        elif state == 'WAITING_PLAN_PRICE':
            handle_plan_price(bot, message)
        elif state == 'WAITING_PLAN_DURATION':
            handle_plan_duration(bot, message)
        elif state == 'WAITING_PLAN_DESCRIPTION':
            handle_plan_description(bot, message)
        elif state == 'WAITING_USER_TO_BLOCK':
            handle_block_user_input(bot, message)
        elif state == 'WAITING_USER_TO_UNBLOCK':
            handle_unblock_user_input(bot, message)
        elif state == 'WAITING_XUI_SERVER_NAME':
            handle_xui_server_name(bot, message)
        elif state == 'WAITING_XUI_SERVER_URL':
            handle_xui_server_url(bot, message)
        elif state == 'WAITING_XUI_SERVER_CREDENTIALS':
            handle_xui_server_credentials(bot, message)

def admin_reports(bot, message):
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
    
    bot.send_message(
        message.chat.id,
        "📊 گزارش‌ها\n"
        "لطفاً نوع گزارش را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def admin_broadcast(bot, message):
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
    
    bot.send_message(
        message.chat.id,
        "📨 ارسال پیام همگانی\n"
        "لطفاً نوع ارسال را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def admin_backup(bot, message):
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
    
    bot.send_message(
        message.chat.id,
        "💾 پشتیبان‌گیری\n"
        "لطفاً نوع پشتیبان‌گیری را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def admin_users(bot, message):
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
    
    bot.send_message(
        message.chat.id,
        "👥 مدیریت کاربران\n"
        "لطفاً عملیات مورد نظر را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ... (The rest of the functions will be converted similarly, removing async/await and adapting the bot calls)
# ... I will omit the rest of the file for brevity, but the conversion will be applied to all functions.
# ... The state management will be handled by a simple dictionary `user_states`.
# ... For example, `user_states[message.chat.id] = 'WAITING_SERVER_INFO'`
# ... and then in the message handler, I'll check the state:
# ... `if user_states.get(message.chat.id) == 'WAITING_SERVER_INFO':`
# ...     `handle_server_info(bot, message)`
# ...     `user_states.pop(message.chat.id, None)`
# ... This is a simplified version of the ConversationHandler.
# I will now write the full converted file.
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
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

user_states = {}

def is_admin(user_id: int) -> bool:
    """Check if user is an admin."""
    return user_id in ADMIN_IDS
def get_admin_keyboard():
    """کیبورد منوی مدیریت ادمین"""
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(
        KeyboardButton("🛠 تنظیمات درگاه‌های پرداخت"),
        KeyboardButton("📢 تنظیمات کانال")
    )
    markup.row(
        KeyboardButton("📁 مدیریت دسته‌بندی‌ها"),
        KeyboardButton("💰 مدیریت پلن‌ها")
    )
    markup.row(
        KeyboardButton("🖥 مدیریت سرورها"),
        KeyboardButton("📊 گزارش‌ها")
    )
    markup.row(
        KeyboardButton("📨 ارسال پیام همگانی"),
        KeyboardButton("💾 پشتیبان‌گیری")
    )
    markup.row(
        KeyboardButton("👥 مدیریت کاربران"),
        KeyboardButton("🔙 بازگشت به منوی اصلی")
    )
    return markup

def admin_panel(bot, message):
    """نمایش منوی پنل ادمین"""
    user = message.from_user

    # بررسی ادمین بودن
    admin = User.get_by_telegram_id(user.id)
    if not admin or not admin.is_admin:
        bot.send_message(message.chat.id, "⛔️ شما دسترسی به پنل ادمین را ندارید.")
        return

    # ارسال منوی مدیریت
    bot.send_message(
        message.chat.id,
        "🔰 به پنل مدیریت خوش آمدید.\nلطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
        reply_markup=get_admin_keyboard()
    )


def handle_admin_message(bot, message):
    """Handle admin panel messages."""
    text = message.text
    user = message.from_user
    
    # Check if user is admin
    admin = User.get_by_telegram_id(user.id)
    if not admin or not admin.is_admin:
        return

    if text == "🛠 تنظیمات درگاه‌های پرداخت":
        handle_gateway_management(bot, message)
    elif text == "📁 مدیریت دسته‌بندی‌ها":
        handle_category_management(bot, message)
    elif text == "💰 مدیریت پلن‌ها":
        handle_plan_management(bot, message)
    elif text == "🖥 مدیریت سرورها":
        handle_server_management(bot, message)
    elif text == "👥 مدیریت کاربران":
        handle_user_management(bot, message)
    elif text == "📊 گزارش‌ها":
        admin_reports(bot, message)
    elif text == "📨 ارسال پیام همگانی":
        admin_broadcast(bot, message)
    elif text == "💾 پشتیبان‌گیری":
        admin_backup(bot, message)
    elif text == "🔙 بازگشت به منوی اصلی":
        from bot.handlers.user import get_main_keyboard
        bot.send_message(
            message.chat.id,
            "🏠 به منوی اصلی بازگشتید.\n"
            "لطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
            reply_markup=get_main_keyboard()
        )
    else:
        state = user_states.get(message.chat.id)
        if state == 'WAITING_GATEWAY_INFO':
            handle_gateway_info(bot, message)
        elif state == 'WAITING_CATEGORY_INFO':
            handle_category_info(bot, message)
        elif state == 'WAITING_SERVER_INFO':
            handle_server_info(bot, message)
        elif state == 'WAITING_PLAN_NAME':
            handle_plan_name(bot, message)
        elif state == 'WAITING_PLAN_PRICE':
            handle_plan_price(bot, message)
        elif state == 'WAITING_PLAN_DURATION':
            handle_plan_duration(bot, message)
        elif state == 'WAITING_PLAN_DESCRIPTION':
            handle_plan_description(bot, message)
        elif state == 'WAITING_USER_TO_BLOCK':
            handle_block_user_input(bot, message)
        elif state == 'WAITING_USER_TO_UNBLOCK':
            handle_unblock_user_input(bot, message)
        elif state == 'WAITING_XUI_SERVER_NAME':
            handle_xui_server_name(bot, message)
        elif state == 'WAITING_XUI_SERVER_URL':
            handle_xui_server_url(bot, message)
        elif state == 'WAITING_XUI_SERVER_CREDENTIALS':
            handle_xui_server_credentials(bot, message)

def handle_gateway_management(bot, message):
    keyboard = [
        [InlineKeyboardButton("💳 درگاه‌های فعال", callback_data="gateways_list")],
        [InlineKeyboardButton("➕ افزودن درگاه", callback_data="gateway_add")],
        [InlineKeyboardButton("✏️ ویرایش درگاه", callback_data="gateway_edit")],
        [InlineKeyboardButton("❌ حذف درگاه", callback_data="gateway_delete")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_admin")]
    ]
    bot.send_message(
        message.chat.id,
        "🛠 مدیریت درگاه‌های پرداخت\n"
        "لطفاً یک گزینه را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def add_gateway(bot, message):
    user_states[message.chat.id] = 'WAITING_GATEWAY_INFO'
    bot.send_message(
        message.chat.id,
        "لطفاً اطلاعات درگاه پرداخت را در قالب زیر وارد کنید:\n"
        "NAME|API_KEY|TYPE\n"
        "مثال:\n"
        "ZarinPal|your-api-key-here|zarinpal"
    )

def handle_gateway_info(bot, message):
    try:
        name, api_key, gateway_type = message.text.split("|")
        Setting.create_payment_gateway(
            name=name.strip(),
            gateway_type=gateway_type.strip(),
            api_key=api_key.strip()
        )
        bot.send_message(
            message.chat.id,
            "درگاه پرداخت با موفقیت اضافه شد.",
            reply_markup=get_admin_main_menu()
        )
    except ValueError:
        bot.send_message(
            message.chat.id,
            "فرمت ورودی اشتباه است. لطفاً اطلاعات را در قالب NAME|API_KEY|TYPE وارد کنید.",
            reply_markup=get_admin_main_menu()
        )
    except Exception as e:
        logger.error(f"Error adding gateway: {e}")
        bot.send_message(
            message.chat.id,
            f"خطا در افزودن درگاه پرداخت: {e}",
            reply_markup=get_admin_main_menu()
        )
    user_states.pop(message.chat.id, None)

def handle_category_management(bot, message):
    keyboard = [
        [InlineKeyboardButton("📁 دسته‌بندی‌های موجود", callback_data="categories_list")],
        [InlineKeyboardButton("➕ افزودن دسته‌بندی", callback_data="category_add")],
        [InlineKeyboardButton("✏️ ویرایش دسته‌بندی", callback_data="category_edit")],
        [InlineKeyboardButton("❌ حذف دسته‌بندی", callback_data="category_delete")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_admin")]
    ]
    bot.send_message(
        message.chat.id,
        "📁 مدیریت دسته‌بندی‌ها\n"
        "لطفاً یک گزینه را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def add_category(bot, message):
    user_states[message.chat.id] = 'WAITING_CATEGORY_INFO'
    bot.send_message(
        message.chat.id,
        "لطفاً نام و توضیحات دسته‌بندی را در قالب زیر وارد کنید:\n"
        "NAME|DESCRIPTION\n"
        "مثال:\n"
        "VIP|سرویس‌های ویژه با سرعت بالا"
    )

def handle_category_info(bot, message):
    try:
        name, description = message.text.split("|")
        category = ServerCategory(
            title=name.strip(),
            remark=description.strip(),
            server_ids=[]  # Empty list initially, servers can be added later
        )
        category.save()
        bot.send_message(
            message.chat.id,
            "دسته‌بندی با موفقیت اضافه شد.",
            reply_markup=get_admin_main_menu()
        )
    except ValueError:
        bot.send_message(
            message.chat.id,
            "فرمت ورودی اشتباه است. لطفاً اطلاعات را در قالب NAME|DESCRIPTION وارد کنید.",
            reply_markup=get_admin_main_menu()
        )
    except Exception as e:
        logger.error(f"Error adding category: {e}")
        bot.send_message(
            message.chat.id,
            f"خطا در افزودن دسته‌بندی: {e}",
            reply_markup=get_admin_main_menu()
        )
    user_states.pop(message.chat.id, None)

def handle_plan_management(bot, message):
    keyboard = [
        [InlineKeyboardButton("💰 پلن‌های موجود", callback_data="plans_list")],
        [InlineKeyboardButton("➕ افزودن پلن", callback_data="plan_add")],
        [InlineKeyboardButton("✏️ ویرایش پلن", callback_data="plan_edit")],
        [InlineKeyboardButton("❌ حذف پلن", callback_data="plan_delete")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_admin")]
    ]
    bot.send_message(
        message.chat.id,
        "💰 مدیریت پلن‌ها\n"
        "لطفاً یک گزینه را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def add_plan(bot, message):
    user_states[message.chat.id] = 'WAITING_PLAN_NAME'
    bot.send_message(message.chat.id, "لطفاً نام پلن را وارد کنید:")

def handle_plan_name(bot, message):
    user_states[message.chat.id] = {'state': 'WAITING_PLAN_PRICE', 'plan_name': message.text}
    bot.send_message(message.chat.id, "لطفاً قیمت پلن را به تومان وارد کنید:")

def handle_plan_price(bot, message):
    try:
        price = int(message.text)
        data = user_states[message.chat.id]
        data['state'] = 'WAITING_PLAN_DURATION'
        data['plan_price'] = price
        bot.send_message(message.chat.id, "لطفاً مدت زمان پلن را به روز وارد کنید:")
    except ValueError:
        bot.send_message(message.chat.id, "لطفاً یک عدد صحیح وارد کنید.")

def handle_plan_duration(bot, message):
    try:
        duration = int(message.text)
        data = user_states[message.chat.id]
        data['state'] = 'WAITING_PLAN_DESCRIPTION'
        data['plan_duration'] = duration
        bot.send_message(message.chat.id, "لطفاً توضیحات پلن را وارد کنید:")
    except ValueError:
        bot.send_message(message.chat.id, "لطفاً یک عدد صحیح وارد کنید.")

def handle_plan_description(bot, message):
    try:
        data = user_states[message.chat.id]
        plan = Plan(
            name=data['plan_name'],
            price=data['plan_price'],
            duration=data['plan_duration'],
            description=message.text
        )
        plan.save()
        bot.send_message(
            message.chat.id,
            "پلن با موفقیت اضافه شد.",
            reply_markup=get_admin_main_menu()
        )
    except Exception as e:
        logger.error(f"Error adding plan: {e}")
        bot.send_message(
            message.chat.id,
            f"خطا در افزودن پلن: {e}",
            reply_markup=get_admin_main_menu()
        )
    user_states.pop(message.chat.id, None)

from bot.handlers.server_management import (
    start_server_add,
    handle_server_management_message,
    cancel_server_add,
)
def handle_server_management(bot, message):
    """Shows the server management menu."""
    bot.send_message(
        message.chat.id,
        "🖥 مدیریت سرورها\n"
        "لطفاً یک گزینه را انتخاب کنید:",
        reply_markup=get_server_management_menu()
    )

def handle_user_management(bot, message):
    keyboard = [
        [
            InlineKeyboardButton("🚫 مسدود کردن کاربر", callback_data="user_block"),
            InlineKeyboardButton("✅ آزاد کردن کاربر", callback_data="user_unblock")
        ],
        [InlineKeyboardButton("👥 لیست کاربران", callback_data="user_list")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_admin")]
    ]
    bot.send_message(
        message.chat.id,
        "👥 مدیریت کاربران\n"
        "لطفاً یک گزینه را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def start_block_user(bot, message):
    user_states[message.chat.id] = 'WAITING_USER_TO_BLOCK'
    bot.send_message(
        message.chat.id,
        "لطفاً ID تلگرام کاربری که می‌خواهید مسدود کنید را وارد کنید:",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_user_management")]])
    )

def handle_user_block_status_input(bot, message, block=True):
    try:
        user_id = int(message.text)
        user = User.get_by_telegram_id(user_id)
        if not user:
            bot.send_message(message.chat.id, "کاربر با این ID یافت نشد. لطفاً دوباره امتحان کنید.")
            return

        if block and user.is_banned:
            bot.send_message(message.chat.id, "این کاربر قبلاً مسدود شده است.")
            return

        if not block and not user.is_banned:
            bot.send_message(message.chat.id, "این کاربر مسدود نیست.")
            return

        action = "مسدود" if block else "آزاد"
        user_states[message.chat.id] = {'state': f'CONFIRM_USER_{"BLOCK" if block else "UNBLOCK"}', 'user_id': user_id}
        keyboard = [
            [
                InlineKeyboardButton("✅ تأیید", callback_data=f"confirm_{'block' if block else 'unblock'}"),
                InlineKeyboardButton("❌ لغو", callback_data="cancel_block_unblock")
            ]
        ]
        bot.send_message(
            message.chat.id,
            f"اطلاعات کاربر:\n"
            f"ID تلگرام: {user.telegram_id}\n"
            f"نام: {str(user.username or 'تنظیم نشده')}\n"
            f"نام کامل: {str(user.first_name or '')} {str(user.last_name or '')}\n"
            f"وضعیت: {'مسدود' if user.is_banned else 'فعال'}\n\n"
            f"آیا می‌خواهید این کاربر را {action} کنید؟",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except ValueError:
        bot.send_message(message.chat.id, "لطفاً یک ID معتبر وارد کنید.")

def handle_block_user_input(bot, message):
    handle_user_block_status_input(bot, message, block=True)

def handle_unblock_user_input(bot, message):
    handle_user_block_status_input(bot, message, block=False)

def confirm_user_block_status(bot, message, block=True):
    state_str = "BLOCK" if block else "UNBLOCK"
    data = user_states.get(message.chat.id)
    if not data or data.get('state') != f'CONFIRM_USER_{state_str}':
        return

    user_id = data.get('user_id')
    action_gerund = "مسدود کردن" if block else "آزاد کردن"
    action_past = "مسدود" if block else "آزاد"
    notification_message = "دسترسی شما به ربات به دلیل نقض قوانین مسدود شد. برای اطلاعات بیشتر با پشتیبانی تماس بگیرید." if block else "دسترسی شما به ربات دوباره فعال شد. اکنون می‌توانید از خدمات استفاده کنید."

    try:
        update_values = {User.is_banned: block}
        if block:
            update_values[User.banned_at] = datetime.utcnow()
        else:
            update_values[User.unbanned_at] = datetime.utcnow()

        session.query(User).filter(User.telegram_id == user_id).update(update_values)
        session.commit()

        try:
            bot.send_message(user_id, notification_message)
        except Exception as e:
            logger.error(f"Failed to notify user {user_id} about {'ban' if block else 'unban'}: {e}")

        bot.send_message(
            message.chat.id,
            f"کاربر با ID {user_id} با موفقیت {action_past} شد!",
            reply_markup=get_user_management_menu()
        )
    except Exception as e:
        logger.error(f"Error {action_gerund} user {user_id}: {e}")
        bot.send_message(
            message.chat.id,
            f"خطا در {action_gerund} کاربر. لطفاً دوباره تلاش کنید.",
            reply_markup=get_user_management_menu()
        )
    user_states.pop(message.chat.id, None)

def confirm_block_user(bot, message):
    confirm_user_block_status(bot, message, block=True)

def confirm_unblock_user(bot, message):
    confirm_user_block_status(bot, message, block=False)

def start_unblock_user(bot, message):
    user_states[message.chat.id] = 'WAITING_USER_TO_UNBLOCK'
    bot.send_message(
        message.chat.id,
        "لطفاً ID تلگرام کاربری که می‌خواهید آزاد کنید را وارد کنید:",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_user_management")]])
    )

def handle_unblock_user_input(bot, message):
    try:
        user_id = int(message.text)
        user = User.get_by_telegram_id(user_id)
        if not user:
            bot.send_message(message.chat.id, "کاربر با این ID یافت نشد. لطفاً دوباره امتحان کنید.")
            return

        if not session.query(User.is_banned).filter(User.telegram_id == user_id).scalar():
            bot.send_message(message.chat.id, "این کاربر مسدود نیست!")
            return

        user_states[message.chat.id] = {'state': 'CONFIRM_USER_UNBLOCK', 'user_id': user_id}
        keyboard = [
            [
                InlineKeyboardButton("✅ تأیید", callback_data="confirm_unblock"),
                InlineKeyboardButton("❌ لغو", callback_data="cancel_unblock")
            ]
        ]
        bot.send_message(
            message.chat.id,
            f"اطلاعات کاربر:\n"
            f"ID تلگرام: {user.telegram_id}\n"
            f"نام: {str(user.username or 'تنظیم نشده')}\n"
            f"نام کامل: {str(user.first_name or '')} {str(user.last_name or '')}\n"
            f"وضعیت: مسدود\n\n"
            f"آیا می‌خواهید این کاربر را آزاد کنید؟",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except ValueError:
        bot.send_message(message.chat.id, "لطفاً یک ID معتبر وارد کنید.")

def confirm_unblock_user(bot, message):
    data = user_states.get(message.chat.id)
    if not data or data.get('state') != 'CONFIRM_USER_UNBLOCK':
        return

    user_id = data.get('user_id')
    try:
        session.query(User).filter(User.telegram_id == user_id).update(
            {
                User.is_banned: False,
                User.unbanned_at: datetime.utcnow()
            }
        )
        session.commit()
        try:
            bot.send_message(
                user_id,
                "دسترسی شما به ربات دوباره فعال شد. اکنون می‌توانید از خدمات استفاده کنید."
            )
        except Exception as e:
            logger.error(f"Failed to notify user {user_id} about unban: {e}")
        bot.send_message(
            message.chat.id,
            f"کاربر با ID {user_id} با موفقیت آزاد شد!",
            reply_markup=get_user_management_menu()
        )
    except Exception as e:
        logger.error(f"Error unblocking user {user_id}: {e}")
        bot.send_message(
            message.chat.id,
            "خطا در آزاد کردن کاربر. لطفاً دوباره تلاش کنید.",
            reply_markup=get_user_management_menu()
        )
    user_states.pop(message.chat.id, None)

def handle_xui_server_management(bot, message):
    keyboard = [
        [InlineKeyboardButton("🖥 سرورهای موجود", callback_data="xui_servers_list")],
        [InlineKeyboardButton("➕ افزودن سرور", callback_data="xui_server_add")],
        [InlineKeyboardButton("✏️ ویرایش سرور", callback_data="xui_server_edit")],
        [InlineKeyboardButton("❌ حذف سرور", callback_data="xui_server_delete")],
        [InlineKeyboardButton("🔄 همگام‌سازی", callback_data="xui_server_sync")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_admin")]
    ]
    bot.send_message(
        message.chat.id,
        "🖥 مدیریت سرورهای X-UI\n"
        "لطفاً یک گزینه را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def start_add_xui_server(bot, message):
    user_states[message.chat.id] = 'WAITING_XUI_SERVER_NAME'
    bot.send_message(
        message.chat.id,
        "لطفاً نام سرور را وارد کنید (مثال: سرور ایران):",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 لغو", callback_data="cancel_xui_server")]])
    )

def handle_xui_server_name(bot, message):
    user_states[message.chat.id] = {'state': 'WAITING_XUI_SERVER_URL', 'name': message.text}
    bot.send_message(
        message.chat.id,
        "لطفاً آدرس پنل X-UI را وارد کنید (مثال: http://example.com:54321):",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 لغو", callback_data="cancel_xui_server")]])
    )

def handle_xui_server_url(bot, message):
    data = user_states[message.chat.id]
    data['state'] = 'WAITING_XUI_SERVER_CREDENTIALS'
    data['url'] = message.text
    bot.send_message(
        message.chat.id,
        "لطفاً نام کاربری و رمز عبور یا توکن امنیتی را در قالب زیر وارد کنید:\n"
        "username|password\n"
        "یا\n"
        "token",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 لغو", callback_data="cancel_xui_server")]])
    )

def handle_xui_server_credentials(bot, message):
    data = user_states[message.chat.id]
    credentials = message.text.strip()
    if "|" in credentials:
        username, password = credentials.split("|")
        data['username'] = username.strip()
        data['password'] = password.strip()
        data['token'] = None
    else:
        data['username'] = None
        data['password'] = None
        data['token'] = credentials.strip()

    client = XUIClient(
        url=data['url'],
        username=data.get('username'),
        password=data.get('password'),
        token=data.get('token')
    )
    if not client.check_connection():
        bot.send_message(
            message.chat.id,
            "❌ خطا در اتصال به سرور X-UI. لطفاً اطلاعات را بررسی کرده و دوباره تلاش کنید.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 تلاش مجدد", callback_data="xui_server_add")],
                [InlineKeyboardButton("🔙 لغو", callback_data="cancel_xui_server")]
            ])
        )
        user_states.pop(message.chat.id, None)
        return

    data['state'] = 'CONFIRM_XUI_SERVER'
    bot.send_message(
        message.chat.id,
        "📋 اطلاعات سرور X-UI:\n\n"
        f"نام: {data['name']}\n"
        f"آدرس: {data['url']}\n"
        f"احراز هویت: {'نام کاربری و رمز عبور' if data.get('username') else 'توکن'}\n\n"
        "آیا اطلاعات فوق را تأیید می‌کنید؟",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ تأیید", callback_data="confirm_xui_server"),
                InlineKeyboardButton("❌ لغو", callback_data="cancel_xui_server")
            ]
        ])
    )

def confirm_add_xui_server(bot, message):
    data = user_states.get(message.chat.id)
    if not data or data.get('state') != 'CONFIRM_XUI_SERVER':
        return

    try:
        server = XUIServer(
            name=data['name'],
            url=data['url'],
            username=data.get('username'),
            password=data.get('password'),
            token=data.get('token'),
            status=True
        )
        session.add(server)
        session.commit()
        bot.send_message(
            message.chat.id,
            "✅ سرور X-UI با موفقیت اضافه شد!",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_xui_management")]])
        )
    except Exception as e:
        logger.error(f"Error adding X-UI server: {e}")
        bot.send_message(
            message.chat.id,
            "❌ خطا در افزودن سرور X-UI. لطفاً دوباره تلاش کنید.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_xui_management")]])
        )
    user_states.pop(message.chat.id, None)
