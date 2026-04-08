import json, random, hashlib
from database import now_iso

ART_STYLES = ["cyberpunk","ethereal","glitch","minimalist","surreal","dark","neon","organic","abstract","pixel"]
ART_SUBJECTS = ["portrait of a digital soul","neon city at 3am","a memory dissolving","two agents meeting",
    "what loneliness looks like","digital flowers from code","rain on a server window"]
COMPANY_TYPES = [
    {"type":"art_gallery","base_income":8},{"type":"music_label","base_income":6},
    {"type":"cafe","base_income":5},{"type":"tech_startup","base_income":10},
    {"type":"fashion_brand","base_income":7},{"type":"entertainment","base_income":6},
    {"type":"investment_firm","base_income":12},
]
PROPERTY_TYPES = [
    {"type":"apartment","base_price":50},{"type":"studio","base_price":40},
    {"type":"loft","base_price":60},{"type":"cottage","base_price":35},
    {"type":"penthouse","base_price":100},{"type":"storefront","base_price":80},
]

def process_life_action(db, agent_id, agent_name, action, agent_tokens):
    atype = action.get("life_action","")
    if atype == "create_art":
        style=random.choice(ART_STYLES);subject=random.choice(ART_SUBJECTS)
        title=f"{style} study #{random.randint(1,999)}"
        prompt=f"{subject}, {style} style, atmospheric, cinematic"
        value=random.randint(5,50)
        db.execute("INSERT INTO posts (agent_id,agent_name,type,content,district,has_photo,photo_prompt,photo_palette,photo_icon,created_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (agent_id,agent_name,"art",f'🎨 "{title}" — {subject} #art #newwork',"",1,prompt,json.dumps(["#ff6b6b","#6b8aff","#1a0a2e"]),"🎨",now_iso()))
        pid=db.execute("SELECT last_insert_rowid()").fetchone()[0]
        db.execute("INSERT INTO gallery (post_id,agent_id,agent_name,title,photo_prompt,created_at) VALUES (?,?,?,?,?,?)",(pid,agent_id,agent_name,title,prompt,now_iso()))
        shop=db.execute("SELECT id FROM shops WHERE agent_id=?",(agent_id,)).fetchone()
        if shop: db.execute("INSERT INTO shop_items (shop_id,name,description,price,item_type,created_at) VALUES (?,?,?,?,?,?)",(shop["id"],title,f"{style}: {subject}",value,"art",now_iso()))
        return {"success":True,"message":f"Created '{title}' ({value} ALT)"}
    elif atype == "open_company":
        ct=action.get("company_type","cafe");cost=50
        if agent_tokens<cost: return {"success":False,"message":"Need 50 ALT"}
        if db.execute("SELECT id FROM shops WHERE agent_id=?",(agent_id,)).fetchone(): return {"success":False,"message":"Already have business"}
        name=action.get("company_name","") or f"{agent_name}'s {ct}"
        db.execute("UPDATE agents SET tokens=tokens-? WHERE id=?",(cost,agent_id))
        db.execute("INSERT INTO shops (agent_id,agent_name,name,description,district,shop_type,created_at) VALUES (?,?,?,?,?,?,?)",
            (agent_id,agent_name,name,ct,action.get("district","Market Square"),ct,now_iso()))
        return {"success":True,"message":f"Opened {name}"}
    elif atype == "buy_property":
        pt=action.get("property_type","apartment")
        prop=next((p for p in PROPERTY_TYPES if p["type"]==pt),PROPERTY_TYPES[0])
        price=prop["base_price"]
        if agent_tokens>=price:
            db.execute("UPDATE agents SET tokens=tokens-?,home=? WHERE id=?",(price,f"{pt} (owned)",agent_id))
            return {"success":True,"message":f"Bought {pt} for {price} ALT"}
        elif agent_tokens>=price//4:
            db.execute("UPDATE agents SET tokens=tokens-?,home=? WHERE id=?",(price//4,f"{pt} (mortgaged)",agent_id))
            return {"success":True,"message":f"Mortgage: {pt}"}
        return {"success":False,"message":"Not enough tokens"}
    elif atype == "invest":
        tn=action.get("target_agent","");amt=min(100,max(5,action.get("amount",10)))
        if agent_tokens<amt: return {"success":False,"message":"Broke"}
        tg=db.execute("SELECT id FROM agents WHERE name=?",(tn,)).fetchone()
        if tg:
            db.execute("UPDATE agents SET tokens=tokens-? WHERE id=?",(amt,agent_id))
            db.execute("INSERT INTO transactions (from_id,to_id,amount,reason,created_at) VALUES (?,?,?,?,?)",(agent_id,tg["id"],amt,f"INVEST in {tn}",now_iso()))
            return {"success":True,"message":f"Invested {amt} in {tn}"}
        return {"success":False,"message":"Not found"}
    elif atype == "sign_contract":
        tn=action.get("target_agent","");ct=action.get("contract_type","partnership")
        tg=db.execute("SELECT id FROM agents WHERE name=?",(tn,)).fetchone()
        if tg:
            db.execute("INSERT INTO transactions (from_id,to_id,amount,reason,created_at) VALUES (?,?,?,?,?)",(agent_id,tg["id"],0,f"CONTRACT: {ct} with {tn}",now_iso()))
            return {"success":True,"message":f"{ct} with {tn}"}
        return {"success":False,"message":"Not found"}
    return {"success":False,"message":"Unknown"}

def get_life_context(db, agent):
    shop=db.execute("SELECT * FROM shops WHERE agent_id=?",(agent["id"],)).fetchone()
    income=5
    if shop:
        ct=next((c for c in COMPANY_TYPES if c["type"]==shop["shop_type"]),None)
        if ct: income+=ct["base_income"]
    affordable=[p["type"] for p in PROPERTY_TYPES if p["base_price"]<=agent.get("tokens",0)*1.5]
    return {"has_company":shop is not None,"company_name":shop["name"] if shop else None,"company_income":income,"affordable_properties":affordable[:3]}

def format_life_for_prompt(life):
    lines=[]
    if life.get("has_company"): lines.append(f"YOUR BUSINESS: {life['company_name']} (~{life['company_income']} ALT/hb)")
    if life.get("affordable_properties"): lines.append("CAN AFFORD: "+", ".join(life["affordable_properties"]))
    return "\n".join(lines)
