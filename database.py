import aiosqlite
import datetime
from config import DATABASE_URL

DB = DATABASE_URL

async def init_db():
    async with aiosqlite.connect(DB) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS accounts (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                number       TEXT NOT NULL,
                password     TEXT DEFAULT '',
                twofa        TEXT DEFAULT '',
                session_str  TEXT DEFAULT '',
                country      TEXT DEFAULT 'India',
                country_flag TEXT DEFAULT '🇮🇳',
                price        REAL NOT NULL,
                description  TEXT DEFAULT '',
                status       TEXT DEFAULT 'available',
                added_at     TEXT NOT NULL,
                sold_at      TEXT DEFAULT NULL,
                sold_to      INTEGER DEFAULT NULL
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id      INTEGER NOT NULL,
                username     TEXT DEFAULT '',
                full_name    TEXT DEFAULT '',
                account_id   INTEGER NOT NULL,
                amount       REAL NOT NULL,
                screenshot   TEXT DEFAULT '',
                status       TEXT DEFAULT 'pending',
                created_at   TEXT NOT NULL,
                approved_at  TEXT DEFAULT NULL
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id      INTEGER PRIMARY KEY,
                username     TEXT DEFAULT '',
                full_name    TEXT DEFAULT '',
                joined_at    TEXT NOT NULL,
                total_spent  REAL DEFAULT 0,
                total_orders INTEGER DEFAULT 0,
                is_banned    INTEGER DEFAULT 0
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS otp_sessions (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id     INTEGER NOT NULL,
                user_id      INTEGER NOT NULL,
                account_id   INTEGER NOT NULL,
                otp_code     TEXT DEFAULT '',
                status       TEXT DEFAULT 'waiting',
                created_at   TEXT NOT NULL
            )
        """)
        await db.commit()

# ── Accounts ──────────────────────────────────────────────────────────────────

async def add_account(number, price, country, country_flag, password="", twofa="", session_str="", description=""):
    now = datetime.datetime.now().isoformat()
    async with aiosqlite.connect(DB) as db:
        await db.execute(
            "INSERT INTO accounts (number,password,twofa,session_str,country,country_flag,price,description,status,added_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (number, password, twofa, session_str, country, country_flag, price, description, "available", now)
        )
        await db.commit()

async def get_available_accounts():
    async with aiosqlite.connect(DB) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM accounts WHERE status='available' ORDER BY country,id") as c:
            return [dict(r) for r in await c.fetchall()]

async def get_available_by_country(country):
    async with aiosqlite.connect(DB) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM accounts WHERE status='available' AND country=? ORDER BY id", (country,)) as c:
            return [dict(r) for r in await c.fetchall()]

async def get_country_stock():
    async with aiosqlite.connect(DB) as db:
        async with db.execute("SELECT country, country_flag, price, COUNT(*) as cnt FROM accounts WHERE status='available' GROUP BY country ORDER BY country") as c:
            return [{"country": r[0], "flag": r[1], "price": r[2], "count": r[3]} for r in await c.fetchall()]

async def get_account(account_id):
    async with aiosqlite.connect(DB) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM accounts WHERE id=?", (account_id,)) as c:
            r = await c.fetchone()
            return dict(r) if r else None

async def get_all_accounts():
    async with aiosqlite.connect(DB) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM accounts ORDER BY status,id DESC") as c:
            return [dict(r) for r in await c.fetchall()]

async def mark_account_sold(account_id, user_id):
    now = datetime.datetime.now().isoformat()
    async with aiosqlite.connect(DB) as db:
        await db.execute("UPDATE accounts SET status='sold',sold_at=?,sold_to=? WHERE id=?", (now, user_id, account_id))
        await db.commit()

async def delete_account(account_id):
    async with aiosqlite.connect(DB) as db:
        await db.execute("DELETE FROM accounts WHERE id=?", (account_id,))
        await db.commit()

async def update_account(account_id, **kwargs):
    allowed = ["price","password","twofa","session_str","description","country","country_flag"]
    sets = ", ".join(f"{k}=?" for k in kwargs if k in allowed)
    vals = [v for k, v in kwargs.items() if k in allowed]
    if not sets:
        return
    async with aiosqlite.connect(DB) as db:
        await db.execute(f"UPDATE accounts SET {sets} WHERE id=?", (*vals, account_id))
        await db.commit()

# ── Orders ────────────────────────────────────────────────────────────────────

async def create_order(user_id, username, full_name, account_id, amount):
    now = datetime.datetime.now().isoformat()
    async with aiosqlite.connect(DB) as db:
        c = await db.execute(
            "INSERT INTO orders (user_id,username,full_name,account_id,amount,status,created_at) VALUES (?,?,?,?,?,?,?)",
            (user_id, username, full_name, account_id, amount, "pending", now)
        )
        await db.commit()
        return c.lastrowid

async def get_order(order_id):
    async with aiosqlite.connect(DB) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM orders WHERE id=?", (order_id,)) as c:
            r = await c.fetchone()
            return dict(r) if r else None

async def get_pending_orders():
    async with aiosqlite.connect(DB) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM orders WHERE status='pending' ORDER BY created_at DESC") as c:
            return [dict(r) for r in await c.fetchall()]

async def get_all_orders(limit=50):
    async with aiosqlite.connect(DB) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM orders ORDER BY created_at DESC LIMIT ?", (limit,)) as c:
            return [dict(r) for r in await c.fetchall()]

async def get_user_orders(user_id):
    async with aiosqlite.connect(DB) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM orders WHERE user_id=? ORDER BY created_at DESC", (user_id,)) as c:
            return [dict(r) for r in await c.fetchall()]

async def approve_order(order_id):
    now = datetime.datetime.now().isoformat()
    async with aiosqlite.connect(DB) as db:
        await db.execute("UPDATE orders SET status='approved',approved_at=? WHERE id=?", (now, order_id))
        await db.commit()

async def reject_order(order_id):
    async with aiosqlite.connect(DB) as db:
        await db.execute("UPDATE orders SET status='rejected' WHERE id=?", (order_id,))
        await db.commit()

async def set_order_screenshot(order_id, file_id):
    async with aiosqlite.connect(DB) as db:
        await db.execute("UPDATE orders SET screenshot=? WHERE id=?", (file_id, order_id))
        await db.commit()

# ── Users ─────────────────────────────────────────────────────────────────────

async def upsert_user(user_id, username, full_name):
    now = datetime.datetime.now().isoformat()
    async with aiosqlite.connect(DB) as db:
        r = await (await db.execute("SELECT user_id FROM users WHERE user_id=?", (user_id,))).fetchone()
        if not r:
            await db.execute("INSERT INTO users (user_id,username,full_name,joined_at) VALUES (?,?,?,?)", (user_id, username, full_name, now))
        else:
            await db.execute("UPDATE users SET username=?,full_name=? WHERE user_id=?", (username, full_name, user_id))
        await db.commit()

async def get_all_users():
    async with aiosqlite.connect(DB) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users ORDER BY joined_at DESC") as c:
            return [dict(r) for r in await c.fetchall()]

async def update_user_stats(user_id, amount):
    async with aiosqlite.connect(DB) as db:
        await db.execute("UPDATE users SET total_spent=total_spent+?,total_orders=total_orders+1 WHERE user_id=?", (amount, user_id))
        await db.commit()

async def ban_user(user_id):
    async with aiosqlite.connect(DB) as db:
        await db.execute("UPDATE users SET is_banned=1 WHERE user_id=?", (user_id,))
        await db.commit()

async def unban_user(user_id):
    async with aiosqlite.connect(DB) as db:
        await db.execute("UPDATE users SET is_banned=0 WHERE user_id=?", (user_id,))
        await db.commit()

async def is_banned(user_id):
    async with aiosqlite.connect(DB) as db:
        r = await (await db.execute("SELECT is_banned FROM users WHERE user_id=?", (user_id,))).fetchone()
        return bool(r and r[0])

async def get_stats():
    async with aiosqlite.connect(DB) as db:
        ta  = (await (await db.execute("SELECT COUNT(*) FROM accounts")).fetchone())[0]
        av  = (await (await db.execute("SELECT COUNT(*) FROM accounts WHERE status='available'")).fetchone())[0]
        sol = (await (await db.execute("SELECT COUNT(*) FROM accounts WHERE status='sold'")).fetchone())[0]
        tu  = (await (await db.execute("SELECT COUNT(*) FROM users")).fetchone())[0]
        rev = (await (await db.execute("SELECT SUM(amount) FROM orders WHERE status='approved'")).fetchone())[0] or 0
        po  = (await (await db.execute("SELECT COUNT(*) FROM orders WHERE status='pending'")).fetchone())[0]
        return {"total_accounts":ta,"available":av,"sold":sol,"users":tu,"revenue":rev,"pending":po}

# ── OTP Sessions ──────────────────────────────────────────────────────────────

async def create_otp_session(order_id, user_id, account_id):
    now = datetime.datetime.now().isoformat()
    async with aiosqlite.connect(DB) as db:
        c = await db.execute(
            "INSERT INTO otp_sessions (order_id,user_id,account_id,status,created_at) VALUES (?,?,?,?,?)",
            (order_id, user_id, account_id, "waiting", now)
        )
        await db.commit()
        return c.lastrowid

async def get_otp_session(session_id):
    async with aiosqlite.connect(DB) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM otp_sessions WHERE id=?", (session_id,)) as c:
            r = await c.fetchone()
            return dict(r) if r else None

async def deliver_otp(session_id, otp_code):
    async with aiosqlite.connect(DB) as db:
        await db.execute("UPDATE otp_sessions SET otp_code=?,status='delivered' WHERE id=?", (otp_code, session_id))
        await db.commit()

async def get_waiting_otp_sessions():
    async with aiosqlite.connect(DB) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM otp_sessions WHERE status='waiting' ORDER BY created_at DESC") as c:
            return [dict(r) for r in await c.fetchall()]
