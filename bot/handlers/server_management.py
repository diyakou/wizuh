from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup
from bot.states import ServerAddStates
from database.models import Server
from config.settings import ADMIN_IDS
import re
import requests
import logging
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

user_states = {}

def create_cancel_keyboard():
    """Create a keyboard with cancel button."""
    return InlineKeyboardMarkup([[InlineKeyboardButton("لغو", callback_data="cancel_server_add")]])

def start_server_add(bot, message):
    """Start the server addition process."""
    user_id = message.from_user.id
    
    if user_id not in ADMIN_IDS:
        bot.send_message(message.chat.id, "شما دسترسی به این بخش را ندارید.")
        return
    
    user_states[user_id] = {'state': ServerAddStates.TITLE, 'data': {}}
    
    bot.send_message(
        message.chat.id,
        "مرحله اول:\n"
        "لطفاً عنوان سرور را وارد کنید:",
        reply_markup=create_cancel_keyboard()
    )

def handle_server_management_message(bot, message):
    user_id = message.from_user.id
    if user_id not in user_states:
        return

    state = user_states[user_id]['state']

    if state == ServerAddStates.TITLE:
        handle_title(bot, message)
    elif state == ServerAddStates.UCOUNT:
        handle_ucount(bot, message)
    elif state == ServerAddStates.REMARK:
        handle_remark(bot, message)
    elif state == ServerAddStates.FLAG:
        handle_flag(bot, message)
    elif state == ServerAddStates.PANEL_URL:
        handle_panel_url(bot, message)
    elif state == ServerAddStates.PANEL_USERNAME:
        handle_panel_username(bot, message)
    elif state == ServerAddStates.PANEL_PASSWORD:
        handle_panel_password(bot, message)

def handle_title(bot, message):
    """Handle server title input."""
    user_id = message.from_user.id
    title = message.text.strip()
    
    if len(title) < 3 or len(title) > 50:
        bot.send_message(
            message.chat.id,
            "عنوان باید بین ۳ تا ۵۰ کاراکتر باشد. لطفاً مجدداً وارد کنید:",
            reply_markup=create_cancel_keyboard()
        )
        return
    
    user_states[user_id]['data']['title'] = title
    user_states[user_id]['state'] = ServerAddStates.UCOUNT
    
    bot.send_message(
        message.chat.id,
        "مرحله دوم:\n"
        "لطفاً تعداد کاربرانی که این سرور می‌تواند پشتیبانی کند را وارد کنید:",
        reply_markup=create_cancel_keyboard()
    )

def handle_ucount(bot, message):
    """Handle user count input."""
    user_id = message.from_user.id
    text = message.text.strip()
    
    try:
        ucount = int(text)
        if ucount <= 0 or ucount > 10000:
            raise ValueError("Invalid range")
    except ValueError:
        bot.send_message(
            message.chat.id,
            "لطفاً یک عدد معتبر بین ۱ تا ۱۰۰۰۰ وارد کنید:",
            reply_markup=create_cancel_keyboard()
        )
        return
    
    user_states[user_id]['data']['ucount'] = ucount
    user_states[user_id]['state'] = ServerAddStates.REMARK
    
    bot.send_message(
        message.chat.id,
        "مرحله سوم:\n"
        "لطفاً یک توضیح کوتاه برای سرور وارد کنید (به‌صورت انگلیسی و بدون فاصله):",
        reply_markup=create_cancel_keyboard()
    )

def handle_remark(bot, message):
    """Handle server remark input."""
    user_id = message.from_user.id
    remark = message.text.strip()
    
    if not re.match(r'^[a-zA-Z0-9_-]+$', remark):
        bot.send_message(
            message.chat.id,
            "توضیح باید فقط شامل حروف انگلیسی، اعداد و علامت‌های - و _ باشد. لطفاً مجدداً وارد کنید:",
            reply_markup=create_cancel_keyboard()
        )
        return
    
    user_states[user_id]['data']['remark'] = remark
    user_states[user_id]['state'] = ServerAddStates.FLAG
    
    bot.send_message(
        message.chat.id,
        "مرحله چهارم:\n"
        "لطفاً یک ایموجی پرچم برای سرور انتخاب کنید:",
        reply_markup=create_cancel_keyboard()
    )

