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

ADMIN_CHANNEL = -1000000000000  # 🔥 ضع ID القناة

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

# ================= DATABASE =================
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
    u = get_user(user.id)
    if not u:
        with closing(db_conn()) as c, c:
            c.execute("""
                INSERT INTO users (user_id, username, full_name, referred_by)
                VALUES (?,?,?,?)
            """, (user.id, user.username or "", user.full_name or "", ref))

        if ref and ref != user.id:
            add_diamonds(ref, REF_REWARD)
            add_log(ref, "Referral Reward", REF_REWARD)
            with closing(db_conn()) as c, c:
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

# ================= LOG SYSTEM =================
def add_log(uid, action, amount=0):
    with closing(db_conn()) as c, c:
        c.execute("""
        INSERT INTO logs (user_id, action, amount)
        VALUES (?, ?, ?)
        """, (uid, action, amount))

# ================= LEVEL SYSTEM =================
def get_level(d):
    if d >= 15000:
        return "🔥 Lv5"
    elif d >= 7000:
        return "💎 Lv4"
    elif d >= 3000:
        return "⭐ Lv3"
    elif d >= 1000:
        return "⚡ Lv2"
    else:
        return "🆕 Lv1"

# ================= WEEKLY 2GB =================
def can_claim_2gb(uid):
    with closing(db_conn()) as c:
        r = c.execute("SELECT last_claim FROM weekly_rewards WHERE user_id=?", (uid,)).fetchone()
        if not r:
            return True
        return time.time() - r["last_claim"] >= 7 * 24 * 3600


def save_2gb(uid):
    with closing(db_conn()) as c, c:
        c.execute("""
        INSERT INTO weekly_rewards (user_id, last_claim)
        VALUES (?, ?)
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
        [InlineKeyboardButton(text="💰 Ooredoo (100 DZ+)", callback_data="ooredoo")],
        [InlineKeyboardButton(text="💰 Djezzy (100 DZ+)", callback_data="djezzy_cash")],
        [InlineKeyboardButton(text="💰 Mobilis (100 DZ+)", callback_data="mobilis")],
        [InlineKeyboardButton(text="📶 Djezzy 2GB = 1000 💎", callback_data="djezzy_gb")],
        [InlineKeyboardButton(text="🔙 Back", callback_data="home")],
    ])

# ================= START =================
@dp.message(CommandStart())
async def start(m: Message):
    ref = None
    if len(m.text.split()) > 1 and "ref_" in m.text:
        try:
            ref = int(m.text.split("_")[1])
        except:
            pass

    u = create_user(m.from_user, ref)

    await m.answer(
        f"👋 Welcome {u['full_name']}\n"
        f"💎 Diamonds: {u['diamonds']}\n"
        f"📊 Level: {get_level(u['diamonds'])}",
        reply_markup=main_kb()
    )

# ================= ADS =================
@dp.callback_query(F.data == "ads")
async def ads(c: CallbackQuery):
    add_diamonds(c.from_user.id, AD_REWARD)
    add_log(c.from_user.id, "Ads Reward", AD_REWARD)
    await c.answer(f"+{AD_REWARD} 💎")

# ================= TASKS =================
@dp.callback_query(F.data == "tasks")
async def tasks(c: CallbackQuery):
    add_diamonds(c.from_user.id, TASK_REWARD)
    add_log(c.from_user.id, "Task Reward", TASK_REWARD)
    await c.answer(f"+{TASK_REWARD} 💎")

# ================= DAILY =================
@dp.callback_query(F.data == "daily")
async def daily(c: CallbackQuery):
    u = get_user(c.from_user.id)
    now = time.time()

    if now - (u["last_daily"] or 0) < 86400:
        await c.answer("⏳ Wait 24h", show_alert=True)
        return

    add_diamonds(c.from_user.id, DAILY_REWARD)
    update(c.from_user.id, last_daily=now)
    add_log(c.from_user.id, "Daily Reward", DAILY_REWARD)

    await c.answer(f"+{DAILY_REWARD} 💎")

# ================= INVITE =================
@dp.callback_query(F.data == "invite")
async def invite(c: CallbackQuery):
    me = await bot.get_me()
    link = f"https://t.me/{me.username}?start=ref_{c.from_user.id}"

    await c.message.edit_text(
        f"👥 Invite Friends\n\n🔗 {link}",
        reply_markup=main_kb()
    )

# ================= SHOP =================
@dp.callback_query(F.data == "shop")
async def shop(c: CallbackQuery):
    await c.message.edit_text("🛒 SHOP", reply_markup=shop_kb())

# ================= CASH =================
@dp.callback_query(F.data.in_(["ooredoo", "djezzy_cash", "mobilis"]))
async def cash(c: CallbackQuery):
    u = get_user(c.from_user.id)

    if u["diamonds"] < MIN_WITHDRAW_DZ:
        await c.answer("❌ Min 100 DZ", show_alert=True)
        return

    await bot.send_message(
        ADMIN_CHANNEL,
        f"💰 Cash Request\n👤 {c.from_user.id}\n💎 {u['diamonds']}"
    )

    add_log(c.from_user.id, "Cash Request", u["diamonds"])
    await c.answer("📨 Sent")

# ================= 2GB =================
@dp.callback_query(F.data == "djezzy_gb")
async def djezzy(c: CallbackQuery):
    uid = c.from_user.id
    u = get_user(uid)

    if not can_claim_2gb(uid):
        await c.answer("⏳ Weekly only", show_alert=True)
        return

    if u["diamonds"] < GB_PRICE:
        await c.answer("❌ Need 1000 💎", show_alert=True)
        return

    add_diamonds(uid, -GB_PRICE)
    save_2gb(uid)

    await bot.send_message(
        ADMIN_CHANNEL,
        f"📶 2GB Request\n👤 {uid}"
    )

    add_log(uid, "2GB Request", GB_PRICE)
    await c.answer("📨 Sent")

# ================= HOME =================
@dp.callback_query(F.data == "home")
async def home(c: CallbackQuery):
    u = get_user(c.from_user.id)

    await c.message.edit_text(
        f"💎 Diamonds: {u['diamonds']}\n"
        f"📊 Level: {get_level(u['diamonds'])}",
        reply_markup=main_kb()
    )

# ================= RUN =================
async def main():
    db_init()
    keep_alive()
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())_", ""))
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
    url = miniapp_url()
    if url:
        try:
            from aiogram.types import MenuButtonWebApp as _MB
            await bot.set_chat_menu_button(menu_button=_MB(
                text="🚀 شبكتي", web_app=WebAppInfo(url=url),
            ))
            log.info(f"🌐 Mini App menu set: {url}")
        except Exception as e:
            log.warning(f"Couldn't set menu button: {e}")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        log.info("👋 Bot stopped")
