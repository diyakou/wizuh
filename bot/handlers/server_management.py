from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup
from bot.states import ServerAddStates
from database.models import Server
from database.db import session
from config.settings import ADMIN_IDS
from api.xui_client import XUIClient
from datetime import datetime
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
        
        # Create new server with available fields from Server model
        server = Server(
            name=data.get("title"),
            ip=urlparse(panel_url).hostname,
            port=urlparse(panel_url).port or (443 if panel_url.startswith("https") else 80),
            username=username,
            password=password,
            type="xui",
            max_users=data.get("ucount"),
            is_active=True,
            current_users=0
        )
        try:
            session.add(server)
            session.commit()
            
            user_states.pop(user_id, None)
            
            bot.send_message(
                message.chat.id,
                "✅ سرور با موفقیت اضافه شد!"
            )
        except Exception as e:
            session.rollback()
            logger.error(f"Error saving server to database: {e}")
            bot.send_message(
                message.chat.id,
                "❌ خطا در ذخیره‌سازی سرور در پایگاه داده. لطفاً دوباره تلاش کنید."
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

def register_handlers(bot):
    """Register handlers for server management."""
    # Command handlers
    bot.message_handler(commands=['addserver'])(lambda message: start_server_add(bot, message))
    
    # Message handlers for server management process
    bot.message_handler(func=lambda message: message.from_user.id in user_states)(
        lambda message: handle_server_management_message(bot, message)
    )
    
    # Callback handlers for server management
    bot.callback_query_handler(func=lambda call: call.data in [
        'server_add', 'server_list', 'server_status', 'server_test', 'back_to_server_menu', 'cancel_server_add'
    ] or call.data.startswith(('edit_server_', 'delete_server_', 'confirm_delete_')))(
        lambda call: handle_server_callback(bot, call)
    )

def handle_server_callback(bot, call):
    """Handle server management callbacks."""
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    data = call.data

    if data == 'server_add':
        # Delete the menu message
        bot.delete_message(chat_id, message_id)
        # Start the server addition process
        start_server_add(bot, call.message)
    
    elif data == 'cancel_server_add':
        user_id = call.from_user.id
        if user_id in user_states:
            user_states.pop(user_id, None)
            bot.edit_message_text(
                "❌ فرآیند افزودن سرور لغو شد.",
                chat_id,
                message_id
            )
    
    elif data == 'server_list':
        show_server_list(bot, chat_id, message_id)
    
    elif data == 'server_status':
        check_servers_status(bot, chat_id, message_id)
    
    elif data == 'server_test':
        test_server_connections(bot, chat_id, message_id)
    
    elif data.startswith('edit_server_'):
        server_id = int(data.split('_')[2])
        start_edit_server(bot, chat_id, message_id, server_id)
    
    elif data.startswith('delete_server_'):
        server_id = int(data.split('_')[2])
        confirm_delete_server(bot, chat_id, message_id, server_id)
    
    elif data.startswith('confirm_delete_'):
        server_id = int(data.split('_')[2])
        delete_server(bot, chat_id, message_id, server_id)
    
    elif data == 'back_to_server_menu':
        show_server_menu(bot, chat_id, message_id)

def show_server_menu(bot, chat_id, message_id=None):
    """Show main server management menu."""
    keyboard = [
        [InlineKeyboardButton("🖥 لیست سرورها", callback_data="server_list")],
        [InlineKeyboardButton("➕ افزودن سرور", callback_data="server_add")],
        [InlineKeyboardButton("📊 وضعیت سرورها", callback_data="server_status")],
        [InlineKeyboardButton("🔄 تست اتصال", callback_data="server_test")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_admin")]
    ]
    
    text = "🖥 مدیریت سرورها\n" \
           "لطفاً یک گزینه را انتخاب کنید:"
    
    if message_id:
        bot.edit_message_text(text, chat_id, message_id, reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        bot.send_message(chat_id, text, reply_markup=InlineKeyboardMarkup(keyboard))

def show_server_list(bot, chat_id, message_id=None):
    """Show list of all servers."""
    servers = session.query(Server).all()
    
    if not servers:
        text = "❌ هیچ سروری یافت نشد!"
        keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_server_menu")]]
    else:
        text = "📋 لیست سرورها:\n\n"
        keyboard = []
        
        for server in servers:
            text += f"🖥 نام: {server.name}\n"
            text += f"🔗 آدرس: {server.ip}:{server.port}\n"
            text += f"👥 کاربران: {server.current_users}/{server.max_users}\n"
            text += f"📊 وضعیت: {'✅ فعال' if server.is_active else '❌ غیرفعال'}\n\n"
            
            keyboard.append([
                InlineKeyboardButton(f"✏️ {server.name}", callback_data=f"edit_server_{server.id}"),
                InlineKeyboardButton("❌", callback_data=f"delete_server_{server.id}")
            ])
    
    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_server_menu")])
    
    if message_id:
        bot.edit_message_text(text, chat_id, message_id, reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        bot.send_message(chat_id, text, reply_markup=InlineKeyboardMarkup(keyboard))

def check_servers_status(bot, chat_id, message_id):
    """Check status of all servers."""
    servers = session.query(Server).all()
    if not servers:
        text = "❌ هیچ سروری یافت نشد!"
    else:
        text = "📊 وضعیت سرورها:\n\n"
        for server in servers:
            # Get total users and traffic from XUI API
            try:
                client = XUIClient(f"http://{server.ip}:{server.port}", server.username, server.password)
                stats = client.get_server_stats()
                status = "✅ آنلاین"
                text += f"🖥 {server.name}:\n"
                text += f"📊 وضعیت: {status}\n"
                text += f"👥 کاربران فعال: {stats.get('active_users', 0)}\n"
                text += f"📈 ترافیک امروز: {stats.get('today_traffic', 0)} GB\n"
                text += f"📉 ترافیک کل: {stats.get('total_traffic', 0)} GB\n\n"
            except Exception as e:
                logger.error(f"Error checking server {server.name}: {e}")
                text += f"🖥 {server.name}:\n"
                text += f"📊 وضعیت: ❌ آفلاین\n\n"
    
    keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_server_menu")]]
    bot.edit_message_text(text, chat_id, message_id, reply_markup=InlineKeyboardMarkup(keyboard))

def test_server_connections(bot, chat_id, message_id):
    """Test connection to all servers."""
    servers = session.query(Server).all()
    if not servers:
        text = "❌ هیچ سروری یافت نشد!"
    else:
        text = "🔄 نتایج تست اتصال:\n\n"
        for server in servers:
            try:
                client = XUIClient(f"http://{server.ip}:{server.port}", server.username, server.password)
                if client.test_connection():
                    text += f"✅ {server.name}: اتصال موفق\n"
                    # Update last_check time
                    server.last_check = datetime.utcnow()
                else:
                    text += f"❌ {server.name}: خطا در اتصال\n"
            except Exception as e:
                logger.error(f"Error testing server {server.name}: {e}")
                text += f"❌ {server.name}: خطا در اتصال - {str(e)}\n"
        
        session.commit()
    
    keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_server_menu")]]
    bot.edit_message_text(text, chat_id, message_id, reply_markup=InlineKeyboardMarkup(keyboard))

def start_edit_server(bot, chat_id, message_id, server_id):
    """Start server editing process."""
    server = session.query(Server).get(server_id)
    if not server:
        text = "❌ سرور مورد نظر یافت نشد!"
        keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_server_menu")]]
    else:
        text = f"✏️ ویرایش سرور {server.name}\n\n"
        text += f"🔗 آدرس فعلی: {server.ip}:{server.port}\n"
        text += f"👥 ظرفیت: {server.max_users}\n"
        text += f"📊 وضعیت: {'✅ فعال' if server.is_active else '❌ غیرفعال'}\n"
        
        keyboard = [
            [InlineKeyboardButton("✏️ تغییر نام", callback_data=f"edit_server_name_{server_id}")],
            [InlineKeyboardButton("✏️ تغییر آدرس", callback_data=f"edit_server_address_{server_id}")],
            [InlineKeyboardButton("✏️ تغییر ظرفیت", callback_data=f"edit_server_capacity_{server_id}")],
            [InlineKeyboardButton("✏️ تغییر وضعیت", callback_data=f"toggle_server_status_{server_id}")],
            [InlineKeyboardButton("🔙 بازگشت", callback_data="server_list")]
        ]
    
    bot.edit_message_text(text, chat_id, message_id, reply_markup=InlineKeyboardMarkup(keyboard))

def confirm_delete_server(bot, chat_id, message_id, server_id):
    """Ask for confirmation before deleting server."""
    server = session.query(Server).get(server_id)
    if not server:
        text = "❌ سرور مورد نظر یافت نشد!"
        keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_server_menu")]]
    else:
        text = f"⚠️ آیا از حذف سرور {server.name} اطمینان دارید؟"
        keyboard = [
            [
                InlineKeyboardButton("✅ بله", callback_data=f"confirm_delete_{server_id}"),
                InlineKeyboardButton("❌ خیر", callback_data="server_list")
            ]
        ]
    
    bot.edit_message_text(text, chat_id, message_id, reply_markup=InlineKeyboardMarkup(keyboard))

def delete_server(bot, chat_id, message_id, server_id):
    """Delete server from database."""
    server = session.query(Server).get(server_id)
    if not server:
        text = "❌ سرور مورد نظر یافت نشد!"
    else:
        try:
            session.delete(server)
            session.commit()
            text = f"✅ سرور {server.name} با موفقیت حذف شد."
        except Exception as e:
            logger.error(f"Error deleting server: {e}")
            text = "❌ خطا در حذف سرور!"
            session.rollback()
    
    keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data="server_list")]]
    bot.edit_message_text(text, chat_id, message_id, reply_markup=InlineKeyboardMarkup(keyboard))
