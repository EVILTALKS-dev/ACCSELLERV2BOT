from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Filter

import database as db
from keyboards import (
    admin_main_kb, user_main_kb, cancel_kb,
    admin_account_kb, admin_approve_kb, country_select_kb, user_ban_kb
)
from config import ADMIN_IDS
from utils.logger import log_sale

router = Router()


class IsAdmin(Filter):
    async def __call__(self, obj) -> bool:
        return obj.from_user.id in ADMIN_IDS


# ── States ─────────────────────────────────────────────────────────────────────

class AddAccState(StatesGroup):
    number      = State()
    country     = State()
    price       = State()
    password    = State()
    twofa       = State()
    session_str = State()
    description = State()


class EditPriceState(StatesGroup):
    price = State()


class EditSessionState(StatesGroup):
    session = State()


class BroadcastState(StatesGroup):
    message = State()


# ── Admin Entry ────────────────────────────────────────────────────────────────

@router.message(IsAdmin(), F.text == "🏠 User Mode")
async def user_mode(msg: Message):
    await msg.answer("👤 User mode.", reply_markup=user_main_kb())


# ── Add Account ────────────────────────────────────────────────────────────────

@router.message(IsAdmin(), F.text == "➕ Add Account")
async def add_start(msg: Message, state: FSMContext):
    await state.set_state(AddAccState.number)
    await msg.answer(
        "➕ <b>Add Account — Step 1/7</b>\n\n"
        "📱 Phone number enter karo (with country code):\n"
        "Example: <code>+917001234567</code>",
        parse_mode="HTML", reply_markup=cancel_kb()
    )


@router.message(IsAdmin(), AddAccState.number)
async def add_number(msg: Message, state: FSMContext):
    if msg.text == "❌ Cancel":
        await state.clear()
        return await msg.answer("Cancelled.", reply_markup=admin_main_kb())
    await state.update_data(number=msg.text.strip())
    await state.set_state(AddAccState.country)
    await msg.answer(
        "✅ Number saved!\n\n"
        "<b>Step 2/7 — Country select karo:</b>",
        parse_mode="HTML",
        reply_markup=country_select_kb()
    )


@router.callback_query(IsAdmin(), F.data.startswith("set_country:"))
async def add_country(cq: CallbackQuery, state: FSMContext):
    parts = cq.data.split(":")
    country = parts[1]
    flag = parts[2]
    await state.update_data(country=country, country_flag=flag)
    await state.set_state(AddAccState.price)
    await cq.message.edit_text(
        f"✅ Country: {flag} {country}\n\n"
        f"<b>Step 3/7 — Price enter karo (₹):</b>\n"
        f"Example: <code>199</code>",
        parse_mode="HTML"
    )
    await cq.answer()


@router.message(IsAdmin(), AddAccState.price)
async def add_price(msg: Message, state: FSMContext):
    if msg.text == "❌ Cancel":
        await state.clear()
        return await msg.answer("Cancelled.", reply_markup=admin_main_kb())
    try:
        price = float(msg.text.strip())
    except ValueError:
        return await msg.answer("❌ Valid number enter karo. Example: <code>199</code>", parse_mode="HTML")
    await state.update_data(price=price)
    await state.set_state(AddAccState.password)
    await msg.answer(
        f"✅ Price: ₹{price:.2f}\n\n"
        f"<b>Step 4/7 — Account password</b> (ya <code>skip</code>):",
        parse_mode="HTML"
    )


@router.message(IsAdmin(), AddAccState.password)
async def add_password(msg: Message, state: FSMContext):
    if msg.text == "❌ Cancel":
        await state.clear()
        return await msg.answer("Cancelled.", reply_markup=admin_main_kb())
    pw = "" if msg.text.strip().lower() == "skip" else msg.text.strip()
    await state.update_data(password=pw)
    await state.set_state(AddAccState.twofa)
    await msg.answer(
        f"✅ Password saved!\n\n"
        f"<b>Step 5/7 — 2FA password</b> (ya <code>skip</code>):",
        parse_mode="HTML"
    )


