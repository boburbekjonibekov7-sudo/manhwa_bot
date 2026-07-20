# database/db.py
import aiosqlite
import asyncio
import json
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from config import config

DB_PATH = config.DB_PATH

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript("""
        PRAGMA journal_mode=WAL;
        PRAGMA synchronous=NORMAL;
        PRAGMA cache_size=10000;
        PRAGMA temp_store=MEMORY;

        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            user_id INTEGER UNIQUE NOT NULL,
            username TEXT,
            full_name TEXT,
            is_banned INTEGER DEFAULT 0,
            is_vip INTEGER DEFAULT 0,
            vip_until TEXT,
            joined_at TEXT DEFAULT CURRENT_TIMESTAMP,
            last_active TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS animes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code INTEGER UNIQUE NOT NULL,
            name TEXT NOT NULL,
            genre TEXT,
            studio TEXT,
            poster_file_id TEXT,
            is_vip INTEGER DEFAULT 0,
            vip_from_episode INTEGER DEFAULT 0,
            vip_from_season INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            forward_status INTEGER DEFAULT 1,
            search_count INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS seasons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            anime_code INTEGER NOT NULL,
            season_number INTEGER NOT NULL,
            season_name TEXT,
            FOREIGN KEY (anime_code) REFERENCES animes(code),
            UNIQUE(anime_code, season_number)
        );

        CREATE TABLE IF NOT EXISTS episodes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            anime_code INTEGER NOT NULL,
            season_number INTEGER DEFAULT 1,
            episode_number INTEGER NOT NULL,
            file_id TEXT NOT NULL,
            file_type TEXT DEFAULT 'video',
            file_name TEXT,
            thumbnail_file_id TEXT,
            is_vip INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (anime_code) REFERENCES animes(code)
        );

        CREATE TABLE IF NOT EXISTS channels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            channel_id TEXT UNIQUE NOT NULL,
            channel_username TEXT,
            channel_name TEXT,
            channel_type TEXT DEFAULT 'public',
            channel_url TEXT,
            is_main INTEGER DEFAULT 0,
            added_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS vip_cards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            card_number TEXT NOT NULL,
            card_type TEXT NOT NULL,
            is_active INTEGER DEFAULT 1,
            added_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS vip_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id TEXT UNIQUE NOT NULL,
            user_id INTEGER NOT NULL,
            duration_days INTEGER NOT NULL,
            amount INTEGER NOT NULL,
            card_id INTEGER,
            status TEXT DEFAULT 'pending',
            receipt_file_id TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        );

        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            username TEXT,
            full_name TEXT,
            added_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS bot_settings (
            key TEXT PRIMARY KEY,
            value TEXT
        );

        CREATE TABLE IF NOT EXISTS promo_codes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            duration_days INTEGER DEFAULT 7,
            is_active INTEGER DEFAULT 1,
            used_by TEXT DEFAULT '[]',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            expires_at TEXT
        );

        CREATE TABLE IF NOT EXISTS broadcast_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            admin_id INTEGER,
            message_type TEXT,
            recipients_count INTEGER,
            sent_count INTEGER,
            failed_count INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS user_watched (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            anime_code INTEGER NOT NULL,
            episode_number INTEGER NOT NULL,
            season_number INTEGER DEFAULT 1,
            watched_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, anime_code, episode_number, season_number)
        );

        CREATE TABLE IF NOT EXISTS join_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            channel_id TEXT NOT NULL,
            requested_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, channel_id)
        );

        INSERT OR IGNORE INTO bot_settings (key, value) VALUES
            ('bot_active', '1'),
            ('auto_post', '1'),
            ('auto_code', '1'),
            ('sharing_enabled', '1'),
            ('start_text', 'Manhwa Botiga xush kelibsiz! 🎬'),
            ('start_media', ''),
            ('start_media_type', ''),
            ('vip_1week_price', '4000'),
            ('vip_2week_price', '8000'),
            ('vip_1month_price', '12000'),
            ('guide_text', 'Bot qo''llanmasi...'),
            ('ads_text', 'Reklama va homiylik uchun admin bilan bog''laning.'),
            ('btn_search', '🔍 Manhwa izlash'),
            ('btn_guide', '📚 Qo''llanma'),
            ('btn_ads', '💰 Reklama va Homiylik'),
            ('btn_stats', '📊 Statistika'),
            ('btn_about', '🤖 Bot haqida'),
            ('btn_vip', '💎 VIP obuna (cheklovlarsiz)'),
            ('bot_username', 'your_bot'),
            ('creator_username', '@creator'),
            ('channel_username', '@channel'),
            ('admin_username', '@admin'),
            ('ads_channel', '@ads_channel'),
            ('bot_version', '3.9');
        """)
        await db.commit()

