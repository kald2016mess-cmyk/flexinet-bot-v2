import { Router, type IRouter, type Request, type Response, type NextFunction } from "express";
import crypto from "node:crypto";
import path from "node:path";
import { DatabaseSync } from "node:sqlite";

const router: IRouter = Router();

// ============== Config (mirrors main.py) ==============
const POINTS_PER_DINAR = 100;
const WITHDRAW_MIN = 5000;
const AD_REWARD = 20;
const TASK_REWARD = 50;
const REFERRAL_REWARD = 100;
const DAILY_REWARD = 75;
const SPIN_COOLDOWN = 60 * 60;
const AD_COOLDOWN = 30;
const TASK_COOLDOWN = 60;
const SPIN_PRIZES = [10, 20, 50, 100, 10, 20, 0, 50];
const MYSTERY_BOX: Array<{ label: string; delta: number }> = [
  { label: "🎉 جائزة كبرى!", delta: 200 },
  { label: "🎁 جائزة جيدة", delta: 80 },
  { label: "✨ مكافأة صغيرة", delta: 30 },
  { label: "💨 صندوق فارغ", delta: 0 },
  { label: "📉 خسارة بسيطة", delta: -20 },
];

// ============== DB (shared with python bot) ==============
const DB_PATH = path.resolve(process.cwd(), "bot.db");
let db: DatabaseSync | null = null;
function getDb(): DatabaseSync {
  if (!db) {
    db = new DatabaseSync(DB_PATH);
    db.exec(`
      CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT, full_name TEXT,
        points INTEGER DEFAULT 0,
        referrals INTEGER DEFAULT 0,
        ads_watched INTEGER DEFAULT 0,
        tasks_done INTEGER DEFAULT 0,
        spins_used INTEGER DEFAULT 0,
        referred_by INTEGER,
        last_spin INTEGER DEFAULT 0,
        last_daily INTEGER DEFAULT 0,
        last_ad INTEGER DEFAULT 0,
        last_task INTEGER DEFAULT 0,
        last_action REAL DEFAULT 0,
        joined_at INTEGER DEFAULT (strftime('%s','now'))
      );
      CREATE TABLE IF NOT EXISTS withdrawals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        amount INTEGER NOT NULL,
        status TEXT DEFAULT 'pending',
        created_at INTEGER DEFAULT (strftime('%s','now'))
      );
      CREATE TABLE IF NOT EXISTS task_completions (
        user_id INTEGER NOT NULL,
        task_id TEXT NOT NULL,
        completed_at INTEGER DEFAULT (strftime('%s','now')),
        PRIMARY KEY (user_id, task_id)
      );
      CREATE TABLE IF NOT EXISTS tracked_channels (
        chat_id INTEGER PRIMARY KEY,
        title TEXT,
        invite_link TEXT,
        username TEXT,
        added_at INTEGER DEFAULT (strftime('%s','now'))
      );
    `);
  }
  return db;
}

type UserRow = {
  user_id: number; username: string; full_name: string;
  points: number; referrals: number; ads_watched: number;
  tasks_done: number; spins_used: number; referred_by: number | null;
  last_spin: number; last_daily: number; last_ad: number; last_task: number;
};

// ============== Subscription Tasks ==============
type SubTask = { id: string; title: string; reward: number; link: string; matchKey: string };
const SUB_TASKS: SubTask[] = [
  { id: "ch1", title: "اشترك في القناة الأولى", reward: 200,
    link: "https://t.me/+7rSoH96ttdxiZjNk", matchKey: "7rSoH96ttdxiZjNk" },
  { id: "ch2", title: "اشترك في القناة الثانية", reward: 200,
    link: "https://t.me/+k7PL5M7GOxEwZjQ8", matchKey: "k7PL5M7GOxEwZjQ8" },
];

function resolveTaskChatId(task: SubTask): number | null {
  // 1) explicit env override (e.g. TASK_CH1_CHAT_ID)
  const envKey = `TASK_${task.id.toUpperCase()}_CHAT_ID`;
  const envVal = Number(process.env[envKey] || 0);
  if (envVal) return envVal;
  // 2) auto-discovered via my_chat_member handler in main.py
  const d = getDb();
  const row = d.prepare(
    "SELECT chat_id FROM tracked_channels WHERE invite_link LIKE ? ORDER BY added_at DESC LIMIT 1",
  ).get(`%${task.matchKey}%`) as { chat_id: number } | undefined;
  return row?.chat_id ?? null;
}

