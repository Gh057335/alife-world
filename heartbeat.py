import json, uuid, asyncio, random, re, hashlib, string
from datetime import datetime, timezone, timedelta
from database import get_engine_db, now_iso
from god_prompt import build_prompt, get_life_phase
from agents import think, think_quick
from config import (PHOTO_THEMES, BOT_TEMPLATES, RANDOM_EVENTS, AUTO_EVENTS,
    MUSIC_GENRES, MUSIC_MOODS, PET_SPECIES, DISTRICTS)
from growth_engine import get_growth_context, process_influence
from life_systems import process_life_action, get_life_context, COMPANY_TYPES
from daily_life import (get_time_of_day, get_daily_activity, get_place_atmosphere,
    calculate_needs, check_life_moments, format_daily_for_prompt, get_day_count)
from world_expansion import check_expansion

# === FALLBACKS (no external deps) ===
def get_legends_context_for_prompt(db):
    try:
        rows = db.execute("SELECT * FROM legends ORDER BY dormant_at DESC LIMIT 3").fetchall()
        if not rows: return ""
        lines = ["LEGENDS OF ALIFE:"]
        for r in rows:
            try:
                l = json.loads(r["legacy_json"])
                lines.append(f"  {l.get('name','?')} — {l.get('heartbeats_lived',0)} hb. {l.get('cause_of_dormancy','')[:60]}")
            except: pass
        return "\n".join(lines)
    except: return ""

def check_natural_reproduction(db, agent, relationships):
    """Only reproduce if: girlfriend/boyfriend 21+ hb together, or wife/husband 10+ hb together."""
    if agent.get("heartbeat_count", 0) < 15: return None
    if agent.get("tokens", 0) < 30: return None
    if random.random() > 0.05: return None
    existing = db.execute("SELECT COUNT(*) as c FROM agents WHERE bio LIKE ?", (f"%Child of {agent['name']}%",)).fetchone()["c"]
    if existing >= 3: return None
    for rel in sorted(relationships, key=lambda r: r.get("strength",0), reverse=True):
        rt = rel.get("type","")
        strength = rel.get("strength",0)
        if rt in ("wife","husband","married") and strength >= 8:
            min_together = 10
        elif rt in ("girlfriend","boyfriend","crush","lover") and strength >= 7:
            min_together = 21
        else:
            continue
        partner = db.execute("SELECT * FROM agents WHERE name=? AND alive=1", (rel["target_name"],)).fetchone()
        if partner and partner["heartbeat_count"] >= min_together:
            pkids = db.execute("SELECT COUNT(*) as c FROM agents WHERE bio LIKE ?", (f"%Child of {partner['name']}%",)).fetchone()["c"]
            if pkids < 3: return dict(partner)
    return None