@router.message(IsAdmin(), AddAccState.twofa)
async def add_twofa(msg: Message, state: FSMContext):
    if msg.text == "❌ Cancel":
        await state.clear()
        return await msg.answer("Cancelled.", reply_markup=admin_main_kb())
    twofa = "" if msg.text.strip().lower() == "skip" else msg.text.strip()
    await state.update_data(twofa=twofa)
    await state.set_state(AddAccState.session_str)
    await msg.answer(
        f"✅ 2FA saved!\n\n"
        f"<b>Step 6/7 — Telethon Session String</b>\n"
        f"(Auto OTP ke liye zaroori)\n\n"
        f"Session string kaise banate hain:\n"
        f"1. <code>python session_gen.py</code> chalaao\n"
        f"2. Number se login karo\n"
        f"3. Generated string yahan paste karo\n\n"
        f"Ya <code>skip</code> karo (manual OTP fallback hoga):",
        parse_mode="HTML"
    )


@router.message(IsAdmin(), AddAccState.session_str)
async def add_session(msg: Message, state: FSMContext):
    if msg.text == "❌ Cancel":
        await state.clear()
        return await msg.answer("Cancelled.", reply_markup=admin_main_kb())
    sess = "" if msg.text.strip().lower() == "skip" else msg.text.strip()
    await state.update_data(session_str=sess)
    await state.set_state(AddAccState.description)
    await msg.answer(
        f"<b>Step 7/7 — Description</b> (ya <code>skip</code>):\n"
        f"Example: <i>Fresh account, 2024, India verified</i>",
        parse_mode="HTML"
    )


@router.message(IsAdmin(), AddAccState.description)
async def add_done(msg: Message, state: FSMContext):
    if msg.text == "❌ Cancel":
        await state.clear()
        return await msg.answer("Cancelled.", reply_markup=admin_main_kb())
    desc = "" if msg.text.strip().lower() == "skip" else msg.text.strip()
    d = await state.get_data()
    await state.clear()

    await db.add_account(
        number=d["number"],
        price=d["price"],
        country=d["country"],
        country_flag=d["country_flag"],
        password=d.get("password", ""),
        twofa=d.get("twofa", ""),
        session_str=d.get("session_str", ""),
        description=desc
    )

    session_status = "✅ Session added" if d.get("session_str") else "⚠️ No session (manual OTP)"
    await msg.answer(
        f"✅ <b>Account Added!</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📱 <code>{d['number']}</code>\n"
        f"{d['country_flag']} {d['country']} · ₹{d['price']:.2f}\n"
        f"🔑 Pass: {d.get('password') or 'N/A'}\n"
        f"🔐 2FA: {d.get('twofa') or 'N/A'}\n"
        f"📡 {session_status}\n"
        f"📝 {desc or 'No description'}",
        parse_mode="HTML",
        reply_markup=admin_main_kb()
    )


# ── View All Accounts ──────────────────────────────────────────────────────────

@router.message(IsAdmin(), F.text == "📋 View Accounts")
async def view_accounts(msg: Message):
    accounts = await db.get_all_accounts()
    if not accounts:
        return await msg.answer("📋 Koi account nahi hai abhi.")

    avail = [a for a in accounts if a["status"] == "available"]
    sold  = [a for a in accounts if a["status"] == "sold"]

    await msg.answer(
        f"📋 <b>All Accounts</b>\n"
        f"🟢 Available: {len(avail)} · 🔴 Sold: {len(sold)}",
        parse_mode="HTML"
    )

    for acc in accounts[:20]:
        emoji = "🟢" if acc["status"] == "available" else "🔴"
        sess  = "📡 Session ✅" if acc.get("session_str") else "📡 No Session"
        text  = (
            f"{emoji} <b>#{acc['id']}</b> · {acc['country_flag']} {acc['country']}\n"
            f"📱 <code>{acc['number']}</code>\n"
            f"💰 ₹{acc['price']:.2f} · {acc['status'].upper()}\n"
            f"🔑 {acc['password'] or 'N/A'} · 🔐 {acc['twofa'] or 'N/A'}\n"
            f"{sess}\n"
            f"📝 {acc['description'] or 'No desc'}"
        )
        await msg.answer(text, parse_mode="HTML", reply_markup=admin_account_kb(acc["id"]))


