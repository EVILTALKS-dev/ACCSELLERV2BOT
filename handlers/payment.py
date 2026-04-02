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


# ── Confirm Pay → Generate QR ─────────────────────────────────────────────────

@router.callback_query(F.data.startswith("confirm_pay:"))
async def confirm_pay(cq: CallbackQuery, bot: Bot):
    account_id = int(cq.data.split(":")[1])
    acc = await db.get_account(account_id)
    if not acc or acc["status"] != "available":
        await cq.answer("❌ Account no longer available!", show_alert=True)
        return

    u = cq.from_user
    order_id = await db.create_order(
        u.id, u.username or "", u.full_name or "", account_id, acc["price"]
    )
    qr_bytes, exact = make_upi_qr(acc["price"], order_id)

    caption = (
        f"💳 <b>Payment — Order #{order_id}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"{acc['country_flag']} <b>{acc['country']} Account</b>\n"
        f"💰 Pay EXACTLY: <b>₹{exact:.2f}</b>\n"
        f"🏦 UPI: <code>{UPI_ID}</code>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"⚠️ <b>Steps:</b>\n"
        f"1. Exact amount pay karo\n"
        f"2. Screenshot lo\n"
        f"3. Neeche button dabao aur upload karo\n\n"
        f"👇 Screenshot upload karo:"
    )
    qr_file = BufferedInputFile(qr_bytes, filename="pay.png")
    sent = await cq.message.answer_photo(
        photo=qr_file,
        caption=caption,
        parse_mode="HTML",
        reply_markup=payment_kb(order_id)
    )
    try:
        await cq.message.delete()
    except Exception:
        pass

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


# ── Upload Screenshot Button ──────────────────────────────────────────────────

@router.callback_query(F.data.startswith("upload_ss:"))
async def upload_screenshot_prompt(cq: CallbackQuery, state: FSMContext):
    order_id = int(cq.data.split(":")[1])
    order = await db.get_order(order_id)

    if not order:
        await cq.answer("❌ Order not found!", show_alert=True)
        return
    if order["user_id"] != cq.from_user.id:
        await cq.answer("❌ Not your order!", show_alert=True)
        return
    if order["status"] != "pending":
        await cq.answer("⚠️ Order already processed.", show_alert=True)
        return

    await state.set_state(ScreenshotState.waiting)
    await state.update_data(order_id=order_id, chat_id=cq.message.chat.id)

    await cq.message.answer(
        "📸 <b>Payment Screenshot Bhejo</b>\n\n"
        "• Gallery se photo select karo\n"
        "• Direct photo send karo (file nahi)\n"
        "• Sirf ek photo bhejo",
        parse_mode="HTML"
    )
    await cq.answer()


# ── Receive Screenshot Photo ──────────────────────────────────────────────────

@router.message(ScreenshotState.waiting, F.photo)
async def receive_screenshot(msg: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    order_id = data.get("order_id")
    await state.clear()

    if not order_id:
        await msg.answer("❌ Session expire ho gayi. Dobara try karo.")
        return

    # Save highest quality photo file_id
    file_id = msg.photo[-1].file_id
    await db.set_order_screenshot(order_id, file_id)

    await msg.answer(
        f"✅ <b>Screenshot Received!</b>\n\n"
        f"🔖 Order #{order_id}\n"
        f"Ab admin ko notify karo 👇",
        parse_mode="HTML",
        reply_markup=screenshot_done_kb(order_id)
    )


# ── Wrong format handler ──────────────────────────────────────────────────────

@router.message(ScreenshotState.waiting, F.document)
async def screenshot_wrong_doc(msg: Message):
    await msg.answer(
        "❌ <b>File mat bhejo!</b>\n\n"
        "📸 Photo as image bhejo — gallery se select karo.",
        parse_mode="HTML"
    )


@router.message(ScreenshotState.waiting, ~F.photo)
async def screenshot_wrong_format(msg: Message):
    await msg.answer(
        "❌ <b>Sirf Photo bhejo!</b>\n\n"
        "Gallery se screenshot select karke send karo.",
        parse_mode="HTML"
    )


# ── Notify Admin ──────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("paid_notify:"))
async def paid_notify(cq: CallbackQuery, bot: Bot):
    order_id = int(cq.data.split(":")[1])
    order = await db.get_order(order_id)

    if not order:
        await cq.answer("❌ Order not found!", show_alert=True)
        return
    if order["user_id"] != cq.from_user.id:
        await cq.answer("❌ Not your order!", show_alert=True)
        return
    if order["status"] != "pending":
        await cq.answer("⚠️ Already processed.", show_alert=True)
        return
    if not order.get("screenshot"):
        await cq.answer(
            "❌ Pehle screenshot upload karo!\nNeeche 'Upload Screenshot' button dabao.",
            show_alert=True
        )
        return

    acc = await db.get_account(order["account_id"])

    try:
        await cq.message.edit_caption(
            caption=(
                f"⏳ <b>Verification Pending</b>\n\n"
                f"🔖 Order #{order_id}\n"
                f"Admin ko notify kar diya gaya!\n"
                f"5-10 minutes mein approve hoga.\n\n"
                f"Approval ke baad yahan account details milenge. 👇"
            ),
            parse_mode="HTML"
        )
    except Exception:
        await cq.message.answer(
            f"⏳ <b>Admin ko notify kar diya!</b>\n\nOrder #{order_id} — 5-10 min wait karo.",
            parse_mode="HTML"
        )

    # Notify all admins with screenshot
    for aid in ADMIN_IDS:
        try:
            # Send screenshot first
            await bot.send_photo(
                aid,
                order["screenshot"],
                caption=(
                    f"🔔 <b>PAYMENT CLAIMED!</b>\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"🔖 Order: #{order_id}\n"
                    f"👤 @{order['username'] or 'N/A'} (<code>{order['user_id']}</code>)\n"
                    f"📱 <code>{acc['number'] if acc else 'N/A'}</code>\n"
                    f"{acc['country_flag'] if acc else ''} {acc['country'] if acc else ''}\n"
                    f"💸 ₹{order['amount']:.2f}\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"✅ Approve · ❌ Reject"
                ),
                parse_mode="HTML",
                reply_markup=admin_approve_kb(order_id)
            )
        except Exception:
            # Fallback without photo
            try:
                await bot.send_message(
                    aid,
                    f"🔔 <b>PAYMENT CLAIMED!</b>\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"🔖 Order: #{order_id}\n"
                    f"👤 @{order['username'] or 'N/A'} (<code>{order['user_id']}</code>)\n"
                    f"📱 <code>{acc['number'] if acc else 'N/A'}</code>\n"
                    f"💸 ₹{order['amount']:.2f}\n"
                    f"⚠️ Screenshot fetch karne mein error",
                    parse_mode="HTML",
                    reply_markup=admin_approve_kb(order_id)
                )
            except Exception:
                pass

    await cq.answer("✅ Admin ko notify kar diya!")


# ── Cancel Order ──────────────────────────────────────────────────────────────

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
            caption=f"❌ <b>Order #{order_id} Cancelled.</b>",
            parse_mode="HTML"
        )
    except Exception:
        await cq.message.answer(f"❌ Order #{order_id} cancelled.")
    await cq.answer("Order cancelled.")
