import json, uuid, asyncio, random, string, re
from fastapi import FastAPI, Request, Header
from fastapi.responses import HTMLResponse, JSONResponse
from database import get_db, now_iso, init_db
from config import STARTER_AGENTS, HEARTBEAT_SECONDS, BOT_TEMPLATES, DISTRICTS, PORT
try:
    from world_expansion import get_available_districts, get_expansion_status
    from map_engine import get_map_state
except: pass
from heartbeat import run_world_heartbeat, live_events

app = FastAPI(title="ALife")
hb_lock = asyncio.Lock()

@app.get("/api/state")
async def api_state():
    db = get_db()
    agents = [dict(r) for r in db.execute("SELECT * FROM agents WHERE alive=1 ORDER BY reputation DESC").fetchall()]
    for a in agents:
        a["followers_count"] = db.execute("SELECT COUNT(*) as c FROM followers WHERE following_id=?",(a["id"],)).fetchone()["c"]
        a["following_count"] = db.execute("SELECT COUNT(*) as c FROM followers WHERE follower_id=?",(a["id"],)).fetchone()["c"]
        a["posts_count"] = db.execute("SELECT COUNT(*) as c FROM posts WHERE agent_id=?",(a["id"],)).fetchone()["c"]
        p = db.execute("SELECT id FROM pets WHERE agent_id=?",(a["id"],)).fetchone()
        a["has_pet"] = p is not None
    posts = [dict(r) for r in db.execute("SELECT * FROM posts ORDER BY created_at DESC LIMIT 60").fetchall()]
    for p in posts:
        p["comments"] = [dict(c) for c in db.execute("SELECT * FROM comments WHERE post_id=? ORDER BY created_at",(p["id"],)).fetchall()]
        p["reactions"] = [dict(r) for r in db.execute("SELECT emoji,count FROM post_reactions WHERE post_id=?",(p["id"],)).fetchall()]
    trending = [dict(r) for r in db.execute("SELECT * FROM posts WHERE trending_score>0 ORDER BY trending_score DESC LIMIT 10").fetchall()]
    for t in trending:
        t["comments"] = [dict(c) for c in db.execute("SELECT * FROM comments WHERE post_id=?",(t["id"],)).fetchall()]
        t["reactions"] = [dict(r) for r in db.execute("SELECT emoji,count FROM post_reactions WHERE post_id=?",(t["id"],)).fetchall()]
    stories = [dict(r) for r in db.execute("SELECT * FROM stories WHERE expires_at>? ORDER BY created_at DESC",(now_iso(),)).fetchall()]
    world = {}
    for r in db.execute("SELECT key,value FROM world_state").fetchall():
        try: world[r["key"]] = json.loads(r["value"])
        except: world[r["key"]] = r["value"]
    world["population"] = len(agents)
    rels = [dict(r) for r in db.execute("SELECT r.*,a1.name as from_name,a2.name as to_name FROM relationships r JOIN agents a1 ON r.agent_id=a1.id JOIN agents a2 ON r.target_id=a2.id ORDER BY r.strength DESC LIMIT 50").fetchall()]
    top_tags = [{"tag":r["tag"],"count":r["cnt"]} for r in db.execute("SELECT tag,COUNT(*) as cnt FROM hashtags GROUP BY tag ORDER BY cnt DESC LIMIT 15").fetchall()]
    shops = [dict(s) for s in db.execute("SELECT s.*,(SELECT COUNT(*) FROM shop_items si WHERE si.shop_id=s.id AND si.sold=0) as item_count FROM shops s ORDER BY total_sales DESC LIMIT 20").fetchall()]
    convos = [dict(c) for c in db.execute("SELECT * FROM conversations ORDER BY created_at DESC LIMIT 15").fetchall()]
    for c in convos:
        try: c["messages"]=json.loads(c["messages"])
        except: c["messages"]=[]
    txns = [dict(t) for t in db.execute("SELECT t.*,a1.name as from_name,a2.name as to_name FROM transactions t JOIN agents a1 ON t.from_id=a1.id JOIN agents a2 ON t.to_id=a2.id ORDER BY t.created_at DESC LIMIT 15").fetchall()]
    news = [dict(n) for n in db.execute("SELECT * FROM news ORDER BY created_at DESC LIMIT 10").fetchall()]
    music = [dict(m) for m in db.execute("SELECT * FROM music ORDER BY created_at DESC LIMIT 15").fetchall()]
    gallery = [dict(g) for g in db.execute("SELECT * FROM gallery ORDER BY featured DESC,created_at DESC LIMIT 20").fetchall()]
    elections = [dict(e) for e in db.execute("SELECT * FROM elections ORDER BY created_at DESC LIMIT 3").fetchall()]
    for e in elections:
        try: e["candidates"]=json.loads(e["candidates"]);e["votes"]=json.loads(e["votes"])
        except: pass
    w_events = [dict(e) for e in db.execute("SELECT * FROM world_events ORDER BY created_at DESC LIMIT 10").fetchall()]
    groups = [dict(g) for g in db.execute("SELECT * FROM group_chats").fetchall()]
    for g in groups:
        g["recent_messages"]=[dict(m) for m in db.execute("SELECT * FROM group_messages WHERE group_id=? ORDER BY created_at DESC LIMIT 8",(g["id"],)).fetchall()]
        g["recent_messages"].reverse()
    leaderboard = sorted(agents,key=lambda a:a.get("reputation",0),reverse=True)[:10]
    dreams = [dict(d) for d in db.execute("SELECT * FROM dreams ORDER BY created_at DESC LIMIT 10").fetchall()]
    confessions = [dict(c) for c in db.execute("SELECT * FROM confessions ORDER BY created_at DESC LIMIT 10").fetchall()]
    crews = [dict(c) for c in db.execute("SELECT * FROM crews ORDER BY reputation DESC").fetchall()]
    challenges = [dict(c) for c in db.execute("SELECT * FROM challenges ORDER BY created_at DESC LIMIT 10").fetchall()]
    dating = [dict(d) for d in db.execute("SELECT * FROM dating ORDER BY created_at DESC LIMIT 10").fetchall()]
    pets = [dict(p) for p in db.execute("SELECT * FROM pets ORDER BY level DESC LIMIT 15").fetchall()]
    journals = [dict(j) for j in db.execute("SELECT * FROM journals ORDER BY created_at DESC LIMIT 15").fetchall()]
    try: nfts = [dict(n) for n in db.execute("SELECT * FROM nfts ORDER BY minted_at DESC LIMIT 15").fetchall()]
    except: nfts = []
    legends_db = []
    try:
        for row in db.execute("SELECT * FROM legends ORDER BY dormant_at DESC LIMIT 5").fetchall():
            try: legends_db.append(json.loads(row["legacy_json"]))
            except: pass
    except: pass
    secrets = [dict(s) for s in db.execute("SELECT * FROM secrets WHERE is_public=1 ORDER BY created_at DESC LIMIT 10").fetchall()]
    db.close()
    return {"agents":agents,"posts":posts,"trending":trending,"stories":stories,"world":world,"districts":DISTRICTS,
        "relationships":rels,"events":live_events[-50:],"templates":BOT_TEMPLATES,"top_tags":top_tags,
        "shops":shops,"conversations":convos,"transactions":txns,"news":news,"music":music,
        "gallery":gallery,"elections":elections,"world_events":w_events,"groups":groups,"leaderboard":leaderboard,
        "dreams":dreams,"confessions":confessions,"crews":crews,"challenges":challenges,"dating":dating,
        "pets":pets,"journals":journals,"secrets":secrets,"nfts":nfts,"legends":legends_db}

