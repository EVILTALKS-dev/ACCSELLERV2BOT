"""
Session String Generator
========================
Isko locally run karo (Railway pe nahi).
Yeh script ek Telethon session string generate karega
jo tum bot mein "Add Account" step mein paste kar sakte ho.

Usage:
    pip install telethon python-dotenv
    python session_gen.py
"""

import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession

# Apna API ID aur API Hash dalo (my.telegram.org se)
API_ID   = int(input("Enter API_ID: ").strip())
API_HASH = input("Enter API_HASH: ").strip()
PHONE    = input("Enter phone number (with country code, e.g. +917001234567): ").strip()


async def generate():
    client = TelegramClient(StringSession(), API_ID, API_HASH)
    await client.start(phone=PHONE)
    session_string = client.session.save()
    await client.disconnect()
    print("\n" + "="*60)
    print("✅ SESSION STRING (bot mein paste karo):")
    print("="*60)
    print(session_string)
    print("="*60 + "\n")
    print("⚠️  Ise kisi ko mat dikhao — yeh tumhara account access hai!")

asyncio.run(generate())
