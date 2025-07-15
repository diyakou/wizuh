from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CallbackQueryHandler, MessageHandler, filters
from database.models import Setting, SettingType
from bot.states import (
    GATEWAY_SELECT, GATEWAY_TYPE, GATEWAY_NAME, GATEWAY_API_KEY,
    GATEWAY_CARD_NUMBER, GATEWAY_CARD_OWNER, GATEWAY_BANK_NAME,
    GATEWAY_STATUS, GATEWAY_CONFIRM,
    CHANNEL_SELECT, CHANNEL_NAME, CHANNEL_ID, CHANNEL_TYPE,
    CHANNEL_MANDATORY, CHANNEL_CONFIRM,
    get_gateway_data, clear_gateway_data,
    get_channel_data, clear_channel_data
)
import logging
import re
import json

logger = logging.getLogger(__name__)

# Payment Gateway Types
GATEWAY_TYPES = {
    'nowpayment': 'NowPayment',
    'weswap': 'Weswap',
    'zarinpal': 'Zarinpal',
    'tron': 'Tron Wallet',
    'perfect_money': 'Perfect Money',
    'nextpay': 'Nextpay',
    'card_to_card': 'کارت‌به‌کارت'
}

# Channel Types
CHANNEL_TYPES = {
    'notification': 'اطلاع‌رسانی',
    'support': 'پشتیبانی',
    'ads': 'تبلیغات'
}

# Payment gateway states
(
    WAITING_GATEWAY_TYPE,
    WAITING_GATEWAY_API_KEY,
    WAITING_GATEWAY_SECRET,
    WAITING_GATEWAY_MERCHANT_ID,
    WAITING_GATEWAY_CALLBACK_URL,
    WAITING_GATEWAY_CARD_NUMBER,
    WAITING_GATEWAY_CARD_HOLDER,
    WAITING_GATEWAY_DESCRIPTION
) = range(8)

# Payment Gateway Management
async def start_gateway_settings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Start the payment gateway settings process."""
    clear_gateway_data(context)
    
    # Get existing gateways
    gateways = Setting.get_payment_gateways()
    
    keyboard = []
    for gateway in gateways:
        status = "✅" if gateway.status else "❌"
        keyboard.append([
            InlineKeyboardButton(
                f"{status} {gateway.extra.get('display_name', gateway.key)}",
                callback_data=f"edit_gateway_{gateway.id}"
            )
        ])
    
    keyboard.append([
        InlineKeyboardButton("➕ افزودن درگاه جدید", callback_data="add_gateway")
    ])
    keyboard.append([
        InlineKeyboardButton("❌ بازگشت", callback_data="cancel")
    ])
    
    await update.message.reply_text(
        "لطفاً درگاه مورد نظر را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return GATEWAY_SELECT

async def handle_gateway_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Handle gateway selection."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "cancel":
        await query.message.edit_text("❌ عملیات لغو شد.")
        return ConversationHandler.END
    
    if query.data == "add_gateway":
        # Show gateway types
        keyboard = []
        for key, name in GATEWAY_TYPES.items():
            keyboard.append([
                InlineKeyboardButton(name, callback_data=f"type_{key}")
            ])
        keyboard.append([
            InlineKeyboardButton("❌ لغو", callback_data="cancel")
        ])
        
        await query.message.edit_text(
            "لطفاً نوع درگاه را انتخاب کنید:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return GATEWAY_TYPE
    
    # Handle edit gateway
    gateway_id = int(query.data.split('_')[-1])
    gateway = Setting.get_by_id(gateway_id)
    if not gateway:
        await query.message.edit_text("❌ درگاه مورد نظر یافت نشد.")
        return ConversationHandler.END
    
    gateway_data = get_gateway_data(context)
    gateway_data.update(gateway.to_dict())
    
    # Show edit options
    keyboard = [
        [InlineKeyboardButton("✏️ ویرایش نام", callback_data="edit_name")],
        [InlineKeyboardButton("🔑 ویرایش کلید API", callback_data="edit_api_key")],
        [InlineKeyboardButton("⚡️ تغییر وضعیت", callback_data="toggle_status")],
        [InlineKeyboardButton("❌ حذف درگاه", callback_data="delete_gateway")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="cancel")]
    ]
    
    await query.message.edit_text(
        f"تنظیمات درگاه {gateway.extra.get('display_name', gateway.key)}:\n"
        f"وضعیت: {'فعال' if gateway.status else 'غیرفعال'}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return GATEWAY_SELECT

async def handle_gateway_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Handle gateway type selection."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "cancel":
        await query.message.edit_text("❌ عملیات لغو شد.")
        return ConversationHandler.END
    
    gateway_type = query.data.split('_')[1]
    gateway_data = get_gateway_data(context)
    gateway_data['type'] = gateway_type
    
    # Ask for gateway name
    await query.message.edit_text(
        "لطفاً نام درگاه را وارد کنید (مثلاً: Zarinpal اصلی):"
    )
    return GATEWAY_NAME

async def handle_gateway_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Handle gateway name input."""
    name = update.message.text.strip()
    
    # Validate name
    if len(name) < 3 or len(name) > 50:
        await update.message.reply_text(
            "❌ نام درگاه باید بین 3 تا 50 کاراکتر باشد. لطفاً دوباره وارد کنید:"
        )
        return GATEWAY_NAME
    
    # Store name
    gateway_data = get_gateway_data(context)
    gateway_data['name'] = name
    
    # If card to card, ask for card number
    if gateway_data['type'] == 'card_to_card':
        await update.message.reply_text(
            "لطفاً شماره کارت ۱۶ رقمی را وارد کنید:"
        )
        return GATEWAY_CARD_NUMBER
    
    # For other gateways, ask for API key
    await update.message.reply_text(
        "لطفاً کلید API یا Merchant ID را وارد کنید:"
    )
    return GATEWAY_API_KEY

