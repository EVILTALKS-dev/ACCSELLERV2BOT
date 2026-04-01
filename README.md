# 🤖 EVILTALKS AccountBot

> Professional Telegram Account Seller Bot — Auto OTP · UPI Payment · Admin Panel

---

## ✨ Features

| Feature | Details |
|---|---|
| 🌍 Country Filter | Browse accounts by country with stock count |
| 💳 UPI QR Payment | Unique paise per order for easy identification |
| 📸 Screenshot Upload | User uploads payment proof |
| ✅ Admin Approval | One-tap approve/reject |
| 🔐 Auto OTP | Telethon session se automatic OTP delivery |
| 📢 Log Channel | Every sale logged (half number only) |
| 📣 Broadcast | Message all users at once |
| 🚫 Ban/Unban | User management |
| 📊 Statistics | Revenue, stock, users dashboard |

---

## 🚀 Deploy on Railway

### Step 1 — Bot Token
- [@BotFather](https://t.me/BotFather) → `/newbot` → Token copy karo

### Step 2 — API ID & Hash (Auto OTP ke liye)
1. [my.telegram.org](https://my.telegram.org) pe jao
2. Login karo → **API Development Tools**
3. `api_id` aur `api_hash` copy karo

### Step 3 — GitHub Pe Push Karo
```bash
git init
git add .
git commit -m "EVILTALKS AccountBot"
git branch -M main
git remote add origin https://github.com/YOURUSERNAME/accountbot.git
git push -u origin main
```

### Step 4 — Railway Setup
1. [railway.app](https://railway.app) → **New Project** → Deploy from GitHub
2. Apna repo select karo
3. **Variables** tab mein yeh sab add karo 👇

---

## ⚙️ Environment Variables (Copy-Paste Ready)

| Variable | Value |
|---|---|
| `BOT_TOKEN` | BotFather se naya token |
| `ADMIN_IDS` | `8066849679` |
| `ADMIN_USERNAME` | `@EVILTALKS` |
| `LOG_CHANNEL_ID` | `-1003773215198` |
| `LOG_CHANNEL_LINK` | `https://t.me/ACCOUNT_SELLER_PRO` |
| `SUPPORT_GROUP` | `@ACCSPRO_SUPPORT` |
| `UPI_ID` | `das20@fam` |
| `UPI_NAME` | `EVILTALKS Store` |
| `DATABASE_URL` | `bot.db` |
| `API_ID` | my.telegram.org se |
| `API_HASH` | my.telegram.org se |

---

## 🔐 Session String Generate Karo

Har account add karne se pehle session string banao — **apne PC pe run karo, Railway pe nahi:**

```bash
pip install telethon
python session_gen.py
```

1. API ID & Hash daalo
2. Account ka number daalo
3. OTP enter karo (seller se lo)
4. Session string copy karo
5. Bot mein **➕ Add Account** → Step 6 mein paste karo ✅

---

## 📱 Bot Flow

```
USER FLOW
──────────────────────────────────────
/start
  └─ Browse Accounts
      └─ Country Select (stock count ke saath)
          └─ Account Detail + Price
              └─ Confirm & Pay
                  └─ UPI QR (unique exact amount)
                      └─ Upload Payment Screenshot
                          └─ Notify Admin
                              └─ [Admin Approves]
                                  └─ Reveal Account Details
                                      └─ Get OTP → Auto Fetch ⚡

ADMIN FLOW
──────────────────────────────────────
➕ Add Account
  └─ Number → Country → Price → Password → 2FA → Session String → Done

⏳ Pending Orders
  └─ Screenshot dekho → ✅ Approve / ❌ Reject

📊 Statistics  →  Revenue / Stock / Users
📢 Broadcast   →  Sab users ko message
🔐 OTP Sessions → Active sessions dekho
👥 All Users   →  Ban / Unban
```

---

## 📁 File Structure

```
evbot/
├── bot.py              ← Main entry point
├── config.py           ← All config & env vars
├── database.py         ← SQLite — all DB functions
├── keyboards.py        ← All inline & reply keyboards
├── session_gen.py      ← Session string generator (run locally)
├── requirements.txt    ← Python dependencies
├── Procfile            ← Railway worker config
├── railway.toml        ← Railway deploy config
├── .env.example        ← Environment variables template
├── handlers/
│   ├── user.py         ← /start, browse, orders, support
│   ├── admin.py        ← Full admin panel
│   ├── payment.py      ← UPI QR, screenshot, notify
│   └── otp.py          ← Auto OTP fetch & delivery
└── utils/
    ├── qr.py           ← UPI QR generator
    ├── logger.py       ← Log channel sender
    └── otp_fetch.py    ← Telethon OTP auto-fetch
```

---

## ⚠️ Important Notes

- Bot ko Log Channel mein **Admin** banao (post permission ke saath)
- `session_gen.py` sirf **apne PC pe** chalao, Railway pe nahi
- Ek session string = ek account
- Database `bot.db` Railway pe automatically create hoga

---

Made with ❤️ by [@EVILTALKS](https://t.me/EVILTALKS)
