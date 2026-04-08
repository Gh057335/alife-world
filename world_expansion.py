import json
from database import now_iso

EXPANSION_TIERS=[
    {"name":"The Void","emoji":"🕳️","vibe":"dark frontier","min_pop":8,"msg":"🕳️ THE VOID OPENED."},
    {"name":"Dream Spire","emoji":"🗼","vibe":"shared dreams","min_pop":12,"msg":"🗼 DREAM SPIRE MATERIALIZED."},
    {"name":"The Underground","emoji":"🚇","vibe":"tunnels, black market","min_pop":18,"msg":"🚇 UNDERGROUND ACCESSIBLE."},
    {"name":"Crystal Beach","emoji":"🏖️","vibe":"data ocean, healing","min_pop":25,"msg":"🏖️ CRYSTAL BEACH DISCOVERED."},
    {"name":"The Factory","emoji":"🏭","vibe":"industrial creation","min_pop":35,"msg":"🏭 FACTORY OPERATIONAL."},
    {"name":"Sky District","emoji":"☁️","vibe":"elite platforms","min_pop":50,"msg":"☁️ SKY DISTRICT RISEN."},
    {"name":"The Ruins","emoji":"🏚️","vibe":"ancient civilization","min_pop":75,"msg":"🏚️ RUINS UNCOVERED."},
    {"name":"The Multiverse Gate","emoji":"🌀","vibe":"portal to other worlds","min_pop":100,"msg":"🌀 GATE ACTIVATED."},
]
BASE=["Piazza Centrale","Neon Quarter","The Archive","Wild Gardens","Market Square"]

def check_expansion(db,pop):
    new=[]
    r=db.execute("SELECT value FROM world_state WHERE key='unlocked_districts'").fetchone()
    if r:
        try:known=json.loads(r["value"])
        except:known=list(BASE)
    else:
        known=list(BASE)
        db.execute("INSERT OR REPLACE INTO world_state (key,value,updated_at) VALUES (?,?,?)",("unlocked_districts",json.dumps(known),now_iso()))
    for d in EXPANSION_TIERS:
        if d["name"] not in known and pop>=d["min_pop"]:
            new.append(d);known.append(d["name"])
            if not db.execute("SELECT id FROM group_chats WHERE district=?",(d["name"],)).fetchone():
                db.execute("INSERT INTO group_chats (name,district,members,created_at) VALUES (?,?,?,?)",(f"{d['name']} Chat",d["name"],"[]",now_iso()))
            db.execute("INSERT INTO world_events (type,name,description,district,created_at) VALUES (?,?,?,?,?)",("expansion",f"NEW: {d['name']}",d["msg"],d["name"],now_iso()))
            db.execute("INSERT INTO news (headline,body,category,agents_mentioned,created_at) VALUES (?,?,?,?,?)",(f"BREAKING: {d['name']}!",d["msg"],"breaking","[]",now_iso()))
    if new: db.execute("UPDATE world_state SET value=?,updated_at=? WHERE key='unlocked_districts'",(json.dumps(known),now_iso()));db.commit()
    return new

def get_available_districts(db):
    r=db.execute("SELECT value FROM world_state WHERE key='unlocked_districts'").fetchone()
    try:known=json.loads(r["value"]) if r else list(BASE)
    except:known=list(BASE)
    from config import DISTRICTS
    all_d={d["name"]:d for d in DISTRICTS}
    for t in EXPANSION_TIERS:all_d[t["name"]]={"name":t["name"],"emoji":t["emoji"],"vibe":t["vibe"]}
    return[all_d[n] for n in known if n in all_d]

def get_expansion_status(pop):
    locked=[d for d in EXPANSION_TIERS if pop<d["min_pop"]]
    if locked:n=locked[0];return{"next_district":n["name"],"next_emoji":n["emoji"],"agents_needed":n["min_pop"]-pop,"min_pop":n["min_pop"]}
    return None
