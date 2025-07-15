from enum import Enum, auto
from telegram.ext import ConversationHandler

class ServerAddStates(Enum):
    TITLE = auto()
    UCOUNT = auto()
    REMARK = auto()
    FLAG = auto()
    PANEL_URL = auto()
    PANEL_USERNAME = auto()
    PANEL_PASSWORD = auto()

class ConversationState:
    """Helper class to manage conversation states and temporary data."""
    
    def __init__(self):
        self.data = {}
    
    def set_state(self, user_id: int, state: Enum) -> None:
        """Set state for a user."""
        self.data[f"state_{user_id}"] = state
    
    def get_state(self, user_id: int) -> Enum:
        """Get current state for a user."""
        return self.data.get(f"state_{user_id}")
    
    def clear_state(self, user_id: int) -> None:
        """Clear state for a user."""
        if f"state_{user_id}" in self.data:
            del self.data[f"state_{user_id}"]
    
    def set_data(self, user_id: int, key: str, value: any) -> None:
        """Set temporary data for a user."""
        if f"data_{user_id}" not in self.data:
            self.data[f"data_{user_id}"] = {}
        self.data[f"data_{user_id}"][key] = value
    
    def get_data(self, user_id: int, key: str, default=None) -> any:
        """Get temporary data for a user."""
        return self.data.get(f"data_{user_id}", {}).get(key, default)
    
    def get_all_data(self, user_id: int) -> dict:
        """Get all temporary data for a user."""
        return self.data.get(f"data_{user_id}", {})
    
    def clear_data(self, user_id: int) -> None:
        """Clear all temporary data for a user."""
        if f"data_{user_id}" in self.data:
            del self.data[f"data_{user_id}"]
    
    def clear_all(self, user_id: int) -> None:
        """Clear both state and data for a user."""
        self.clear_state(user_id)
        self.clear_data(user_id)

# Category Management States
CATEGORY_NAME = 'category_name'
CATEGORY_REMARK = 'category_remark'
CATEGORY_FLAG = 'category_flag'
CATEGORY_SERVERS = 'category_servers'
CATEGORY_CONFIRM = 'category_confirm'

# Plan Management States
PLAN_NAME = 'plan_name'
PLAN_VOLUME = 'plan_volume'
PLAN_DURATION = 'plan_duration'
PLAN_PRICE = 'plan_price'
PLAN_CATEGORY = 'plan_category'
PLAN_SERVERS = 'plan_servers'
PLAN_CONFIRM = 'plan_confirm'

# Settings Management States
# Payment Gateway States
GATEWAY_SELECT = 'gateway_select'
GATEWAY_TYPE = 'gateway_type'
GATEWAY_NAME = 'gateway_name'
GATEWAY_API_KEY = 'gateway_api_key'
GATEWAY_CARD_NUMBER = 'gateway_card_number'
GATEWAY_CARD_OWNER = 'gateway_card_owner'
GATEWAY_BANK_NAME = 'gateway_bank_name'
GATEWAY_STATUS = 'gateway_status'
GATEWAY_CONFIRM = 'gateway_confirm'

# Channel States
CHANNEL_SELECT = 'channel_select'
CHANNEL_NAME = 'channel_name'
CHANNEL_ID = 'channel_id'
CHANNEL_TYPE = 'channel_type'
CHANNEL_MANDATORY = 'channel_mandatory'
CHANNEL_CONFIRM = 'channel_confirm'

