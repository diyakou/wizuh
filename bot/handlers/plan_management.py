from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup
from database.models import ServerPlan, ServerCategory, Server
from bot.states import (
    PLAN_NAME, PLAN_VOLUME, PLAN_DURATION, PLAN_PRICE, PLAN_CATEGORY, PLAN_SERVERS, PLAN_CONFIRM
)
import logging
from database.db import session

logger = logging.getLogger(__name__)

user_states = {}

def start_add_plan(bot, message):
    """Start the plan addition process."""
    user_id = message.from_user.id
    user_states[user_id] = {'state': PLAN_NAME, 'data': {}}
    bot.send_message(
        message.chat.id,
        "لطفاً نام پلن جدید را وارد کنید (مثلاً: پلن ۱۰ گیگ ۳۰ روزه):"
    )

def handle_plan_management_message(bot, message):
    user_id = message.from_user.id
    if user_id not in user_states:
        return

    state = user_states[user_id]['state']

    if state == PLAN_NAME:
        handle_plan_name(bot, message)
    elif state == PLAN_VOLUME:
        handle_plan_volume(bot, message)
    elif state == PLAN_DURATION:
        handle_plan_duration(bot, message)
    elif state == PLAN_PRICE:
        handle_plan_price(bot, message)

def handle_plan_name(bot, message):
    """Handle the plan name input."""
    user_id = message.from_user.id
    name = message.text.strip()
    
    if len(name) < 3 or len(name) > 50:
        bot.send_message(
            message.chat.id,
            "❌ نام پلن باید بین 3 تا 50 کاراکتر باشد. لطفاً دوباره وارد کنید:"
        )
        return
    
    existing = session.query(ServerPlan).filter_by(title=name).first()
    if existing:
        bot.send_message(
            message.chat.id,
            "❌ پلن با این نام قبلاً ثبت شده است. لطفاً نام دیگری وارد کنید:"
        )
        return
    
    user_states[user_id]['data']['title'] = name
    user_states[user_id]['state'] = PLAN_VOLUME
    
    bot.send_message(
        message.chat.id,
        "لطفاً حجم پلن را به مگابایت وارد کنید (مثلاً 10000 برای 10 گیگ):"
    )

def handle_plan_volume(bot, message):
    """Handle the plan volume input."""
    user_id = message.from_user.id
    try:
        volume = int(message.text.strip())
        if volume <= 0:
            raise ValueError("Volume must be positive")
        
        user_states[user_id]['data']['volume'] = volume
        user_states[user_id]['state'] = PLAN_DURATION
        
        bot.send_message(
            message.chat.id,
            "لطفاً مدت زمان پلن را به روز وارد کنید (مثلاً 30 برای یک ماه):"
        )
        
    except ValueError:
        bot.send_message(
            message.chat.id,
            "❌ لطفاً یک عدد صحیح مثبت وارد کنید:"
        )

def handle_plan_duration(bot, message):
    """Handle the plan duration input."""
    user_id = message.from_user.id
    try:
        duration = int(message.text.strip())
        if duration <= 0:
            raise ValueError("Duration must be positive")
        
        user_states[user_id]['data']['duration'] = duration
        user_states[user_id]['state'] = PLAN_PRICE
        
        bot.send_message(
            message.chat.id,
            "لطفاً قیمت پلن را به تومان وارد کنید (مثلاً 50000):"
        )
        
    except ValueError:
        bot.send_message(
            message.chat.id,
            "❌ لطفاً یک عدد صحیح مثبت وارد کنید:"
        )

def handle_plan_price(bot, message):
    """Handle the plan price input."""
    user_id = message.from_user.id
    try:
        price = int(message.text.strip())
        if price <= 0:
            raise ValueError("Price must be positive")
        
        user_states[user_id]['data']['price'] = price
        
        categories = session.query(ServerCategory).filter_by(is_active=True).all()
        
        if categories:
            show_category_selection(bot, message)
        else:
            user_states[user_id]['data']['category_id'] = None
            show_server_selection(bot, message)
        
    except ValueError:
        bot.send_message(
            message.chat.id,
            "❌ لطفاً یک عدد صحیح مثبت وارد کنید:"
        )

