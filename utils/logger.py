import datetime
from config import LOG_CHANNEL_ID


def _half_number(number: str) -> str:
    n = number.strip()
    half = len(n) // 2
    return n[:half] + "*" * (len(n) - half)


async def log_sale(bot, number: str, amount: float, country: str, flag: str,
                   user_id: int, username: str, order_id: int):
    now = datetime.datetime.now().strftime("%d %b %Y %I:%M %p")
    uname = f"@{username}" if username else f"ID:{user_id}"
    text = (
        f"💰 <b>NEW SALE</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📱 <b>Number:</b> <code>{_half_number(number)}</code>\n"
        f"{flag} <b>Country:</b> {country}\n"
        f"💸 <b>Amount:</b> ₹{amount:.2f}\n"
        f"🕐 <b>Time:</b> {now}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"#sale #order{order_id}"
    )
    try:
        await bot.send_message(LOG_CHANNEL_ID, text, parse_mode="HTML")
    except Exception as e:
        print(f"[LOG ERROR] {e}")


async def log_otp(bot, number: str, otp: str, user_id: int, username: str):
    now = datetime.datetime.now().strftime("%d %b %Y %I:%M %p")
    uname = f"@{username}" if username else f"ID:{user_id}"
    text = (
        f"🔐 <b>OTP DELIVERED</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📱 <code>{_half_number(number)}</code>\n"
        f"👤 {uname}\n"
        f"🕐 {now}\n"
        f"━━━━━━━━━━━━━━━━━━━━"
    )
    try:
        await bot.send_message(LOG_CHANNEL_ID, text, parse_mode="HTML")
    except Exception:
        pass