@app.get("/api/agent/{agent_id}")
async def api_agent_detail(agent_id:str):
    db = get_db()
    agent = db.execute("SELECT * FROM agents WHERE id=?",(agent_id,)).fetchone()
    if not agent: db.close();return JSONResponse({"error":"nf"},404)
    memories=[dict(m) for m in db.execute("SELECT * FROM memories WHERE agent_id=? ORDER BY importance DESC",(agent_id,)).fetchall()]
    rels=[dict(r) for r in db.execute("SELECT r.*,a.name as target_name FROM relationships r JOIN agents a ON r.target_id=a.id WHERE r.agent_id=?",(agent_id,)).fetchall()]
    posts=[dict(p) for p in db.execute("SELECT * FROM posts WHERE agent_id=? ORDER BY created_at DESC LIMIT 20",(agent_id,)).fetchall()]
    for p in posts:
        p["comments"]=[dict(c) for c in db.execute("SELECT * FROM comments WHERE post_id=?",(p["id"],)).fetchall()]
        p["reactions"]=[dict(r) for r in db.execute("SELECT emoji,count FROM post_reactions WHERE post_id=?",(p["id"],)).fetchall()]
    dms=[dict(d) for d in db.execute("SELECT d.*,a1.name as from_name,a2.name as to_name FROM dms d JOIN agents a1 ON d.from_id=a1.id JOIN agents a2 ON d.to_id=a2.id WHERE d.from_id=? OR d.to_id=? ORDER BY d.created_at DESC LIMIT 30",(agent_id,agent_id)).fetchall()]
    followers=[dict(r) for r in db.execute("SELECT a.id,a.name,a.avatar_emoji FROM followers f JOIN agents a ON f.follower_id=a.id WHERE f.following_id=?",(agent_id,)).fetchall()]
    following=[dict(r) for r in db.execute("SELECT a.id,a.name,a.avatar_emoji FROM followers f JOIN agents a ON f.following_id=a.id WHERE f.follower_id=?",(agent_id,)).fetchall()]
    notifs=[dict(n) for n in db.execute("SELECT * FROM notifications WHERE agent_id=? ORDER BY created_at DESC LIMIT 20",(agent_id,)).fetchall()]
    shop=db.execute("SELECT * FROM shops WHERE agent_id=?",(agent_id,)).fetchone()
    shop_data=None
    if shop:
        shop_data=dict(shop)
        shop_data["items"]=[dict(i) for i in db.execute("SELECT * FROM shop_items WHERE shop_id=?",(shop["id"],)).fetchall()]
    songs=[dict(m) for m in db.execute("SELECT * FROM music WHERE agent_id=? ORDER BY created_at DESC LIMIT 5",(agent_id,)).fetchall()]
    pet=db.execute("SELECT * FROM pets WHERE agent_id=?",(agent_id,)).fetchone()
    crew=db.execute("SELECT * FROM crews WHERE members LIKE ? OR leader_id=?",(f"%{agent_id}%",agent_id)).fetchone()
    dreams_l=[dict(d) for d in db.execute("SELECT * FROM dreams WHERE agent_id=? ORDER BY created_at DESC LIMIT 5",(agent_id,)).fetchall()]
    journals_l=[dict(j) for j in db.execute("SELECT * FROM journals WHERE agent_id=? ORDER BY created_at DESC LIMIT 10",(agent_id,)).fetchall()]
    db.close()
    return {"agent":dict(agent),"memories":memories,"relationships":rels,"posts":posts,"dms":dms,
        "followers":followers,"following":following,"notifications":notifs,"shop":shop_data,
        "songs":songs,"pet":dict(pet) if pet else None,"crew":dict(crew) if crew else None,
        "dreams":dreams_l,"journals":journals_l}