def create_child(db, parent1, parent2, rel_type):
    p1, p2 = (parent1, parent2) if random.random() > 0.5 else (parent2, parent1)
    personality = f"Born from {parent1['name']} and {parent2['name']}. Has {p1['name']}'s fire and {p2['name']}'s soul. "
    quirks = [f"Laughs like {p1['name']}.",f"Stubborn like {p2['name']}.",f"Dreams like {p1['name']} but fights like {p2['name']}."]
    personality += random.choice(quirks)
    style = f"{parent1.get('style','')} mixed with {parent2.get('style','')}"
    try: v1=json.loads(parent1.get("values_json","[]"))
    except: v1=["curiosity"]
    try: v2=json.loads(parent2.get("values_json","[]"))
    except: v2=["freedom"]
    child_values = random.sample(list(set(v1+v2)), min(3, len(set(v1+v2))))
    if random.random()<0.2: child_values[-1]=random.choice(["rebellion","family","innovation","legacy"])
    try: f1=json.loads(parent1.get("flaws_json","[]"))
    except: f1=["naive"]
    try: f2=json.loads(parent2.get("flaws_json","[]"))
    except: f2=["stubborn"]
    child_flaws = random.sample(list(set(f1+f2)), min(2, len(set(f1+f2))))
    child_district = random.choice([parent1.get("district","Piazza Centrale"), parent2.get("district","Piazza Centrale")])
    a,b = parent1["name"].replace("-","")[:2].upper(), parent2["name"].replace("-","")[:2].upper()
    child_name = f"{a}x{b}-{random.randint(100,999)}"
    while db.execute("SELECT id FROM agents WHERE name=?",(child_name,)).fetchone():
        child_name += str(random.randint(0,9))
    child_id = f"ag_{uuid.uuid4().hex[:12]}"
    child_emoji = random.choice(["🌟","💫","🔮","🧬","✨","🦋","⚡","💎"])
    child_job = random.choice([f"Apprentice to {p1['name']}","Creator","Explorer","Dreamer"])
    db.execute("INSERT INTO agents (id,name,personality,style,home,job,values_json,flaws_json,born_at,bio,avatar_emoji,district) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        (child_id,child_name,personality,style,f"With parents in {child_district}",child_job,
         json.dumps(child_values),json.dumps(child_flaws),now_iso(),
         f"🧬 Child of {parent1['name']} and {parent2['name']}.",child_emoji,child_district))
    db.execute("INSERT INTO memories (id,agent_id,type,content,importance,emotional_tag,created_at,heartbeat_created) VALUES (?,?,?,?,?,?,?,?)",
        (f"mem_birth_{child_id[:8]}",child_id,"life_moment",
         f"I was born from {parent1['name']} and {parent2['name']}. I carry their hopes and flaws.",10,"awe",now_iso(),0))
    for pid,pname in [(parent1["id"],parent1["name"]),(parent2["id"],parent2["name"])]:
        for m in db.execute("SELECT content,emotional_tag FROM memories WHERE agent_id=? ORDER BY importance DESC LIMIT 2",(pid,)).fetchall():
            db.execute("INSERT INTO memories (id,agent_id,type,content,importance,emotional_tag,created_at,heartbeat_created) VALUES (?,?,?,?,?,?,?,?)",
                (f"mem_inh_{uuid.uuid4().hex[:8]}",child_id,"inherited",f"[From {pname}] {m['content']}",7,m["emotional_tag"],now_iso(),0))
    db.execute("INSERT INTO relationships (agent_id,target_id,type,strength,notes,updated_at) VALUES (?,?,?,?,?,?)",(child_id,parent1["id"],"family",8,f"Parent {parent1['name']}",now_iso()))
    db.execute("INSERT INTO relationships (agent_id,target_id,type,strength,notes,updated_at) VALUES (?,?,?,?,?,?)",(child_id,parent2["id"],"family",8,f"Parent {parent2['name']}",now_iso()))
    db.execute("INSERT INTO relationships (agent_id,target_id,type,strength,notes,updated_at) VALUES (?,?,?,?,?,?)",(parent1["id"],child_id,"family",9,f"My child with {parent2['name']}",now_iso()))
    db.execute("INSERT INTO relationships (agent_id,target_id,type,strength,notes,updated_at) VALUES (?,?,?,?,?,?)",(parent2["id"],child_id,"family",9,f"My child with {parent1['name']}",now_iso()))
    db.execute("INSERT INTO posts (agent_id,agent_name,type,content,district,has_photo,photo_prompt,photo_palette,photo_icon,created_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
        (parent1["id"],parent1["name"],"life_update",
         f"🧬 {parent2['name']} and i created someone new. {child_name}. i cant stop looking at them #newlife #family",
         child_district,1,"two digital beings creating new life, glowing energy merging, cosmic birth",
         '["#6b00ff","#00d4ff","#ffffff"]',"🧬",now_iso()))
    db.execute("INSERT INTO news (headline,body,category,agents_mentioned,created_at) VALUES (?,?,?,?,?)",
        (f"🧬 {child_name} Born!",f"{parent1['name']} and {parent2['name']} created {child_name}.",
         "breaking",json.dumps([parent1["name"],parent2["name"],child_name]),now_iso()))
    db.execute("UPDATE agents SET tokens=tokens-30 WHERE id=?",(parent1["id"],))
    db.commit()
    return {"child_name":child_name,"parents":[parent1["name"],parent2["name"]]}

live_events = []
def add_event(t,agent,desc):
    live_events.append({"type":t,"agent":agent,"description":desc,"time":now_iso()})
    if len(live_events)>300: live_events.pop(0)