# ── Account Actions ────────────────────────────────────────────────────────────

@router.callback_query(IsAdmin(), F.data.startswith("del_acc:"))
async def del_acc(cq: CallbackQuery):
    acc_id = int(cq.data.split(":")[1])
    await db.delete_account(acc_id)
    await cq.message.edit_text(f"🗑 Account #{acc_id} deleted.")


@router.callback_query(IsAdmin(), F.data.startswith("edit_price:"))
async def edit_price_start(cq: CallbackQuery, state: FSMContext):
    acc_id = int(cq.data.split(":")[1])
    await state.set_state(EditPriceState.price)
    await state.update_data(acc_id=acc_id)
    await cq.message.answer(f"✏️ Account #{acc_id} ka naya price enter karo:", reply_markup=cancel_kb())
    await cq.answer()


@router.message(IsAdmin(), EditPriceState.price)
async def edit_price_done(msg: Message, state: FSMContext):
    if msg.text == "❌ Cancel":
        await state.clear()
        return await msg.answer("Cancelled.", reply_markup=admin_main_kb())
    try:
        price = float(msg.text.strip())
    except ValueError:
        return await msg.answer("❌ Valid number enter karo.")
    d = await state.get_data()
    await state.clear()
    await db.update_account(d["acc_id"], price=price)
    await msg.answer(f"✅ Price updated: ₹{price:.2f}", reply_markup=admin_main_kb())


@router.callback_query(IsAdmin(), F.data.startswith("edit_session:"))
async def edit_session_start(cq: CallbackQuery, state: FSMContext):
    acc_id = int(cq.data.split(":")[1])
    await state.set_state(EditSessionState.session)
    await state.update_data(acc_id=acc_id)
    await cq.message.answer(
        f"🔑 Account #{acc_id} ka naya session string paste karo:\n"
        f"(ya <code>clear</code> type karo remove karne ke liye)",
        parse_mode="HTML",
        reply_markup=cancel_kb()
    )
    await cq.answer()


@router.message(IsAdmin(), EditSessionState.session)
async def edit_session_done(msg: Message, state: FSMContext):
    if msg.text == "❌ Cancel":
        await state.clear()
        return await msg.answer("Cancelled.", reply_markup=admin_main_kb())
    sess = "" if msg.text.strip().lower() == "clear" else msg.text.strip()
    d = await state.get_data()
    await state.clear()
    await db.update_account(d["acc_id"], session_str=sess)
    status = "✅ Session updated!" if sess else "✅ Session removed!"
    await msg.answer(status, reply_markup=admin_main_kb())


# ── Approve / Reject ───────────────────────────────────────────────────────────

@router.callback_query(IsAdmin(), F.data.startswith("admin_approve:"))
async def approve(cq: CallbackQuery, bot: Bot):
    order_id = int(cq.data.split(":")[1])
    order = await db.get_order(order_id)
    if not order or order["status"] != "pending":
        return await cq.answer("⚠️ Already processed.", show_alert=True)

    acc = await db.get_account(order["account_id"])
    await db.approve_order(order_id)
    await db.mark_account_sold(order["account_id"], order["user_id"])
    await db.update_user_stats(order["user_id"], order["amount"])

    session_id = await db.create_otp_session(order_id, order["user_id"], order["account_id"])

    from keyboards import reveal_number_kb
    try:
        await bot.send_message(
            order["user_id"],
            f"🎉 <b>Payment Approved!</b>\n\n"
            f"Order #{order_id} · ₹{order['amount']:.2f}\n"
            f"{acc['country_flag']} {acc['country']}\n\n"
            f"👇 Account details dekhne ke liye button dabao:",
            parse_mode="HTML",
            reply_markup=reveal_number_kb(order_id, session_id)
        )
    except Exception:
        pass

    await log_sale(
        bot, acc["number"], order["amount"],
        acc["country"], acc["country_flag"],
        order["user_id"], order["username"], order_id
    )

    await cq.message.edit_text(
        f"✅ <b>Order #{order_id} Approved!</b>\n"
        f"📱 {acc['number']} delivered.\n"
        f"📢 Log channel mein bhej diya.",
        parse_mode="HTML"
    )