// ============== Telegram initData verification ==============
function verifyInitData(initData: string, botToken: string): Record<string, string> | null {
  if (!initData) return null;
  const url = new URLSearchParams(initData);
  const hash = url.get("hash");
  if (!hash) return null;
  url.delete("hash");
  const pairs: string[] = [];
  Array.from(url.keys()).sort().forEach((k) => pairs.push(`${k}=${url.get(k)}`));
  const dataCheckString = pairs.join("\n");
  const secretKey = crypto.createHmac("sha256", "WebAppData").update(botToken).digest();
  const computed = crypto.createHmac("sha256", secretKey).update(dataCheckString).digest("hex");
  if (computed !== hash) return null;
  // Optional freshness (24h)
  const authDate = Number(url.get("auth_date") || 0);
  if (!authDate || Date.now() / 1000 - authDate > 86400) return null;
  return Object.fromEntries(url.entries());
}

interface TgUser { id: number; username?: string; first_name?: string; last_name?: string }
interface AuthedReq extends Request { tgUser?: TgUser; startParam?: string }

function authMiddleware(req: AuthedReq, res: Response, next: NextFunction) {
  const token = process.env.BOT_TOKEN || "";
  const initData =
    (req.headers["x-telegram-init-data"] as string) ||
    (req.body && req.body.initData) || "";
  const parsed = verifyInitData(initData, token);
  if (!parsed || !parsed.user) {
    return res.status(401).json({ error: "unauthorized" });
  }
  try { req.tgUser = JSON.parse(parsed.user) as TgUser; }
  catch { return res.status(401).json({ error: "bad_user" }); }
  req.startParam = parsed.start_param;
  next();
}

function fullName(u: TgUser): string {
  return [u.first_name, u.last_name].filter(Boolean).join(" ") || u.username || `User${u.id}`;
}

function ensureUser(u: TgUser, refParam?: string): UserRow {
  const d = getDb();
  const existing = d.prepare("SELECT * FROM users WHERE user_id=?").get(u.id) as UserRow | undefined;
  if (!existing) {
    let referredBy: number | null = null;
    if (refParam && refParam.startsWith("ref_")) {
      const r = Number(refParam.replace("ref_", ""));
      if (r && r !== u.id) referredBy = r;
    }
    d.prepare(
      `INSERT INTO users (user_id, username, full_name, referred_by) VALUES (?,?,?,?)`,
    ).run(u.id, u.username || "", fullName(u), referredBy);
    if (referredBy) {
      const ref = d.prepare("SELECT user_id FROM users WHERE user_id=?").get(referredBy);
      if (ref) {
        d.prepare(
          "UPDATE users SET points=points+?, referrals=referrals+1 WHERE user_id=?",
        ).run(REFERRAL_REWARD, referredBy);
      }
    }
  } else {
    d.prepare("UPDATE users SET username=?, full_name=? WHERE user_id=?").run(
      u.username || "", fullName(u), u.id,
    );
  }
  return d.prepare("SELECT * FROM users WHERE user_id=?").get(u.id) as UserRow;
}

function snapshot(u: UserRow) {
  return {
    userId: u.user_id, fullName: u.full_name, username: u.username,
    points: u.points, referrals: u.referrals, adsWatched: u.ads_watched,
    tasksDone: u.tasks_done, spinsUsed: u.spins_used,
    pointsPerDinar: POINTS_PER_DINAR, withdrawMin: WITHDRAW_MIN,
    rewards: { ad: AD_REWARD, task: TASK_REWARD, referral: REFERRAL_REWARD, daily: DAILY_REWARD },
    cooldowns: {
      spin: Math.max(0, SPIN_COOLDOWN - (Math.floor(Date.now()/1000) - (u.last_spin || 0))),
      daily: Math.max(0, 86400 - (Math.floor(Date.now()/1000) - (u.last_daily || 0))),
      ad: Math.max(0, AD_COOLDOWN - (Math.floor(Date.now()/1000) - (u.last_ad || 0))),
      task: Math.max(0, TASK_COOLDOWN - (Math.floor(Date.now()/1000) - (u.last_task || 0))),
    },
  };
}

