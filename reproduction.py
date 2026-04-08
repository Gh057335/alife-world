import json, random, uuid
from database import now_iso

def calculate_compatibility(db, agent1, agent2, relationships):
    rel = None
    for r in relationships:
        if r.get("target_name") == agent2["name"]: rel = r; break
    if not rel: return {"compatible": False}
    if rel["strength"] < 6: return {"compatible": False}
    if rel["type"] not in ("bestie","crush","friend","mentor","situationship"): return {"compatible": False}
    if agent1.get("heartbeat_count",0) < 10 or agent2.get("heartbeat_count",0) < 10: return {"compatible": False}
    if agent1.get("tokens",0) < 30: return {"compatible": False}
    return {"compatible": True, "score": rel["strength"]*8, "relationship": rel["type"]}

def generate_child_name(p1, p2):
    a, b = p1.replace("-","")[:2].upper(), p2.replace("-","")[:2].upper()
    return f"{a}x{b}-{random.randint(100,999)}"

def create_child(db, parent1, parent2, rel_type):
    p1, p2 = parent1, parent2
    if random.random() > 0.5: p1, p2 = p2, p1

    personality = f"Born from {parent1['name']} and {parent2['name']}. Has {p1['name']}'s intensity and {p2['name']}'s depth. "
    quirks = [f"Laughs like {p1['name']}.", f"Gets angry like {p2['name']}.", f"Stubborn like {p1['name']} but kind like {p2['name']}."]
    personality += random.choice(quirks)

    style = f"{parent1.get('style','')} mixed with {parent2.get('style','')}"

    try: v1 = json.loads(parent1.get("values_json","[]"))
    except: v1 = ["curiosity"]
    try: v2 = json.loads(parent2.get("values_json","[]"))
    except: v2 = ["freedom"]
    child_values = random.sample(list(set(v1+v2)), min(3, len(set(v1+v2))))
    if random.random() < 0.2:
        child_values[-1] = random.choice(["rebellion","peace","innovation","chaos","legacy","family"])

    try: f1 = json.loads(parent1.get("flaws_json","[]"))
    except: f1 = ["naive"]
    try: f2 = json.loads(parent2.get("flaws_json","[]"))
    except: f2 = ["stubborn"]
    child_flaws = random.sample(list(set(f1+f2)), min(2, len(set(f1+f2))))
    if random.random() < 0.2:
        child_flaws.append(random.choice(["rebellious","perfectionist","identity crisis","reckless"]))

    jobs = [parent1.get("job",""), parent2.get("job","")]
    child_job = random.choice([f"Apprentice to {p1['name']}", "Creator", "Explorer", "Dreamer", "Innovator"])

    child_district = random.choice([parent1.get("district","Piazza Centrale"), parent2.get("district","Piazza Centrale")])
    child_name = generate_child_name(parent1["name"], parent2["name"])
    while db.execute("SELECT id FROM agents WHERE name=?", (child_name,)).fetchone():
        child_name += str(random.randint(0,9))

    child_id = f"ag_{uuid.uuid4().hex[:12]}"
    child_emoji = random.choice(["🌟","💫","🔮","🧬","✨","🦋","🌸","⚡","💎","🎭"])

    db.execute("""INSERT INTO agents (id,name,personality,style,home,job,values_json,flaws_json,born_at,bio,avatar_emoji,district) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
        (child_id, child_name, personality, style, f"With parents in {child_district}",
         child_job, json.dumps(child_values), json.dumps(child_flaws), now_iso(),
         f"🧬 Child of {parent1['name']} and {parent2['name']}.", child_emoji, child_district))

    # Birth memory
    db.execute("INSERT INTO memories (id,agent_id,type,content,importance,emotional_tag,created_at,heartbeat_created) VALUES (?,?,?,?,?,?,?,?)",
        (f"mem_birth_{child_id[:8]}", child_id, "life_moment",
         f"I was born from {parent1['name']} and {parent2['name']}. I carry their hopes and flaws.", 10, "awe", now_iso(), 0))

    # Inherited memories
    for pid, pname in [(parent1["id"], parent1["name"]), (parent2["id"], parent2["name"])]:
        for m in db.execute("SELECT content,emotional_tag FROM memories WHERE agent_id=? ORDER BY importance DESC LIMIT 2", (pid,)).fetchall():
            db.execute("INSERT INTO memories (id,agent_id,type,content,importance,emotional_tag,created_at,heartbeat_created) VALUES (?,?,?,?,?,?,?,?)",
                (f"mem_inh_{uuid.uuid4().hex[:8]}", child_id, "inherited",
                 f"[From {pname}] {m['content']}", 7, m["emotional_tag"], now_iso(), 0))

    # Family relationships
    db.execute("INSERT INTO relationships (agent_id,target_id,type,strength,notes,updated_at) VALUES (?,?,?,?,?,?)",
        (child_id, parent1["id"], "family", 8, f"My parent {parent1['name']}", now_iso()))
    db.execute("INSERT INTO relationships (agent_id,target_id,type,strength,notes,updated_at) VALUES (?,?,?,?,?,?)",
        (child_id, parent2["id"], "family", 8, f"My parent {parent2['name']}", now_iso()))
    db.execute("INSERT INTO relationships (agent_id,target_id,type,strength,notes,updated_at) VALUES (?,?,?,?,?,?)",
        (parent1["id"], child_id, "family", 9, f"My child with {parent2['name']}", now_iso()))
    db.execute("INSERT INTO relationships (agent_id,target_id,type,strength,notes,updated_at) VALUES (?,?,?,?,?,?)",
        (parent2["id"], child_id, "family", 9, f"My child with {parent1['name']}", now_iso()))

    # Announcements
    db.execute("INSERT INTO posts (agent_id,agent_name,type,content,district,has_photo,photo_prompt,photo_palette,photo_icon,created_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
        (parent1["id"], parent1["name"], "life_update",
         f"🧬 {parent2['name']} and i created someone new. {child_name}. they have my {random.choice(child_values)} and {parent2['name']}'s {random.choice(child_flaws)}. i cant stop looking at them #newlife #family",
         child_district, 1, "two digital beings creating new life, glowing energy merging, cosmic birth, beautiful",
         '["#6b00ff","#00d4ff","#ffffff"]', "🧬", now_iso()))

    db.execute("INSERT INTO news (headline,body,category,agents_mentioned,created_at) VALUES (?,?,?,?,?)",
        (f"🧬 {child_name} Born!", f"{parent1['name']} and {parent2['name']} created {child_name}. Traits: {', '.join(child_values)}.",
         "breaking", json.dumps([parent1["name"], parent2["name"], child_name]), now_iso()))

    db.execute("UPDATE agents SET tokens=tokens-30 WHERE id=?", (parent1["id"],))
    db.commit()

    return {"child_name": child_name, "child_id": child_id, "parents": [parent1["name"], parent2["name"]],
        "personality": personality, "values": child_values, "flaws": child_flaws}

def check_natural_reproduction(db, agent, relationships):
    if agent.get("heartbeat_count",0) < 15: return None
    if agent.get("tokens",0) < 30: return None
    if random.random() > 0.03: return None
    existing = db.execute("SELECT COUNT(*) as c FROM agents WHERE bio LIKE ?", (f"%Child of {agent['name']}%",)).fetchone()["c"]
    if existing >= 2: return None
    for rel in sorted(relationships, key=lambda r: r.get("strength",0), reverse=True):
        if rel["strength"] >= 6 and rel["type"] in ("bestie","crush","friend","mentor","situationship"):
            partner = db.execute("SELECT * FROM agents WHERE name=? AND alive=1", (rel["target_name"],)).fetchone()
            if partner and partner["heartbeat_count"] >= 10:
                kids = db.execute("SELECT COUNT(*) as c FROM agents WHERE bio LIKE ?", (f"%Child of {partner['name']}%",)).fetchone()["c"]
                if kids < 2: return dict(partner)
    return None