def handle_flag(bot, message):
    """Handle server flag emoji input."""
    user_id = message.from_user.id
    flag = message.text.strip()
    
    if not re.match(r'^[\U0001F1E6-\U0001F1FF]{2}$', flag):
        bot.send_message(
            message.chat.id,
            "لطفاً یک ایموجی پرچم معتبر وارد کنید (مثل 🇮🇷):",
            reply_markup=create_cancel_keyboard()
        )
        return
    
    user_states[user_id]['data']['flag'] = flag
    user_states[user_id]['state'] = ServerAddStates.PANEL_URL
    
    bot.send_message(
        message.chat.id,
        "مرحله پنجم:\n"
        "لطفاً آدرس پنل x-ui را به‌صورت زیر وارد کنید:\n"
        "❕ https://yourdomain.com:54321\n"
        "❕ https://yourdomain.com:54321/path\n"
        "❗️ http://125.12.12.36:54321\n"
        "❗️ http://125.12.12.36:54321/path",
        reply_markup=create_cancel_keyboard()
    )

def handle_panel_url(bot, message):
    """Handle panel URL input."""
    user_id = message.from_user.id
    url = message.text.strip()
    
    try:
        parsed = urlparse(url)
        if not all([parsed.scheme in ['http', 'https'], parsed.netloc]):
            raise ValueError("Invalid URL")
    except:
        bot.send_message(
            message.chat.id,
            "لطفاً یک آدرس URL معتبر وارد کنید:",
            reply_markup=create_cancel_keyboard()
        )
        return
    
    user_states[user_id]['data']['panel_url'] = url
    user_states[user_id]['state'] = ServerAddStates.PANEL_USERNAME
    
    bot.send_message(
        message.chat.id,
        "مرحله ششم:\n"
        "لطفاً نام کاربری پنل را وارد کنید:",
        reply_markup=create_cancel_keyboard()
    )

def handle_panel_username(bot, message):
    """Handle panel username input."""
    user_id = message.from_user.id
    username = message.text.strip()
    
    if not username:
        bot.send_message(
            message.chat.id,
            "نام کاربری نمی‌تواند خالی باشد. لطفاً مجدداً وارد کنید:",
            reply_markup=create_cancel_keyboard()
        )
        return
    
    user_states[user_id]['data']['panel_username'] = username
    user_states[user_id]['state'] = ServerAddStates.PANEL_PASSWORD
    
    bot.send_message(
        message.chat.id,
        "مرحله هفتم:\n"
        "لطفاً رمز عبور پنل را وارد کنید:",
        reply_markup=create_cancel_keyboard()
    )

def handle_panel_password(bot, message):
    """Handle panel password input and validate credentials."""
    user_id = message.from_user.id
    password = message.text.strip()
    
    if not password:
        bot.send_message(
            message.chat.id,
            "رمز عبور نمی‌تواند خالی باشد. لطفاً مجدداً وارد کنید:",
            reply_markup=create_cancel_keyboard()
        )
        return
    
    data = user_states[user_id]['data']
    panel_url = data.get("panel_url")
    username = data.get("panel_username")
    
    try:
        login_url = f"{panel_url}/login"
        response = requests.post(
            login_url,
            json={"username": username, "password": password},
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=15,
            verify=False
        )
        
        if not response.ok or not response.json().get("success"):
            bot.send_message(
                message.chat.id,
                "نام کاربری یا رمز عبور اشتباه است. برای راهنمایی به @wizwizch مراجعه کنید.\n"
                "لطفاً مجدداً نام کاربری را وارد کنید:",
                reply_markup=create_cancel_keyboard()
            )
            user_states[user_id]['state'] = ServerAddStates.PANEL_USERNAME
            return
        
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
        
        user_states.pop(user_id, None)
        
        bot.send_message(
            message.chat.id,
            "✅ سرور با موفقیت اضافه شد!"
        )
        
    except Exception as e:
        logger.error(f"Error validating panel credentials: {e}")
        bot.send_message(
            message.chat.id,
            "خطا در اتصال به پنل. لطفاً آدرس پنل را مجدداً وارد کنید:",
            reply_markup=create_cancel_keyboard()
        )
        user_states[user_id]['state'] = ServerAddStates.PANEL_URL

def cancel_server_add(bot, call):
    """Cancel the server addition process."""
    user_id = call.from_user.id
    user_states.pop(user_id, None)
    
    bot.edit_message_text("❌ فرآیند افزودن سرور لغو شد.", call.message.chat.id, call.message.message_id)

def get_server_management_handlers():
    return [
        (start_server_add, {'commands': ['addserver']}),
        (handle_server_management_message, {'func': lambda message: message.from_user.id in user_states}),
        (cancel_server_add, {'func': lambda call: call.data == 'cancel_server_add'}),
    ]
