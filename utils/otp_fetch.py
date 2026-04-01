import asyncio, re
from config import API_ID, API_HASH


async def auto_fetch_otp(session_str: str, timeout: int = 90) -> str | None:
    """
    Connect to the sold account's Telethon session.
    Wait for a Telegram OTP message and return the code.
    """
    if not API_ID or not API_HASH or not session_str:
        return None

    try:
        from telethon import TelegramClient, events
        from telethon.sessions import StringSession
    except ImportError:
        return None

    found = {"code": None}
    otp_event = asyncio.Event()

    try:
        client = TelegramClient(StringSession(session_str), API_ID, API_HASH)
        await client.connect()

        # ── Check recent saved messages / service messages first ──────────────
        async for msg in client.iter_messages(limit=10, entity="me"):
            text = msg.text or ""
            m = re.search(r'\b(\d{4,6})\b', text)
            if m:
                found["code"] = m.group(1)
                otp_event.set()
                break

        if not otp_event.is_set():
            @client.on(events.NewMessage(incoming=True))
            async def handler(event):
                text = event.message.text or ""
                m = re.search(r'\b(\d{4,6})\b', text)
                if m:
                    found["code"] = m.group(1)
                    otp_event.set()

            await asyncio.wait_for(otp_event.wait(), timeout=timeout)

        await client.disconnect()
        return found["code"]

    except asyncio.TimeoutError:
        try: await client.disconnect()
        except Exception: pass
        return None
    except Exception:
        return None


async def get_session_string(phone: str, password: str, api_id: int, api_hash: str) -> str | None:
    """
    Admin tool: Login to account and generate a session string.
    Returns the string session, or None on failure.
    """
    try:
        from telethon import TelegramClient
        from telethon.sessions import StringSession
        client = TelegramClient(StringSession(), api_id, api_hash)
        await client.connect()
        # This is used only by admin manually via helper script
        session = client.session.save()
        await client.disconnect()
        return session
    except Exception:
        return None