# ==================== USER ====================
async def get_user(user_id: int) -> Optional[Dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users WHERE user_id=?", (user_id,)) as cur:
            row = await cur.fetchone()
            return dict(row) if row else None

async def add_user(user_id: int, username: str, full_name: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT OR IGNORE INTO users (user_id, username, full_name)
            VALUES (?, ?, ?)
        """, (user_id, username, full_name))
        await db.execute("""
            UPDATE users SET username=?, full_name=?, last_active=CURRENT_TIMESTAMP
            WHERE user_id=?
        """, (username, full_name, user_id))
        await db.commit()

async def get_all_users(vip_only=False, non_vip_only=False) -> List[Dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        if vip_only:
            q = "SELECT * FROM users WHERE is_banned=0 AND is_vip=1"
        elif non_vip_only:
            q = "SELECT * FROM users WHERE is_banned=0 AND is_vip=0"
        else:
            q = "SELECT * FROM users WHERE is_banned=0"
        async with db.execute(q) as cur:
            return [dict(r) for r in await cur.fetchall()]

async def get_users_count() -> Dict:
    async with aiosqlite.connect(DB_PATH) as db:
        today = datetime.now().strftime("%Y-%m-%d")
        async with db.execute("SELECT COUNT(*) FROM users") as cur:
            total = (await cur.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM users WHERE DATE(joined_at)=?", (today,)) as cur:
            today_count = (await cur.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM users WHERE is_vip=1") as cur:
            vip_count = (await cur.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM users WHERE is_banned=1") as cur:
            banned_count = (await cur.fetchone())[0]
        return {"total": total, "today": today_count, "vip": vip_count, "banned": banned_count}

async def ban_user(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET is_banned=1 WHERE user_id=?", (user_id,))
        await db.commit()

async def unban_user(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET is_banned=0 WHERE user_id=?", (user_id,))
        await db.commit()

async def get_banned_users() -> List[Dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users WHERE is_banned=1") as cur:
            return [dict(r) for r in await cur.fetchall()]

# ==================== VIP ====================
async def set_vip(user_id: int, days: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT vip_until, is_vip FROM users WHERE user_id=?", (user_id,)) as cur:
            row = await cur.fetchone()
        
        now = datetime.now()
        if row and row["is_vip"] and row["vip_until"]:
            try:
                current_until = datetime.fromisoformat(row["vip_until"])
                if current_until > now:
                    new_until = current_until + timedelta(days=days)
                else:
                    new_until = now + timedelta(days=days)
            except:
                new_until = now + timedelta(days=days)
        else:
            new_until = now + timedelta(days=days)
        
        await db.execute("""
            UPDATE users SET is_vip=1, vip_until=? WHERE user_id=?
        """, (new_until.isoformat(), user_id))
        await db.commit()
        return new_until

async def remove_vip(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET is_vip=0, vip_until=NULL WHERE user_id=?", (user_id,))
        await db.commit()

async def check_vip_expiry():
    """Expired VIPlarni o'chirish"""
    async with aiosqlite.connect(DB_PATH) as db:
        now = datetime.now().isoformat()
        await db.execute("""
            UPDATE users SET is_vip=0, vip_until=NULL 
            WHERE is_vip=1 AND vip_until IS NOT NULL AND vip_until < ?
        """, (now,))
        await db.commit()

# ==================== ANIME ====================
async def get_next_available_code() -> int:
    """Auto kod: DB dagi eng katta koddan +1 qaytaradi (bo'sh bo'lsa 1 dan boshlaydi)."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT MAX(code) FROM animes") as cur:
            row = await cur.fetchone()
            max_code = row[0] if row and row[0] is not None else 0
    return max_code + 1

async def get_anime(code: int) -> Optional[Dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM animes WHERE code=?", (code,)) as cur:
            row = await cur.fetchone()
            return dict(row) if row else None

async def get_anime_by_name(name: str) -> List[Dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM animes WHERE name LIKE ? AND is_active=1",
            (f"%{name}%",)
        ) as cur:
            return [dict(r) for r in await cur.fetchall()]

async def get_all_animes(page=1, per_page=8) -> Dict:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        offset = (page - 1) * per_page
        async with db.execute("SELECT COUNT(*) FROM animes WHERE is_active=1") as cur:
            total = (await cur.fetchone())[0]
        async with db.execute(
            "SELECT * FROM animes WHERE is_active=1 ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (per_page, offset)
        ) as cur:
            items = [dict(r) for r in await cur.fetchall()]
        return {"items": items, "total": total, "pages": (total + per_page - 1) // per_page}


async def get_codes_sections(ANIME_PER_SECTION=70) -> Dict:
    """
    Kodlar ro'yxatini bo'limlarga ajratish.
    Oddiy (is_vip=0, forward_status=1) va ongoing (forward_status=0) va VIP alohida.
    Har bo'limda ANIME_PER_SECTION ta manhwa.
    """
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        # VIP manhwalar
        async with db.execute(
            "SELECT * FROM animes WHERE is_active=1 AND is_vip=1 ORDER BY code ASC"
        ) as cur:
            vip_items = [dict(r) for r in await cur.fetchall()]

        # Ongoing (forward_status=0, is_vip=0)
        async with db.execute(
            "SELECT * FROM animes WHERE is_active=1 AND is_vip=0 AND forward_status=0 ORDER BY code ASC"
        ) as cur:
            ongoing_items = [dict(r) for r in await cur.fetchall()]

        # Oddiy (forward_status=1, is_vip=0)
        async with db.execute(
            "SELECT * FROM animes WHERE is_active=1 AND is_vip=0 AND forward_status=1 ORDER BY code ASC"
        ) as cur:
            normal_items = [dict(r) for r in await cur.fetchall()]

        # Bo'limlarni yaratish
        sections = []
        section_num = 1
        for i in range(0, len(normal_items), ANIME_PER_SECTION):
            chunk = normal_items[i:i + ANIME_PER_SECTION]
            codes = [a['code'] for a in chunk]
            sections.append({
                "type": "normal",
                "label": f"{section_num}-bo'lim",
                "count": len(chunk),
                "codes": codes,
                "min_code": min(codes) if codes else 0,
                "max_code": max(codes) if codes else 0,
                "range": f"({min(codes)}-{max(codes)})" if codes else "(bo'sh)"
            })
            section_num += 1

        # Ongoing bo'limlar
        ongoing_section_num = 1
        for i in range(0, len(ongoing_items), ANIME_PER_SECTION):
            chunk = ongoing_items[i:i + ANIME_PER_SECTION]
            codes = [a['code'] for a in chunk]
            sections.append({
                "type": "ongoing",
                "label": f"{ongoing_section_num}-ongoing",
                "count": len(chunk),
                "codes": codes,
                "min_code": min(codes) if codes else 0,
                "max_code": max(codes) if codes else 0,
                "range": f"({min(codes)}-{max(codes)})" if codes else "(bo'sh)"
            })
            ongoing_section_num += 1

        # VIP bo'limlar
        vip_section_num = 1
        for i in range(0, len(vip_items), ANIME_PER_SECTION):
            chunk = vip_items[i:i + ANIME_PER_SECTION]
            codes = [a['code'] for a in chunk]
            sections.append({
                "type": "vip",
                "label": f"{vip_section_num}-vip",
                "count": len(chunk),
                "codes": codes,
                "min_code": min(codes) if codes else 0,
                "max_code": max(codes) if codes else 0,
                "range": f"({min(codes)}-{max(codes)})" if codes else "(bo'sh)"
            })
            vip_section_num += 1

        total = len(normal_items) + len(ongoing_items) + len(vip_items)
        return {
            "sections": sections,
            "total": total,
            "normal_count": len(normal_items),
            "ongoing_count": len(ongoing_items),
            "vip_count": len(vip_items),
            "normal_items": normal_items,
            "ongoing_items": ongoing_items,
            "vip_items": vip_items,
        }


async def get_section_animes(section_index: int, ANIME_PER_SECTION=70) -> Dict:
    """Bir bo'lim ichidagi manhwalar ro'yxatini olish."""
    result = await get_codes_sections(ANIME_PER_SECTION)
    if section_index < 0 or section_index >= len(result["sections"]):
        return {"items": [], "section": None}
    section = result["sections"][section_index]
    codes = section["codes"]
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        if codes:
            placeholders = ",".join(["?"] * len(codes))
            async with db.execute(
                f"SELECT * FROM animes WHERE code IN ({placeholders}) ORDER BY code ASC",
                codes
            ) as cur:
                items = [dict(r) for r in await cur.fetchall()]
        else:
            items = []
    return {"items": items, "section": section, "section_index": section_index}


async def get_all_active_animes() -> List[Dict]:
    """Barcha aktiv manhwalar ro'yxati."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM animes WHERE is_active=1 ORDER BY code ASC"
        ) as cur:
            return [dict(r) for r in await cur.fetchall()]

async def add_anime(code: int, name: str, genre: str, studio: str, poster_file_id: str) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        try:
            await db.execute("""
                INSERT INTO animes (code, name, genre, studio, poster_file_id)
                VALUES (?, ?, ?, ?, ?)
            """, (code, name, genre, studio, poster_file_id))
            await db.commit()
            return True
        except:
            return False

async def update_anime(code: int, new_code: int = None, **kwargs):
    """Manhwani yangilash. Kodni o'zgartirish uchun new_code parametridan foydalaning."""
    if new_code is not None:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("UPDATE animes SET code=? WHERE code=?", (new_code, code))
            await db.execute("UPDATE episodes SET anime_code=? WHERE anime_code=?", (new_code, code))
            await db.execute("UPDATE seasons SET anime_code=? WHERE anime_code=?", (new_code, code))
            await db.commit()
        code = new_code
    if kwargs:
        sets = ", ".join(f"{k}=?" for k in kwargs)
        vals = list(kwargs.values()) + [code]
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(f"UPDATE animes SET {sets} WHERE code=?", vals)
            await db.commit()

async def delete_anime(code: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM animes WHERE code=?", (code,))
        await db.execute("DELETE FROM episodes WHERE anime_code=?", (code,))
        await db.execute("DELETE FROM seasons WHERE anime_code=?", (code,))
        await db.commit()

async def increment_search(code: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE animes SET search_count=search_count+1 WHERE code=?", (code,))
        await db.commit()

async def get_animes_count() -> Dict:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM animes WHERE is_active=1") as cur:
            total = (await cur.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM episodes") as cur:
            episodes = (await cur.fetchone())[0]
        return {"total": total, "episodes": episodes}

# ==================== EPISODES ====================
async def add_episode(anime_code: int, season_number: int, episode_number: int, file_id: str,
                       is_vip: int = 0, file_type: str = "video", file_name: str = None):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT OR REPLACE INTO episodes (anime_code, season_number, episode_number, file_id, is_vip, file_type, file_name)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (anime_code, season_number, episode_number, file_id, is_vip, file_type, file_name))
        await db.commit()

async def get_episodes(anime_code: int, season_number: int = None) -> List[Dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        if season_number:
            q = "SELECT * FROM episodes WHERE anime_code=? AND season_number=? ORDER BY episode_number"
            args = (anime_code, season_number)
        else:
            q = "SELECT * FROM episodes WHERE anime_code=? ORDER BY season_number, episode_number"
            args = (anime_code,)
        async with db.execute(q, args) as cur:
            return [dict(r) for r in await cur.fetchall()]

async def get_episode(anime_code: int, season_number: int, episode_number: int) -> Optional[Dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT * FROM episodes WHERE anime_code=? AND season_number=? AND episode_number=?
        """, (anime_code, season_number, episode_number)) as cur:
            row = await cur.fetchone()
            return dict(row) if row else None

async def delete_episode(anime_code: int, season_number: int, episode_number: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            DELETE FROM episodes WHERE anime_code=? AND season_number=? AND episode_number=?
        """, (anime_code, season_number, episode_number))
        await db.commit()

async def update_episode_vip(anime_code: int, from_episode: int = 0, from_season: int = 0):
    """
    Har chaqiriq faqat ko'rsatilgan doiraga tegadi, boshqa fasllar/qismlarga
    tegmaydi — shuning uchun oldingi sozlamalar saqlanib qoladi.

    from_season > 0 (from_episode = 0): shu FASL butunlay VIP (faqat shu fasl)
    from_episode > 0 (from_season = 0): 1-faslda shu qismdan VIP (faqat 1-fasl)
    ikkalasi ham 0: BUTUN anime (barcha fasl, barcha qism) VIP
    """
    async with aiosqlite.connect(DB_PATH) as db:
        if from_season > 0:
            # Faqat shu fasl butunlay VIP - boshqa fasllarga tegmaydi
            await db.execute("""
                UPDATE episodes SET is_vip=1 
                WHERE anime_code=? AND season_number=?
            """, (anime_code, from_season))
        elif from_episode > 0:
            # 1-faslda shu qismdan VIP, undan oldingilari oddiy - boshqa fasllarga tegmaydi
            await db.execute("""
                UPDATE episodes SET is_vip=1 
                WHERE anime_code=? AND season_number=1 AND episode_number>=?
            """, (anime_code, from_episode))
            await db.execute("""
                UPDATE episodes SET is_vip=0 
                WHERE anime_code=? AND season_number=1 AND episode_number<?
            """, (anime_code, from_episode))
        else:
            # Butun anime VIP (barcha fasl, barcha qism)
            await db.execute("UPDATE episodes SET is_vip=1 WHERE anime_code=?", (anime_code,))

        await db.execute(
            "UPDATE animes SET is_vip=1 WHERE code=?",
            (anime_code,)
        )
        await db.commit()

async def clear_episode_vip(anime_code: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE episodes SET is_vip=0 WHERE anime_code=?", (anime_code,))
        await db.execute("UPDATE animes SET is_vip=0, vip_from_episode=0, vip_from_season=0 WHERE code=?", (anime_code,))
        await db.commit()

# ==================== SEASONS ====================
async def add_season(anime_code: int, season_number: int, season_name: str = None):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT OR IGNORE INTO seasons (anime_code, season_number, season_name)
            VALUES (?, ?, ?)
        """, (anime_code, season_number, season_name or f"{season_number}-fasl"))
        await db.commit()

async def get_seasons(anime_code: int) -> List[Dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT s.*, COUNT(e.id) as episode_count 
            FROM seasons s
            LEFT JOIN episodes e ON e.anime_code=s.anime_code AND e.season_number=s.season_number
            WHERE s.anime_code=? GROUP BY s.season_number ORDER BY s.season_number
        """, (anime_code,)) as cur:
            return [dict(r) for r in await cur.fetchall()]

# ==================== CHANNELS ====================
async def get_main_channels() -> List[Dict]:
    """Asosiy kanallar - post qilish uchun"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM channels WHERE is_main=1 ORDER BY id") as cur:
            return [dict(r) for r in await cur.fetchall()]

async def set_main_channel(channel_id: str, is_main: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE channels SET is_main=? WHERE channel_id=?", (is_main, channel_id))
        await db.commit()

async def get_channels() -> List[Dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM channels ORDER BY id") as cur:
            return [dict(r) for r in await cur.fetchall()]

async def add_channel(channel_id: str, username: str, name: str, ch_type: str, url: str = None):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT OR IGNORE INTO channels (channel_id, channel_username, channel_name, channel_type, channel_url)
            VALUES (?, ?, ?, ?, ?)
        """, (channel_id, username, name, ch_type, url))
        await db.commit()

async def delete_channel(channel_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM channels WHERE channel_id=?", (channel_id,))
        await db.commit()

# ==================== VIP CARDS ====================
async def get_vip_cards() -> List[Dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM vip_cards WHERE is_active=1") as cur:
            return [dict(r) for r in await cur.fetchall()]

async def add_vip_card(card_number: str, card_type: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT INTO vip_cards (card_number, card_type) VALUES (?, ?)", (card_number, card_type))
        await db.commit()

async def delete_vip_card(card_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM vip_cards WHERE id=?", (card_id,))
        await db.commit()

# ==================== VIP ORDERS ====================
async def create_vip_order(user_id: int, duration_days: int, amount: int) -> str:
    import random, string
    order_id = "VIP" + "".join(random.choices(string.digits, k=4))
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO vip_orders (order_id, user_id, duration_days, amount)
            VALUES (?, ?, ?, ?)
        """, (order_id, user_id, duration_days, amount))
        await db.commit()
    return order_id

async def update_order(order_id: str, **kwargs):
    if not kwargs:
        return
    sets = ", ".join(f"{k}=?" for k in kwargs) + ", updated_at=CURRENT_TIMESTAMP"
    vals = list(kwargs.values()) + [order_id]
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(f"UPDATE vip_orders SET {sets} WHERE order_id=?", vals)
        await db.commit()

async def get_pending_orders() -> List[Dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT o.*, u.username, u.full_name 
            FROM vip_orders o JOIN users u ON u.user_id=o.user_id
            WHERE o.status='pending' ORDER BY o.created_at
        """) as cur:
            return [dict(r) for r in await cur.fetchall()]

async def get_order(order_id: str) -> Optional[Dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM vip_orders WHERE order_id=?", (order_id,)) as cur:
            row = await cur.fetchone()
            return dict(row) if row else None

async def get_user_orders(user_id: int) -> List[Dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT * FROM vip_orders WHERE user_id=? ORDER BY created_at DESC
        """, (user_id,)) as cur:
            return [dict(r) for r in await cur.fetchall()]

# ==================== ADMINS ====================
async def get_admins() -> List[Dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM admins") as cur:
            return [dict(r) for r in await cur.fetchall()]

async def add_admin(user_id: int, username: str = None, full_name: str = None):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT OR IGNORE INTO admins (user_id, username, full_name) VALUES (?, ?, ?)
        """, (user_id, username, full_name))
        await db.commit()

async def remove_admin(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM admins WHERE user_id=?", (user_id,))
        await db.commit()

async def is_admin(user_id: int) -> bool:
    if user_id in config.ADMIN_IDS:
        return True
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT id FROM admins WHERE user_id=?", (user_id,)) as cur:
            return await cur.fetchone() is not None

# ==================== SETTINGS ====================
async def get_setting(key: str) -> Optional[str]:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT value FROM bot_settings WHERE key=?", (key,)) as cur:
            row = await cur.fetchone()
            return row[0] if row else None

async def set_setting(key: str, value: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT OR REPLACE INTO bot_settings (key, value) VALUES (?, ?)", (key, value))
        await db.commit()

async def get_all_settings() -> Dict:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM bot_settings") as cur:
            return {r["key"]: r["value"] for r in await cur.fetchall()}

# ==================== PROMO CODES ====================
async def create_promo(code: str, days: int = 7):
    expires = (datetime.now() + timedelta(days=days)).isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT OR REPLACE INTO promo_codes (code, duration_days, is_active, used_by, expires_at)
            VALUES (?, ?, 1, '[]', ?)
        """, (code, days, expires))
        await db.commit()

async def get_active_promo() -> Optional[Dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        now = datetime.now().isoformat()
        async with db.execute("""
            SELECT * FROM promo_codes WHERE is_active=1 AND expires_at > ? ORDER BY created_at DESC LIMIT 1
        """, (now,)) as cur:
            row = await cur.fetchone()
            return dict(row) if row else None

async def use_promo(code: str, user_id: int) -> Optional[Dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        now = datetime.now().isoformat()
        async with db.execute("""
            SELECT * FROM promo_codes WHERE code=? AND is_active=1 AND expires_at > ?
        """, (code, now)) as cur:
            promo = await cur.fetchone()
        if not promo:
            return None
        promo = dict(promo)
        used_by = json.loads(promo["used_by"])
        if user_id in used_by:
            return {"error": "already_used"}
        used_by.append(user_id)
        await db.execute("UPDATE promo_codes SET used_by=? WHERE code=?",
                        (json.dumps(used_by), code))
        await db.commit()
        return promo

async def delete_promo(code: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM promo_codes WHERE code=?", (code,))
        await db.commit()

# ==================== WATCHED ====================
async def save_join_request(user_id: int, channel_id: str):
    """Foydalanuvchi kanalga qo'shilish so'rovi yuborganda saqlaymiz."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT OR IGNORE INTO join_requests (user_id, channel_id) VALUES (?, ?)
        """, (user_id, channel_id))
        await db.commit()

async def has_join_request(user_id: int, channel_id: str) -> bool:
    """Foydalanuvchi shu kanalga so'rov yuborganmi tekshiramiz."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("""
            SELECT 1 FROM join_requests WHERE user_id=? AND channel_id=?
        """, (user_id, channel_id)) as cur:
            return await cur.fetchone() is not None

async def mark_watched(user_id: int, anime_code: int, episode_number: int, season_number: int = 1):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT OR IGNORE INTO user_watched (user_id, anime_code, episode_number, season_number)
            VALUES (?, ?, ?, ?)
        """, (user_id, anime_code, episode_number, season_number))
        await db.commit()

async def get_watched(user_id: int, anime_code: int, season_number: int = None) -> List[int]:
    async with aiosqlite.connect(DB_PATH) as db:
        if season_number is not None:
            async with db.execute("""
                SELECT episode_number FROM user_watched 
                WHERE user_id=? AND anime_code=? AND season_number=?
            """, (user_id, anime_code, season_number)) as cur:
                return [r[0] for r in await cur.fetchall()]
        else:
            async with db.execute("""
                SELECT episode_number FROM user_watched 
                WHERE user_id=? AND anime_code=?
            """, (user_id, anime_code)) as cur:
                return [r[0] for r in await cur.fetchall()]

# ==================== RESET / INIT HOLATGA QAYTARISH ====================
async def reset_database():
    """
    Botni boshlang'ich holatiga qaytarish.
    Barcha userlar, animes, episodes, seasons, channels, vip_cards, vip_orders,
    admins, promo_codes, broadcast_logs, user_watched, join_requests — o'chiriladi.
    bot_settings saqlanib qoladi.
    """
    async with aiosqlite.connect(DB_PATH) as db:
        tables_to_clear = [
            "user_watched",
            "join_requests",
            "broadcast_logs",
            "promo_codes",
            "admins",
            "vip_orders",
            "vip_cards",
            "episodes",
            "seasons",
            "channels",
            "animes",
            "users",
        ]
        for table in tables_to_clear:
            await db.execute(f"DELETE FROM {table}")
        await db.commit()

# ==================== BACKUP ====================
async def export_db() -> Dict:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        data = {}
        for table in ["users", "animes", "episodes", "seasons", "channels", "admins", "bot_settings"]:
            async with db.execute(f"SELECT * FROM {table}") as cur:
                data[table] = [dict(r) for r in await cur.fetchall()]
    return data

async def import_users(user_ids: List[int]):
    async with aiosqlite.connect(DB_PATH) as db:
        for uid in user_ids:
            await db.execute("""
                INSERT OR IGNORE INTO users (user_id, username, full_name) VALUES (?, ?, ?)
            """, (uid, None, "Imported"))
        await db.commit()