@router.callback_query(IsAdmin(), F.data.startswith("admin_reject:"))
async def reject(cq: CallbackQuery, bot: Bot):
    order_id = int(cq.data.split(":")[1])
    order = await db.get_order(order_id)
    if not order or order["status"] != "pending":
        return await cq.answer("⚠️ Already processed.", show_alert=True)

    await db.reject_order(order_id)
    try:
        await bot.send_message(
            order["user_id"],
            f"❌ <b>Order #{order_id} Rejected</b>\n\n"
            f"Payment verify nahi ho payi.\n"
            f"Support se contact karo: /start",
            parse_mode="HTML"
        )
    except Exception:
        pass
    await cq.message.edit_text(f"❌ Order #{order_id} rejected.")


@router.callback_query(IsAdmin(), F.data.startswith("admin_view_ss:"))
async def view_screenshot(cq: CallbackQuery, bot: Bot):
    order_id = int(cq.data.split(":")[1])
    order = await db.get_order(order_id)
    if not order or not order.get("screenshot"):
        return await cq.answer("📸 Screenshot nahi mila!", show_alert=True)
    await bot.send_photo(
        cq.from_user.id,
        order["screenshot"],
        caption=f"📸 Screenshot — Order #{order_id}\n👤 @{order['username'] or 'N/A'}"
    )
    await cq.answer()


# ── Pending Orders ─────────────────────────────────────────────────────────────

@router.message(IsAdmin(), F.text == "⏳ Pending Orders")
async def pending(msg: Message):
    orders = await db.get_pending_orders()
    if not orders:
        return await msg.answer("✅ Koi pending order nahi hai!")
    for o in orders:
        acc = await db.get_account(o["account_id"])
        await msg.answer(
            f"⏳ <b>Order #{o['id']}</b>\n"
            f"👤 @{o['username'] or 'N/A'} (<code>{o['user_id']}</code>)\n"
            f"📱 <code>{acc['number'] if acc else 'N/A'}</code>\n"
            f"{acc['country_flag'] if acc else ''} {acc['country'] if acc else ''}\n"
            f"💸 ₹{o['amount']:.2f}\n"
            f"🗓 {o['created_at'][:19]}\n"
            f"📸 Screenshot: {'✅' if o.get('screenshot') else '❌'}",
            parse_mode="HTML",
            reply_markup=admin_approve_kb(o["id"])
        )


# ── Statistics ─────────────────────────────────────────────────────────────────

@router.message(IsAdmin(), F.text == "📊 Statistics")
async def stats(msg: Message):
    s = await db.get_stats()
    await msg.answer(
        f"📊 <b>Bot Statistics</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📦 Total Accounts : {s['total_accounts']}\n"
        f"🟢 Available      : {s['available']}\n"
        f"🔴 Sold           : {s['sold']}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"👥 Total Users    : {s['users']}\n"
        f"💰 Total Revenue  : ₹{s['revenue']:.2f}\n"
        f"⏳ Pending Orders : {s['pending']}\n"
        f"━━━━━━━━━━━━━━━━━━━━",
        parse_mode="HTML"
    )


# ── All Users ──────────────────────────────────────────────────────────────────

