"""
🤖 Telegram Earnings Bot (aiogram 3.x)
=======================================
بوت تيليجرام كامل بنظام نقاط، عجلة الحظ، إحالات، مكافآت يومية،
صناديق غامضة، ترتيب، وسحب — قاعدة بيانات SQLite.

تشغيل على Replit:
  1) ضع توكن البوت في Secrets باسم: BOT_TOKEN  (من @BotFather)
  2) شغّل الـ workflow "Telegram Bot" أو نفّذ:  python main.py
"""

import asyncio
import logging
import os
import random
import sqlite3
import time
from contextlib import closing
from typing import Optional

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

# ============================ الإعدادات ============================
BOT_TOKEN = os.environ.get("BOT_TOKEN", "").strip()
if not BOT_TOKEN:
    raise SystemExit("❌ BOT_TOKEN غير موجود. أضفه في Replit Secrets.")

POINTS_PER_DINAR = 100          # كل 100 نقطة = 1 دينار
WITHDRAW_MIN = 5000             # الحد الأدنى للسحب
AD_REWARD = 20                  # نقاط الإعلان
TASK_REWARD = 50                # نقاط المهمة
REFERRAL_REWARD = 100           # نقاط الإحالة
DAILY_REWARD = 75               # المكافأة اليومية
SPIN_COOLDOWN = 60 * 60         # ساعة واحدة بين كل لفّة
AD_COOLDOWN = 30                # 30 ثانية بين كل إعلان
TASK_COOLDOWN = 60              # دقيقة بين كل مهمة
ACTION_COOLDOWN = 1.5           # ضد السبام العام (ثواني)
DB_PATH = "bot.db"

SPIN_PRIZES = [10, 20, 50, 100, 10, 20, 0, 50]
MYSTERY_BOX = [
    ("🎉 جائزة كبرى!", 200),
    ("🎁 جائزة جيدة", 80),
    ("✨ مكافأة صغيرة", 30),
    ("💨 صندوق فارغ", 0),
    ("📉 خسارة بسيطة", -20),
]

# ============================ السجلات ============================
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s | %(levelname)s | %(message)s")
log = logging.getLogger("bot")

# ============================ قاعدة البيانات ============================

