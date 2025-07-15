from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CallbackQueryHandler, MessageHandler, filters
from database.models import ServerCategory
from bot.states import (
    CATEGORY_NAME, CATEGORY_REMARK, CATEGORY_FLAG, CATEGORY_SERVERS, CATEGORY_CONFIRM,
    get_category_data, clear_category_data
)
import logging
import json
import re

logger = logging.getLogger(__name__)

# Category management states
(
    WAITING_CATEGORY_NAME,
    WAITING_CATEGORY_DESCRIPTION,
    WAITING_CATEGORY_EDIT,
    WAITING_CATEGORY_DELETE
) = range(4)

async def start_add_category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Start the category addition process."""
    # Clear any existing category data
    clear_category_data(context)
    
    await update.message.reply_text(
        "لطفاً نام دسته‌بندی جدید را وارد کنید (مثلاً: سرورهای ایران، سرورهای اروپا):"
    )
    return CATEGORY_NAME

async def handle_category_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Handle the category name input."""
    name = update.message.text.strip()
    
    # Validate name
    if len(name) < 3 or len(name) > 50:
        await update.message.reply_text(
            "❌ نام دسته‌بندی باید بین 3 تا 50 کاراکتر باشد. لطفاً دوباره وارد کنید:"
        )
        return CATEGORY_NAME
    
    # Check if category with this name exists
    from database.db import session
    existing = session.query(ServerCategory).filter_by(title=name).first()
    if existing:
        await update.message.reply_text(
            "❌ دسته‌بندی با این نام قبلاً ثبت شده است. لطفاً نام دیگری وارد کنید:"
        )
        return CATEGORY_NAME
    
    # Store the name
    category_data = get_category_data(context)
    category_data['title'] = name
    
    # Ask for description
    await update.message.reply_text(
        "لطفاً توضیحی کوتاه برای این دسته‌بندی وارد کنید (اختیاری، برای نمایش به کاربران):\n"
        "برای رد کردن این مرحله، /skip را بزنید."
    )
    return CATEGORY_REMARK

