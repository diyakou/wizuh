from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, filters
from bot.states import ServerAddStates, ConversationState
from database.models import Server
from config.settings import ADMIN_IDS
import re
import requests
import logging
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# Initialize conversation state manager
state_manager = ConversationState()

def create_cancel_keyboard():
    """Create a keyboard with cancel button."""
    return InlineKeyboardMarkup([[InlineKeyboardButton("لغو", callback_data="cancel_server_add")]])

async def start_server_add(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the server addition process."""
    user_id = update.effective_user.id
    
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("شما دسترسی به این بخش را ندارید.")
        return ConversationHandler.END
    
    # Clear any existing state and data
    state_manager.clear_all(user_id)
    
    # Set initial state
    state_manager.set_state(user_id, ServerAddStates.TITLE)
    
    await update.message.reply_text(
        "مرحله اول:\n"
        "لطفاً عنوان سرور را وارد کنید:",
        reply_markup=create_cancel_keyboard()
    )
    return ServerAddStates.TITLE

async def handle_title(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle server title input."""
    user_id = update.effective_user.id
    title = update.message.text.strip()
    
    if len(title) < 3 or len(title) > 50:
        await update.message.reply_text(
            "عنوان باید بین ۳ تا ۵۰ کاراکتر باشد. لطفاً مجدداً وارد کنید:",
            reply_markup=create_cancel_keyboard()
        )
        return ServerAddStates.TITLE
    
    # Save title
    state_manager.set_data(user_id, "title", title)
    
    await update.message.reply_text(
        "مرحله دوم:\n"
        "لطفاً تعداد کاربرانی که این سرور می‌تواند پشتیبانی کند را وارد کنید:",
        reply_markup=create_cancel_keyboard()
    )
    return ServerAddStates.UCOUNT

async def handle_ucount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle user count input."""
    user_id = update.effective_user.id
    text = update.message.text.strip()
    
    try:
        ucount = int(text)
        if ucount <= 0 or ucount > 10000:
            raise ValueError("Invalid range")
    except ValueError:
        await update.message.reply_text(
            "لطفاً یک عدد معتبر بین ۱ تا ۱۰۰۰۰ وارد کنید:",
            reply_markup=create_cancel_keyboard()
        )
        return ServerAddStates.UCOUNT
    
    # Save user count
    state_manager.set_data(user_id, "ucount", ucount)
    
    await update.message.reply_text(
        "مرحله سوم:\n"
        "لطفاً یک توضیح کوتاه برای سرور وارد کنید (به‌صورت انگلیسی و بدون فاصله):",
        reply_markup=create_cancel_keyboard()
    )
    return ServerAddStates.REMARK

async def handle_remark(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle server remark input."""
    user_id = update.effective_user.id
    remark = update.message.text.strip()
    
    if not re.match(r'^[a-zA-Z0-9_-]+$', remark):
        await update.message.reply_text(
            "توضیح باید فقط شامل حروف انگلیسی، اعداد و علامت‌های - و _ باشد. لطفاً مجدداً وارد کنید:",
            reply_markup=create_cancel_keyboard()
        )
        return ServerAddStates.REMARK
    
    # Save remark
    state_manager.set_data(user_id, "remark", remark)
    
    await update.message.reply_text(
        "مرحله چهارم:\n"
        "لطفاً یک ایموجی پرچم برای سرور انتخاب کنید:",
        reply_markup=create_cancel_keyboard()
    )
    return ServerAddStates.FLAG

async def handle_flag(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle server flag emoji input."""
    user_id = update.effective_user.id
    flag = update.message.text.strip()
    
    if not re.match(r'^[\U0001F1E6-\U0001F1FF]{2}$', flag):
        await update.message.reply_text(
            "لطفاً یک ایموجی پرچم معتبر وارد کنید (مثل 🇮🇷):",
            reply_markup=create_cancel_keyboard()
        )
        return ServerAddStates.FLAG
    
    # Save flag
    state_manager.set_data(user_id, "flag", flag)
    
    await update.message.reply_text(
        "مرحله پنجم:\n"
        "لطفاً آدرس پنل x-ui را به‌صورت زیر وارد کنید:\n"
        "❕ https://yourdomain.com:54321\n"
        "❕ https://yourdomain.com:54321/path\n"
        "❗️ http://125.12.12.36:54321\n"
        "❗️ http://125.12.12.36:54321/path",
        reply_markup=create_cancel_keyboard()
    )
    return ServerAddStates.PANEL_URL

async def handle_panel_url(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle panel URL input."""
    user_id = update.effective_user.id
    url = update.message.text.strip()
    
    try:
        parsed = urlparse(url)
        if not all([parsed.scheme in ['http', 'https'], parsed.netloc]):
            raise ValueError("Invalid URL")
    except:
        await update.message.reply_text(
            "لطفاً یک آدرس URL معتبر وارد کنید:",
            reply_markup=create_cancel_keyboard()
        )
        return ServerAddStates.PANEL_URL
    
    # Save panel URL
    state_manager.set_data(user_id, "panel_url", url)
    
    await update.message.reply_text(
        "مرحله ششم:\n"
        "لطفاً نام کاربری پنل را وارد کنید:",
        reply_markup=create_cancel_keyboard()
    )
    return ServerAddStates.PANEL_USERNAME

async def handle_panel_username(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle panel username input."""
    user_id = update.effective_user.id
    username = update.message.text.strip()
    
    if not username:
        await update.message.reply_text(
            "نام کاربری نمی‌تواند خالی باشد. لطفاً مجدداً وارد کنید:",
            reply_markup=create_cancel_keyboard()
        )
        return ServerAddStates.PANEL_USERNAME
    
    # Save panel username
    state_manager.set_data(user_id, "panel_username", username)
    
    await update.message.reply_text(
        "مرحله هفتم:\n"
        "لطفاً رمز عبور پنل را وارد کنید:",
        reply_markup=create_cancel_keyboard()
    )
    return ServerAddStates.PANEL_PASSWORD

async def handle_panel_password(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle panel password input and validate credentials."""
    user_id = update.effective_user.id
    password = update.message.text.strip()
    
    if not password:
        await update.message.reply_text(
            "رمز عبور نمی‌تواند خالی باشد. لطفاً مجدداً وارد کنید:",
            reply_markup=create_cancel_keyboard()
        )
        return ServerAddStates.PANEL_PASSWORD
    
    # Get saved data
    data = state_manager.get_all_data(user_id)
    panel_url = data.get("panel_url")
    username = data.get("panel_username")
    
    # Validate panel credentials
    try:
        login_url = f"{panel_url}/login"
        response = requests.post(
            login_url,
            json={"username": username, "password": password},
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=15,
            verify=False  # For self-signed certificates
        )
        
        if not response.ok or not response.json().get("success"):
            await update.message.reply_text(
                "نام کاربری یا رمز عبور اشتباه است. برای راهنمایی به @wizwizch مراجعه کنید.\n"
                "لطفاً مجدداً نام کاربری را وارد کنید:",
                reply_markup=create_cancel_keyboard()
            )
            return ServerAddStates.PANEL_USERNAME
        
        # Save panel password
        state_manager.set_data(user_id, "panel_password", password)
        
        # Save server to database
        server = Server(
            name=data.get("title"),
            ip=urlparse(panel_url).hostname,
            port=urlparse(panel_url).port or (443 if panel_url.startswith("https") else 80),
            username=username,
            password=password,
            type="xui",
            max_users=data.get("ucount"),
            is_active=True
        )
        server.save()
        
        # Clear conversation state
        state_manager.clear_all(user_id)
        
        await update.message.reply_text(
            "✅ سرور با موفقیت اضافه شد!"
        )
        return ConversationHandler.END
        
    except Exception as e:
        logger.error(f"Error validating panel credentials: {e}")
        await update.message.reply_text(
            "خطا در اتصال به پنل. لطفاً آدرس پنل را مجدداً وارد کنید:",
            reply_markup=create_cancel_keyboard()
        )
        return ServerAddStates.PANEL_URL

async def cancel_server_add(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the server addition process."""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    state_manager.clear_all(user_id)
    
    await query.edit_message_text("❌ فرآیند افزودن سرور لغو شد.")
    return ConversationHandler.END

# Create conversation handler
server_add_handler = ConversationHandler(
    entry_points=[CommandHandler("addserver", start_server_add)],
    states={
        ServerAddStates.TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_title)],
        ServerAddStates.UCOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_ucount)],
        ServerAddStates.REMARK: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_remark)],
        ServerAddStates.FLAG: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_flag)],
        ServerAddStates.PANEL_URL: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_panel_url)],
        ServerAddStates.PANEL_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_panel_username)],
        ServerAddStates.PANEL_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_panel_password)],
    },
    fallbacks=[
        CommandHandler("cancel", cancel_server_add),
        MessageHandler(filters.Regex(r"^لغو$"), cancel_server_add),
    ],
    name="server_add",
    persistent=True,
) 