# Add to ALL_STATES
ALL_STATES = {
    # ... existing states ...
    CATEGORY_NAME: 'category_name',
    CATEGORY_REMARK: 'category_remark',
    CATEGORY_FLAG: 'category_flag',
    CATEGORY_SERVERS: 'category_servers',
    CATEGORY_CONFIRM: 'category_confirm',
    PLAN_NAME: 'plan_name',
    PLAN_VOLUME: 'plan_volume',
    PLAN_DURATION: 'plan_duration',
    PLAN_PRICE: 'plan_price',
    PLAN_CATEGORY: 'plan_category',
    PLAN_SERVERS: 'plan_servers',
    PLAN_CONFIRM: 'plan_confirm',
    # Payment Gateway States
    GATEWAY_SELECT: 'gateway_select',
    GATEWAY_TYPE: 'gateway_type',
    GATEWAY_NAME: 'gateway_name',
    GATEWAY_API_KEY: 'gateway_api_key',
    GATEWAY_CARD_NUMBER: 'gateway_card_number',
    GATEWAY_CARD_OWNER: 'gateway_card_owner',
    GATEWAY_BANK_NAME: 'gateway_bank_name',
    GATEWAY_STATUS: 'gateway_status',
    GATEWAY_CONFIRM: 'gateway_confirm',
    # Channel States
    CHANNEL_SELECT: 'channel_select',
    CHANNEL_NAME: 'channel_name',
    CHANNEL_ID: 'channel_id',
    CHANNEL_TYPE: 'channel_type',
    CHANNEL_MANDATORY: 'channel_mandatory',
    CHANNEL_CONFIRM: 'channel_confirm',
}

# Add to TIMEOUT_STATES
TIMEOUT_STATES = {
    # ... existing states ...
    CATEGORY_NAME: 300,  # 5 minutes timeout
    CATEGORY_REMARK: 300,
    CATEGORY_FLAG: 300,
    CATEGORY_SERVERS: 300,
    CATEGORY_CONFIRM: 300,
    PLAN_NAME: 300,  # 5 minutes timeout
    PLAN_VOLUME: 300,
    PLAN_DURATION: 300,
    PLAN_PRICE: 300,
    PLAN_CATEGORY: 300,
    PLAN_SERVERS: 300,
    PLAN_CONFIRM: 300,
    # Payment Gateway States
    GATEWAY_SELECT: 300,
    GATEWAY_TYPE: 300,
    GATEWAY_NAME: 300,
    GATEWAY_API_KEY: 300,
    GATEWAY_CARD_NUMBER: 300,
    GATEWAY_CARD_OWNER: 300,
    GATEWAY_BANK_NAME: 300,
    GATEWAY_STATUS: 300,
    GATEWAY_CONFIRM: 300,
    # Channel States
    CHANNEL_SELECT: 300,
    CHANNEL_NAME: 300,
    CHANNEL_ID: 300,
    CHANNEL_TYPE: 300,
    CHANNEL_MANDATORY: 300,
    CHANNEL_CONFIRM: 300,
}

def get_category_data(context):
    """Get category data from user_data."""
    if 'category_data' not in context.user_data:
        context.user_data['category_data'] = {}
    return context.user_data['category_data']

def clear_category_data(context):
    """Clear category data from user_data."""
    if 'category_data' in context.user_data:
        del context.user_data['category_data']

def get_plan_data(context):
    """Get plan data from user_data."""
    if 'plan_data' not in context.user_data:
        context.user_data['plan_data'] = {}
    return context.user_data['plan_data']

def clear_plan_data(context):
    """Clear plan data from user_data."""
    if 'plan_data' in context.user_data:
        del context.user_data['plan_data']

def get_gateway_data(context):
    """Get gateway data from user_data."""
    if 'gateway_data' not in context.user_data:
        context.user_data['gateway_data'] = {}
    return context.user_data['gateway_data']

def clear_gateway_data(context):
    """Clear gateway data from user_data."""
    if 'gateway_data' in context.user_data:
        del context.user_data['gateway_data']

def get_channel_data(context):
    """Get channel data from user_data."""
    if 'channel_data' not in context.user_data:
        context.user_data['channel_data'] = {}
    return context.user_data['channel_data']

def clear_channel_data(context):
    """Clear channel data from user_data."""
    if 'channel_data' in context.user_data:
        del context.user_data['channel_data'] 