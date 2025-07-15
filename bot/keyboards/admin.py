from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def get_admin_main_menu() -> InlineKeyboardMarkup:
    """Get main admin menu keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("مدیریت سرورها", callback_data="admin_servers"),
            InlineKeyboardButton("مدیریت کاربران", callback_data="admin_users")
        ],
        [
            InlineKeyboardButton("مدیریت پلن‌ها", callback_data="admin_plans"),
            InlineKeyboardButton("گزارش‌ها", callback_data="admin_reports")
        ],
        [
            InlineKeyboardButton("تنظیمات ربات", callback_data="admin_settings"),
            InlineKeyboardButton("پشتیبان‌گیری", callback_data="admin_backup")
        ],
        [InlineKeyboardButton("بازگشت به منوی اصلی", callback_data="start")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_server_management_menu() -> InlineKeyboardMarkup:
    """Get server management menu keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("افزودن سرور", callback_data="add_server"),
            InlineKeyboardButton("لیست سرورها", callback_data="list_servers")
        ],
        [
            InlineKeyboardButton("وضعیت سرورها", callback_data="server_status"),
            InlineKeyboardButton("حذف سرور", callback_data="delete_server")
        ],
        [InlineKeyboardButton("بازگشت", callback_data="admin_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_user_management_menu() -> InlineKeyboardMarkup:
    """Get user management menu keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("لیست کاربران", callback_data="list_users"),
            InlineKeyboardButton("جستجوی کاربر", callback_data="search_user")
        ],
        [
            InlineKeyboardButton("کاربران مسدود", callback_data="banned_users"),
            InlineKeyboardButton("کاربران فعال", callback_data="active_users")
        ],
        [InlineKeyboardButton("بازگشت", callback_data="admin_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_plan_management_menu() -> InlineKeyboardMarkup:
    """Get plan management menu keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("افزودن پلن", callback_data="add_plan"),
            InlineKeyboardButton("لیست پلن‌ها", callback_data="list_plans")
        ],
        [
            InlineKeyboardButton("ویرایش پلن", callback_data="edit_plan"),
            InlineKeyboardButton("حذف پلن", callback_data="delete_plan")
        ],
        [InlineKeyboardButton("بازگشت", callback_data="admin_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_settings_menu() -> InlineKeyboardMarkup:
    """Get bot settings menu keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("متن‌های ربات", callback_data="bot_texts"),
            InlineKeyboardButton("درگاه‌های پرداخت", callback_data="payment_gateways")
        ],
        [
            InlineKeyboardButton("تنظیمات اعلان", callback_data="notification_settings"),
            InlineKeyboardButton("تنظیمات پشتیبان", callback_data="backup_settings")
        ],
        [InlineKeyboardButton("بازگشت", callback_data="admin_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_reports_menu() -> InlineKeyboardMarkup:
    """Get reports menu keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("گزارش روزانه", callback_data="daily_report"),
            InlineKeyboardButton("گزارش هفتگی", callback_data="weekly_report")
        ],
        [
            InlineKeyboardButton("گزارش تراکنش‌ها", callback_data="transaction_report"),
            InlineKeyboardButton("گزارش سرورها", callback_data="server_report")
        ],
        [InlineKeyboardButton("بازگشت", callback_data="admin_menu")]
    ]
    return InlineKeyboardMarkup(keyboard) 