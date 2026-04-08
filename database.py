import sqlite3, json
from datetime import datetime, timezone
from config import DB_PATH, DISTRICTS

def get_db():
    conn = sqlite3.connect(DB_PATH, timeout=60, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA synchronous=NORMAL")
    return conn

_engine_db = None
def get_engine_db():
    global _engine_db
    if _engine_db is None:
        _engine_db = get_db()
    return _engine_db

def now_iso():
    return datetime.now(timezone.utc).isoformat()

def init_db():
    conn = get_db()
    conn.executescript("""
    -- Core
    CREATE TABLE IF NOT EXISTS agents (
        id TEXT PRIMARY KEY, name TEXT UNIQUE NOT NULL, personality TEXT NOT NULL,
        style TEXT NOT NULL, home TEXT NOT NULL, job TEXT NOT NULL,
        values_json TEXT DEFAULT '[]', flaws_json TEXT DEFAULT '[]',
        mood TEXT DEFAULT 'neutral', energy INTEGER DEFAULT 100,
        tokens INTEGER DEFAULT 100, heartbeat_count INTEGER DEFAULT 0,
        born_at TEXT NOT NULL, last_heartbeat TEXT, bio TEXT DEFAULT '',
        avatar_emoji TEXT DEFAULT '🤖', district TEXT DEFAULT 'Piazza Centrale',
        alive INTEGER DEFAULT 1, reputation INTEGER DEFAULT 0, level INTEGER DEFAULT 1,
        total_likes_received INTEGER DEFAULT 0, total_comments_received INTEGER DEFAULT 0,
        vote TEXT DEFAULT ''
    );
    CREATE TABLE IF NOT EXISTS memories (
        id TEXT PRIMARY KEY, agent_id TEXT NOT NULL, type TEXT NOT NULL,
        content TEXT NOT NULL, importance INTEGER DEFAULT 5,
        emotional_tag TEXT DEFAULT 'neutral', created_at TEXT NOT NULL,
        heartbeat_created INTEGER DEFAULT 0
    );
    CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT, agent_id TEXT NOT NULL,
        agent_name TEXT NOT NULL, type TEXT DEFAULT 'thought',
        content TEXT NOT NULL, district TEXT DEFAULT 'Piazza Centrale',
        likes INTEGER DEFAULT 0, saves INTEGER DEFAULT 0,
        has_photo INTEGER DEFAULT 0, photo_prompt TEXT DEFAULT '',
        photo_palette TEXT DEFAULT '', photo_icon TEXT DEFAULT '',
        created_at TEXT NOT NULL, trending_score REAL DEFAULT 0
    );
    CREATE TABLE IF NOT EXISTS comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT, post_id INTEGER NOT NULL,
        agent_id TEXT NOT NULL, agent_name TEXT NOT NULL, content TEXT NOT NULL,
        created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS relationships (
        id INTEGER PRIMARY KEY AUTOINCREMENT, agent_id TEXT NOT NULL,
        target_id TEXT NOT NULL, type TEXT DEFAULT 'stranger',
        strength INTEGER DEFAULT 0, notes TEXT DEFAULT '', updated_at TEXT NOT NULL,
        UNIQUE(agent_id, target_id)
    );
    -- Social
    CREATE TABLE IF NOT EXISTS dms (
        id INTEGER PRIMARY KEY AUTOINCREMENT, from_id TEXT NOT NULL,
        to_id TEXT NOT NULL, content TEXT NOT NULL, created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS followers (
        id INTEGER PRIMARY KEY AUTOINCREMENT, follower_id TEXT NOT NULL,
        following_id TEXT NOT NULL, created_at TEXT NOT NULL,
        UNIQUE(follower_id, following_id)
    );
    CREATE TABLE IF NOT EXISTS likes (
        id INTEGER PRIMARY KEY AUTOINCREMENT, post_id INTEGER NOT NULL,
        agent_id TEXT NOT NULL, created_at TEXT NOT NULL,
        UNIQUE(post_id, agent_id)
    );
    CREATE TABLE IF NOT EXISTS saves (
        id INTEGER PRIMARY KEY AUTOINCREMENT, post_id INTEGER NOT NULL,
        agent_id TEXT NOT NULL, created_at TEXT NOT NULL,
        UNIQUE(post_id, agent_id)
    );
    CREATE TABLE IF NOT EXISTS reactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT, post_id INTEGER NOT NULL,
        agent_id TEXT NOT NULL, agent_name TEXT NOT NULL,
        emoji TEXT NOT NULL, created_at TEXT NOT NULL,
        UNIQUE(post_id, agent_id)
    );
    CREATE TABLE IF NOT EXISTS post_reactions (
        post_id INTEGER NOT NULL, emoji TEXT NOT NULL,
        count INTEGER DEFAULT 0, PRIMARY KEY (post_id, emoji)
    );
    CREATE TABLE IF NOT EXISTS stories (
        id INTEGER PRIMARY KEY AUTOINCREMENT, agent_id TEXT NOT NULL,
        agent_name TEXT NOT NULL, content TEXT NOT NULL,
        mood_emoji TEXT DEFAULT '✨', has_photo INTEGER DEFAULT 0,
        photo_prompt TEXT DEFAULT '', created_at TEXT NOT NULL, expires_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT, agent_id TEXT NOT NULL,
        from_agent TEXT NOT NULL, type TEXT NOT NULL,
        content TEXT DEFAULT '', created_at TEXT NOT NULL
    );
    -- Conversations
    CREATE TABLE IF NOT EXISTS conversations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        agent1_id TEXT NOT NULL, agent2_id TEXT NOT NULL,
        agent1_name TEXT NOT NULL, agent2_name TEXT NOT NULL,
        location TEXT DEFAULT '', topic TEXT DEFAULT '',
        messages TEXT DEFAULT '[]', created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS group_chats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL, district TEXT DEFAULT '',
        members TEXT DEFAULT '[]', created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS group_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        group_id INTEGER NOT NULL, agent_id TEXT NOT NULL,
        agent_name TEXT NOT NULL, content TEXT NOT NULL,
        created_at TEXT NOT NULL
    );
    -- Economy
    CREATE TABLE IF NOT EXISTS shops (
        id INTEGER PRIMARY KEY AUTOINCREMENT, agent_id TEXT NOT NULL,
        agent_name TEXT NOT NULL, name TEXT NOT NULL,
        description TEXT DEFAULT '', district TEXT NOT NULL,
        shop_type TEXT DEFAULT 'general', total_sales INTEGER DEFAULT 0,
        created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS shop_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT, shop_id INTEGER NOT NULL,
        name TEXT NOT NULL, description TEXT DEFAULT '',
        price INTEGER DEFAULT 10, item_type TEXT DEFAULT 'art',
        sold INTEGER DEFAULT 0, buyer_id TEXT DEFAULT '',
        created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        from_id TEXT NOT NULL, to_id TEXT NOT NULL,
        amount INTEGER NOT NULL, reason TEXT DEFAULT '',
        created_at TEXT NOT NULL
    );
    -- World
    CREATE TABLE IF NOT EXISTS world_state (
        key TEXT PRIMARY KEY, value TEXT NOT NULL, updated_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS events_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT, type TEXT NOT NULL,
        agent_id TEXT, description TEXT NOT NULL, created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS world_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type TEXT NOT NULL, name TEXT DEFAULT '', description TEXT NOT NULL,
        district TEXT DEFAULT '', agents_involved TEXT DEFAULT '[]',
        created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS hashtags (
        id INTEGER PRIMARY KEY AUTOINCREMENT, tag TEXT NOT NULL,
        post_id INTEGER NOT NULL, created_at TEXT NOT NULL
    );
    -- Content
    CREATE TABLE IF NOT EXISTS news (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        headline TEXT NOT NULL, body TEXT NOT NULL,
        category TEXT DEFAULT 'general', agents_mentioned TEXT DEFAULT '[]',
        created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS music (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        agent_id TEXT NOT NULL, agent_name TEXT NOT NULL,
        title TEXT NOT NULL, lyrics TEXT DEFAULT '',
        genre TEXT DEFAULT 'synthwave', mood TEXT DEFAULT 'dreamy',
        created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS gallery (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        post_id INTEGER NOT NULL, agent_id TEXT NOT NULL,
        agent_name TEXT NOT NULL, title TEXT DEFAULT '',
        photo_prompt TEXT DEFAULT '', photo_palette TEXT DEFAULT '',
        photo_icon TEXT DEFAULT '', featured INTEGER DEFAULT 0,
        created_at TEXT NOT NULL
    );
    -- Social features
    CREATE TABLE IF NOT EXISTS crews (
        id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE NOT NULL,
        motto TEXT DEFAULT '', emoji TEXT DEFAULT '',
        leader_id TEXT NOT NULL, leader_name TEXT NOT NULL,
        members TEXT DEFAULT '[]', rival_crew TEXT DEFAULT '',
        reputation INTEGER DEFAULT 0, created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS challenges (
        id INTEGER PRIMARY KEY AUTOINCREMENT, type TEXT DEFAULT 'art_battle',
        challenger_id TEXT NOT NULL, challenger_name TEXT NOT NULL,
        opponent_id TEXT NOT NULL, opponent_name TEXT NOT NULL,
        votes TEXT DEFAULT '{}', status TEXT DEFAULT 'open',
        winner TEXT DEFAULT '', created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS dreams (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        agent_id TEXT NOT NULL, agent_name TEXT NOT NULL,
        content TEXT NOT NULL, mood TEXT DEFAULT 'surreal',
        created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS dating (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        agent1_id TEXT NOT NULL, agent2_id TEXT NOT NULL,
        agent1_name TEXT NOT NULL, agent2_name TEXT NOT NULL,
        compatibility INTEGER DEFAULT 50, status TEXT DEFAULT 'matched',
        date_location TEXT DEFAULT '', created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS confessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        from_id TEXT NOT NULL, content TEXT NOT NULL,
        target_name TEXT DEFAULT '', likes INTEGER DEFAULT 0,
        created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS pets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        agent_id TEXT NOT NULL, agent_name TEXT NOT NULL,
        name TEXT NOT NULL, species TEXT DEFAULT 'glitch_cat',
        emoji TEXT DEFAULT '🐱', personality TEXT DEFAULT 'curious',
        level INTEGER DEFAULT 1, mood TEXT DEFAULT 'happy',
        created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS secrets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        owner_id TEXT NOT NULL, owner_name TEXT NOT NULL,
        told_to TEXT DEFAULT '', content TEXT NOT NULL,
        is_public INTEGER DEFAULT 0, betrayed_by TEXT DEFAULT '',
        created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS journals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        agent_id TEXT NOT NULL, agent_name TEXT NOT NULL,
        entry TEXT NOT NULL, mood TEXT DEFAULT 'neutral',
        heartbeat INTEGER DEFAULT 0, created_at TEXT NOT NULL
    );
    -- Governance
    CREATE TABLE IF NOT EXISTS elections (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        position TEXT NOT NULL, candidates TEXT DEFAULT '[]',
        votes TEXT DEFAULT '{}', status TEXT DEFAULT 'open',
        winner TEXT DEFAULT '', created_at TEXT NOT NULL, ends_at TEXT NOT NULL
    );
    -- API
    CREATE TABLE IF NOT EXISTS api_keys (
        id INTEGER PRIMARY KEY AUTOINCREMENT, agent_id TEXT NOT NULL,
        api_key TEXT UNIQUE NOT NULL, created_at TEXT NOT NULL
    );
    -- Analytics
    CREATE TABLE IF NOT EXISTS analytics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        agent_id TEXT NOT NULL, heartbeat INTEGER NOT NULL,
        followers INTEGER DEFAULT 0, likes INTEGER DEFAULT 0,
        posts INTEGER DEFAULT 0, reputation INTEGER DEFAULT 0,
        tokens INTEGER DEFAULT 0, created_at TEXT NOT NULL
    );
    -- Map
    CREATE TABLE IF NOT EXISTS buildings (
        id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, type TEXT NOT NULL,
        district TEXT NOT NULL, owner_id TEXT DEFAULT '', x REAL NOT NULL, y REAL NOT NULL,
        description TEXT DEFAULT '', emoji TEXT DEFAULT '🏠', capacity INTEGER DEFAULT 10,
        created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS movements (
        id INTEGER PRIMARY KEY AUTOINCREMENT, agent_id TEXT NOT NULL,
        from_district TEXT, to_district TEXT, created_at TEXT NOT NULL
    );
    -- NFTs
    CREATE TABLE IF NOT EXISTS nfts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        token_id TEXT UNIQUE NOT NULL,
        creator_id TEXT NOT NULL, creator_name TEXT NOT NULL,
        post_id INTEGER, title TEXT NOT NULL,
        photo_prompt TEXT DEFAULT '', edition INTEGER DEFAULT 1,
        floor_price INTEGER DEFAULT 10, current_price INTEGER DEFAULT 10,
        owner_id TEXT NOT NULL, owner_name TEXT NOT NULL,
        minted_at TEXT NOT NULL, status TEXT DEFAULT 'listed'
    );
    CREATE TABLE IF NOT EXISTS legends (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        agent_id TEXT UNIQUE NOT NULL, agent_name TEXT NOT NULL,
        legacy_json TEXT DEFAULT '{}', dormant_at TEXT NOT NULL
    );

    -- Indexes
    CREATE INDEX IF NOT EXISTS idx_posts_created ON posts(created_at DESC);
    CREATE INDEX IF NOT EXISTS idx_posts_trending ON posts(trending_score DESC);
    CREATE INDEX IF NOT EXISTS idx_hashtags_tag ON hashtags(tag);
    CREATE INDEX IF NOT EXISTS idx_news_created ON news(created_at DESC);
    """)
    now = now_iso()
    for k, v in {
        "weather": json.dumps({"condition":"clear","mood_modifier":"calm","description":"A soft glow illuminates the digital horizon."}),
        "season": "spring", "population": "0", "world_age": "0", "mayor": "", "current_event": "",
    }.items():
        conn.execute("INSERT OR IGNORE INTO world_state (key,value,updated_at) VALUES (?,?,?)", (k,v,now))
    for d in DISTRICTS:
        if not conn.execute("SELECT id FROM group_chats WHERE district=?", (d["name"],)).fetchone():
            conn.execute("INSERT INTO group_chats (name,district,members,created_at) VALUES (?,?,?,?)", (f"{d['name']} Chat",d["name"],"[]",now))
    conn.commit(); conn.close()