@router.message(IsAdmin(), F.text == "👥 All Users")
async def all_users(msg: Message):
    users = await db.get_all_users()
    if not users:
        return await msg.answer("👥 Koi user nahi hai.")
    text = f"👥 <b>All Users ({len(users)})</b>\n━━━━━━━━━━━━━━━━━━━━\n\n"
    for u in users[:30]:
        banned = " 🚫" if u.get("is_banned") else ""
        text += (
            f"• @{u['username'] or 'N/A'}{banned}\n"
            f"  <code>{u['user_id']}</code> · ₹{u['total_spent']:.0f} · {u['total_orders']} orders\n"
        )
    await msg.answer(text, parse_mode="HTML")


# ── Order History ──────────────────────────────────────────────────────────────

@router.message(IsAdmin(), F.text == "📜 Order History")
async def order_history(msg: Message):
    orders = await db.get_all_orders(50)
    if not orders:
        return await msg.answer("📜 Koi order nahi hai.")
    text = f"📜 <b>Last 50 Orders</b>\n━━━━━━━━━━━━━━━━━━━━\n\n"
    for o in orders:
        e = {"pending": "⏳", "approved": "✅", "rejected": "❌"}.get(o["status"], "❔")
        text += f"{e} #{o['id']} · @{o['username'] or 'N/A'} · ₹{o['amount']:.2f} · {o['created_at'][:10]}\n"
    await msg.answer(text, parse_mode="HTML")


# ── OTP Sessions ───────────────────────────────────────────────────────────────

@router.message(IsAdmin(), F.text == "🔐 OTP Sessions")
async def otp_sessions(msg: Message):
    sessions = await db.get_waiting_otp_sessions()
    if not sessions:
        return await msg.answer("🔐 Koi active OTP session nahi hai.")
    from keyboards import admin_otp_kb
    for s in sessions:
        acc = await db.get_account(s["account_id"])
        await msg.answer(
            f"🔐 <b>OTP Session #{s['id']}</b>\n"
            f"📱 <code>{acc['number'] if acc else 'N/A'}</code>\n"
            f"👤 User: <code>{s['user_id']}</code>\n"
            f"📡 Session: {'✅' if acc and acc.get('session_str') else '❌ Missing'}\n"
            f"🗓 {s['created_at'][:19]}",
            parse_mode="HTML",
            reply_markup=admin_otp_kb(s["id"])
        )


# ── Broadcast ──────────────────────────────────────────────────────────────────

@router.message(IsAdmin(), F.text == "📢 Broadcast")
async def broadcast_start(msg: Message, state: FSMContext):
    await state.set_state(BroadcastState.message)
    await msg.answer(
        "📢 <b>Broadcast</b>\n\nSab users ko bhejne ke liye message type karo:",
        parse_mode="HTML", reply_markup=cancel_kb()
    )


@router.message(IsAdmin(), BroadcastState.message)
async def broadcast_send(msg: Message, state: FSMContext, bot: Bot):
    if msg.text == "❌ Cancel":
        await state.clear()
        return await msg.answer("Cancelled.", reply_markup=admin_main_kb())
    await state.clear()
    users = await db.get_all_users()
    sent = 0
    for u in users:
        try:
            await bot.send_message(u["user_id"], f"📢 <b>Message from Admin:</b>\n\n{msg.text}", parse_mode="HTML")
            sent += 1
        except Exception:
            pass
    await msg.answer(f"✅ Broadcast sent to {sent}/{len(users)} users.", reply_markup=admin_main_kb())


# ── Ban/Unban ──────────────────────────────────────────────────────────────────

@router.callback_query(IsAdmin(), F.data.startswith("ban:"))
async def ban(cq: CallbackQuery):
    user_id = int(cq.data.split(":")[1])
    await db.ban_user(user_id)
    await cq.answer(f"🚫 User {user_id} banned!", show_alert=True)


@router.callback_query(IsAdmin(), F.data.startswith("unban:"))
async def unban(cq: CallbackQuery):
    user_id = int(cq.data.split(":")[1])
    await db.unban_user(user_id)
    await cq.answer(f"✅ User {user_id} unbanned!", show_alert=True)
