import asyncio
import logging
import os
import sqlite3
import time
from contextlib import closing
from flask import Flask
from threading import Thread

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

# ================= CONFIG =================
BOT_TOKEN = os.environ.get("BOT_TOKEN", "").strip()
if not BOT_TOKEN:
    raise SystemExit("❌ BOT_TOKEN missing")

ADMIN_CHANNEL = int(os.environ.get("ADMIN_CHANNEL", "-1003950488987"))

AD_REWARD = 20
TASK_REWARD = 50
DAILY_REWARD = 75
REF_REWARD = 100

MIN_WITHDRAW_DZ = 100
GB_PRICE = 1000

DB_PATH = "bot.db"

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("bot")

# ================= KEEP ALIVE =================
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is alive 🔥"

def run():
    app.run(host="0.0.0.0", port=8080)

def keep_alive():
    Thread(target=run).start()

# ================= DB =================
def db_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def db_init():
    with closing(db_conn()) as c, c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            full_name TEXT,
            diamonds INTEGER DEFAULT 0,
            referrals INTEGER DEFAULT 0,
            referred_by INTEGER,
            last_daily INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS weekly_rewards (
            user_id INTEGER PRIMARY KEY,
            last_claim INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            action TEXT,
            amount INTEGER,
            created_at INTEGER DEFAULT (strftime('%s','now'))
        );
        """)

# ================= USERS =================
def get_user(uid):
    with closing(db_conn()) as c:
        return c.execute("SELECT * FROM users WHERE user_id=?", (uid,)).fetchone()


def create_user(user, ref=None):
    if get_user(user.id):
        return get_user(user.id)

    with closing(db_conn()) as c, c:
        c.execute("""
            INSERT INTO users (user_id, username, full_name, referred_by)
            VALUES (?,?,?,?)
        """, (user.id, user.username or "", user.full_name or "", ref))

        if ref and ref != user.id:
            add_diamonds(ref, REF_REWARD)
            add_log(ref, "Referral", REF_REWARD)

            c.execute("UPDATE users SET referrals = referrals + 1 WHERE user_id=?", (ref,))

    return get_user(user.id)


def update(uid, **fields):
    keys = ",".join(f"{k}=?" for k in fields)
    vals = list(fields.values()) + [uid]
    with closing(db_conn()) as c, c:
        c.execute(f"UPDATE users SET {keys} WHERE user_id=?", vals)


def add_diamonds(uid, amount):
    with closing(db_conn()) as c, c:
        c.execute("UPDATE users SET diamonds = diamonds + ? WHERE user_id=?", (amount, uid))

# ================= LOG =================
def add_log(uid, action, amount=0):
    with closing(db_conn()) as c, c:
        c.execute("INSERT INTO logs (user_id, action, amount) VALUES (?,?,?)",
                  (uid, action, amount))

# ================= LEVEL =================
def get_level(d):
    if d >= 15000: return "🔥 Lv5"
    if d >= 7000: return "💎 Lv4"
    if d >= 3000: return "⭐ Lv3"
    if d >= 1000: return "⚡ Lv2"
    return "🆕 Lv1"

# ================= WEEKLY 2GB =================
def can_claim_2gb(uid):
    with closing(db_conn()) as c:
        r = c.execute("SELECT last_claim FROM weekly_rewards WHERE user_id=?", (uid,)).fetchone()
        if not r:
            return True
        return time.time() - r["last_claim"] >= 7 * 86400


def save_2gb(uid):
    with closing(db_conn()) as c, c:
        c.execute("""
        INSERT INTO weekly_rewards (user_id, last_claim)
        VALUES (?,?)
        ON CONFLICT(user_id) DO UPDATE SET last_claim=excluded.last_claim
        """, (uid, int(time.time())))

# ================= BOT =================
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# ================= KEYBOARD =================
def main_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎬 Ads", callback_data="ads")],
        [InlineKeyboardButton(text="📋 Tasks", callback_data="tasks")],
        [InlineKeyboardButton(text="💎 Daily", callback_data="daily")],
        [InlineKeyboardButton(text="👥 Invite", callback_data="invite")],
        [InlineKeyboardButton(text="🛒 Shop", callback_data="shop")],
    ])

def shop_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 Cash Withdraw", callback_data="cash")],
        [InlineKeyboardButton(text="📶 Djezzy 2GB = 1000💎", callback_data="gb")],
        [InlineKeyboardButton(text="🔙 Back", callback_data="home")],
    ])

# ================= START =================
@dp.message(CommandStart())
async def start(m: Message):
    ref = None
    if "ref_" in m.text:
        try:
            ref = int(m.text.split("_")[1])
        except:
            pass

    u = create_user(m.from_user, ref)

    await m.answer(
        f"👋 Welcome\n💎 {u['diamonds']}\n📊 {get_level(u['diamonds'])}",
        reply_markup=main_kb()
    )

# ================= ADS =================
@dp.callback_query(F.data == "ads")
async def ads(c: CallbackQuery):
    add_diamonds(c.from_user.id, AD_REWARD)
    add_log(c.from_user.id, "Ads", AD_REWARD)
    await c.answer(f"+{AD_REWARD} 💎")

# ================= TASKS =================
@dp.callback_query(F.data == "tasks")
async def tasks(c: CallbackQuery):
    add_diamonds(c.from_user.id, TASK_REWARD)
    add_log(c.from_user.id, "Tasks", TASK_REWARD)
    await c.answer(f"+{TASK_REWARD} 💎")

# ================= DAILY =================
@dp.callback_query(F.data == "daily")
async def daily(c: CallbackQuery):
    u = get_user(c.from_user.id)
    now = time.time()

    if now - (u["last_daily"] or 0) < 86400:
        await c.answer("⏳ Wait", show_alert=True)
        return

    add_diamonds(c.from_user.id, DAILY_REWARD)
    update(c.from_user.id, last_daily=now)
    add_log(c.from_user.id, "Daily", DAILY_REWARD)

    await c.answer(f"+{DAILY_REWARD} 💎")

# ================= SHOP =================
@dp.callback_query(F.data == "shop")
async def shop(c: CallbackQuery):
    await c.message.edit_text("🛒 Shop", reply_markup=shop_kb())

# ================= CASH =================
@dp.callback_query(F.data == "cash")
async def cash(c: CallbackQuery):
    u = get_user(c.from_user.id)

    if u["diamonds"] < MIN_WITHDRAW_DZ:
        await c.answer("❌ Min 100 DZ", show_alert=True)
        return

    await bot.send_message(
        ADMIN_CHANNEL,
        f"💰 Cash\n👤 {c.from_user.id}\n💎 {u['diamonds']}"
    )

    add_log(c.from_user.id, "Cash", u["diamonds"])
    await c.answer("Sent")

# ================= 2GB =================
@dp.callback_query(F.data == "gb")
async def gb(c: CallbackQuery):
    uid = c.from_user.id
    u = get_user(uid)

    if not can_claim_2gb(uid):
        await c.answer("⏳ Weekly", show_alert=True)
        return

    if u["diamonds"] < GB_PRICE:
        await c.answer("❌ 1000 💎", show_alert=True)
        return

    add_diamonds(uid, -GB_PRICE)
    save_2gb(uid)

    await bot.send_message(
        ADMIN_CHANNEL,
        f"📶 2GB\n👤 {uid}"
    )

    add_log(uid, "2GB", GB_PRICE)
    await c.answer("Sent")

# ================= RUN =================
async def main():
    db_init()
    keep_alive()
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