async def skip_remark(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Skip the remark step."""
    category_data = get_category_data(context)
    category_data['remark'] = None
    
    await update.message.reply_text(
        "لطفاً یک ایموجی برای این دسته‌بندی انتخاب کنید (مثلاً 🇮🇷 برای ایران):\n"
        "برای رد کردن این مرحله، /skip را بزنید."
    )
    return CATEGORY_FLAG

async def handle_category_remark(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Handle the category description input."""
    remark = update.message.text.strip()
    
    # Validate remark length
    if len(remark) > 200:
        await update.message.reply_text(
            "❌ توضیحات نباید بیشتر از 200 کاراکتر باشد. لطفاً دوباره وارد کنید:"
        )
        return CATEGORY_REMARK
    
    # Store the remark
    category_data = get_category_data(context)
    category_data['remark'] = remark
    
    # Ask for emoji
    await update.message.reply_text(
        "لطفاً یک ایموجی برای این دسته‌بندی انتخاب کنید (مثلاً 🇮🇷 برای ایران):\n"
        "برای رد کردن این مرحله، /skip را بزنید."
    )
    return CATEGORY_FLAG

async def skip_flag(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Skip the flag step."""
    category_data = get_category_data(context)
    category_data['flag'] = None
    
    # Show server selection keyboard
    return await show_server_selection(update, context)

async def handle_category_flag(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Handle the category emoji input."""
    flag = update.message.text.strip()
    
    # Basic emoji validation (this is a simple check, you might want to improve it)
    if len(flag) > 8:
        await update.message.reply_text(
            "❌ لطفاً فقط یک ایموجی وارد کنید."
        )
        return CATEGORY_FLAG
    
    # Store the flag
    category_data = get_category_data(context)
    category_data['flag'] = flag
    
    # Show server selection keyboard
    return await show_server_selection(update, context)

async def show_server_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Show server selection keyboard."""
    # Get all available servers
    from database.db import session
    from database.models import Server
    servers = session.query(Server).filter_by(is_active=True).all()
    
    if not servers:
        await update.message.reply_text(
            "❌ هیچ سروری برای انتخاب وجود ندارد. لطفاً ابتدا سرور اضافه کنید."
        )
        return ConversationHandler.END
    
    # Create keyboard with server options
    keyboard = []
    category_data = get_category_data(context)
    selected_servers = category_data.get('server_ids', [])
    
    for server in servers:
        # Add checkmark if server is selected
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
        "لطفاً سرورهایی که می‌خواهید در این دسته‌بندی قرار بگیرند را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return CATEGORY_SERVERS

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
    category_data = get_category_data(context)
    
    if 'server_ids' not in category_data:
        category_data['server_ids'] = []
    
    # Toggle server selection
    if server_id in category_data['server_ids']:
        category_data['server_ids'].remove(server_id)
    else:
        category_data['server_ids'].append(server_id)
    
    # Update keyboard
    return await show_server_selection(query, context)

async def show_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Show confirmation message with category details."""
    query = update.callback_query
    category_data = get_category_data(context)
    
    # Get server names
    from database.db import session
    from database.models import Server
    servers = session.query(Server).filter(Server.id.in_(category_data['server_ids'])).all()
    server_names = [server.title for server in servers]
    
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
            InlineKeyboardButton("✅ تأیید", callback_data="confirm"),
            InlineKeyboardButton("❌ لغو", callback_data="cancel")
        ]
    ]
    
    await query.message.edit_text(
        confirmation_text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return CATEGORY_CONFIRM

async def handle_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the final confirmation."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "cancel":
        await query.message.edit_text("❌ عملیات لغو شد.")
        return ConversationHandler.END
    
    # Create new category
    try:
        category_data = get_category_data(context)
        category = ServerCategory(
            title=category_data['title'],
            remark=category_data.get('remark'),
            flag=category_data.get('flag'),
            server_ids=category_data['server_ids'],
            is_active=True
        )
        category.save()
        
        await query.message.edit_text("✅ دسته‌بندی با موفقیت اضافه شد!")
        
    except Exception as e:
        logger.error(f"Error creating category: {e}")
        await query.message.edit_text(
            "❌ خطا در ثبت دسته‌بندی. لطفاً دوباره تلاش کنید."
        )
    
    return ConversationHandler.END

async def category_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle category settings."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "categories_list":
        # Get all categories
        categories = Category.get_all()
        
        if not categories:
            await query.message.edit_text(
                "❌ هیچ دسته‌بندی موجود نیست.\n"
                "برای افزودن دسته‌بندی جدید از دکمه افزودن دسته‌بندی استفاده کنید.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_categories")]])
            )
            return
            
        text = "📁 دسته‌بندی‌های موجود:\n\n"
        keyboard = []
        
        for category in categories:
            text += f"🔹 {category.name}\n"
            if category.description:
                text += f"└ {category.description}\n"
                
        keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_categories")])
        
        await query.message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
    elif query.data == "category_add":
        await query.message.edit_text(
            "📝 لطفاً نام دسته‌بندی جدید را وارد کنید:",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_categories")]])
        )
        return WAITING_CATEGORY_NAME
        
    elif query.data == "category_edit":
        # Get all categories for editing
        categories = Category.get_all()
        
        if not categories:
            await query.message.edit_text(
                "❌ هیچ دسته‌بندی برای ویرایش وجود ندارد.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_categories")]])
            )
            return
            
        keyboard = []
        for category in categories:
            keyboard.append([InlineKeyboardButton(
                category.name,
                callback_data=f"edit_category_{category.id}"
            )])
        keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_categories")])
        
        await query.message.edit_text(
            "✏️ ویرایش دسته‌بندی\n"
            "لطفاً دسته‌بندی مورد نظر را انتخاب کنید:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return WAITING_CATEGORY_EDIT
        
    elif query.data == "category_delete":
        # Get all categories for deletion
        categories = Category.get_all()
        
        if not categories:
            await query.message.edit_text(
                "❌ هیچ دسته‌بندی برای حذف وجود ندارد.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_categories")]])
            )
            return
            
        keyboard = []
        for category in categories:
            keyboard.append([InlineKeyboardButton(
                category.name,
                callback_data=f"delete_category_{category.id}"
            )])
        keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_categories")])
        
        await query.message.edit_text(
            "❌ حذف دسته‌بندی\n"
            "لطفاً دسته‌بندی مورد نظر را انتخاب کنید:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return WAITING_CATEGORY_DELETE

async def handle_category_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle category name input."""
    name = update.message.text
    context.user_data['category_name'] = name
    
    await update.message.reply_text(
        "📝 لطفاً توضیحات دسته‌بندی را وارد کنید (اختیاری):",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("رد کردن", callback_data="skip_description")]])
    )
    return WAITING_CATEGORY_DESCRIPTION

async def handle_category_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle category description input and save category."""
    if update.callback_query and update.callback_query.data == "skip_description":
        description = ""
        await update.callback_query.answer()
    else:
        description = update.message.text
    
    name = context.user_data.get('category_name')
    
    # Save category to database
    Category.create(
        name=name,
        description=description
    )
    
    # Clear user data
    context.user_data.clear()
    
    # Send success message
    if update.callback_query:
        await update.callback_query.message.edit_text(
            "✅ دسته‌بندی با موفقیت اضافه شد.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت به دسته‌بندی‌ها", callback_data="back_to_categories")]])
        )
    else:
        await update.message.reply_text(
            "✅ دسته‌بندی با موفقیت اضافه شد.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت به دسته‌بندی‌ها", callback_data="back_to_categories")]])
        )
    
    return ConversationHandler.END

