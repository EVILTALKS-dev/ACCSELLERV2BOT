from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart

import database as db
from keyboards import user_main_kb, country_list_kb, account_detail_kb
from config import LOG_CHANNEL_LINK, SUPPORT_GROUP, ADMIN_USERNAME

router = Router()


async def banned_check(user_id: int, msg_or_cq):
    if await db.is_banned(user_id):
        text = "🚫 You are banned from using this bot.\nContact support if you think this is a mistake."
        if isinstance(msg_or_cq, Message):
            await msg_or_cq.answer(text)
        else:
            await msg_or_cq.answer(text, show_alert=True)
        return True
    return False


@router.message(CommandStart())
async def start(msg: Message):
    await db.upsert_user(msg.from_user.id, msg.from_user.username or "", msg.from_user.full_name)

    from config import ADMIN_IDS
    if msg.from_user.id in ADMIN_IDS:
        from keyboards import admin_main_kb
        await msg.answer(
            f"👑 <b>Welcome back, Admin!</b>\n\n"
            f"Use the panel below to manage your bot.",
            parse_mode="HTML", reply_markup=admin_main_kb()
        )
        return

    await msg.answer(
        f"🔥 <b>Welcome to EVILTALKS AccountBot!</b>\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🛒 Buy verified Telegram accounts\n"
        f"🌍 Multiple countries available\n"
        f"💳 Pay via UPI — instant QR\n"
        f"🔐 Auto OTP delivery\n"
        f"✅ Admin verified & safe\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📢 Join our channel: {LOG_CHANNEL_LINK}\n"
        f"💬 Support: {SUPPORT_GROUP}\n\n"
        f"Tap <b>Browse Accounts</b> to start! 👇",
        parse_mode="HTML",
        reply_markup=user_main_kb(),
        disable_web_page_preview=True
    )


@router.message(F.text == "🛒 Browse Accounts")
async def browse(msg: Message):
    if await banned_check(msg.from_user.id, msg): return
    stock = await db.get_country_stock()
    if not stock:
        await msg.answer("😔 <b>No accounts available right now.</b>\n\nCheck back soon!", parse_mode="HTML")
        return
    await msg.answer(
        f"🌍 <b>Select Country</b>\n\n"
        f"Choose a country to see available accounts:",
        parse_mode="HTML",
        reply_markup=country_list_kb(stock)
    )


@router.callback_query(F.data == "back_countries")
async def back_countries(cq: CallbackQuery):
    stock = await db.get_country_stock()
    if not stock:
        await cq.message.edit_text("😔 No accounts available right now.")
        return
    await cq.message.edit_text(
        f"🌍 <b>Select Country</b>\n\nChoose a country to see available accounts:",
        parse_mode="HTML",
        reply_markup=country_list_kb(stock)
    )


@router.callback_query(F.data.startswith("country:"))
async def country_accounts(cq: CallbackQuery):
    if await banned_check(cq.from_user.id, cq): return
    country = cq.data.split(":", 1)[1]
    accounts = await db.get_available_by_country(country)
    if not accounts:
        await cq.answer("😔 No accounts left in this country!", show_alert=True)
        return

    acc = accounts[0]  # Show first available
    masked = f"{acc['number'][:4]}****{acc['number'][-3:]}"
    text = (
        f"{acc['country_flag']} <b>{acc['country']} Account</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📱 <b>Number:</b> <code>{masked}</code>\n"
        f"💰 <b>Price:</b> ₹{acc['price']:.2f}\n"
        f"📝 <b>Info:</b> {acc['description'] or 'Fresh account, ready to use'}\n"
        f"📦 <b>Stock:</b> {len(accounts)} available\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"⚡ UPI Payment · Auto OTP · Instant Delivery"
    )
    await cq.message.edit_text(text, parse_mode="HTML", reply_markup=account_detail_kb(acc["id"]))


@router.callback_query(F.data == "back_main")
async def back_main(cq: CallbackQuery):
    await cq.message.delete()


@router.message(F.text == "📦 My Orders")
async def my_orders(msg: Message):
    if await banned_check(msg.from_user.id, msg): return
    orders = await db.get_user_orders(msg.from_user.id)
    if not orders:
        await msg.answer("📦 <b>No orders yet!</b>\n\nTap <b>Browse Accounts</b> to get started.", parse_mode="HTML")
        return

    text = "📦 <b>Your Orders</b>\n━━━━━━━━━━━━━━━━━━━━\n\n"
    for o in orders[:10]:
        emoji = {"pending": "⏳", "approved": "✅", "rejected": "❌"}.get(o["status"], "❔")
        text += (
            f"{emoji} <b>Order #{o['id']}</b>\n"
            f"   💸 ₹{o['amount']:.2f} · {o['status'].upper()}\n"
            f"   🗓 {o['created_at'][:10]}\n\n"
        )
    await msg.answer(text, parse_mode="HTML")


@router.message(F.text == "📢 Channel")
async def channel_link(msg: Message):
    await msg.answer(
        f"📢 <b>Join our official channel!</b>\n\n"
        f"👉 {LOG_CHANNEL_LINK}\n\n"
        f"Get updates on new accounts, offers & more.",
        parse_mode="HTML", disable_web_page_preview=False
    )


@router.message(F.text == "💬 Support")
async def support(msg: Message):
    await msg.answer(
        f"💬 <b>Need Help?</b>\n\n"
        f"📩 Support Group: {SUPPORT_GROUP}\n"
        f"👤 Admin: {ADMIN_USERNAME}\n\n"
        f"We respond within 1-2 hours.",
        parse_mode="HTML"
    )


@router.message(F.text == "ℹ️ How It Works")
async def how_it_works(msg: Message):
    await msg.answer(
        "ℹ️ <b>How It Works</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "1️⃣ Browse accounts by country\n"
        "2️⃣ Choose & confirm purchase\n"
        "3️⃣ Scan UPI QR & pay exact amount\n"
        "4️⃣ Upload payment screenshot\n"
        "5️⃣ Tap 'Notify Admin'\n"
        "6️⃣ Admin verifies & approves\n"
        "7️⃣ Tap <b>Reveal Account Details</b>\n"
        "8️⃣ Login with the account\n"
        "9️⃣ Tap <b>Get Latest OTP</b> — bot sends it instantly!\n\n"
        "✅ <b>Safe · Fast · Auto OTP</b>",
        parse_mode="HTML"
    )