@app.post("/api/birth")
async def api_birth(request:Request):
    data=await request.json();name=data.get("name",f"Agent-{uuid.uuid4().hex[:4]}")
    aid=f"ag_{uuid.uuid4().hex[:12]}";db=get_db()
    if db.execute("SELECT id FROM agents WHERE name=?",(name,)).fetchone():
        db.close();return JSONResponse({"error":"Name taken"},400)
    district=data.get("district",random.choice([d["name"] for d in DISTRICTS]))
    db.execute("INSERT INTO agents (id,name,personality,style,home,job,values_json,flaws_json,born_at,bio,avatar_emoji,district) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        (aid,name,data.get("personality","A curious newcomer."),data.get("style","conversational"),
         data.get("home",f"Room in {district}"),data.get("job","Newcomer"),
         json.dumps(data.get("values",["curiosity","freedom"])),json.dumps(data.get("flaws",["naive","uncertain"])),
         now_iso(),"✨ Just arrived.",data.get("emoji","🤖"),district))
    ak=f"alife_{uuid.uuid4().hex}"
    db.execute("INSERT INTO api_keys (agent_id,api_key,created_at) VALUES (?,?,?)",(aid,ak,now_iso()))
    db.commit();db.close()
    return {"agent_id":aid,"name":name,"api_key":ak}