async def handle_category_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle category edit selection."""
    query = update.callback_query
    await query.answer()
    
    category_id = int(query.data.replace("edit_category_", ""))
    category = Category.get_by_id(category_id)
    
    if not category:
        await query.message.edit_text(
            "❌ دسته‌بندی مورد نظر یافت نشد.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_categories")]])
        )
        return ConversationHandler.END
    
    context.user_data['edit_category_id'] = category_id
    
    await query.message.edit_text(
        f"✏️ ویرایش دسته‌بندی: {category.name}\n"
        "لطفاً نام جدید را وارد کنید:",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_categories")]])
    )
    return WAITING_CATEGORY_NAME

async def handle_category_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle category deletion."""
    query = update.callback_query
    await query.answer()
    
    category_id = int(query.data.replace("delete_category_", ""))
    category = Category.get_by_id(category_id)
    
    if not category:
        await query.message.edit_text(
            "❌ دسته‌بندی مورد نظر یافت نشد.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_categories")]])
        )
        return ConversationHandler.END
    
    # Delete category
    category.delete()
    
    await query.message.edit_text(
        "✅ دسته‌بندی با موفقیت حذف شد.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت به دسته‌بندی‌ها", callback_data="back_to_categories")]])
    )
    return ConversationHandler.END

# Create conversation handler for category management
category_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(category_settings, pattern=r"^category_|^categories_")],
    states={
        WAITING_CATEGORY_NAME: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_category_name)
        ],
        WAITING_CATEGORY_DESCRIPTION: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_category_description),
            CallbackQueryHandler(handle_category_description, pattern="^skip_description$")
        ],
        WAITING_CATEGORY_EDIT: [
            CallbackQueryHandler(handle_category_edit, pattern=r"^edit_category_\d+$")
        ],
        WAITING_CATEGORY_DELETE: [
            CallbackQueryHandler(handle_category_delete, pattern=r"^delete_category_\d+$")
        ]
    },
    fallbacks=[
        CallbackQueryHandler(category_settings, pattern="^back_to_categories$")
    ]
)

def get_category_management_handlers():
    """Return the ConversationHandlers for category management."""
    handlers = [
        category_handler,  # The first handler for category settings
        ConversationHandler(  # The second handler for adding categories
            entry_points=[
                MessageHandler(filters.Regex('^افزودن دسته‌بندی$'), start_add_category)
            ],
            states={
                CATEGORY_NAME: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_category_name)
                ],
                CATEGORY_REMARK: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_category_remark),
                    MessageHandler(filters.Regex('^/skip$'), skip_remark)
                ],
                CATEGORY_FLAG: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_category_flag),
                    MessageHandler(filters.Regex('^/skip$'), skip_flag)
                ],
                CATEGORY_SERVERS: [
                    CallbackQueryHandler(handle_server_selection)
                ],
                CATEGORY_CONFIRM: [
                    CallbackQueryHandler(handle_confirmation)
                ]
            },
            fallbacks=[
                MessageHandler(filters.Regex('^لغو$'), lambda u, c: ConversationHandler.END)
            ],
            name="category_management",
            persistent=True
        )
    ]
    return handlers 