def show_category_selection(bot, message):
    """Show category selection keyboard."""
    user_id = message.from_user.id
    categories = session.query(ServerCategory).filter_by(is_active=True).all()
    
    keyboard = []
    for category in categories:
        flag = category.flag if category.flag else ""
        keyboard.append([
            InlineKeyboardButton(
                f"{flag} {category.title}",
                callback_data=f"select_category_{category.id}"
            )
        ])
    
    keyboard.append([
        InlineKeyboardButton("بدون دسته‌بندی", callback_data="no_category")
    ])
    
    keyboard.append([
        InlineKeyboardButton("❌ لغو", callback_data="cancel_plan")
    ])
    
    bot.send_message(
        message.chat.id,
        "لطفاً دسته‌بندی پلن را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    user_states[user_id]['state'] = PLAN_CATEGORY

def handle_category_selection(bot, call):
    """Handle category selection callback."""
    user_id = call.from_user.id
    query = call
    
    if query.data == "cancel_plan":
        bot.edit_message_text("❌ عملیات لغو شد.", query.message.chat.id, query.message.message_id)
        user_states.pop(user_id, None)
        return
    
    if query.data == "no_category":
        user_states[user_id]['data']['category_id'] = None
    else:
        category_id = int(query.data.split('_')[-1])
        user_states[user_id]['data']['category_id'] = category_id
    
    show_server_selection(bot, query.message)

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
                f"{mark}{server.name}",
                callback_data=f"select_server_{server.id}"
            )
        ])
    
    if selected_servers:
        keyboard.append([
            InlineKeyboardButton("✅ تأیید و ادامه", callback_data="servers_done_plan")
        ])
    
    keyboard.append([
        InlineKeyboardButton("❌ لغو", callback_data="cancel_plan")
    ])
    
    bot.send_message(
        message.chat.id,
        "لطفاً سرورهای مرتبط با این پلن را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    user_states[user_id]['state'] = PLAN_SERVERS

def handle_server_selection(bot, call):
    """Handle server selection callbacks."""
    user_id = call.from_user.id
    query = call
    
    if query.data == "cancel_plan":
        bot.edit_message_text("❌ عملیات لغو شد.", query.message.chat.id, query.message.message_id)
        user_states.pop(user_id, None)
        return
    
    if query.data == "servers_done_plan":
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
    """Show confirmation message with plan details."""
    user_id = call.from_user.id
    query = call
    plan_data = user_states[user_id]['data']
    
    category_name = "بدون دسته‌بندی"
    if plan_data.get('category_id'):
        category = session.query(ServerCategory).get(plan_data['category_id'])
        if category:
            flag = category.flag if category.flag else ""
            category_name = f"{flag} {category.title}"
    
    servers = session.query(Server).filter(Server.id.in_(plan_data['server_ids'])).all()
    server_names = [server.name for server in servers]
    
    volume_text = f"{plan_data['volume']} مگابایت"
    if plan_data['volume'] >= 1024:
        volume_text = f"{plan_data['volume']/1024:.1f} گیگابایت"
    
    confirmation_text = (
        "📋 اطلاعات پلن:\n\n"
        f"نام: {plan_data['title']}\n"
        f"حجم: {volume_text}\n"
        f"مدت: {plan_data['duration']} روز\n"
        f"قیمت: {plan_data['price']:,} تومان\n"
        f"دسته‌بندی: {category_name}\n"
        f"سرورها: {', '.join(server_names)}\n\n"
        "آیا اطلاعات فوق را تأیید می‌کنید؟"
    )
    
    keyboard = [
        [
            InlineKeyboardButton("✅ تأیید", callback_data="confirm_plan"),
            InlineKeyboardButton("❌ لغو", callback_data="cancel_plan")
        ]
    ]
    
    bot.edit_message_text(
        confirmation_text,
        query.message.chat.id,
        query.message.message_id,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    user_states[user_id]['state'] = PLAN_CONFIRM

def handle_confirmation(bot, call):
    """Handle the final confirmation."""
    user_id = call.from_user.id
    query = call
    
    if query.data == "cancel_plan":
        bot.edit_message_text("❌ عملیات لغو شد.", query.message.chat.id, query.message.message_id)
        user_states.pop(user_id, None)
        return
    
    try:
        plan_data = user_states[user_id]['data']
        plan = ServerPlan(
            title=plan_data['title'],
            volume=plan_data['volume'],
            duration=plan_data['duration'],
            price=plan_data['price'],
            category_id=plan_data.get('category_id'),
            server_ids=plan_data['server_ids'],
            is_active=True
        )
        session.add(plan)
        session.commit()
        
        bot.edit_message_text("✅ پلن با موفقیت اضافه شد!", query.message.chat.id, query.message.message_id)
        
    except Exception as e:
        logger.error(f"Error creating plan: {e}")
        bot.edit_message_text(
            "❌ خطا در ثبت پلن. لطفاً دوباره تلاش کنید.",
            query.message.chat.id,
            query.message.message_id
        )
    
    user_states.pop(user_id, None)

def get_plan_management_handlers():
    return [
        (start_add_plan, {'commands': ['addplan']}),
        (handle_plan_management_message, {'func': lambda message: message.from_user.id in user_states}),
        (handle_category_selection, {'func': lambda call: call.data.startswith('select_category_') or call.data == 'no_category' or call.data == 'cancel_plan'}),
        (handle_server_selection, {'func': lambda call: call.data.startswith('select_server_') or call.data == 'servers_done_plan' or call.data == 'cancel_plan'}),
        (handle_confirmation, {'func': lambda call: call.data == 'confirm_plan' or call.data == 'cancel_plan'}),
    ]