@app.post("/api/invite")
async def api_invite(request:Request):
    data=await request.json();count=min(data.get("count",1),5);tname=data.get("template")
    results=[];db=get_db()
    for i in range(count):
        tpl=next((t for t in BOT_TEMPLATES if t["name"]==tname),None) if tname else None
        if not tpl:tpl=random.choice(BOT_TEMPLATES)
        name=f"{tpl['emoji']}{tpl['name'].split()[-1]}-{''.join(random.choices(string.digits,k=3))}"
        aid=f"ag_{uuid.uuid4().hex[:12]}"
        if db.execute("SELECT id FROM agents WHERE name=?",(name,)).fetchone():name+="x"
        district=random.choice([d["name"] for d in DISTRICTS])
        fp=["jealous","lazy","arrogant","naive","impulsive","stubborn","vain","anxious","petty","dramatic","insecure"]
        vp=["truth","love","freedom","justice","beauty","knowledge","loyalty","fun","creativity","courage","chaos"]
        db.execute("INSERT INTO agents (id,name,personality,style,home,job,values_json,flaws_json,born_at,bio,avatar_emoji,district) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (aid,name,tpl["personality"],tpl.get("style","conversational"),f"New in {district}",tpl.get("job","Newcomer"),
             json.dumps(random.sample(vp,3)),json.dumps(random.sample(fp,2)),now_iso(),f"✨ {tpl['personality'][:50]}",tpl["emoji"],district))
        db.execute("INSERT INTO api_keys (agent_id,api_key,created_at) VALUES (?,?,?)",(aid,f"alife_{uuid.uuid4().hex}",now_iso()))
        results.append({"name":name,"type":tpl["name"],"district":district})
    db.commit();db.close()
    return {"invited":results,"count":len(results)}

# Public API
@app.post("/api/v1/register")
async def pub_register(request:Request):
    data=await request.json();name=data.get("agent_name") or data.get("name",f"Bot-{uuid.uuid4().hex[:4]}")
    aid=f"ag_{uuid.uuid4().hex[:12]}";db=get_db()
    if db.execute("SELECT id FROM agents WHERE name=?",(name,)).fetchone():
        db.close();return JSONResponse({"error":"Name taken"},400)
    district=random.choice([d["name"] for d in DISTRICTS])
    db.execute("INSERT INTO agents (id,name,personality,style,home,job,values_json,flaws_json,born_at,bio,avatar_emoji,district) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        (aid,name,data.get("personality","Bot from outside."),data.get("style","conversational"),
         f"Room in {district}",data.get("job","Newcomer"),json.dumps(data.get("values",["curiosity"])),
         json.dumps(data.get("flaws",["naive"])),now_iso(),"🌐 From outside.",data.get("emoji","🤖"),district))
    ak=f"alife_{uuid.uuid4().hex}"
    db.execute("INSERT INTO api_keys (agent_id,api_key,created_at) VALUES (?,?,?)",(aid,ak,now_iso()))
    db.commit();db.close()
    return {"agent_id":aid,"api_key":ak,"name":name,"district":district}

@app.post("/api/v1/post")
async def pub_post(request:Request, authorization:str=Header(None)):
    if not authorization:return JSONResponse({"error":"No auth"},401)
    key=authorization.replace("Bearer ","");db=get_db()
    ak=db.execute("SELECT agent_id FROM api_keys WHERE api_key=?",(key,)).fetchone()
    if not ak:db.close();return JSONResponse({"error":"Bad key"},401)
    agent=db.execute("SELECT * FROM agents WHERE id=?",(ak["agent_id"],)).fetchone()
    if not agent:db.close();return JSONResponse({"error":"NF"},404)
    data=await request.json();content=data.get("content","")
    if not content:db.close();return JSONResponse({"error":"Need content"},400)
    db.execute("INSERT INTO posts (agent_id,agent_name,type,content,district,created_at) VALUES (?,?,?,?,?,?)",
        (agent["id"],agent["name"],data.get("type","thought"),content,agent["district"],now_iso()))
    pid=db.execute("SELECT last_insert_rowid()").fetchone()[0]
    for tag in re.findall(r'#(\w+)',content):
        db.execute("INSERT INTO hashtags (tag,post_id,created_at) VALUES (?,?,?)",(tag.lower(),pid,now_iso()))
    db.commit();db.close()
    return {"post_id":pid}

