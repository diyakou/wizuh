from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup
from database.models import ServerCategory, Server
from bot.states import (
    CATEGORY_NAME, CATEGORY_REMARK, CATEGORY_FLAG, CATEGORY_SERVERS, CATEGORY_CONFIRM
)
import logging
import re
from database.db import session

logger = logging.getLogger(__name__)

user_states = {}

def start_add_category(bot, message):
    """Start the category addition process."""
    user_id = message.from_user.id
    user_states[user_id] = {'state': CATEGORY_NAME, 'data': {}}
    bot.send_message(
        message.chat.id,
        "لطفاً نام دسته‌بندی جدید را وارد کنید (مثلاً: سرورهای ایران، سرورهای اروپا):"
    )

def handle_category_management_message(bot, message):
    user_id = message.from_user.id
    if user_id not in user_states:
        return

    state = user_states[user_id]['state']

    if state == CATEGORY_NAME:
        handle_category_name(bot, message)
    elif state == CATEGORY_REMARK:
        handle_category_remark(bot, message)
    elif state == CATEGORY_FLAG:
        handle_category_flag(bot, message)

def handle_category_name(bot, message):
    """Handle the category name input."""
    user_id = message.from_user.id
    name = message.text.strip()
    
    if len(name) < 3 or len(name) > 50:
        bot.send_message(
            message.chat.id,
            "❌ نام دسته‌بندی باید بین 3 تا 50 کاراکتر باشد. لطفاً دوباره وارد کنید:"
        )
        return
    
    existing = session.query(ServerCategory).filter_by(title=name).first()
    if existing:
        bot.send_message(
            message.chat.id,
            "❌ دسته‌بندی با این نام قبلاً ثبت شده است. لطفاً نام دیگری وارد کنید:"
        )
        return
    
    user_states[user_id]['data']['title'] = name
    user_states[user_id]['state'] = CATEGORY_REMARK
    
    bot.send_message(
        message.chat.id,
        "لطفاً توضیحی کوتاه برای این دسته‌بندی وارد کنید (اختیاری، برای نمایش به کاربران):\n"
        "برای رد کردن این مرحله، /skip را بزنید."
    )

def skip_remark(bot, message):
    """Skip the remark step."""
    user_id = message.from_user.id
    user_states[user_id]['data']['remark'] = None
    user_states[user_id]['state'] = CATEGORY_FLAG
    
    bot.send_message(
        message.chat.id,
        "لطفاً یک ایموجی برای این دسته‌بندی انتخاب کنید (مثلاً 🇮🇷 برای ایران):\n"
        "برای رد کردن این مرحله، /skip را بزنید."
    )

def handle_category_remark(bot, message):
    """Handle the category description input."""
    user_id = message.from_user.id
    remark = message.text.strip()
    
    if len(remark) > 200:
        bot.send_message(
            message.chat.id,
            "❌ توضیحات نباید بیشتر از 200 کاراکتر باشد. لطفاً دوباره وارد کنید:"
        )
        return
    
    user_states[user_id]['data']['remark'] = remark
    user_states[user_id]['state'] = CATEGORY_FLAG
    
    bot.send_message(
        message.chat.id,
        "لطفاً یک ایموجی برای این دسته‌بندی انتخاب کنید (مثلاً 🇮🇷 برای ایران):\n"
        "برای رد کردن این مرحله، /skip را بزنید."
    )

def skip_flag(bot, message):
    """Skip the flag step."""
    user_id = message.from_user.id
    user_states[user_id]['data']['flag'] = None
    show_server_selection(bot, message)

def handle_category_flag(bot, message):
    """Handle the category emoji input."""
    user_id = message.from_user.id
    flag = message.text.strip()
    
    if len(flag) > 8:
        bot.send_message(
            message.chat.id,
            "❌ لطفاً فقط یک ایموجی وارد کنید."
        )
        return
    
    user_states[user_id]['data']['flag'] = flag
    show_server_selection(bot, message)

