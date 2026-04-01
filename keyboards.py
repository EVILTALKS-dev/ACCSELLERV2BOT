from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton
)

COUNTRIES = [
    ("🇮🇳", "India"), ("🇺🇸", "USA"), ("🇬🇧", "UK"),
    ("🇷🇺", "Russia"), ("🇧🇩", "Bangladesh"), ("🇵🇰", "Pakistan"),
    ("🇳🇬", "Nigeria"), ("🇧🇷", "Brazil"), ("🇮🇩", "Indonesia"),
    ("🇹🇷", "Turkey"), ("🇺🇦", "Ukraine"), ("🇰🇿", "Kazakhstan"),
    ("🇵🇭", "Philippines"), ("🇪🇬", "Egypt"), ("🇻🇳", "Vietnam"),
    ("🇲🇾", "Malaysia"), ("🇿🇦", "South Africa"), ("🇸🇦", "Saudi Arabia"),
    ("🇦🇪", "UAE"), ("🇲🇲", "Myanmar"),
]

# ── User Keyboards ─────────────────────────────────────────────────────────────

def user_main_kb():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="🛒 Browse Accounts"), KeyboardButton(text="📦 My Orders")],
        [KeyboardButton(text="📢 Channel"),         KeyboardButton(text="💬 Support")],
        [KeyboardButton(text="ℹ️ How It Works")],
    ], resize_keyboard=True)


def country_list_kb(stock: list):
    """stock = [{"country","flag","price","count"}]"""
    buttons = []
    for s in stock:
        buttons.append([InlineKeyboardButton(
            text=f"{s['flag']} {s['country']}  ·  ₹{s['price']:.0f}  ·  {s['count']} in stock",
            callback_data=f"country:{s['country']}"
        )])
    buttons.append([InlineKeyboardButton(text="🔙 Back", callback_data="back_main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def account_detail_kb(account_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Buy This Account", callback_data=f"confirm_pay:{account_id}")],
        [InlineKeyboardButton(text="🔙 Back to Countries",  callback_data="back_countries")],
    ])


def payment_kb(order_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📸 Upload Payment Screenshot", callback_data=f"upload_ss:{order_id}")],
        [InlineKeyboardButton(text="❌ Cancel Order", callback_data=f"cancel_order:{order_id}")],
    ])


def screenshot_done_kb(order_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ I've Uploaded — Notify Admin", callback_data=f"paid_notify:{order_id}")],
        [InlineKeyboardButton(text="❌ Cancel Order", callback_data=f"cancel_order:{order_id}")],
    ])


def reveal_number_kb(order_id: int, session_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👁 Reveal Account Details", callback_data=f"reveal:{order_id}")],
        [InlineKeyboardButton(text="🔐 Get Latest OTP",         callback_data=f"get_otp:{session_id}")],
    ])


def otp_kb(session_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔐 Get Latest OTP", callback_data=f"get_otp:{session_id}")],
    ])

# ── Admin Keyboards ────────────────────────────────────────────────────────────

def admin_main_kb():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="➕ Add Account"),    KeyboardButton(text="📋 View Accounts")],
        [KeyboardButton(text="⏳ Pending Orders"), KeyboardButton(text="📊 Statistics")],
        [KeyboardButton(text="👥 All Users"),      KeyboardButton(text="📜 Order History")],
        [KeyboardButton(text="🔐 OTP Sessions"),   KeyboardButton(text="📢 Broadcast")],
        [KeyboardButton(text="🏠 User Mode")],
    ], resize_keyboard=True)


def admin_approve_kb(order_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Approve",  callback_data=f"admin_approve:{order_id}"),
            InlineKeyboardButton(text="❌ Reject",   callback_data=f"admin_reject:{order_id}"),
        ],
        [InlineKeyboardButton(text="📸 View Screenshot", callback_data=f"admin_view_ss:{order_id}")],
    ])


def admin_account_kb(account_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✏️ Edit Price",    callback_data=f"edit_price:{account_id}"),
            InlineKeyboardButton(text="🔑 Edit Session",  callback_data=f"edit_session:{account_id}"),
        ],
        [InlineKeyboardButton(text="🗑 Delete Account",   callback_data=f"del_acc:{account_id}")],
    ])


def admin_otp_kb(session_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📤 Send OTP Manually", callback_data=f"manual_otp:{session_id}")],
    ])


def country_select_kb():
    buttons = []
    row = []
    for flag, name in COUNTRIES:
        row.append(InlineKeyboardButton(text=f"{flag} {name}", callback_data=f"set_country:{name}:{flag}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def cancel_kb():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Cancel")]],
        resize_keyboard=True, one_time_keyboard=True
    )


def user_ban_kb(user_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🚫 Ban User",   callback_data=f"ban:{user_id}"),
            InlineKeyboardButton(text="✅ Unban User", callback_data=f"unban:{user_id}"),
        ],
    ])
