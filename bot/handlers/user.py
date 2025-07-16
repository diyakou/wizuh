from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from database.models import User, Config, Plan, Transaction, UserRole
from database.db import session
from config.settings import ADMIN_IDS, CHANNEL_ID, CHANNEL_LOCK_ENABLED
import logging

logger = logging.getLogger(__name__)

def get_main_keyboard():
    """کیبورد منوی اصلی ربات"""
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(
        KeyboardButton("🛒 خرید اشتراک"),
        KeyboardButton("📱 کانفیگ های من")
    )
    markup.row(
        KeyboardButton("💰 کیف پول"),
        KeyboardButton("❓ راهنما")
    )
    markup.row(
        KeyboardButton("👤 پروفایل")
    )
    return markup


def get_wallet_keyboard():
    """کیبورد منوی کیف پول"""
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(
        KeyboardButton("💳 افزایش موجودی"),
        KeyboardButton("📊 تراکنش ها")
    )
    markup.row(
        KeyboardButton("🔙 بازگشت به منوی اصلی")
    )
    return markup


def get_profile_keyboard():
    """کیبورد منوی پروفایل"""
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(
        KeyboardButton("📝 ویرایش نام"),
        KeyboardButton("📞 ویرایش شماره")
    )
    markup.row(
        KeyboardButton("🔙 بازگشت به منوی اصلی")
    )
    return markup

def check_channel_membership(bot, user_id: int) -> bool:
    """Check if user is member of the required channel."""
    logger.info(f"Checking membership for user {user_id} in channel {CHANNEL_ID}, lock_enabled={CHANNEL_LOCK_ENABLED}")
    if not CHANNEL_LOCK_ENABLED:
        logger.info("Channel lock disabled, allowing access")
        return True
    
    try:
        member = bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        logger.info(f"Membership status: {member.status}")
        return member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        logger.error(f"Error checking channel membership: {e}", exc_info=True)
        return False