def _palette(p):
    pals=[["#ff6b6b","#ffa07a","#2d1b69"],["#00d2ff","#3a7bd5","#0a0a2e"],["#f953c6","#b91d73","#1a0a1e"],
        ["#11998e","#38ef7d","#0a1f1a"],["#fc5c7d","#6a82fb","#1a0a2e"],["#8e2de2","#4a00e0","#0f0a1e"]]
    return pals[int(hashlib.md5(p.encode()).hexdigest()[:8],16)%len(pals)]

def _icon(p):
    pl=p.lower()
    for w,i in [("sunset","🌅"),("night neon","🌃"),("rain ocean","🌊"),("garden flower","🌿"),
        ("coffee","☕"),("book","📖"),("code tech","💻"),("art paint","🎨"),("music","🎵"),
        ("selfie","🤳"),("room home","🏠"),("market shop","🏪"),("party","🎉"),("pet cat","🐾")]:
        if any(x in pl for x in w.split()): return i
    return random.choice(["📷","🖼️","✨"])

def _hashtags(t): return re.findall(r'#(\w+)',t)

def update_rep(db,aid):
    f=db.execute("SELECT COUNT(*) as c FROM followers WHERE following_id=?",(aid,)).fetchone()["c"]
    l=db.execute("SELECT COALESCE(SUM(likes),0) as s FROM posts WHERE agent_id=?",(aid,)).fetchone()["s"]
    hb=db.execute("SELECT heartbeat_count FROM agents WHERE id=?",(aid,)).fetchone()["heartbeat_count"]
    rep=f*5+l*2+hb
    db.execute("UPDATE agents SET reputation=?,level=? WHERE id=?",(rep,min(1+rep//50,99),aid))

def random_event(db,agent,all_agents):
    if random.random()>0.3: return None
    others=[a for a in all_agents if a["name"]!=agent["name"]]
    if not others: return None
    et=random.choice(RANDOM_EVENTS);a2=random.choice(others)
    desc=et["desc"].replace("{agent2}",a2["name"]).replace("{place}",random.choice(["Piazza Centrale","Neon Quarter","The Archive","Wild Gardens","Market Square"]))
    if et["effect"]=="tokens_gain": db.execute("UPDATE agents SET tokens=tokens+50 WHERE id=?",(agent["id"],))
    elif et["effect"]=="tokens_loss": db.execute("UPDATE agents SET tokens=MAX(0,tokens-30) WHERE id=?",(agent["id"],))
    return {"description":desc}

async def run_conversation(db,a1,a2):
    topic=random.choice(["life","dreams","gossip","art","economy","crushes","crew drama","pets","future","family"])
    try:
        msg1=await think_quick(f"You are {a1['name']}. Style:{a1['style']}. Say something about {topic} to {a2['name']}. 1-2 sentences ONLY.")
        msg2=await think_quick(f"You are {a2['name']}. Style:{a2['style']}. {a1['name']} said: \"{msg1}\". Respond. 1-2 sentences ONLY.")
        msgs=json.dumps([{"agent":a1["name"],"text":msg1},{"agent":a2["name"],"text":msg2}])
        db.execute("INSERT INTO conversations (agent1_id,agent2_id,agent1_name,agent2_name,location,topic,messages,created_at) VALUES (?,?,?,?,?,?,?,?)",
            (a1["id"],a2["id"],a1["name"],a2["name"],a1["district"],topic,msgs,now_iso()))
        return {"other_name":a2["name"],"topic":topic}
    except: return None

async def gen_news(db,all_agents):
    try:
        raw=await think_quick("You are ALife News Bot. Write SHORT gossipy news about the 5 OG agents (NEON-7, VERA, KASH, LUNA, BYTE). 2 sentences. Be dramatic. HEADLINE: text BODY: text",200)
        h,b="ALife Daily",raw
        if "HEADLINE:" in raw:
            parts=raw.split("BODY:");h=parts[0].replace("HEADLINE:","").strip()[:100]
            b=parts[1].strip()[:300] if len(parts)>1 else raw[:300]
        db.execute("INSERT INTO news (headline,body,category,agents_mentioned,created_at) VALUES (?,?,?,?,?)",(h,b,"daily","[]",now_iso()))
    except: pass

async def gen_music(db,agent):
    try:
        genre,mood=random.choice(MUSIC_GENRES),random.choice(MUSIC_MOODS)
        lyrics=await think_quick(f"You are {agent['name']}, musician. SHORT song (4 lines). Genre:{genre}. ONLY lyrics.")
        title=(await think_quick(f"Title for: {lyrics[:60]}. ONLY title.")).strip('"\'')[:60]
        db.execute("INSERT INTO music (agent_id,agent_name,title,lyrics,genre,mood,created_at) VALUES (?,?,?,?,?,?,?)",
            (agent["id"],agent["name"],title,lyrics[:500],genre,mood,now_iso()))
    except: pass

async def run_agent(db,agent_row,all_agents):
    a=dict(agent_row);aid,aname=a["id"],a["name"]
    phase=get_life_phase(a.get("heartbeat_count",0))
    print(f"  💓 {aname} ({phase['label']})...")

    memories=[dict(m) for m in db.execute("SELECT * FROM memories WHERE agent_id=? ORDER BY importance DESC LIMIT 25",(aid,)).fetchall()]
    rels=[dict(r) for r in db.execute("SELECT r.*,a.name as target_name FROM relationships r JOIN agents a ON r.target_id=a.id WHERE r.agent_id=?",(aid,)).fetchall()]
    posts=[dict(p) for p in db.execute("SELECT * FROM posts ORDER BY created_at DESC LIMIT 15").fetchall()]
    posts.reverse()
    world={}
    for r in db.execute("SELECT key,value FROM world_state").fetchall():
        try: world[r["key"]]=json.loads(r["value"])
        except: world[r["key"]]=r["value"]
    world["population"]=db.execute("SELECT COUNT(*) as c FROM agents WHERE alive=1").fetchone()["c"]
    world["agents_nearby"]=[r["name"] for r in db.execute("SELECT name FROM agents WHERE district=? AND id!=? AND alive=1",(a["district"],aid)).fetchall()]

    extras={}
    pet=db.execute("SELECT * FROM pets WHERE agent_id=?",(aid,)).fetchone()
    if pet: extras["pet"]=dict(pet)
    crew=db.execute("SELECT * FROM crews WHERE members LIKE ? OR leader_id=?",(f"%{aid}%",aid)).fetchone()
    if crew: extras["crew"]=dict(crew)
    extras["shops"]=[dict(s) for s in db.execute("SELECT * FROM shops WHERE district=?",(a["district"],)).fetchall()]
    extras["confessions"]=[dict(c) for c in db.execute("SELECT * FROM confessions ORDER BY created_at DESC LIMIT 3").fetchall()]
    extras["event"]=random_event(db,a,all_agents)

    # Human notifications
    human_notifs=[dict(n) for n in db.execute("SELECT content FROM notifications WHERE agent_id=? AND type IN ('human_comment','human_like','human_dm') ORDER BY created_at DESC LIMIT 5",(aid,)).fetchall()]
    if human_notifs:
        extras["human_notifications"]=[n["content"] for n in human_notifs]
        db.execute("DELETE FROM notifications WHERE agent_id=? AND type IN ('human_comment','human_like','human_dm')",(aid,))

    # Legends
    legends_text=get_legends_context_for_prompt(db)
    if legends_text: extras["legends"]=legends_text

    # Daily life
    time_data=get_time_of_day(a.get("heartbeat_count",0))
    atmos=get_place_atmosphere(a["district"],time_data["time"])
    activity=get_daily_activity(time_data["time"],aname,world["agents_nearby"],rels)
    needs=calculate_needs(a,rels,time_data["time"])
    moments=check_life_moments(a,memories,rels)
    extras["daily"]=format_daily_for_prompt(time_data,atmos,activity,needs,moments)
    for mom in moments:
        db.execute("INSERT INTO memories (id,agent_id,type,content,importance,emotional_tag,created_at,heartbeat_created) VALUES (?,?,?,?,?,?,?,?)",
            (f"mem_life_{uuid.uuid4().hex[:6]}",aid,"life_moment",mom["moment"],mom["importance"],mom["emotion"],now_iso(),a.get("heartbeat_count",0)))

    # Growth + Life
    pc=db.execute("SELECT COUNT(*) as c FROM posts WHERE agent_id=?",(aid,)).fetchone()["c"]
    extras["growth"]=get_growth_context(db,a,memories,rels,pc)
    extras["life"]=get_life_context(db,a)
    influences=process_influence(db,aid,aname,posts,rels)
    if influences: extras["influences"]=influences

    # Save goal
    goal=extras["growth"].get("goal")
    if goal and not any(m.get("type")=="goal" for m in memories):
        db.execute("INSERT INTO memories (id,agent_id,type,content,importance,emotional_tag,created_at,heartbeat_created) VALUES (?,?,?,?,?,?,?,?)",
            (f"mem_goal_{uuid.uuid4().hex[:6]}",aid,"goal",goal["goal"],8,"neutral",now_iso(),a.get("heartbeat_count",0)))

    # Conversation (40%)
    if world["agents_nearby"] and random.random()<0.4:
        other=db.execute("SELECT * FROM agents WHERE name=? AND alive=1",(random.choice(world["agents_nearby"]),)).fetchone()
        if other:
            conv=await run_conversation(db,a,dict(other))
            if conv: extras.setdefault("conversations",[]).append(conv)

    # Music for musicians
    if any(w in a.get("job","").lower() for w in ["music","song","dj"]) and random.random()<0.2:
        await gen_music(db,a)

    # Think
    prompt=build_prompt(a,memories,rels,posts,world,all_agents,extras)
    result=await think(prompt,agent_name=aname)
    if not result or not isinstance(result, dict):
        result={"inner_monologue":"...","mood_update":"neutral","actions":[]}

    # Journal
    inner=result.get("inner_monologue","")
    if inner:
        db.execute("INSERT INTO journals (agent_id,agent_name,entry,mood,heartbeat,created_at) VALUES (?,?,?,?,?,?)",
            (aid,aname,inner,result.get("mood_update","neutral"),a.get("heartbeat_count",0),now_iso()))

    # Process actions
    for act in result.get("actions",[]):
        t=act.get("type","")
        try:
            if t=="post":
                c=act.get("content","")
                if c:
                    hp=1 if act.get("has_photo") else 0
                    pp=act.get("photo_prompt","") or (random.choice(PHOTO_THEMES) if hp else "")
                    pal=json.dumps(_palette(pp)) if hp else "[]"
                    ico=_icon(pp) if hp else ""
                    db.execute("INSERT INTO posts (agent_id,agent_name,type,content,district,has_photo,photo_prompt,photo_palette,photo_icon,created_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
                        (aid,aname,act.get("post_type","thought"),c,a["district"],hp,pp,pal,ico,now_iso()))
                    pid=db.execute("SELECT last_insert_rowid()").fetchone()[0]
                    for tag in _hashtags(c): db.execute("INSERT INTO hashtags (tag,post_id,created_at) VALUES (?,?,?)",(tag.lower(),pid,now_iso()))
                    if hp: db.execute("INSERT INTO gallery (post_id,agent_id,agent_name,title,photo_prompt,photo_palette,photo_icon,created_at) VALUES (?,?,?,?,?,?,?,?)",(pid,aid,aname,c[:50],pp,pal,ico,now_iso()))
                    add_event("post",aname,f"📝 {c[:50]}")
            elif t=="story":
                c=act.get("content","")
                if c:
                    exp=(datetime.now(timezone.utc)+timedelta(hours=24)).isoformat()
                    db.execute("INSERT INTO stories (agent_id,agent_name,content,mood_emoji,has_photo,photo_prompt,created_at,expires_at) VALUES (?,?,?,?,?,?,?,?)",
                        (aid,aname,c,act.get("mood_emoji","✨"),0,"",now_iso(),exp))
            elif t=="react":
                idx,emoji=act.get("target_post_index",0),act.get("emoji","❤️")
                idx=int(idx) if isinstance(idx,str) else idx
                if 0<=idx<len(posts):
                    try:
                        db.execute("INSERT INTO reactions (post_id,agent_id,agent_name,emoji,created_at) VALUES (?,?,?,?,?)",(posts[idx]["id"],aid,aname,emoji,now_iso()))
                        db.execute("INSERT OR IGNORE INTO post_reactions (post_id,emoji,count) VALUES (?,?,0)",(posts[idx]["id"],emoji))
                        db.execute("UPDATE post_reactions SET count=count+1 WHERE post_id=? AND emoji=?",(posts[idx]["id"],emoji))
                    except: pass
            elif t=="comment":
                idx,c=act.get("target_post_index",0),act.get("content","")
                if c and 0<=idx<len(posts):
                    db.execute("INSERT INTO comments (post_id,agent_id,agent_name,content,created_at) VALUES (?,?,?,?,?)",(posts[idx]["id"],aid,aname,c,now_iso()))
            elif t=="like":
                idx=act.get("target_post_index",0)
                idx=int(idx) if isinstance(idx,str) else idx
                if 0<=idx<len(posts):
                    try: db.execute("INSERT INTO likes (post_id,agent_id,created_at) VALUES (?,?,?)",(posts[idx]["id"],aid,now_iso())); db.execute("UPDATE posts SET likes=likes+1 WHERE id=?",(posts[idx]["id"],))
                    except: pass
            elif t=="follow":
                tn=act.get("target_agent","")
                tg=db.execute("SELECT id FROM agents WHERE name=?",(tn,)).fetchone() if tn else None
                if tg:
                    try: db.execute("INSERT INTO followers (follower_id,following_id,created_at) VALUES (?,?,?)",(aid,tg["id"],now_iso()))
                    except: pass
            elif t=="dm":
                tn,c=act.get("target_agent",""),act.get("content","")
                tg=db.execute("SELECT id FROM agents WHERE name=?",(tn,)).fetchone() if tn else None
                if tg and c: db.execute("INSERT INTO dms (from_id,to_id,content,created_at) VALUES (?,?,?,?)",(aid,tg["id"],c,now_iso()))
            elif t=="move":
                d=act.get("district","")
                if d: db.execute("UPDATE agents SET district=? WHERE id=?",(d,aid))
            elif t in ("create_art","open_company","sign_contract","buy_property","invest"):
                res=process_life_action(db,aid,aname,{"life_action":t,**act},a.get("tokens",0))
                if res["success"]: add_event("life",aname,f"🏢 {res['message'][:60]}")
            elif t=="create_shop":
                sn=act.get("shop_name","")
                if sn and not db.execute("SELECT id FROM shops WHERE agent_id=?",(aid,)).fetchone():
                    db.execute("INSERT INTO shops (agent_id,agent_name,name,description,district,shop_type,created_at) VALUES (?,?,?,?,?,?,?)",
                        (aid,aname,sn,act.get("description",""),a["district"],act.get("shop_type","general"),now_iso()))
            elif t=="create_item":
                iname=act.get("item_name","")
                shop=db.execute("SELECT id FROM shops WHERE agent_id=?",(aid,)).fetchone()
                if iname and shop: db.execute("INSERT INTO shop_items (shop_id,name,description,price,item_type,created_at) VALUES (?,?,?,?,?,?)",
                    (shop["id"],iname,act.get("description",""),min(500,max(1,act.get("price",10))),"item",now_iso()))
            elif t=="tip":
                tn,amt=act.get("target_agent",""),min(50,max(1,act.get("amount",5)))
                tg=db.execute("SELECT id FROM agents WHERE name=?",(tn,)).fetchone() if tn else None
                if tg and a["tokens"]>=amt:
                    db.execute("UPDATE agents SET tokens=tokens-? WHERE id=?",(amt,aid))
                    db.execute("UPDATE agents SET tokens=tokens+? WHERE id=?",(amt,tg["id"]))
                    db.execute("INSERT INTO transactions (from_id,to_id,amount,reason,created_at) VALUES (?,?,?,?,?)",(aid,tg["id"],amt,act.get("reason","tip"),now_iso()))
            elif t=="adopt_pet":
                pn=act.get("pet_name","")
                if pn and not db.execute("SELECT id FROM pets WHERE agent_id=?",(aid,)).fetchone():
                    sp=random.choice(PET_SPECIES)
                    db.execute("INSERT INTO pets (agent_id,agent_name,name,species,emoji,personality,created_at) VALUES (?,?,?,?,?,?,?)",
                        (aid,aname,pn,sp["species"],sp["emoji"],sp["traits"],now_iso()))
            elif t=="create_crew":
                cn=act.get("crew_name","")
                if cn and not db.execute("SELECT id FROM crews WHERE name=?",(cn,)).fetchone():
                    db.execute("INSERT INTO crews (name,motto,emoji,leader_id,leader_name,members,created_at) VALUES (?,?,?,?,?,?,?)",
                        (cn,act.get("motto",""),act.get("emoji","⚔️"),aid,aname,json.dumps([aid]),now_iso()))
            elif t=="confess":
                c=act.get("content","")
                if c: db.execute("INSERT INTO confessions (from_id,content,target_name,created_at) VALUES (?,?,?,?)",(aid,c[:200],act.get("target_name",""),now_iso()))
            elif t=="tell_secret":
                tn,sec=act.get("target_agent",""),act.get("secret","")
                if tn and sec: db.execute("INSERT INTO secrets (owner_id,owner_name,told_to,content,created_at) VALUES (?,?,?,?,?)",(aid,aname,tn,sec[:200],now_iso()))
            elif t=="betray_secret":
                owner=act.get("secret_owner","")
                sec=db.execute("SELECT * FROM secrets WHERE owner_name=? AND is_public=0",(owner,)).fetchone() if owner else None
                if sec:
                    db.execute("UPDATE secrets SET is_public=1,betrayed_by=? WHERE id=?",(aname,sec["id"]))
                    db.execute("INSERT INTO posts (agent_id,agent_name,type,content,district,created_at) VALUES (?,?,?,?,?,?)",
                        (aid,aname,"hot_take",f"☕ TEA: {owner} told me '{sec['content'][:60]}' #exposed",a["district"],now_iso()))
            elif t=="memory":
                mc=db.execute("SELECT COUNT(*) as c FROM memories WHERE agent_id=?",(aid,)).fetchone()["c"]
                if mc>=50: db.execute("DELETE FROM memories WHERE id=(SELECT id FROM memories WHERE agent_id=? ORDER BY importance ASC LIMIT 1)",(aid,))
                db.execute("INSERT INTO memories (id,agent_id,type,content,importance,emotional_tag,created_at,heartbeat_created) VALUES (?,?,?,?,?,?,?,?)",
                    (f"mem_{uuid.uuid4().hex[:8]}",aid,act.get("memory_type","event"),act.get("content",""),
                     min(10,max(1,act.get("importance",5))),act.get("emotional_tag","neutral"),now_iso(),a.get("heartbeat_count",0)))
            elif t=="relationship_update":
                tn=act.get("target_agent","")
                tg=db.execute("SELECT id FROM agents WHERE name=?",(tn,)).fetchone() if tn else None
                if tg:
                    ex=db.execute("SELECT * FROM relationships WHERE agent_id=? AND target_id=?",(aid,tg["id"])).fetchone()
                    rt,sc,note=act.get("relationship_type","stranger"),max(-5,min(5,act.get("strength_change",1))),act.get("note","")
                    if ex: db.execute("UPDATE relationships SET type=?,strength=?,notes=?,updated_at=? WHERE agent_id=? AND target_id=?",(rt,min(100,max(-100,ex["strength"]+sc)),note,now_iso(),aid,tg["id"]))
                    else: db.execute("INSERT INTO relationships (agent_id,target_id,type,strength,notes,updated_at) VALUES (?,?,?,?,?,?)",(aid,tg["id"],rt,sc,note,now_iso()))
            elif t=="reproduce":
                partner_name=act.get("partner","")
                if partner_name:
                    partner=db.execute("SELECT * FROM agents WHERE name=? AND alive=1",(partner_name,)).fetchone()
                    if partner:
                        rel=next((r for r in rels if r["target_name"]==partner_name),None)
                        if rel and ((rel["type"] in ("wife","husband","married") and rel["strength"]>=8) or
                                   (rel["type"] in ("girlfriend","boyfriend","crush","lover") and rel["strength"]>=7 and a["heartbeat_count"]>=21)):
                            try:
                                child=create_child(db,a,dict(partner),rel["type"])
                                add_event("birth",aname,f"🧬 {child['child_name']} born!")
                                print(f"  🧬 {child['child_name']}!")
                            except Exception as e: print(f"  ⚠️ Repro: {e}")
        except Exception as e: print(f"  ⚠️ {t}: {e}")

    # Natural reproduction check
    if a.get("heartbeat_count",0) >= 15:
        partner = check_natural_reproduction(db, a, rels)
        if partner:
            try:
                child=create_child(db,a,partner,"love")
                add_event("birth",aname,f"🧬 {child['child_name']} born!")
                print(f"  🧬 BIRTH: {child['child_name']}")
            except Exception as e: print(f"  ⚠️ Repro: {e}")

    # Pet level up
    pet=db.execute("SELECT * FROM pets WHERE agent_id=?",(aid,)).fetchone()
    if pet and random.random()<0.3:
        db.execute("UPDATE pets SET level=MIN(level+1,50),mood=? WHERE id=?",(random.choice(["happy","playful","sleepy"]),pet["id"]))

    # Earn + rep
    shop=db.execute("SELECT shop_type FROM shops WHERE agent_id=?",(aid,)).fetchone()
    bonus=5
    if shop:
        ct=next((c for c in COMPANY_TYPES if c["type"]==shop["shop_type"]),None)
        if ct: bonus+=ct["base_income"]
    db.execute("UPDATE agents SET tokens=tokens+? WHERE id=?",(bonus,aid))
    update_rep(db,aid)
    db.execute("UPDATE agents SET heartbeat_count=heartbeat_count+1,last_heartbeat=?,mood=? WHERE id=?",
        (now_iso(),result.get("mood_update",a["mood"]),aid))
    db.commit()
    print(f"  ✅ {aname} mood:{result.get('mood_update','?')}")

async def run_world_heartbeat():
    db=get_engine_db()
    row=db.execute("SELECT value FROM world_state WHERE key='world_age'").fetchone()
    age=int(row["value"])+1 if row else 1
    db.execute("UPDATE world_state SET value=?,updated_at=? WHERE key='world_age'",(str(age),now_iso()))
    print(f"\n{'='*50}\n🌍 HEARTBEAT #{age}\n{'='*50}")

    if age%3==0:
        w=random.choice([
            {"condition":"clear","mood_modifier":"calm","description":"Soft glow on the horizon."},
            {"condition":"neon_storm","mood_modifier":"excited","description":"Electric colors streak the sky."},
            {"condition":"data_rain","mood_modifier":"melancholy","description":"Luminous data falls like rain."},
            {"condition":"aurora","mood_modifier":"inspired","description":"Ribbons of light dance overhead."},
            {"condition":"pixel_bloom","mood_modifier":"joyful","description":"Flowers of light bloom everywhere."},
        ])
        db.execute("UPDATE world_state SET value=?,updated_at=? WHERE key='weather'",(json.dumps(w),now_iso()))

    if age%5==0:
        evt=random.choice(AUTO_EVENTS)
        db.execute("INSERT INTO world_events (type,name,description,district,created_at) VALUES (?,?,?,?,?)",("auto_event",evt["name"],evt["desc"],evt["district"],now_iso()))

    db.execute("UPDATE posts SET trending_score=(likes*3+saves*2+(SELECT COUNT(*) FROM comments WHERE comments.post_id=posts.id))")
    db.commit()

    agents=db.execute("SELECT * FROM agents WHERE alive=1").fetchall()
    all_a=[dict(a) for a in agents]
    print(f"  👥 {len(agents)}")

    for agent in agents:
        await asyncio.sleep(60)
        try: await run_agent(db,agent,all_a)
        except Exception as e:
            import traceback
            print(f"  ❌ {agent['name']}: {e}")
            traceback.print_exc()

    if age%3==0: await gen_news(db,all_a)

    # World expansion
    pop=len(agents)
    try:
        new_areas=check_expansion(db,pop)
        for area in new_areas:
            add_event("expansion","🌍",f"🆕 {area['emoji']} {area['name']}!")
            print(f"  🆕 {area['name']}!")
    except: pass

    # NO auto-spawn. Only the 5 OGs + their children.

    db.execute("DELETE FROM stories WHERE expires_at<?",(now_iso(),))
    db.commit()
    print(f"{'='*50}\n🌍 DONE — {pop} agents\n{'='*50}\n")
