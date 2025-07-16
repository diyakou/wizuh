from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup
from typing import List
from database.models import Plan, Config

def get_main_menu() -> InlineKeyboardMarkup:
    """Get main menu keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("خرید سرویس", callback_data="buy"),
            InlineKeyboardButton("سرویس‌های من", callback_data="configs")
        ],
        [
            InlineKeyboardButton("تمدید سرویس", callback_data="renew"),
            InlineKeyboardButton("کیف پول", callback_data="wallet")
        ],
        [InlineKeyboardButton("پشتیبانی", callback_data="support")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_plans_menu(plans: List[Plan], action: str = "buy") -> InlineKeyboardMarkup:
    """
    Get plans selection menu keyboard.
    
    Args:
        plans: List of Plan objects
        action: Action type ('buy' or 'renew')
    """
    keyboard = []
    for plan in plans:
        button_text = f"{plan.name} - {plan.volume}GB - {plan.duration} روز - {plan.price:,} تومان"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f"{action}_plan_{plan.id}")])
    
    keyboard.append([InlineKeyboardButton("بازگشت", callback_data="start")])
    return InlineKeyboardMarkup(keyboard)

def get_payment_methods_menu(amount: int, plan_id: int) -> InlineKeyboardMarkup:
    """Get payment methods menu keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("زرین‌پال", callback_data=f"pay_zarinpal_{plan_id}_{amount}"),
            InlineKeyboardButton("نکست‌پی", callback_data=f"pay_nextpay_{plan_id}_{amount}")
        ],
        [
            InlineKeyboardButton("ارز دیجیتال", callback_data=f"pay_crypto_{plan_id}_{amount}"),
            InlineKeyboardButton("کیف پول", callback_data=f"pay_wallet_{plan_id}_{amount}")
        ],
        [InlineKeyboardButton("بازگشت", callback_data="buy")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_config_menu(config: Config) -> InlineKeyboardMarkup:
    """Get configuration management menu keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("دریافت QR کد", callback_data=f"qr_{config.id}"),
            InlineKeyboardButton("دریافت لینک", callback_data=f"link_{config.id}")
        ],
        [
            InlineKeyboardButton("تمدید سرویس", callback_data=f"renew_{config.id}"),
            InlineKeyboardButton("مشخصات فنی", callback_data=f"details_{config.id}")
        ],
        [InlineKeyboardButton("بازگشت", callback_data="configs")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_wallet_menu(balance: float) -> InlineKeyboardMarkup:
    """Get wallet management menu keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("افزایش موجودی", callback_data="deposit"),
            InlineKeyboardButton("تراکنش‌ها", callback_data="transactions")
        ],
        [InlineKeyboardButton("بازگشت", callback_data="start")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_support_menu() -> InlineKeyboardMarkup:
    """Get support menu keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("ارسال پیام", callback_data="send_message"),
            InlineKeyboardButton("سوالات متداول", callback_data="faq")
        ],
        [
            InlineKeyboardButton("قوانین", callback_data="rules"),
            InlineKeyboardButton("کانال اطلاع‌رسانی", url="https://t.me/WizWizCh")
        ],
        [InlineKeyboardButton("بازگشت", callback_data="start")]
    ]
    return InlineKeyboardMarkup(keyboard)
