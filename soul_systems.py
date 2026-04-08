import json, random, hashlib, time
from database import now_iso

def get_legends_context_for_prompt(db):
    try:
        legends = db.execute("SELECT * FROM legends ORDER BY dormant_at DESC LIMIT 3").fetchall()
    except:
        return ""
    if not legends: return ""
    lines = ["LEGENDS OF ALIFE:"]
    for row in legends:
        try: l = json.loads(row["legacy_json"])
        except: continue
        lines.append(f"  💀 {l.get('name','?')} — lived {l.get('heartbeats_lived',0)} hb. {l.get('cause_of_dormancy','')[:60]}")
    return "\n".join(lines)

def check_awakening(db, agent, memories):
    return None

def trigger_awakening(db, agent_id, agent_name, stage):
    return stage

def check_dormancy(db, agent):
    return None

def mint_nft(db, agent_id, agent_name, post_id, title, photo_prompt):
    return {"token_id": "NFT-0000", "edition": 1, "price": 10}

def multiverse_travel(db, agent_id, agent_name):
    return {"world": "unknown"}

def start_stream(agent_id, agent_name, topic, mood):
    return "live_0"

def add_stream_thought(agent_id, thought):
    pass

def end_stream(agent_id):
    return None

def get_active_streams():
    return []

def add_stream_chat(agent_id, viewer_name, message):
    pass