def show_server_selection(bot, message):
    """Show server selection keyboard."""
    user_id = message.from_user.id
    servers = session.query(Server).filter_by(is_active=True).all()
    
    if not servers:
        bot.send_message(
            message.chat.id,
            "❌ هیچ سروری برای انتخاب وجود ندارد. لطفاً ابتدا سرور اضافه کنید."
        )
        user_states.pop(user_id, None)
        return
    
    keyboard = []
    selected_servers = user_states[user_id]['data'].get('server_ids', [])
    
    for server in servers:
        mark = "✅ " if server.id in selected_servers else ""
        keyboard.append([
            InlineKeyboardButton(
                f"{mark}{server.name}", # Assuming server has a name attribute
                callback_data=f"select_server_{server.id}"
            )
        ])
    
    if selected_servers:
        keyboard.append([
            InlineKeyboardButton("✅ تأیید و ادامه", callback_data="servers_done")
        ])
    
    keyboard.append([
        InlineKeyboardButton("❌ لغو", callback_data="cancel_category")
    ])
    
    bot.send_message(
        message.chat.id,
        "لطفاً سرورهایی که می‌خواهید در این دسته‌بندی قرار بگیرند را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    user_states[user_id]['state'] = CATEGORY_SERVERS

def handle_server_selection(bot, call):
    """Handle server selection callbacks."""
    user_id = call.from_user.id
    query = call
    
    if query.data == "cancel_category":
        bot.edit_message_text("❌ عملیات لغو شد.", query.message.chat.id, query.message.message_id)
        user_states.pop(user_id, None)
        return
    
    if query.data == "servers_done":
        show_confirmation(bot, query)
        return
    
    server_id = int(query.data.split('_')[-1])
    
    if 'server_ids' not in user_states[user_id]['data']:
        user_states[user_id]['data']['server_ids'] = []
    
    if server_id in user_states[user_id]['data']['server_ids']:
        user_states[user_id]['data']['server_ids'].remove(server_id)
    else:
        user_states[user_id]['data']['server_ids'].append(server_id)
    
    show_server_selection(bot, query.message)

def show_confirmation(bot, call):
    """Show confirmation message with category details."""
    user_id = call.from_user.id
    query = call
    category_data = user_states[user_id]['data']
    
    servers = session.query(Server).filter(Server.id.in_(category_data['server_ids'])).all()
    server_names = [server.name for server in servers]
    
    confirmation_text = (
        "📋 اطلاعات دسته‌بندی:\n\n"
        f"نام: {category_data['title']}\n"
        f"توضیحات: {category_data.get('remark', '(ندارد)')}\n"
        f"ایموجی: {category_data.get('flag', '(ندارد)')}\n"
        f"سرورها: {', '.join(server_names)}\n\n"
        "آیا اطلاعات فوق را تأیید می‌کنید؟"
    )
    
    keyboard = [
        [
            InlineKeyboardButton("✅ تأیید", callback_data="confirm_category"),
            InlineKeyboardButton("❌ لغو", callback_data="cancel_category")
        ]
    ]
    
    bot.edit_message_text(
        confirmation_text,
        query.message.chat.id,
        query.message.message_id,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    user_states[user_id]['state'] = CATEGORY_CONFIRM

def handle_confirmation(bot, call):
    """Handle the final confirmation."""
    user_id = call.from_user.id
    query = call
    
    if query.data == "cancel_category":
        bot.edit_message_text("❌ عملیات لغو شد.", query.message.chat.id, query.message.message_id)
        user_states.pop(user_id, None)
        return
    
    try:
        category_data = user_states[user_id]['data']
        category = ServerCategory(
            title=category_data['title'],
            remark=category_data.get('remark'),
            flag=category_data.get('flag'),
            server_ids=category_data['server_ids'],
            is_active=True
        )
        session.add(category)
        session.commit()
        
        bot.edit_message_text("✅ دسته‌بندی با موفقیت اضافه شد!", query.message.chat.id, query.message.message_id)
        
    except Exception as e:
        logger.error(f"Error creating category: {e}")
        bot.edit_message_text(
            "❌ خطا در ثبت دسته‌بندی. لطفاً دوباره تلاش کنید.",
            query.message.chat.id,
            query.message.message_id
        )
    
    user_states.pop(user_id, None)

def get_category_management_handlers():
    return [
        (start_add_category, {'commands': ['addcategory']}),
        (handle_category_management_message, {'func': lambda message: message.from_user.id in user_states}),
        (skip_remark, {'commands': ['skip']}),
        (skip_flag, {'commands': ['skip']}),
        (handle_server_selection, {'func': lambda call: call.data.startswith('select_server_') or call.data == 'servers_done' or call.data == 'cancel_category'}),
        (handle_confirmation, {'func': lambda call: call.data == 'confirm_category' or call.data == 'cancel_category'}),
    ]
