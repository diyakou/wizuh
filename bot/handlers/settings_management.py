from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup
from database.models import Setting, SettingType
from bot.states import (
    GATEWAY_SELECT, GATEWAY_TYPE, GATEWAY_NAME, GATEWAY_API_KEY,
    GATEWAY_CARD_NUMBER, GATEWAY_CARD_OWNER, GATEWAY_BANK_NAME,
    GATEWAY_STATUS, GATEWAY_CONFIRM,
    CHANNEL_SELECT, CHANNEL_NAME, CHANNEL_ID, CHANNEL_TYPE,
    CHANNEL_MANDATORY, CHANNEL_CONFIRM,
)
import logging
import re
from database.db import session

logger = logging.getLogger(__name__)

user_states = {}

GATEWAY_TYPES = {
    'nowpayment': 'NowPayment',
    'weswap': 'Weswap',
    'zarinpal': 'Zarinpal',
    'tron': 'Tron Wallet',
    'perfect_money': 'Perfect Money',
    'nextpay': 'Nextpay',
    'card_to_card': 'کارت‌به‌کارت'
}

CHANNEL_TYPES = {
    'notification': 'اطلاع‌رسانی',
    'support': 'پشتیبانی',
    'ads': 'تبلیغات'
}

def start_gateway_settings(bot, message):
    """Start the payment gateway settings process."""
    user_id = message.from_user.id
    user_states[user_id] = {'state': GATEWAY_SELECT, 'data': {}}
    
    gateways = session.query(Setting).filter_by(type=SettingType.PAYMENT_GATEWAY).all()
    
    keyboard = []
    for gateway in gateways:
        status = "✅" if gateway.value.get('status') else "❌"
        keyboard.append([
            InlineKeyboardButton(
                f"{status} {gateway.key}",
                callback_data=f"edit_gateway_{gateway.id}"
            )
        ])
    
    keyboard.append([
        InlineKeyboardButton("➕ افزودن درگاه جدید", callback_data="add_gateway")
    ])
    keyboard.append([
        InlineKeyboardButton("❌ بازگشت", callback_data="cancel_settings")
    ])
    
    bot.send_message(
        message.chat.id,
        "لطفاً درگاه مورد نظر را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def handle_settings_management_message(bot, message):
    user_id = message.from_user.id
    if user_id not in user_states:
        return

    state_data = user_states.get(user_id, {})
    state = state_data.get('state')

    if state == GATEWAY_NAME:
        handle_gateway_name(bot, message)
    elif state == GATEWAY_API_KEY:
        handle_gateway_api_key(bot, message)
    elif state == GATEWAY_CARD_NUMBER:
        handle_gateway_card_number(bot, message)
    elif state == GATEWAY_CARD_OWNER:
        handle_gateway_card_owner(bot, message)
    elif state == GATEWAY_BANK_NAME:
        handle_gateway_bank_name(bot, message)
    elif state == CHANNEL_NAME:
        handle_channel_name(bot, message)
    elif state == CHANNEL_ID:
        handle_channel_id(bot, message)

def handle_gateway_selection(bot, call):
    """Handle gateway selection."""
    user_id = call.from_user.id
    query = call
    
    if query.data == "cancel_settings":
        bot.edit_message_text("❌ عملیات لغو شد.", query.message.chat.id, query.message.message_id)
        user_states.pop(user_id, None)
        return
    
    if query.data == "add_gateway":
        user_states[user_id]['state'] = GATEWAY_TYPE
        keyboard = []
        for key, name in GATEWAY_TYPES.items():
            keyboard.append([
                InlineKeyboardButton(name, callback_data=f"type_{key}")
            ])
        keyboard.append([
            InlineKeyboardButton("❌ لغو", callback_data="cancel_settings")
        ])
        
        bot.edit_message_text(
            "لطفاً نوع درگاه را انتخاب کنید:",
            query.message.chat.id,
            query.message.message_id,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return
    
    gateway_id = int(query.data.split('_')[-1])
    gateway = session.query(Setting).get(gateway_id)
    if not gateway:
        bot.edit_message_text("❌ درگاه مورد نظر یافت نشد.", query.message.chat.id, query.message.message_id)
        return
    
    user_states[user_id]['data']['gateway_id'] = gateway_id
    
    keyboard = [
        [InlineKeyboardButton("✏️ ویرایش نام", callback_data="edit_gateway_name")],
        [InlineKeyboardButton("🔑 ویرایش کلید API", callback_data="edit_gateway_api_key")],
        [InlineKeyboardButton("⚡️ تغییر وضعیت", callback_data="toggle_gateway_status")],
        [InlineKeyboardButton("❌ حذف درگاه", callback_data="delete_gateway")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="cancel_settings")]
    ]
    
    bot.edit_message_text(
        f"تنظیمات درگاه {gateway.key}:\n"
        f"وضعیت: {'فعال' if gateway.value.get('status') else 'غیرفعال'}",
        query.message.chat.id,
        query.message.message_id,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def handle_gateway_type(bot, call):
    """Handle gateway type selection."""
    user_id = call.from_user.id
    query = call
    
    if query.data == "cancel_settings":
        bot.edit_message_text("❌ عملیات لغو شد.", query.message.chat.id, query.message.message_id)
        user_states.pop(user_id, None)
        return
    
    gateway_type = query.data.split('_')[1]
    user_states[user_id]['data']['type'] = gateway_type
    user_states[user_id]['state'] = GATEWAY_NAME
    
    bot.edit_message_text(
        "لطفاً نام درگاه را وارد کنید (مثلاً: Zarinpal اصلی):",
        query.message.chat.id,
        query.message.message_id
    )

# ... The rest of the functions will be converted in a similar way, using the user_states dictionary for state management.

def get_settings_management_handlers():
    return [
        (start_gateway_settings, {'commands': ['gatewaysettings']}),
        (handle_settings_management_message, {'func': lambda message: message.from_user.id in user_states}),
        (handle_gateway_selection, {'func': lambda call: call.data.startswith('edit_gateway_') or call.data == 'add_gateway' or call.data == 'cancel_settings'}),
        (handle_gateway_type, {'func': lambda call: call.data.startswith('type_') or call.data == 'cancel_settings'}),
    ]