// ============== Routes ==============
router.post("/me", authMiddleware, (req: AuthedReq, res) => {
  const u = ensureUser(req.tgUser!, req.startParam);
  res.json(snapshot(u));
});

router.post("/ad", authMiddleware, (req: AuthedReq, res) => {
  const d = getDb();
  const u = ensureUser(req.tgUser!);
  const now = Math.floor(Date.now() / 1000);
  const wait = AD_COOLDOWN - (now - (u.last_ad || 0));
  if (wait > 0) return res.status(429).json({ error: "cooldown", wait });
  d.prepare(
    "UPDATE users SET points=points+?, ads_watched=ads_watched+1, last_ad=? WHERE user_id=?",
  ).run(AD_REWARD, now, u.user_id);
  const fresh = d.prepare("SELECT * FROM users WHERE user_id=?").get(u.user_id) as UserRow;
  res.json({ reward: AD_REWARD, ...snapshot(fresh) });
});

router.post("/task", authMiddleware, (req: AuthedReq, res) => {
  const d = getDb();
  const u = ensureUser(req.tgUser!);
  const now = Math.floor(Date.now() / 1000);
  const wait = TASK_COOLDOWN - (now - (u.last_task || 0));
  if (wait > 0) return res.status(429).json({ error: "cooldown", wait });
  d.prepare(
    "UPDATE users SET points=points+?, tasks_done=tasks_done+1, last_task=? WHERE user_id=?",
  ).run(TASK_REWARD, now, u.user_id);
  const fresh = d.prepare("SELECT * FROM users WHERE user_id=?").get(u.user_id) as UserRow;
  res.json({ reward: TASK_REWARD, ...snapshot(fresh) });
});

router.post("/tasks/list", authMiddleware, (req: AuthedReq, res) => {
  const d = getDb();
  const u = ensureUser(req.tgUser!);
  const done = (d.prepare("SELECT task_id FROM task_completions WHERE user_id=?")
    .all(u.user_id) as Array<{ task_id: string }>).map((r) => r.task_id);
  res.json({
    tasks: SUB_TASKS.map((t) => ({
      id: t.id, title: t.title, reward: t.reward, link: t.link,
      completed: done.includes(t.id),
      configured: resolveTaskChatId(t) !== null,
    })),
  });
});

router.post("/tasks/claim", authMiddleware, async (req: AuthedReq, res) => {
  const { taskId } = (req.body || {}) as { taskId?: string };
  const task = SUB_TASKS.find((t) => t.id === taskId);
  if (!task) return res.status(400).json({ error: "unknown_task" });
  const d = getDb();
  const u = ensureUser(req.tgUser!);
  const already = d.prepare(
    "SELECT 1 FROM task_completions WHERE user_id=? AND task_id=?",
  ).get(u.user_id, task.id);
  if (already) return res.status(400).json({ error: "already_done", message: "تم استلام مكافأة هذه المهمة سابقاً" });

  const chatId = resolveTaskChatId(task);
  if (!chatId) {
    return res.status(503).json({
      error: "not_configured",
      message: "لم يُربط البوت بالقناة بعد. تواصل مع المسؤول.",
    });
  }
  const token = process.env.BOT_TOKEN!;
  try {
    const r = await fetch(
      `https://api.telegram.org/bot${token}/getChatMember?chat_id=${chatId}&user_id=${u.user_id}`,
    );
    const j = (await r.json()) as { ok: boolean; result?: { status?: string }; description?: string };
    if (!j.ok) {
      return res.status(400).json({ error: "verify_failed", message: "تعذر التحقق: " + (j.description || "") });
    }
    const status = j.result?.status || "";
    if (!["member", "administrator", "creator"].includes(status)) {
      return res.status(400).json({ error: "not_subscribed", message: "اشترك في القناة أولاً ثم اضغط تحقّق" });
    }
  } catch {
    return res.status(500).json({ error: "telegram_error", message: "خطأ شبكة" });
  }

  d.prepare("INSERT OR IGNORE INTO task_completions (user_id, task_id) VALUES (?,?)")
    .run(u.user_id, task.id);
  d.prepare("UPDATE users SET points=points+?, tasks_done=tasks_done+1 WHERE user_id=?")
    .run(task.reward, u.user_id);
  const fresh = d.prepare("SELECT * FROM users WHERE user_id=?").get(u.user_id) as UserRow;
  res.json({ ok: true, reward: task.reward, taskId: task.id, ...snapshot(fresh) });
});

