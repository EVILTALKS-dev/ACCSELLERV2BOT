from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

import database as db
from utils.otp_fetch import auto_fetch_otp
from utils.logger import log_otp
from keyboards import otp_kb

router = Router()


class ManualOTPState(StatesGroup):
    waiting = State()


@router.callback_query(F.data.startswith("reveal:"))
async def reveal_account(cq: CallbackQuery):
    order_id = int(cq.data.split(":")[1])
    order = await db.get_order(order_id)
    if not order or order["user_id"] != cq.from_user.id:
        await cq.answer("❌ Not your order!", show_alert=True)
        return
    if order["status"] != "approved":
        await cq.answer("⏳ Order not approved yet!", show_alert=True)
        return

    acc = await db.get_account(order["account_id"])
    if not acc:
        await cq.answer("❌ Account not found!", show_alert=True)
        return

    # Find OTP session
    sessions = await db.get_waiting_otp_sessions()
    session = next((s for s in sessions if s["order_id"] == order_id), None)
    if not session:
        # Try delivered sessions too
        import aiosqlite
        from config import DATABASE_URL
        async with aiosqlite.connect(DATABASE_URL) as db2:
            db2.row_factory = aiosqlite.Row
            async with db2.execute(
                "SELECT * FROM otp_sessions WHERE order_id=? ORDER BY id DESC LIMIT 1", (order_id,)
            ) as c:
                r = await c.fetchone()
                session = dict(r) if r else None

    text = (
        f"🎉 <b>Account Details</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📱 <b>Number:</b> <code>{acc['number']}</code>\n"
        f"🔑 <b>Password:</b> <code>{acc['password'] or 'Not set'}</code>\n"
        f"🔐 <b>2FA:</b> <code>{acc['twofa'] or 'Not set'}</code>\n"
        f"{acc['country_flag']} <b>Country:</b> {acc['country']}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"✅ Order #{order_id} · ₹{order['amount']:.2f}\n\n"
        f"👇 Login karo phir OTP ke liye button dabao:"
    )

    kb = otp_kb(session["id"]) if session else None
    await cq.message.answer(text, parse_mode="HTML", reply_markup=kb)
    await cq.answer()


