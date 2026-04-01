from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message, BufferedInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

import database as db
from utils.qr import make_upi_qr
from keyboards import payment_kb, screenshot_done_kb, admin_approve_kb
from config import ADMIN_IDS, UPI_ID

router = Router()


class ScreenshotState(StatesGroup):
    waiting = State()


@router.callback_query(F.data.startswith("confirm_pay:"))
async def confirm_pay(cq: CallbackQuery, bot: Bot):
    account_id = int(cq.data.split(":")[1])
    acc = await db.get_account(account_id)
    if not acc or acc["status"] != "available":
        await cq.answer("❌ Account no longer available!", show_alert=True)
        return

    u = cq.from_user
    order_id = await db.create_order(u.id, u.username or "", u.full_name or "", account_id, acc["price"])
    qr_bytes, exact = make_upi_qr(acc["price"], order_id)

    caption = (
        f"💳 <b>Payment — Order #{order_id}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"{acc['country_flag']} <b>{acc['country']} Account</b>\n"
        f"💰 Pay EXACTLY: <b>₹{exact:.2f}</b>\n"
        f"🏦 UPI: <code>{UPI_ID}</code>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"⚠️ <b>Important:</b>\n"
        f"• Pay the exact amount (unique paise = your ID)\n"
        f"• Screenshot leke upload karo neeche\n"
        f"• Admin 5-10 min mein verify karega\n\n"
        f"👇 Payment ke baad screenshot upload karo:"
    )
    qr_file = BufferedInputFile(qr_bytes, filename="pay.png")
    await cq.message.answer_photo(
        photo=qr_file,
        caption=caption,
        parse_mode="HTML",
        reply_markup=payment_kb(order_id)
    )
    await cq.message.delete()

    for aid in ADMIN_IDS:
        try:
            await bot.send_message(
                aid,
                f"🛎 <b>New Order!</b>\n\n"
                f"👤 @{u.username or 'N/A'} (<code>{u.id}</code>)\n"
                f"{acc['country_flag']} {acc['country']} · <code>{acc['number']}</code>\n"
                f"💸 ₹{exact:.2f} · Order #{order_id}",
                parse_mode="HTML"
            )
        except Exception:
            pass


@router.callback_query(F.data.startswith("upload_ss:"))
async def upload_screenshot(cq: CallbackQuery, state: FSMContext):
    order_id = int(cq.data.split(":")[1])
    order = await db.get_order(order_id)
    if not order or order["user_id"] != cq.from_user.id:
        await cq.answer("❌ Not your order!", show_alert=True)
        return
    await state.set_state(ScreenshotState.waiting)
    await state.update_data(order_id=order_id)
    await cq.message.answer(
        "📸 <b>Send your payment screenshot now</b>\n\n"
        "Photo ke roop mein bhejo (file nahi)",
        parse_mode="HTML"
    )
    await cq.answer()


@router.message(ScreenshotState.waiting, F.photo)
async def receive_screenshot(msg: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    order_id = data["order_id"]
    await state.clear()

    file_id = msg.photo[-1].file_id
    await db.set_order_screenshot(order_id, file_id)

    await msg.answer(
        f"✅ <b>Screenshot received!</b>\n\n"
        f"Order #{order_id} — Ab admin ko notify karo.",
        parse_mode="HTML",
        reply_markup=screenshot_done_kb(order_id)
    )


@router.message(ScreenshotState.waiting)
async def wrong_ss_format(msg: Message):
    await msg.answer("❌ Photo bhejo, file ya text nahi!")


@router.callback_query(F.data.startswith("paid_notify:"))
async def paid_notify(cq: CallbackQuery, bot: Bot):
    order_id = int(cq.data.split(":")[1])
    order = await db.get_order(order_id)
    if not order or order["user_id"] != cq.from_user.id:
        await cq.answer("❌ Not your order!", show_alert=True)
        return
    if order["status"] != "pending":
        await cq.answer("⚠️ Order already processed.", show_alert=True)
        return

    acc = await db.get_account(order["account_id"])
    await cq.message.edit_caption(
        caption=(
            f"⏳ <b>Verification Pending</b>\n\n"
            f"Order #{order_id} — Admin ko notify kar diya gaya!\n"
            f"Usually 5-10 minutes lagte hain.\n\n"
            f"Approval ke baad account details yahan milenge. 👇"
        ),
        parse_mode="HTML"
    )

    for aid in ADMIN_IDS:
        try:
            notif = await bot.send_message(
                aid,
                f"🔔 <b>PAYMENT CLAIMED — Action Required!</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"🔖 Order: #{order_id}\n"
                f"👤 @{order['username'] or 'N/A'} (<code>{order['user_id']}</code>)\n"
                f"📱 <code>{acc['number'] if acc else 'N/A'}</code>\n"
                f"{acc['country_flag'] if acc else ''} {acc['country'] if acc else ''}\n"
                f"💸 ₹{order['amount']:.2f}\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"Screenshot dekho → Approve ya Reject karo",
                parse_mode="HTML",
                reply_markup=admin_approve_kb(order_id)
            )
        except Exception:
            pass


@router.callback_query(F.data.startswith("cancel_order:"))
async def cancel_order(cq: CallbackQuery):
    order_id = int(cq.data.split(":")[1])
    order = await db.get_order(order_id)
    if not order or order["user_id"] != cq.from_user.id:
        await cq.answer("❌ Not your order!", show_alert=True)
        return
    if order["status"] != "pending":
        await cq.answer("⚠️ Cannot cancel processed order.", show_alert=True)
        return
    await db.reject_order(order_id)
    try:
        await cq.message.edit_caption(
            caption=f"❌ Order #{order_id} cancelled.",
            parse_mode="HTML"
        )
    except Exception:
        await cq.message.answer(f"❌ Order #{order_id} cancelled.")