def db_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def db_init():
    with closing(db_conn()) as c, c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            user_id     INTEGER PRIMARY KEY,
            username    TEXT,
            full_name   TEXT,
            points      INTEGER DEFAULT 0,
            referrals   INTEGER DEFAULT 0,
            ads_watched INTEGER DEFAULT 0,
            tasks_done  INTEGER DEFAULT 0,
            spins_used  INTEGER DEFAULT 0,
            referred_by INTEGER,
            last_spin   INTEGER DEFAULT 0,
            last_daily  INTEGER DEFAULT 0,
            last_ad     INTEGER DEFAULT 0,
            last_task   INTEGER DEFAULT 0,
            last_action REAL    DEFAULT 0,
            joined_at   INTEGER DEFAULT (strftime('%s','now'))
        );
        CREATE TABLE IF NOT EXISTS withdrawals (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id   INTEGER NOT NULL,
            amount    INTEGER NOT NULL,
            status    TEXT DEFAULT 'pending',
            created_at INTEGER DEFAULT (strftime('%s','now'))
        );
        """)


def get_user(user_id: int) -> Optional[sqlite3.Row]:
    with closing(db_conn()) as c:
        return c.execute("SELECT * FROM users WHERE user_id=?", (user_id,)).fetchone()


def upsert_user(msg_user, referred_by: Optional[int] = None) -> sqlite3.Row:
    existing = get_user(msg_user.id)
    with closing(db_conn()) as c, c:
        if existing is None:
            c.execute(
                """INSERT INTO users (user_id, username, full_name, referred_by)
                   VALUES (?,?,?,?)""",
                (msg_user.id, msg_user.username or "", msg_user.full_name or "",
                 referred_by if referred_by and referred_by != msg_user.id else None),
            )
            if referred_by and referred_by != msg_user.id:
                ref = c.execute("SELECT user_id FROM users WHERE user_id=?",
                                (referred_by,)).fetchone()
                if ref:
                    c.execute(
                        "UPDATE users SET points=points+?, referrals=referrals+1 WHERE user_id=?",
                        (REFERRAL_REWARD, referred_by),
                    )
        else:
            c.execute("UPDATE users SET username=?, full_name=? WHERE user_id=?",
                      (msg_user.username or "", msg_user.full_name or "", msg_user.id))
    return get_user(msg_user.id)


def update_user(user_id: int, **fields):
    if not fields:
        return
    cols = ", ".join(f"{k}=?" for k in fields.keys())
    vals = list(fields.values()) + [user_id]
    with closing(db_conn()) as c, c:
        c.execute(f"UPDATE users SET {cols} WHERE user_id=?", vals)


def add_points(user_id: int, delta: int):
    with closing(db_conn()) as c, c:
        c.execute("UPDATE users SET points = MAX(0, points + ?) WHERE user_id=?",
                  (delta, user_id))


def top_by(field: str, limit: int = 10):
    assert field in ("points", "referrals")
    with closing(db_conn()) as c:
        return c.execute(
            f"SELECT user_id, full_name, username, {field} AS val FROM users "
            f"ORDER BY {field} DESC, user_id ASC LIMIT ?", (limit,)
        ).fetchall()


def add_withdrawal(user_id: int, amount: int):
    with closing(db_conn()) as c, c:
        c.execute("INSERT INTO withdrawals (user_id, amount) VALUES (?,?)",
                  (user_id, amount))
        c.execute("UPDATE users SET points = points - ? WHERE user_id=?",
                  (amount, user_id))


# ============================ أدوات مساعدة ============================

def fmt_time(seconds: int) -> str:
    seconds = int(max(0, seconds))
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    if h: return f"{h}س {m}د"
    if m: return f"{m}د {s}ث"
    return f"{s}ث"


def to_dinar(points: int) -> float:
    return round(points / POINTS_PER_DINAR, 2)


def progress_bar(current: int, target: int, width: int = 12) -> str:
    pct = min(1.0, current / target) if target else 0
    filled = int(pct * width)
    return "▓" * filled + "░" * (width - filled)


def anti_spam(user_row) -> bool:
    """يرجع True إذا الضغط مسموح، False إذا في سبام."""
    now = time.time()
    if now - (user_row["last_action"] or 0) < ACTION_COOLDOWN:
        return False
    update_user(user_row["user_id"], last_action=now)
    return True


# ============================ الواجهات ============================

def main_keyboard() -> InlineKeyboardMarkup:
    kb = [
        [InlineKeyboardButton(text="🎬 شاهد الإعلانات", callback_data="ads"),
         InlineKeyboardButton(text="📋 إنجاز المهام", callback_data="tasks")],
        [InlineKeyboardButton(text="👥 ادع الأصدقاء", callback_data="invite"),
         InlineKeyboardButton(text="💰 سحب", callback_data="withdraw")],
        [InlineKeyboardButton(text="🎡 عجلة الحظ", callback_data="spin"),
         InlineKeyboardButton(text="🎁 صندوق غامض", callback_data="mystery")],
        [InlineKeyboardButton(text="🏆 الترتيب", callback_data="leaderboard"),
         InlineKeyboardButton(text="🎁 مكافأة يومية", callback_data="daily")],
        [InlineKeyboardButton(text="📊 إحصائياتي", callback_data="stats"),
         InlineKeyboardButton(text="🔄 تحديث", callback_data="home")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)


def back_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🔙 رجوع للقائمة", callback_data="home")
    ]])


def render_home(u) -> str:
    points = u["points"]
    bar = progress_bar(points, WITHDRAW_MIN)
    return (
        f"<b>⚡ شبكتي</b>\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"👤 <b>{u['full_name'] or 'مستخدم'}</b>\n\n"
        f"💎 <b>رصيدك:</b> <code>{points}</code> نقطة\n"
        f"💵 <b>= {to_dinar(points)} دينار</b>\n"
        f"📊 <b>التقدم نحو السحب:</b>\n"
        f"<code>{bar}</code> {points}/{WITHDRAW_MIN}\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"👥 الإحالات: <b>{u['referrals']}</b>   "
        f"🎬 الإعلانات: <b>{u['ads_watched']}</b>   "
        f"📋 المهام: <b>{u['tasks_done']}</b>\n\n"
        f"اختر من القائمة 👇"
    )


# ============================ البوت ============================
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()


@dp.message(CommandStart())
async def cmd_start(message: Message):
    args = message.text.split(maxsplit=1)
    referred_by = None
    if len(args) > 1 and args[1].startswith("ref_"):
        try:
            referred_by = int(args[1].replace("ref_", ""))
        except ValueError:
            pass
    u = upsert_user(message.from_user, referred_by=referred_by)
    await message.answer(render_home(u), reply_markup=main_keyboard())


@dp.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "🤖 <b>مساعدة البوت</b>\n"
        "/start — القائمة الرئيسية\n"
        "/stats — عرض إحصائياتك\n"
        "/help — هذه الرسالة\n",
        reply_markup=back_kb(),
    )


@dp.message(Command("stats"))
async def cmd_stats(message: Message):
    u = upsert_user(message.from_user)
    await message.answer(stats_text(u), reply_markup=back_kb())


# ---------------------- معالج الأزرار ----------------------

async def safe_edit(cb: CallbackQuery, text: str, kb: InlineKeyboardMarkup):
    try:
        await cb.message.edit_text(text, reply_markup=kb)
    except Exception:
        await cb.message.answer(text, reply_markup=kb)


@dp.callback_query(F.data == "home")
async def cb_home(cb: CallbackQuery):
    u = upsert_user(cb.from_user)
    if not anti_spam(u):
        await cb.answer("⏳ تمهّل قليلاً…", show_alert=False); return
    await safe_edit(cb, render_home(u), main_keyboard())
    await cb.answer()


@dp.callback_query(F.data == "ads")
async def cb_ads(cb: CallbackQuery):
    u = upsert_user(cb.from_user)
    if not anti_spam(u):
        await cb.answer("⏳ تمهّل قليلاً…"); return
    now = int(time.time())
    wait = AD_COOLDOWN - (now - (u["last_ad"] or 0))
    if wait > 0:
        await cb.answer(f"⏳ انتظر {fmt_time(wait)} قبل الإعلان التالي", show_alert=True)
        return
    add_points(u["user_id"], AD_REWARD)
    update_user(u["user_id"], last_ad=now,
                ads_watched=(u["ads_watched"] or 0) + 1)
    u = get_user(u["user_id"])
    await safe_edit(
        cb,
        f"🎬 <b>تم مشاهدة الإعلان!</b>\n\n"
        f"➕ حصلت على <b>{AD_REWARD}</b> نقطة\n"
        f"💎 رصيدك الحالي: <b>{u['points']}</b> نقطة",
        back_kb(),
    )
    await cb.answer(f"+{AD_REWARD} نقطة 🎉")


@dp.callback_query(F.data == "tasks")
async def cb_tasks(cb: CallbackQuery):
    u = upsert_user(cb.from_user)
    if not anti_spam(u):
        await cb.answer("⏳ تمهّل قليلاً…"); return
    now = int(time.time())
    wait = TASK_COOLDOWN - (now - (u["last_task"] or 0))
    if wait > 0:
        await cb.answer(f"⏳ انتظر {fmt_time(wait)} قبل مهمة جديدة", show_alert=True)
        return
    add_points(u["user_id"], TASK_REWARD)
    update_user(u["user_id"], last_task=now,
                tasks_done=(u["tasks_done"] or 0) + 1)
    u = get_user(u["user_id"])
    await safe_edit(
        cb,
        f"📋 <b>تم إنجاز المهمة!</b>\n\n"
        f"➕ حصلت على <b>{TASK_REWARD}</b> نقطة\n"
        f"💎 رصيدك الحالي: <b>{u['points']}</b> نقطة",
        back_kb(),
    )
    await cb.answer(f"+{TASK_REWARD} نقطة ✅")


@dp.callback_query(F.data == "invite")
async def cb_invite(cb: CallbackQuery):
    u = upsert_user(cb.from_user)
    if not anti_spam(u):
        await cb.answer("⏳ تمهّل قليلاً…"); return
    me = await bot.get_me()
    link = f"https://t.me/{me.username}?start=ref_{u['user_id']}"
    text = (
        f"👥 <b>ادعُ أصدقاءك واربح!</b>\n\n"
        f"🎁 لكل صديق ينضم عبر رابطك تحصل على <b>{REFERRAL_REWARD}</b> نقطة.\n\n"
        f"🔗 <b>رابط الدعوة الخاص بك:</b>\n"
        f"<code>{link}</code>\n\n"
        f"📊 إحالاتك حتى الآن: <b>{u['referrals']}</b>"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="📤 شارك الرابط",
            url=f"https://t.me/share/url?url={link}&text=انضم%20واربح%20نقاط%20مجانية!")],
        [InlineKeyboardButton(text="🔙 رجوع", callback_data="home")],
    ])
    await safe_edit(cb, text, kb)
    await cb.answer()


@dp.callback_query(F.data == "withdraw")
async def cb_withdraw(cb: CallbackQuery):
    u = upsert_user(cb.from_user)
    if not anti_spam(u):
        await cb.answer("⏳ تمهّل قليلاً…"); return
    if u["points"] < WITHDRAW_MIN:
        need = WITHDRAW_MIN - u["points"]
        await safe_edit(
            cb,
            f"💰 <b>طلب سحب</b>\n\n"
            f"❌ رصيدك غير كافٍ.\n"
            f"💎 رصيدك: <b>{u['points']}</b>\n"
            f"🎯 الحد الأدنى: <b>{WITHDRAW_MIN}</b>\n"
            f"⚠️ ينقصك: <b>{need}</b> نقطة",
            back_kb(),
        )
        await cb.answer()
        return
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"✅ تأكيد سحب {WITHDRAW_MIN} نقطة",
                              callback_data="withdraw_confirm")],
        [InlineKeyboardButton(text="🔙 إلغاء", callback_data="home")],
    ])
    await safe_edit(
        cb,
        f"💰 <b>طلب سحب</b>\n\n"
        f"💎 رصيدك: <b>{u['points']}</b> نقطة\n"
        f"💵 = <b>{to_dinar(u['points'])} دينار</b>\n\n"
        f"سيتم خصم <b>{WITHDRAW_MIN}</b> نقطة "
        f"(<b>{to_dinar(WITHDRAW_MIN)} دينار</b>) من رصيدك.\n"
        f"اضغط للتأكيد 👇",
        kb,
    )
    await cb.answer()


@dp.callback_query(F.data == "withdraw_confirm")
async def cb_withdraw_confirm(cb: CallbackQuery):
    u = upsert_user(cb.from_user)
    if u["points"] < WITHDRAW_MIN:
        await cb.answer("❌ الرصيد غير كافٍ", show_alert=True); return
    add_withdrawal(u["user_id"], WITHDRAW_MIN)
    u = get_user(u["user_id"])
    await safe_edit(
        cb,
        f"✅ <b>تم تسجيل طلب السحب!</b>\n\n"
        f"💵 المبلغ: <b>{to_dinar(WITHDRAW_MIN)} دينار</b>\n"
        f"💎 رصيدك المتبقي: <b>{u['points']}</b> نقطة\n\n"
        f"⏳ سيتم مراجعة طلبك خلال 24-48 ساعة.",
        back_kb(),
    )
    await cb.answer("تم إرسال الطلب ✅", show_alert=True)


@dp.callback_query(F.data == "spin")
async def cb_spin(cb: CallbackQuery):
    u = upsert_user(cb.from_user)
    if not anti_spam(u):
        await cb.answer("⏳ تمهّل قليلاً…"); return
    now = int(time.time())
    wait = SPIN_COOLDOWN - (now - (u["last_spin"] or 0))
    if wait > 0:
        await cb.answer(f"⏳ متاحة بعد {fmt_time(wait)}", show_alert=True)
        return
    prize = random.choice(SPIN_PRIZES)
    add_points(u["user_id"], prize)
    update_user(u["user_id"], last_spin=now,
                spins_used=(u["spins_used"] or 0) + 1)
    u = get_user(u["user_id"])
    msg = (
        f"🎡 <b>عجلة الحظ</b>\n\n"
        f"🎯 ربحت: <b>{prize}</b> نقطة\n"
        f"💎 رصيدك: <b>{u['points']}</b> نقطة\n\n"
        f"⏰ متاحة مجدداً بعد ساعة."
    ) if prize > 0 else (
        f"🎡 <b>عجلة الحظ</b>\n\n"
        f"😅 لم تربح هذه المرة\n"
        f"💎 رصيدك: <b>{u['points']}</b> نقطة\n\n"
        f"⏰ حاول بعد ساعة."
    )
    await safe_edit(cb, msg, back_kb())
    await cb.answer(f"+{prize} نقطة" if prize else "حظ أوفر!")


@dp.callback_query(F.data == "mystery")
async def cb_mystery(cb: CallbackQuery):
    u = upsert_user(cb.from_user)
    if not anti_spam(u):
        await cb.answer("⏳ تمهّل قليلاً…"); return
    label, delta = random.choice(MYSTERY_BOX)
    add_points(u["user_id"], delta)
    u = get_user(u["user_id"])
    sign = "+" if delta >= 0 else ""
    await safe_edit(
        cb,
        f"🎁 <b>الصندوق الغامض</b>\n\n"
        f"النتيجة: <b>{label}</b>\n"
        f"التغيير: <b>{sign}{delta}</b> نقطة\n"
        f"💎 رصيدك: <b>{u['points']}</b> نقطة",
        back_kb(),
    )
    await cb.answer(f"{sign}{delta} نقطة")


@dp.callback_query(F.data == "leaderboard")
async def cb_leaderboard(cb: CallbackQuery):
    u = upsert_user(cb.from_user)
    if not anti_spam(u):
        await cb.answer("⏳ تمهّل قليلاً…"); return
    top_p = top_by("points", 10)
    top_r = top_by("referrals", 10)
    medals = ["🥇", "🥈", "🥉"] + ["🔹"] * 7

    def fmt(rows, suffix):
        if not rows: return "— لا يوجد —"
        out = []
        for i, r in enumerate(rows):
            name = r["full_name"] or r["username"] or f"User{r['user_id']}"
            out.append(f"{medals[i]} <b>{name[:18]}</b> — {r['val']} {suffix}")
        return "\n".join(out)

    text = (
        f"🏆 <b>الترتيب</b>\n"
        f"━━━━━━━━━━━━━━━━━\n"
        f"💎 <b>أفضل 10 بالنقاط</b>\n{fmt(top_p, 'نقطة')}\n\n"
        f"👥 <b>أفضل 10 بالإحالات</b>\n{fmt(top_r, 'إحالة')}"
    )
    await safe_edit(cb, text, back_kb())
    await cb.answer()


@dp.callback_query(F.data == "daily")
async def cb_daily(cb: CallbackQuery):
    u = upsert_user(cb.from_user)
    if not anti_spam(u):
        await cb.answer("⏳ تمهّل قليلاً…"); return
    now = int(time.time())
    wait = 24 * 3600 - (now - (u["last_daily"] or 0))
    if wait > 0:
        await cb.answer(f"⏳ متاحة بعد {fmt_time(wait)}", show_alert=True)
        return
    add_points(u["user_id"], DAILY_REWARD)
    update_user(u["user_id"], last_daily=now)
    u = get_user(u["user_id"])
    await safe_edit(
        cb,
        f"🎁 <b>المكافأة اليومية</b>\n\n"
        f"➕ حصلت على <b>{DAILY_REWARD}</b> نقطة\n"
        f"💎 رصيدك: <b>{u['points']}</b> نقطة\n\n"
        f"📅 عُد غداً للحصول على مكافأة جديدة!",
        back_kb(),
    )
    await cb.answer(f"+{DAILY_REWARD} نقطة 🎉")


def stats_text(u) -> str:
    return (
        f"📊 <b>إحصائياتي</b>\n"
        f"━━━━━━━━━━━━━━━━━\n"
        f"👤 الاسم: <b>{u['full_name'] or '—'}</b>\n"
        f"🆔 المعرّف: <code>{u['user_id']}</code>\n\n"
        f"💎 النقاط: <b>{u['points']}</b>\n"
        f"💵 = <b>{to_dinar(u['points'])} دينار</b>\n"
        f"👥 الإحالات: <b>{u['referrals']}</b>\n"
        f"🎬 الإعلانات: <b>{u['ads_watched']}</b>\n"
        f"📋 المهام: <b>{u['tasks_done']}</b>\n"
        f"🎡 لفّات عجلة الحظ: <b>{u['spins_used']}</b>"
    )


@dp.callback_query(F.data == "stats")
async def cb_stats(cb: CallbackQuery):
    u = upsert_user(cb.from_user)
    if not anti_spam(u):
        await cb.answer("⏳ تمهّل قليلاً…"); return
    await safe_edit(cb, stats_text(u), back_kb())
    await cb.answer()


# ============================ التشغيل ============================
async def main():
    db_init()
    log.info("✅ Database ready")
    me = await bot.get_me()
    log.info(f"🤖 Bot @{me.username} starting…")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        log.info("👋 Bot stopped")