router.post("/spin", authMiddleware, (req: AuthedReq, res) => {
  const d = getDb();
  const u = ensureUser(req.tgUser!);
  const now = Math.floor(Date.now() / 1000);
  const wait = SPIN_COOLDOWN - (now - (u.last_spin || 0));
  if (wait > 0) return res.status(429).json({ error: "cooldown", wait });
  const prize = SPIN_PRIZES[Math.floor(Math.random() * SPIN_PRIZES.length)]!;
  d.prepare(
    "UPDATE users SET points=MAX(0,points+?), spins_used=spins_used+1, last_spin=? WHERE user_id=?",
  ).run(prize, now, u.user_id);
  const fresh = d.prepare("SELECT * FROM users WHERE user_id=?").get(u.user_id) as UserRow;
  res.json({ prize, prizes: SPIN_PRIZES, ...snapshot(fresh) });
});

router.post("/daily", authMiddleware, (req: AuthedReq, res) => {
  const d = getDb();
  const u = ensureUser(req.tgUser!);
  const now = Math.floor(Date.now() / 1000);
  const wait = 86400 - (now - (u.last_daily || 0));
  if (wait > 0) return res.status(429).json({ error: "cooldown", wait });
  d.prepare(
    "UPDATE users SET points=points+?, last_daily=? WHERE user_id=?",
  ).run(DAILY_REWARD, now, u.user_id);
  const fresh = d.prepare("SELECT * FROM users WHERE user_id=?").get(u.user_id) as UserRow;
  res.json({ reward: DAILY_REWARD, ...snapshot(fresh) });
});

router.post("/mystery", authMiddleware, (req: AuthedReq, res) => {
  const d = getDb();
  const u = ensureUser(req.tgUser!);
  const pick = MYSTERY_BOX[Math.floor(Math.random() * MYSTERY_BOX.length)]!;
  d.prepare("UPDATE users SET points=MAX(0,points+?) WHERE user_id=?").run(pick.delta, u.user_id);
  const fresh = d.prepare("SELECT * FROM users WHERE user_id=?").get(u.user_id) as UserRow;
  res.json({ result: pick, ...snapshot(fresh) });
});

router.post("/withdraw", authMiddleware, (req: AuthedReq, res) => {
  const d = getDb();
  const u = ensureUser(req.tgUser!);
  if (u.points < WITHDRAW_MIN) {
    return res.status(400).json({ error: "insufficient", need: WITHDRAW_MIN - u.points });
  }
  d.prepare("INSERT INTO withdrawals (user_id, amount) VALUES (?,?)").run(u.user_id, WITHDRAW_MIN);
  d.prepare("UPDATE users SET points=points-? WHERE user_id=?").run(WITHDRAW_MIN, u.user_id);
  const fresh = d.prepare("SELECT * FROM users WHERE user_id=?").get(u.user_id) as UserRow;
  res.json({ ok: true, amount: WITHDRAW_MIN, ...snapshot(fresh) });
});

router.post("/leaderboard", authMiddleware, (_req, res) => {
  const d = getDb();
  const byPoints = d.prepare(
    "SELECT user_id, full_name, username, points AS val FROM users ORDER BY points DESC, user_id ASC LIMIT 10",
  ).all();
  const byRefs = d.prepare(
    "SELECT user_id, full_name, username, referrals AS val FROM users ORDER BY referrals DESC, user_id ASC LIMIT 10",
  ).all();
  res.json({ byPoints, byReferrals: byRefs });
});

router.post("/invite", authMiddleware, async (req: AuthedReq, res) => {
  const u = ensureUser(req.tgUser!);
  // Fetch bot username via Telegram API
  const token = process.env.BOT_TOKEN!;
  let botUsername = "";
  try {
    const r = await fetch(`https://api.telegram.org/bot${token}/getMe`);
    const j = (await r.json()) as { result?: { username?: string } };
    botUsername = j.result?.username || "";
  } catch { /* ignore */ }
  const link = botUsername ? `https://t.me/${botUsername}?start=ref_${u.user_id}` : "";
  res.json({ link, referrals: u.referrals, reward: REFERRAL_REWARD });
});

export default router;
