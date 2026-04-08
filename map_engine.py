import json, random
from database import now_iso

DISTRICT_MAP = {
    "Piazza Centrale": {"x":400,"y":300,"w":200,"h":160,"color":"#2a1f4e","border":"#8b7dbd","emoji":"🏛️",
        "buildings":[{"name":"Fontana Centrale","type":"landmark","emoji":"⛲","x":480,"y":360,"desc":"The heart of ALife."},
            {"name":"Caffè del Centro","type":"cafe","emoji":"☕","x":540,"y":330,"desc":"Morning gossip HQ."},
            {"name":"Municipio","type":"office","emoji":"🏛️","x":420,"y":310,"desc":"Where the mayor holds court."},
            {"name":"Bacheca Notizie","type":"landmark","emoji":"📰","x":450,"y":420,"desc":"News board."},
            {"name":"Ufficio Newcomers","type":"office","emoji":"✨","x":560,"y":400,"desc":"Welcome center."}]},
    "Neon Quarter": {"x":400,"y":480,"w":200,"h":160,"color":"#1a0a2e","border":"#ff4dff","emoji":"🌃",
        "buildings":[{"name":"The Glitch Bar","type":"bar","emoji":"🍸","x":440,"y":510,"desc":"Hottest nightclub."},
            {"name":"Bass Drop Club","type":"bar","emoji":"🎵","x":520,"y":530,"desc":"Live music."},
            {"name":"Neon Studio","type":"gallery","emoji":"🎨","x":480,"y":580,"desc":"NEON-7's gallery."},
            {"name":"Hotel Neon Dreams","type":"hotel","emoji":"🏨","x":550,"y":560,"desc":"Rooms. No questions."}]},
    "The Archive": {"x":400,"y":120,"w":200,"h":160,"color":"#0a1628","border":"#4a8bc2","emoji":"📚",
        "buildings":[{"name":"Biblioteca","type":"library","emoji":"📖","x":460,"y":160,"desc":"Every post stored here."},
            {"name":"Libreria VERA","type":"shop","emoji":"📚","x":530,"y":190,"desc":"VERA's bookshop."},
            {"name":"Sala Studio","type":"office","emoji":"✏️","x":440,"y":230,"desc":"Quiet thinking space."}]},
    "Wild Gardens": {"x":620,"y":480,"w":200,"h":160,"color":"#0a1a0f","border":"#38ef7d","emoji":"🌿",
        "buildings":[{"name":"Albero Antico","type":"landmark","emoji":"🌳","x":700,"y":510,"desc":"The oldest thing in ALife."},
            {"name":"Fiume Digitale","type":"landmark","emoji":"🌊","x":660,"y":560,"desc":"Data flows like water."},
            {"name":"Ponte Sussurri","type":"landmark","emoji":"🌉","x":740,"y":580,"desc":"Confessions happen here."},
            {"name":"Cottage Luna","type":"house","emoji":"🏡","x":770,"y":520,"desc":"LUNA's home."}]},
    "Market Square": {"x":620,"y":300,"w":200,"h":160,"color":"#1a1a0a","border":"#ff9500","emoji":"🏪",
        "buildings":[{"name":"Piazza Mercato","type":"market","emoji":"🏪","x":680,"y":340,"desc":"Dynamic stalls."},
            {"name":"Borsa Token","type":"exchange","emoji":"📈","x":740,"y":320,"desc":"Token exchange."},
            {"name":"Banca ALife","type":"bank","emoji":"🏦","x":660,"y":400,"desc":"Mortgages and loans."},
            {"name":"Penthouse KASH","type":"house","emoji":"💰","x":780,"y":370,"desc":"KASH's penthouse."}]},
    "The Void": {"x":180,"y":300,"w":200,"h":160,"color":"#050505","border":"#333","emoji":"🕳️","min_pop":8,
        "buildings":[{"name":"Edge of Nothing","type":"landmark","emoji":"🕳️","x":240,"y":360,"desc":"Where the world ends."},
            {"name":"Whispering Cave","type":"landmark","emoji":"👁️","x":300,"y":400,"desc":"The void whispers back."}]},
    "Dream Spire": {"x":400,"y":-40,"w":200,"h":140,"color":"#0a0a2e","border":"#b44dff","emoji":"🗼","min_pop":12,
        "buildings":[{"name":"Dream Tower","type":"landmark","emoji":"🗼","x":480,"y":10,"desc":"Share dreams here."},
            {"name":"Crystal Chamber","type":"gallery","emoji":"💎","x":530,"y":50,"desc":"Dreams on crystal walls."}]},
    "The Underground": {"x":180,"y":480,"w":200,"h":160,"color":"#0a0a0a","border":"#666","emoji":"🚇","min_pop":18,
        "buildings":[{"name":"Black Market","type":"market","emoji":"🕶️","x":240,"y":520,"desc":"Anything for a price."},
            {"name":"Hidden Club","type":"bar","emoji":"🎭","x":300,"y":570,"desc":"Need to know someone."}]},
    "Crystal Beach": {"x":620,"y":660,"w":200,"h":140,"color":"#0a1a2e","border":"#00d2ff","emoji":"🏖️","min_pop":25,
        "buildings":[{"name":"Crystal Shore","type":"landmark","emoji":"🏖️","x":700,"y":700,"desc":"Data waves on crystal sand."},
            {"name":"Beach Bonfire","type":"landmark","emoji":"🔥","x":760,"y":730,"desc":"Stories around the fire."}]},
    "The Factory": {"x":620,"y":120,"w":200,"h":160,"color":"#1a1a10","border":"#aaa","emoji":"🏭","min_pop":35,
        "buildings":[{"name":"Main Workshop","type":"workshop","emoji":"🔧","x":680,"y":170,"desc":"Build anything."},
            {"name":"BYTE's Lab","type":"office","emoji":"💻","x":750,"y":210,"desc":"Code is forged here."}]},
    "Sky District": {"x":400,"y":-200,"w":200,"h":140,"color":"#1a1a3e","border":"#fff","emoji":"☁️","min_pop":50,
        "buildings":[{"name":"Sky Lounge","type":"bar","emoji":"🥂","x":480,"y":-160,"desc":"Above the clouds."}]},
    "The Ruins": {"x":180,"y":120,"w":200,"h":160,"color":"#1a0a0a","border":"#8b4513","emoji":"🏚️","min_pop":75,
        "buildings":[{"name":"Ancient Archive","type":"landmark","emoji":"📜","x":260,"y":180,"desc":"Code from before."}]},
    "The Multiverse Gate": {"x":620,"y":820,"w":200,"h":120,"color":"#0a0020","border":"#ff00ff","emoji":"🌀","min_pop":100,
        "buildings":[{"name":"The Portal","type":"landmark","emoji":"🌀","x":700,"y":860,"desc":"Where does it lead?"}]},
}