async def handle_gateway_api_key(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Handle gateway API key input."""
    api_key = update.message.text.strip()
    
    # Store API key
    gateway_data = get_gateway_data(context)
    gateway_data['api_key'] = api_key
    
    # TODO: Validate API key with gateway's API if possible
    
    # Ask for status
    keyboard = [
        [
            InlineKeyboardButton("✅ فعال", callback_data="status_active"),
            InlineKeyboardButton("❌ غیرفعال", callback_data="status_inactive")
        ]
    ]
    
    await update.message.reply_text(
        "آیا این درگاه فعال باشد؟",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return GATEWAY_STATUS

async def handle_gateway_card_number(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Handle card number input."""
    card_number = update.message.text.strip().replace('-', '').replace(' ', '')
    
    # Validate card number
    if not re.match(r'^\d{16}$', card_number):
        await update.message.reply_text(
            "❌ شماره کارت باید ۱۶ رقم باشد. لطفاً دوباره وارد کنید:"
        )
        return GATEWAY_CARD_NUMBER
    
    # Store card number
    gateway_data = get_gateway_data(context)
    gateway_data['card_number'] = card_number
    
    # Ask for card owner name
    await update.message.reply_text(
        "لطفاً نام صاحب کارت را وارد کنید:"
    )
    return GATEWAY_CARD_OWNER

async def handle_gateway_card_owner(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Handle card owner name input."""
    owner_name = update.message.text.strip()
    
    # Validate owner name
    if len(owner_name) < 3:
        await update.message.reply_text(
            "❌ نام صاحب کارت باید حداقل ۳ کاراکتر باشد. لطفاً دوباره وارد کنید:"
        )
        return GATEWAY_CARD_OWNER
    
    # Store owner name
    gateway_data = get_gateway_data(context)
    gateway_data['card_owner'] = owner_name
    
    # Ask for bank name
    await update.message.reply_text(
        "لطفاً نام بانک را وارد کنید:"
    )
    return GATEWAY_BANK_NAME

async def handle_gateway_bank_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Handle bank name input."""
    bank_name = update.message.text.strip()
    
    # Store bank name
    gateway_data = get_gateway_data(context)
    gateway_data['bank_name'] = bank_name
    
    # Ask for status
    keyboard = [
        [
            InlineKeyboardButton("✅ فعال", callback_data="status_active"),
            InlineKeyboardButton("❌ غیرفعال", callback_data="status_inactive")
        ]
    ]
    
    await update.message.reply_text(
        "آیا این درگاه فعال باشد؟",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return GATEWAY_STATUS

async def handle_gateway_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Handle gateway status selection."""
    query = update.callback_query
    await query.answer()
    
    gateway_data = get_gateway_data(context)
    gateway_data['status'] = query.data == "status_active"
    
    # Show confirmation
    if gateway_data['type'] == 'card_to_card':
        confirmation_text = (
            "📋 اطلاعات درگاه:\n\n"
            f"نوع: کارت‌به‌کارت\n"
            f"نام: {gateway_data['name']}\n"
            f"شماره کارت: {gateway_data['card_number'][:4]}****{gateway_data['card_number'][-4:]}\n"
            f"صاحب کارت: {gateway_data['card_owner']}\n"
            f"بانک: {gateway_data['bank_name']}\n"
            f"وضعیت: {'فعال' if gateway_data['status'] else 'غیرفعال'}\n\n"
            "آیا اطلاعات فوق را تأیید می‌کنید؟"
        )
    else:
        confirmation_text = (
            "📋 اطلاعات درگاه:\n\n"
            f"نوع: {GATEWAY_TYPES[gateway_data['type']]}\n"
            f"نام: {gateway_data['name']}\n"
            f"کلید API: {'*' * 20}\n"
            f"وضعیت: {'فعال' if gateway_data['status'] else 'غیرفعال'}\n\n"
            "آیا اطلاعات فوق را تأیید می‌کنید؟"
        )
    
    keyboard = [
        [
            InlineKeyboardButton("✅ تأیید", callback_data="confirm"),
            InlineKeyboardButton("❌ لغو", callback_data="cancel")
        ]
    ]
    
    await query.message.edit_text(
        confirmation_text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return GATEWAY_CONFIRM

async def handle_gateway_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle gateway confirmation."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "cancel":
        await query.message.edit_text("❌ عملیات لغو شد.")
        return ConversationHandler.END
    
    try:
        gateway_data = get_gateway_data(context)
        
        # Prepare extra data
        extra = {
            'display_name': gateway_data['name']
        }
        
        if gateway_data['type'] == 'card_to_card':
            extra.update({
                'card_owner': gateway_data['card_owner'],
                'bank_name': gateway_data['bank_name']
            })
            api_key = gateway_data['card_number']
        else:
            api_key = gateway_data['api_key']
        
        # Create or update gateway
        setting = Setting.create_payment_gateway(
            name=gateway_data['name'],
            gateway_type=gateway_data['type'],
            api_key=api_key,
            extra=extra
        )
        
        await query.message.edit_text("✅ درگاه با موفقیت اضافه/ویرایش شد!")
        
    except Exception as e:
        logger.error(f"Error saving gateway: {e}")
        await query.message.edit_text(
            "❌ خطا در ثبت درگاه. لطفاً دوباره تلاش کنید."
        )
    
    return ConversationHandler.END

# Channel Management
async def start_channel_settings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Start the channel settings process."""
    clear_channel_data(context)
    
    # Get existing channels
    channels = Setting.get_channels()
    
    keyboard = []
    for channel in channels:
        status = "✅" if channel.status else "❌"
        mandatory = "🔒" if channel.extra.get('mandatory', False) else ""
        keyboard.append([
            InlineKeyboardButton(
                f"{status} {mandatory} {channel.extra.get('display_name', channel.key)}",
                callback_data=f"edit_channel_{channel.id}"
            )
        ])
    
    keyboard.append([
        InlineKeyboardButton("➕ افزودن کانال جدید", callback_data="add_channel")
    ])
    keyboard.append([
        InlineKeyboardButton("❌ بازگشت", callback_data="cancel")
    ])
    
    await update.message.reply_text(
        "لطفاً کانال مورد نظر را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return CHANNEL_SELECT

async def handle_channel_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Handle channel selection."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "cancel":
        await query.message.edit_text("❌ عملیات لغو شد.")
        return ConversationHandler.END
    
    if query.data == "add_channel":
        await query.message.edit_text(
            "لطفاً نام کانال را وارد کنید (مثلاً: کانال اطلاع‌رسانی):"
        )
        return CHANNEL_NAME
    
    # Handle edit channel
    channel_id = int(query.data.split('_')[-1])
    channel = Setting.get_by_id(channel_id)
    if not channel:
        await query.message.edit_text("❌ کانال مورد نظر یافت نشد.")
        return ConversationHandler.END
    
    channel_data = get_channel_data(context)
    channel_data.update(channel.to_dict())
    
    # Show edit options
    keyboard = [
        [InlineKeyboardButton("✏️ ویرایش نام", callback_data="edit_name")],
        [InlineKeyboardButton("🔗 ویرایش لینک/ID", callback_data="edit_id")],
        [InlineKeyboardButton("🔒 تغییر وضعیت اجباری", callback_data="toggle_mandatory")],
        [InlineKeyboardButton("⚡️ تغییر وضعیت", callback_data="toggle_status")],
        [InlineKeyboardButton("❌ حذف کانال", callback_data="delete_channel")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="cancel")]
    ]
    
    await query.message.edit_text(
        f"تنظیمات کانال {channel.extra.get('display_name', channel.key)}:\n"
        f"وضعیت: {'فعال' if channel.status else 'غیرفعال'}\n"
        f"عضویت اجباری: {'فعال' if channel.extra.get('mandatory', False) else 'غیرفعال'}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return CHANNEL_SELECT

async def handle_channel_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Handle channel name input."""
    name = update.message.text.strip()
    
    # Validate name
    if len(name) < 3 or len(name) > 50:
        await update.message.reply_text(
            "❌ نام کانال باید بین 3 تا 50 کاراکتر باشد. لطفاً دوباره وارد کنید:"
        )
        return CHANNEL_NAME
    
    # Store name
    channel_data = get_channel_data(context)
    channel_data['name'] = name
    
    # Ask for channel ID/link
    await update.message.reply_text(
        "لطفاً ID یا لینک کانال را وارد کنید (مثل @WizWizChannel یا t.me/WizWizChannel):"
    )
    return CHANNEL_ID

async def handle_channel_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Handle channel ID/link input."""
    channel_id = update.message.text.strip()
    
    # Validate channel ID/link
    if not re.match(r'^(@[\w\d_]+|https?://t\.me/[\w\d_]+)$', channel_id):
        await update.message.reply_text(
            "❌ فرمت ID/لینک کانال نامعتبر است. لطفاً دوباره وارد کنید:"
        )
        return CHANNEL_ID
    
    # Store channel ID
    channel_data = get_channel_data(context)
    channel_data['channel_id'] = channel_id
    
    # Ask for channel type
    keyboard = []
    for key, name in CHANNEL_TYPES.items():
        keyboard.append([
            InlineKeyboardButton(name, callback_data=f"type_{key}")
        ])
    
    await update.message.reply_text(
        "لطفاً نوع کانال را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return CHANNEL_TYPE

async def handle_channel_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Handle channel type selection."""
    query = update.callback_query
    await query.answer()
    
    channel_type = query.data.split('_')[1]
    channel_data = get_channel_data(context)
    channel_data['type'] = channel_type
    
    # Ask for mandatory status
    keyboard = [
        [
            InlineKeyboardButton("✅ فعال", callback_data="mandatory_yes"),
            InlineKeyboardButton("❌ غیرفعال", callback_data="mandatory_no")
        ]
    ]
    
    await query.message.edit_text(
        "آیا عضویت در این کانال اجباری باشد؟",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return CHANNEL_MANDATORY

async def handle_channel_mandatory(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Handle channel mandatory status selection."""
    query = update.callback_query
    await query.answer()
    
    channel_data = get_channel_data(context)
    channel_data['mandatory'] = query.data == "mandatory_yes"
    
    # Show confirmation
    confirmation_text = (
        "📋 اطلاعات کانال:\n\n"
        f"نام: {channel_data['name']}\n"
        f"ID/لینک: {channel_data['channel_id']}\n"
        f"نوع: {CHANNEL_TYPES[channel_data['type']]}\n"
        f"عضویت اجباری: {'فعال' if channel_data['mandatory'] else 'غیرفعال'}\n\n"
        "آیا اطلاعات فوق را تأیید می‌کنید؟"
    )
    
    keyboard = [
        [
            InlineKeyboardButton("✅ تأیید", callback_data="confirm"),
            InlineKeyboardButton("❌ لغو", callback_data="cancel")
        ]
    ]
    
    await query.message.edit_text(
        confirmation_text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return CHANNEL_CONFIRM

async def handle_channel_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle channel confirmation."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "cancel":
        await query.message.edit_text("❌ عملیات لغو شد.")
        return ConversationHandler.END
    
    try:
        channel_data = get_channel_data(context)
        
        # Create or update channel
        setting = Setting.create_channel(
            name=channel_data['name'],
            channel_id=channel_data['channel_id'],
            channel_type=channel_data['type'],
            is_mandatory=channel_data['mandatory']
        )
        
        await query.message.edit_text("✅ کانال با موفقیت اضافه/ویرایش شد!")
        
    except Exception as e:
        logger.error(f"Error saving channel: {e}")
        await query.message.edit_text(
            "❌ خطا در ثبت کانال. لطفاً دوباره تلاش کنید."
        )
    
    return ConversationHandler.END

def get_settings_management_handlers():
    """Return the ConversationHandler for settings management."""
    return [
        # Payment Gateway Management Handler
        ConversationHandler(
            entry_points=[
                MessageHandler(filters.Regex('^تنظیمات درگاه‌های پرداخت$'), start_gateway_settings)
            ],
            states={
                GATEWAY_SELECT: [
                    CallbackQueryHandler(handle_gateway_selection)
                ],
                GATEWAY_TYPE: [
                    CallbackQueryHandler(handle_gateway_type)
                ],
                GATEWAY_NAME: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_gateway_name)
                ],
                GATEWAY_API_KEY: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_gateway_api_key)
                ],
                GATEWAY_CARD_NUMBER: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_gateway_card_number)
                ],
                GATEWAY_CARD_OWNER: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_gateway_card_owner)
                ],
                GATEWAY_BANK_NAME: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_gateway_bank_name)
                ],
                GATEWAY_STATUS: [
                    CallbackQueryHandler(handle_gateway_status)
                ],
                GATEWAY_CONFIRM: [
                    CallbackQueryHandler(handle_gateway_confirm)
                ]
            },
            fallbacks=[
                MessageHandler(filters.Regex('^لغو$'), lambda u, c: ConversationHandler.END)
            ],
            name="gateway_management",
            persistent=True
        ),
        
        # Channel Management Handler
        ConversationHandler(
            entry_points=[
                MessageHandler(filters.Regex('^تنظیمات کانال$'), start_channel_settings)
            ],
            states={
                CHANNEL_SELECT: [
                    CallbackQueryHandler(handle_channel_selection)
                ],
                CHANNEL_NAME: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_channel_name)
                ],
                CHANNEL_ID: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_channel_id)
                ],
                CHANNEL_TYPE: [
                    CallbackQueryHandler(handle_channel_type)
                ],
                CHANNEL_MANDATORY: [
                    CallbackQueryHandler(handle_channel_mandatory)
                ],
                CHANNEL_CONFIRM: [
                    CallbackQueryHandler(handle_channel_confirm)
                ]
            },
            fallbacks=[
                MessageHandler(filters.Regex('^لغو$'), lambda u, c: ConversationHandler.END)
            ],
            name="channel_management",
            persistent=True
        )
    ] 