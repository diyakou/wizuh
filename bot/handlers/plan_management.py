from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CallbackQueryHandler, MessageHandler, filters
from database.models import ServerPlan, ServerCategory, Server
from bot.states import (
    PLAN_NAME, PLAN_VOLUME, PLAN_DURATION, PLAN_PRICE, PLAN_CATEGORY, PLAN_SERVERS, PLAN_CONFIRM,
    get_plan_data, clear_plan_data
)
import logging
import re

logger = logging.getLogger(__name__)

async def start_add_plan(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Start the plan addition process."""
    # Clear any existing plan data
    clear_plan_data(context)
    
    await update.message.reply_text(
        "لطفاً نام پلن جدید را وارد کنید (مثلاً: پلن ۱۰ گیگ ۳۰ روزه):"
    )
    return PLAN_NAME

async def handle_plan_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Handle the plan name input."""
    name = update.message.text.strip()
    
    # Validate name
    if len(name) < 3 or len(name) > 50:
        await update.message.reply_text(
            "❌ نام پلن باید بین 3 تا 50 کاراکتر باشد. لطفاً دوباره وارد کنید:"
        )
        return PLAN_NAME
    
    # Check if plan with this name exists
    from database.db import session
    existing = session.query(ServerPlan).filter_by(title=name).first()
    if existing:
        await update.message.reply_text(
            "❌ پلن با این نام قبلاً ثبت شده است. لطفاً نام دیگری وارد کنید:"
        )
        return PLAN_NAME
    
    # Store the name
    plan_data = get_plan_data(context)
    plan_data['title'] = name
    
    # Ask for volume
    await update.message.reply_text(
        "لطفاً حجم پلن را به مگابایت وارد کنید (مثلاً 10000 برای 10 گیگ):"
    )
    return PLAN_VOLUME

async def handle_plan_volume(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Handle the plan volume input."""
    try:
        volume = int(update.message.text.strip())
        if volume <= 0:
            raise ValueError("Volume must be positive")
        
        # Store the volume
        plan_data = get_plan_data(context)
        plan_data['volume'] = volume
        
        # Ask for duration
        await update.message.reply_text(
            "لطفاً مدت زمان پلن را به روز وارد کنید (مثلاً 30 برای یک ماه):"
        )
        return PLAN_DURATION
        
    except ValueError:
        await update.message.reply_text(
            "❌ لطفاً یک عدد صحیح مثبت وارد کنید:"
        )
        return PLAN_VOLUME

async def handle_plan_duration(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Handle the plan duration input."""
    try:
        duration = int(update.message.text.strip())
        if duration <= 0:
            raise ValueError("Duration must be positive")
        
        # Store the duration
        plan_data = get_plan_data(context)
        plan_data['duration'] = duration
        
        # Ask for price
        await update.message.reply_text(
            "لطفاً قیمت پلن را به تومان وارد کنید (مثلاً 50000):"
        )
        return PLAN_PRICE
        
    except ValueError:
        await update.message.reply_text(
            "❌ لطفاً یک عدد صحیح مثبت وارد کنید:"
        )
        return PLAN_DURATION

async def handle_plan_price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Handle the plan price input."""
    try:
        price = int(update.message.text.strip())
        if price <= 0:
            raise ValueError("Price must be positive")
        
        # Store the price
        plan_data = get_plan_data(context)
        plan_data['price'] = price
        
        # Show category selection if categories exist
        from database.db import session
        categories = session.query(ServerCategory).filter_by(is_active=True).all()
        
        if categories:
            return await show_category_selection(update, context)
        else:
            # Skip to server selection if no categories
            plan_data['category_id'] = None
            return await show_server_selection(update, context)
        
    except ValueError:
        await update.message.reply_text(
            "❌ لطفاً یک عدد صحیح مثبت وارد کنید:"
        )
        return PLAN_PRICE

async def show_category_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Show category selection keyboard."""
    from database.db import session
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
    
    # Add "No Category" option
    keyboard.append([
        InlineKeyboardButton("بدون دسته‌بندی", callback_data="no_category")
    ])
    
    keyboard.append([
        InlineKeyboardButton("❌ لغو", callback_data="cancel")
    ])
    
    await update.message.reply_text(
        "لطفاً دسته‌بندی پلن را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return PLAN_CATEGORY

async def handle_category_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Handle category selection callback."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "cancel":
        await query.message.edit_text("❌ عملیات لغو شد.")
        return ConversationHandler.END
    
    plan_data = get_plan_data(context)
    
    if query.data == "no_category":
        plan_data['category_id'] = None
    else:
        category_id = int(query.data.split('_')[-1])
        plan_data['category_id'] = category_id
    
    # Move to server selection
    return await show_server_selection(query, context)

async def show_server_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Show server selection keyboard."""
    from database.db import session
    servers = session.query(Server).filter_by(is_active=True).all()
    
    if not servers:
        await update.message.reply_text(
            "❌ هیچ سروری برای انتخاب وجود ندارد. لطفاً ابتدا سرور اضافه کنید."
        )
        return ConversationHandler.END
    
    keyboard = []
    plan_data = get_plan_data(context)
    selected_servers = plan_data.get('server_ids', [])
    
    for server in servers:
        mark = "✅ " if server.id in selected_servers else ""
        keyboard.append([
            InlineKeyboardButton(
                f"{mark}{server.title}",
                callback_data=f"select_server_{server.id}"
            )
        ])
    
    # Add Done button if at least one server is selected
    if selected_servers:
        keyboard.append([
            InlineKeyboardButton("✅ تأیید و ادامه", callback_data="servers_done")
        ])
    
    keyboard.append([
        InlineKeyboardButton("❌ لغو", callback_data="cancel")
    ])
    
    await update.message.reply_text(
        "لطفاً سرورهای مرتبط با این پلن را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return PLAN_SERVERS

async def handle_server_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Handle server selection callbacks."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "cancel":
        await query.message.edit_text("❌ عملیات لغو شد.")
        return ConversationHandler.END
    
    if query.data == "servers_done":
        return await show_confirmation(update, context)
    
    # Handle server selection
    server_id = int(query.data.split('_')[-1])
    plan_data = get_plan_data(context)
    
    if 'server_ids' not in plan_data:
        plan_data['server_ids'] = []
    
    # Toggle server selection
    if server_id in plan_data['server_ids']:
        plan_data['server_ids'].remove(server_id)
    else:
        plan_data['server_ids'].append(server_id)
    
    # Update keyboard
    return await show_server_selection(query, context)

async def show_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Show confirmation message with plan details."""
    query = update.callback_query
    plan_data = get_plan_data(context)
    
    # Get category name if selected
    category_name = "بدون دسته‌بندی"
    if plan_data.get('category_id'):
        from database.db import session
        category = session.query(ServerCategory).get(plan_data['category_id'])
        if category:
            flag = category.flag if category.flag else ""
            category_name = f"{flag} {category.title}"
    
    # Get server names
    servers = session.query(Server).filter(Server.id.in_(plan_data['server_ids'])).all()
    server_names = [server.title for server in servers]
    
    # Format volume to GB if larger than 1024 MB
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
            InlineKeyboardButton("✅ تأیید", callback_data="confirm"),
            InlineKeyboardButton("❌ لغو", callback_data="cancel")
        ]
    ]
    
    await query.message.edit_text(
        confirmation_text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return PLAN_CONFIRM

async def handle_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the final confirmation."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "cancel":
        await query.message.edit_text("❌ عملیات لغو شد.")
        return ConversationHandler.END
    
    # Create new plan
    try:
        plan_data = get_plan_data(context)
        plan = ServerPlan(
            title=plan_data['title'],
            volume=plan_data['volume'],
            duration=plan_data['duration'],
            price=plan_data['price'],
            category_id=plan_data.get('category_id'),
            server_ids=plan_data['server_ids'],
            is_active=True
        )
        plan.save()
        
        await query.message.edit_text("✅ پلن با موفقیت اضافه شد!")
        
    except Exception as e:
        logger.error(f"Error creating plan: {e}")
        await query.message.edit_text(
            "❌ خطا در ثبت پلن. لطفاً دوباره تلاش کنید."
        )
    
    return ConversationHandler.END

def get_plan_management_handlers():
    handlers = [
        ConversationHandler(
            entry_points=[
                MessageHandler(filters.Regex('^افزودن پلن$'), start_add_plan)
            ],
            states={
                PLAN_NAME: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_plan_name)
                ],
                PLAN_VOLUME: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_plan_volume)
                ],
                PLAN_DURATION: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_plan_duration)
                ],
                PLAN_PRICE: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_plan_price)
                ],
                PLAN_CATEGORY: [
                    CallbackQueryHandler(handle_category_selection)
                ],
                PLAN_SERVERS: [
                    CallbackQueryHandler(handle_server_selection)
                ],
                PLAN_CONFIRM: [
                    CallbackQueryHandler(handle_confirmation)
                ]
            },
            fallbacks=[
                MessageHandler(filters.Regex('^لغو$'), lambda u, c: ConversationHandler.END)
            ],
            name="plan_management",
            persistent=True
        )
    ]
    return handlers