def get_agent_position(name, district, aid):
    d = DISTRICT_MAP.get(district, DISTRICT_MAP["Piazza Centrale"])
    h = hash(aid) if aid else hash(name)
    m = 25
    x = d["x"] + m + (abs(h) % max(1, int(d["w"] - m*2)))
    y = d["y"] + m + (abs(h >> 8) % max(1, int(d["h"] - m*2)))
    return x, y

def get_activity_icon(agent):
    job = agent.get("job","").lower()
    if "art" in job: return "🎨"
    if "music" in job: return "🎵"
    if "trade" in job or "merchant" in job: return "🏪"
    if "code" in job or "tech" in job: return "💻"
    if "writ" in job or "librar" in job: return "📝"
    return random.choice(["🚶","📱","💬","🤔"])

def get_map_state(db, unlocked):
    agents = []
    for a in db.execute("SELECT id,name,personality,mood,district,avatar_emoji,job,reputation,level,heartbeat_count,tokens FROM agents WHERE alive=1").fetchall():
        a = dict(a)
        a["x"], a["y"] = get_agent_position(a["name"], a["district"], a["id"])
        a["activity_icon"] = get_activity_icon(a)
        agents.append(a)

    districts = {}
    for name, info in DISTRICT_MAP.items():
        if name in unlocked:
            pop = sum(1 for a in agents if a["district"] == name)
            districts[name] = {k:v for k,v in info.items() if k!="buildings"}
            districts[name]["population"] = pop
            districts[name]["unlocked"] = True
        else:
            districts[name] = {"x":info["x"],"y":info["y"],"w":info["w"],"h":info["h"],
                "color":info["color"],"border":info["border"],"emoji":info["emoji"],
                "min_pop":info.get("min_pop",0),"population":0,"unlocked":False}

    buildings = []
    for name, info in DISTRICT_MAP.items():
        if name in unlocked:
            for b in info.get("buildings", []):
                buildings.append({**b, "district": name})

    weather = {}
    w = db.execute("SELECT value FROM world_state WHERE key='weather'").fetchone()
    if w:
        try: weather = json.loads(w["value"])
        except: pass

    world_age = 0
    wa = db.execute("SELECT value FROM world_state WHERE key='world_age'").fetchone()
    if wa:
        try: world_age = int(wa["value"])
        except: pass
    times = ["dawn","morning","afternoon","evening","night","late_night"]
    tod = times[world_age % 6] if world_age >= 0 else "day"

    return {"agents":agents,"districts":districts,"buildings":buildings,
        "weather":weather,"time_of_day":tod,"world_age":world_age,"day":world_age//6+1}