def start_handler(bot, message):
    """Handle /start command and main menu."""
    logger.info(f"Received /start command from user {message.from_user.id}")
    try:
        user = message.from_user
        logger.info(f"Processing user: {user.id}, username: {user.username}")

        # Check channel membership
        logger.info("Checking channel membership...")
        if not check_channel_membership(bot, user.id):
            logger.info("User not in channel, sending membership prompt")
            keyboard = [[InlineKeyboardButton("عضویت در کانال", url=f"https://t.me/{CHANNEL_ID[1:]}")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            bot.send_message(
                message.chat.id,
                "برای استفاده از ربات، لطفاً ابتدا در کانال ما عضو شوید:",
                reply_markup=reply_markup
            )
            return

        # Get or create user in database
        logger.info("Querying database for user...")
        db_user = session.query(User).filter_by(telegram_id=user.id).first()
        if not db_user:
            logger.info("Creating new user in database")
            db_user = User(
                telegram_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name
            )
            # ⬇️ اگر آیدی در لیست ادمین‌ها بود، نقش را admin قرار بده
            if user.id in ADMIN_IDS:
                db_user.role = UserRole.ADMIN

            session.add(db_user)
            session.commit()

        else:
            # ⬇️ اگر از قبل وجود داشت ولی هنوز admin نیست، بررسی کن
            if user.id in ADMIN_IDS and db_user.role != UserRole.ADMIN:
                db_user.role = UserRole.ADMIN
                session.commit()

        # Send welcome message with main menu keyboard
        logger.info("Sending welcome message...")
        bot.send_message(
            message.chat.id,
            f"سلام {user.first_name}!\n"
            "به ربات WizWiz خوش آمدید.\n"
            "لطفاً از منوی زیر گزینه مورد نظر خود را انتخاب کنید:",
            reply_markup=get_main_keyboard()
        )

    except Exception as e:
        logger.error(f"Error in start_handler: {e}", exc_info=True)
        bot.send_message(message.chat.id, "متأسفانه خطایی رخ داد. لطفاً دوباره تلاش کنید.")

def handle_main_menu(bot, message):
    """Handle main menu button clicks."""
    try:
        text = message.text
        
        if text == "🛒 خرید اشتراک":
            handle_buy_menu(bot, message)
        elif text == "📱 کانفیگ های من":
            handle_configs_menu(bot, message)
        elif text == "💰 کیف پول":
            handle_wallet_menu(bot, message)
        elif text == "❓ راهنما":
            handle_help_menu(bot, message)
        elif text == "👤 پروفایل":
            handle_profile_menu(bot, message)
            
    except Exception as e:
        logger.error(f"Error in main menu handler: {e}")
        bot.send_message(message.chat.id, "متأسفانه خطایی رخ داد. لطفاً دوباره تلاش کنید.")

def handle_buy_menu(bot, message):
    """Handle buy subscription menu."""
    try:
        # Get available plans
        plans = session.query(Plan).filter_by(is_active=True).all()
        if not plans:
            bot.send_message(
                message.chat.id,
                "در حال حاضر هیچ طرحی موجود نیست.",
                reply_markup=get_main_keyboard()
            )
            return
        
        # Create plan selection keyboard
        keyboard = []
        for plan in plans:
            button_text = f"{plan.name} - {plan.price:,} تومان"
            keyboard.append([InlineKeyboardButton(button_text, callback_data=f"plan_{plan.id}")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        bot.send_message(
            message.chat.id,
            "لطفاً طرح مورد نظر خود را انتخاب کنید:",
            reply_markup=reply_markup
        )
        
    except Exception as e:
        logger.error(f"Error in buy menu handler: {e}")
        bot.send_message(message.chat.id, "متأسفانه خطایی رخ داد. لطفاً دوباره تلاش کنید.")

def handle_configs_menu(bot, message):
    """Handle configs menu."""
    try:
        user = message.from_user
        db_user = session.query(User).filter_by(telegram_id=user.id).first()
        
        configs = session.query(Config).filter_by(user_id=db_user.id).all()
        if not configs:
            bot.send_message(
                message.chat.id,
                "شما هیچ پیکربندی فعالی ندارید.",
                reply_markup=get_main_keyboard()
            )
            return
        
        # Create config selection keyboard
        keyboard = []
        for config in configs:
            button_text = f"{config.name} ({config.protocol})"
            keyboard.append([InlineKeyboardButton(button_text, callback_data=f"config_{config.id}")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        bot.send_message(
            message.chat.id,
            "پیکربندی‌های شما:\n"
            "برای مشاهده جزئیات هر پیکربندی، روی آن کلیک کنید:",
            reply_markup=reply_markup
        )
        
    except Exception as e:
        logger.error(f"Error in configs menu handler: {e}")
        bot.send_message(message.chat.id, "متأسفانه خطایی رخ داد. لطفاً دوباره تلاش کنید.")

def handle_wallet_menu(bot, message):
    """Handle wallet menu."""
    try:
        user = message.from_user
        db_user = session.query(User).filter_by(telegram_id=user.id).first()
        
        bot.send_message(
            message.chat.id,
            f"💰 موجودی کیف پول شما: {db_user.balance:,} تومان\n\n"
            "لطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
            reply_markup=get_wallet_keyboard()
        )
        
    except Exception as e:
        logger.error(f"Error in wallet menu handler: {e}")
        bot.send_message(message.chat.id, "متأسفانه خطایی رخ داد. لطفاً دوباره تلاش کنید.")

def handle_help_menu(bot, message):
    """Handle help menu."""
    help_text = (
        "🤖 راهنمای استفاده از ربات:\n\n"
        "📌 بخش‌های اصلی:\n"
        "🛒 خرید اشتراک - خرید پلن‌های جدید\n"
        "📱 کانفیگ های من - مدیریت کانفیگ‌های فعال\n"
        "💰 کیف پول - شارژ حساب و مشاهده تراکنش‌ها\n"
        "👤 پروفایل - ویرایش اطلاعات کاربری\n\n"
        "📌 نکات مهم:\n"
        "• برای خرید اشتراک، ابتدا باید در کانال ما عضو شوید\n"
        "• موجودی کیف پول خود را می‌توانید از طریق درگاه‌های پرداخت افزایش دهید\n"
        "• پیکربندی‌های شما پس از اتمام حجم یا زمان، به‌طور خودکار غیرفعال می‌شوند\n"
        "• برای دریافت پشتیبانی، با @WizWizSupport در ارتباط باشید"
    )
    
    bot.send_message(
        message.chat.id,
        help_text,
        reply_markup=get_main_keyboard()
    )

def handle_profile_menu(bot, message):
    """Handle profile menu."""
    try:
        user = message.from_user
        db_user = session.query(User).filter_by(telegram_id=user.id).first()
        
        profile_text = (
            "👤 اطلاعات پروفایل شما:\n\n"
            f"نام: {db_user.first_name or '---'}\n"
            f"نام خانوادگی: {db_user.last_name or '---'}\n"
            f"شماره تماس: {db_user.phone or '---'}\n"
            f"نام کاربری: {db_user.username or '---'}"
        )
        
        bot.send_message(
            message.chat.id,
            profile_text,
            reply_markup=get_profile_keyboard()
        )
        
    except Exception as e:
        logger.error(f"Error in profile menu handler: {e}")
        bot.send_message(message.chat.id, "متأسفانه خطایی رخ داد. لطفاً دوباره تلاش کنید.")

def handle_back_to_main(bot, message):
    """Handle back to main menu button."""
    bot.send_message(
        message.chat.id,
        "به منوی اصلی بازگشتید.",
        reply_markup=get_main_keyboard()
    )
