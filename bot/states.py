from enum import Enum, auto

class ServerAddStates(Enum):
    TITLE = auto()
    UCOUNT = auto()
    REMARK = auto()
    FLAG = auto()
    PANEL_URL = auto()
    PANEL_USERNAME = auto()
    PANEL_PASSWORD = auto()

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