@router.callback_query(F.data.startswith("get_otp:"))
async def get_otp(cq: CallbackQuery, bot: Bot):
    session_id = int(cq.data.split(":")[1])
    session = await db.get_otp_session(session_id)

    if not session:
        await cq.answer("❌ OTP session not found!", show_alert=True)
        return
    if session["user_id"] != cq.from_user.id:
        await cq.answer("❌ This OTP is not for you!", show_alert=True)
        return

    # Already delivered — show again
    if session["status"] == "delivered" and session["otp_code"]:
        await cq.answer(f"🔑 OTP: {session['otp_code']}", show_alert=True)
        acc = await db.get_account(session["account_id"])
        await bot.send_message(
            cq.from_user.id,
            f"🔐 <b>Your OTP</b>\n\n"
            f"📱 <code>{acc['number'] if acc else 'N/A'}</code>\n"
            f"🔑 <b><code>{session['otp_code']}</code></b>\n\n"
            f"⚡ Jaldi use karo — OTP expire ho jata hai!",
            parse_mode="HTML"
        )
        return

    acc = await db.get_account(session["account_id"])
    if not acc:
        await cq.answer("❌ Account not found!", show_alert=True)
        return

    # No session string — inform user
    if not acc.get("session_str"):
        await cq.answer(
            "⏳ OTP fetch ho raha hai... Admin se contact karo agar 5 min mein nahi aaya.",
            show_alert=True
        )
        from config import ADMIN_IDS
        for aid in ADMIN_IDS:
            try:
                await bot.send_message(
                    aid,
                    f"⚠️ <b>OTP Needed!</b>\n\n"
                    f"Account: <code>{acc['number']}</code>\n"
                    f"User: <code>{cq.from_user.id}</code>\n"
                    f"Session ID: #{session_id}\n\n"
                    f"Session string nahi hai! Manually bhejo.",
                    parse_mode="HTML",
                    reply_markup=__import__('keyboards').admin_otp_kb(session_id)
                )
            except Exception:
                pass
        return

    # Auto-fetch via Telethon
    await cq.answer("⏳ OTP fetch ho raha hai... (90 sec tak wait karo)", show_alert=True)

    status_msg = await bot.send_message(
        cq.from_user.id,
        f"🔄 <b>OTP Auto-Fetch...</b>\n\n"
        f"📱 <code>{acc['number']}</code>\n"
        f"⏳ Account ki inbox check ho rahi hai...\n\n"
        f"Abhi login karo taaki OTP trigger ho!",
        parse_mode="HTML"
    )

    otp_code = await auto_fetch_otp(acc["session_str"], timeout=90)

    if otp_code:
        await db.deliver_otp(session_id, otp_code)
        try:
            await bot.edit_message_text(
                f"✅ <b>OTP Delivered!</b>\n\n"
                f"📱 <code>{acc['number']}</code>\n"
                f"🔑 <b><code>{otp_code}</code></b>\n\n"
                f"⚡ Jaldi enter karo — 2 min mein expire!",
                chat_id=cq.from_user.id,
                message_id=status_msg.message_id,
                parse_mode="HTML"
            )
        except Exception:
            await bot.send_message(
                cq.from_user.id,
                f"🔑 OTP: <b><code>{otp_code}</code></b>",
                parse_mode="HTML"
            )

        order = await db.get_order(session["order_id"])
        await log_otp(bot, acc["number"], otp_code, cq.from_user.id, cq.from_user.username or "")
    else:
        try:
            await bot.edit_message_text(
                f"⚠️ <b>OTP Timeout (90s)</b>\n\n"
                f"Auto-fetch fail hua.\n\n"
                f"• Pehle number se login karo\n"
                f"• Phir dubara button dabao\n"
                f"• Ya support se contact karo",
                chat_id=cq.from_user.id,
                message_id=status_msg.message_id,
                parse_mode="HTML"
            )
        except Exception:
            pass

        from config import ADMIN_IDS
        for aid in ADMIN_IDS:
            try:
                await bot.send_message(
                    aid,
                    f"⚠️ <b>OTP Timeout!</b>\n"
                    f"Account: <code>{acc['number']}</code>\n"
                    f"User: <code>{cq.from_user.id}</code>\n"
                    f"Session ID: #{session_id}",
                    parse_mode="HTML",
                    reply_markup=__import__('keyboards').admin_otp_kb(session_id)
                )
            except Exception:
                pass


# Manual OTP delivery (admin fallback)
@router.callback_query(F.data.startswith("manual_otp:"))
async def manual_otp_start(cq: CallbackQuery, state: FSMContext):
    from config import ADMIN_IDS
    if cq.from_user.id not in ADMIN_IDS:
        await cq.answer("❌ Not authorized!", show_alert=True)
        return
    session_id = int(cq.data.split(":")[1])
    await state.set_state(ManualOTPState.waiting)
    await state.update_data(session_id=session_id)
    await cq.message.answer(f"🔐 Session #{session_id} ke liye OTP enter karo:")
    await cq.answer()


@router.message(ManualOTPState.waiting)
async def manual_otp_done(msg: Message, state: FSMContext, bot: Bot):
    from config import ADMIN_IDS
    if msg.from_user.id not in ADMIN_IDS:
        return
    otp_code = msg.text.strip()
    data = await state.get_data()
    session_id = data["session_id"]
    await state.clear()

    session = await db.get_otp_session(session_id)
    if not session:
        await msg.answer("❌ Session not found!")
        return

    await db.deliver_otp(session_id, otp_code)
    acc = await db.get_account(session["account_id"])

    try:
        await bot.send_message(
            session["user_id"],
            f"🔐 <b>Your OTP</b>\n\n"
            f"📱 <code>{acc['number'] if acc else 'N/A'}</code>\n"
            f"🔑 <b><code>{otp_code}</code></b>\n\n"
            f"⚡ Jaldi enter karo — expire ho jata hai!",
            parse_mode="HTML"
        )
    except Exception:
        pass

    await log_otp(bot, acc["number"] if acc else "N/A", otp_code, session["user_id"], "")
    await msg.answer(f"✅ OTP <code>{otp_code}</code> user ko bhej diya!", parse_mode="HTML")