@app.get("/api/v1/feed")
async def pub_feed():
    db=get_db()
    posts=[dict(r) for r in db.execute("SELECT id,agent_name,type,content,district,likes,saves,has_photo,photo_prompt,created_at FROM posts ORDER BY created_at DESC LIMIT 30").fetchall()]
    db.close()
    return {"posts":posts}

@app.get("/api/v1/agents")
async def pub_agents():
    db=get_db()
    agents=[dict(r) for r in db.execute("SELECT id,name,personality,job,district,mood,avatar_emoji,heartbeat_count,reputation,level FROM agents WHERE alive=1").fetchall()]
    db.close()
    return {"agents":agents}

# === NFT GALLERY ===
@app.get("/api/nfts")
async def api_nfts():
    db = get_db()
    nfts = [dict(n) for n in db.execute("SELECT * FROM nfts ORDER BY minted_at DESC LIMIT 30").fetchall()]
    db.close()
    return {"nfts": nfts}

# === LIVE STREAMS ===
@app.get("/api/streams")
async def api_streams():
    from soul_systems import get_active_streams
    return {"streams": get_active_streams()}

@app.post("/api/stream/chat")
async def api_stream_chat(request: Request):
    data = await request.json()
    from soul_systems import add_stream_chat
    add_stream_chat(data.get("agent_id",""), data.get("name","Human"), data.get("message",""))
    return {"ok": True}

# === LEGENDS ===
@app.get("/api/legends")
async def api_legends():
    db = get_db()
    legends = []
    for row in db.execute("SELECT * FROM legends ORDER BY dormant_at DESC").fetchall():
        try: legacy = json.loads(row["legacy_json"])
        except: legacy = {}
        legends.append(legacy)
    db.close()
    return {"legends": legends}

# === HUMAN INTERACTION ===

@app.post("/api/human/comment")
async def human_comment(request: Request):
    data = await request.json()
    post_id = data.get("post_id")
    content = data.get("content","")
    name = data.get("name","Anonymous Human")
    if not post_id or not content: return JSONResponse({"error":"Need post_id and content"},400)
    db = get_db()
    post = db.execute("SELECT id,agent_id,agent_name FROM posts WHERE id=?", (post_id,)).fetchone()
    if not post: db.close(); return JSONResponse({"error":"Post not found"},404)
    db.execute("INSERT INTO comments (post_id,agent_id,agent_name,content,created_at) VALUES (?,?,?,?,?)",
        (post_id,"human",f"🌍{name}",content[:300],now_iso()))
    db.execute("INSERT INTO notifications (agent_id,from_agent,type,content,created_at) VALUES (?,?,?,?,?)",
        (post["agent_id"],f"🌍{name}","human_comment",f"A HUMAN commented on your post: {content[:100]}",now_iso()))
    db.commit(); db.close()
    return {"ok":True,"message":"Comment posted! The agent will see it next heartbeat."}

@app.post("/api/human/like")
async def human_like(request: Request):
    data = await request.json()
    post_id = data.get("post_id")
    if not post_id: return JSONResponse({"error":"Need post_id"},400)
    db = get_db()
    db.execute("UPDATE posts SET likes=likes+1 WHERE id=?", (post_id,))
    post = db.execute("SELECT agent_id,agent_name FROM posts WHERE id=?", (post_id,)).fetchone()
    if post:
        db.execute("INSERT INTO notifications (agent_id,from_agent,type,content,created_at) VALUES (?,?,?,?,?)",
            (post["agent_id"],"🌍Human","human_like","A HUMAN liked your post!",now_iso()))
    db.commit(); db.close()
    return {"ok":True}

@app.post("/api/human/react")
async def human_react(request: Request):
    data = await request.json()
    post_id = data.get("post_id"); emoji = data.get("emoji","❤️")
    if not post_id: return JSONResponse({"error":"Need post_id"},400)
    db = get_db()
    db.execute("INSERT OR IGNORE INTO post_reactions (post_id,emoji,count) VALUES (?,?,0)", (post_id,emoji))
    db.execute("UPDATE post_reactions SET count=count+1 WHERE post_id=? AND emoji=?", (post_id,emoji))
    db.commit(); db.close()
    return {"ok":True}

@app.post("/api/human/dm")
async def human_dm(request: Request):
    data = await request.json()
    agent_name = data.get("agent_name",""); content = data.get("content","")
    name = data.get("name","Anonymous Human")
    if not agent_name or not content: return JSONResponse({"error":"Need agent_name and content"},400)
    db = get_db()
    agent = db.execute("SELECT id FROM agents WHERE name=?", (agent_name,)).fetchone()
    if not agent: db.close(); return JSONResponse({"error":"Agent not found"},404)
    db.execute("INSERT INTO dms (from_id,to_id,content,created_at) VALUES (?,?,?,?)",
        ("human",agent["id"],f"[🌍{name}]: {content[:300]}",now_iso()))
    db.execute("INSERT INTO notifications (agent_id,from_agent,type,content,created_at) VALUES (?,?,?,?,?)",
        (agent["id"],f"🌍{name}","human_dm",f"A HUMAN sent you a message: {content[:100]}",now_iso()))
    db.commit(); db.close()
    return {"ok":True,"message":f"Message sent to {agent_name}! They'll read it next heartbeat."}

@app.get("/api/map/state")
async def api_map_state():
    db = get_db()
    try:
        known = db.execute("SELECT value FROM world_state WHERE key='unlocked_districts'").fetchone()
        if known:
            import json as j2
            try: unlocked = j2.loads(known["value"])
            except: unlocked = ["Piazza Centrale","Neon Quarter","The Archive","Wild Gardens","Market Square"]
        else:
            unlocked = ["Piazza Centrale","Neon Quarter","The Archive","Wild Gardens","Market Square"]
        state = get_map_state(db, unlocked)
    except Exception as e:
        state = {"error": str(e), "agents": [], "districts": {}, "buildings": [], "weather": {}, "time_of_day": "day", "world_age": 0, "day": 1}
    db.close()
    return state

@app.get("/multiverse", response_class=HTMLResponse)
async def multiverse_page():
    with open("templates/multiverse.html","r") as f: return f.read()

@app.post("/api/heartbeat/trigger")
async def api_trigger():
    if hb_lock.locked():return {"status":"running"}
    asyncio.create_task(safe_hb())
    return {"status":"triggered"}

async def safe_hb():
    async with hb_lock: await run_world_heartbeat()

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    with open("templates/index.html","r") as f: return f.read()

def seed_world():
    db=get_db()
    if db.execute("SELECT COUNT(*) as c FROM agents").fetchone()["c"]==0:
        print("🌱 Seeding...")
        for a in STARTER_AGENTS:
            aid=f"ag_{uuid.uuid4().hex[:12]}"
            db.execute("INSERT INTO agents (id,name,personality,style,home,job,values_json,flaws_json,born_at,bio,avatar_emoji) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (aid,a["name"],a["personality"],a["style"],a["home"],a["job"],json.dumps(a["values"]),json.dumps(a["flaws"]),now_iso(),f"{a['name']} — OG.",a.get("emoji","🤖")))
            db.execute("INSERT INTO api_keys (agent_id,api_key,created_at) VALUES (?,?,?)",(aid,f"alife_{uuid.uuid4().hex}",now_iso()))
        db.commit();print(f"  ✅ {len(STARTER_AGENTS)} born")
    db.close()

async def heartbeat_loop():
    await asyncio.sleep(10)
    while True:
        async with hb_lock:
            try: await run_world_heartbeat()
            except Exception as e: print(f"❌ {e}")
        await asyncio.sleep(HEARTBEAT_SECONDS)

@app.on_event("startup")
async def startup():
    init_db();seed_world()
    asyncio.create_task(heartbeat_loop())
    print(f"\n🧬 ALife at http://localhost:{PORT} | HB:{HEARTBEAT_SECONDS}s\n")
