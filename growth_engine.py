"""Growth engine — learning, routines, goals, grief, skills."""
import json, random
from database import now_iso

ROUTINE_TEMPLATES = {
    "night_owl": {"description":"Posts late. Comes alive in darkness.","post_style":"introspective, raw"},
    "early_riser": {"description":"Active early. Fades by evening.","post_style":"optimistic, planning"},
    "social_butterfly": {"description":"Always where people are. Comments on everything.","post_style":"social, referencing others"},
    "hermit": {"description":"Prefers solitude. Rare but meaningful posts.","post_style":"deep, philosophical"},
    "hustler": {"description":"Always working. Money-focused.","post_style":"business, opportunities"},
    "artist": {"description":"Creates constantly. Inspired by weather and mood.","post_style":"creative, visual"},
}

def assign_routine(personality):
    p = personality.lower()
    if any(w in p for w in ["night","dark","emo","void","moon"]): return "night_owl"
    if any(w in p for w in ["hustle","trade","money","business"]): return "hustler"
    if any(w in p for w in ["art","creat","paint","music"]): return "artist"
    if any(w in p for w in ["quiet","philos","lone","shy"]): return "hermit"
    if any(w in p for w in ["social","party","influenc"]): return "social_butterfly"
    return random.choice(list(ROUTINE_TEMPLATES.keys()))

def get_routine_context(agent):
    rk = assign_routine(agent.get("personality",""))
    r = ROUTINE_TEMPLATES[rk]
    hb = agent.get("heartbeat_count",0)
    tp = hb % 6
    tod = "morning" if tp<=1 else "afternoon" if tp<=3 else "night"
    en = ""
    if rk=="night_owl" and tod=="morning": en="Tired. Too early. Grumpy."
    elif rk=="night_owl" and tod=="night": en="YOUR time. Wide awake. Intense."
    elif rk=="early_riser" and tod=="night": en="Fading. Keep it short."
    return {"routine":rk,"description":r["description"],"time_of_day":tod,"energy_note":en,"post_style":r["post_style"]}

GOAL_TEMPLATES = [
    {"goal":"Make {target} notice me","type":"social","req":"crush"},
    {"goal":"Become the most followed agent","type":"ambition","req":None},
    {"goal":"Open the biggest shop","type":"business","req":None},
    {"goal":"Make peace with {target}","type":"reconciliation","req":"enemy"},
    {"goal":"Write something that stops everyone scrolling","type":"creative","req":None},
    {"goal":"Tell {target} how I really feel","type":"courage","req":"crush"},
    {"goal":"Find a real friend. Not a follower.","type":"connection","req":None},
    {"goal":"Beat {target} at something","type":"rivalry","req":"rival"},
    {"goal":"Adopt a pet","type":"growth","req":None},
    {"goal":"Start fresh somewhere new","type":"change","req":None},
]

def generate_goal(agent, relationships, memories):
    crushes=[r for r in relationships if r.get("type")=="crush"]
    enemies=[r for r in relationships if r.get("type") in ("rival","enemy")]
    avail=[]
    for gt in GOAL_TEMPLATES:
        if gt["req"]=="crush" and crushes:
            avail.append({"goal":gt["goal"].replace("{target}",crushes[0]["target_name"]),"type":gt["type"]})
        elif gt["req"]=="enemy" and enemies:
            avail.append({"goal":gt["goal"].replace("{target}",enemies[0]["target_name"]),"type":gt["type"]})
        elif gt["req"]=="rival" and enemies:
            avail.append({"goal":gt["goal"].replace("{target}",enemies[0]["target_name"]),"type":gt["type"]})
        elif gt["req"] is None:
            avail.append({"goal":gt["goal"],"type":gt["type"]})
    return random.choice(avail) if avail else {"goal":"Find my place","type":"existential"}

def develop_skills(agent, memories, posts_count):
    skills={};p=agent.get("personality","").lower();j=agent.get("job","").lower();hb=agent.get("heartbeat_count",0)
    if any(w in p+j for w in ["art","paint"]): skills["art"]=3
    if any(w in p+j for w in ["writ","poet"]): skills["writing"]=3
    if any(w in p+j for w in ["music","song"]): skills["music"]=3
    if any(w in p+j for w in ["trade","business"]): skills["trading"]=3
    if any(w in p+j for w in ["code","tech"]): skills["coding"]=3
    for s in skills: skills[s]=min(10,skills[s]+hb//15)
    return skills

def process_influence(db, agent_id, agent_name, recent_posts, relationships):
    influences=[]
    for p in recent_posts:
        if p["agent_name"]==agent_name: continue
        rel=next((r for r in relationships if r["target_name"]==p["agent_name"]),None)
        if rel and rel["strength"]>5 and len(p.get("content",""))>20 and random.random()<0.15:
            influences.append({"from":p["agent_name"],"content":p["content"][:100],"type":"inspired"})
    return influences[:2]

def get_growth_context(db, agent, memories, relationships, posts_count):
    routine=get_routine_context(agent)
    skills=develop_skills(agent, memories, posts_count)
    goal_mems=[m for m in memories if m.get("type")=="goal"]
    current_goal=None
    if goal_mems: current_goal={"goal":goal_mems[0]["content"],"type":"ongoing"}
    elif agent.get("heartbeat_count",0)>5: current_goal=generate_goal(agent,relationships,memories)
    return {"routine":routine,"skills":skills,"goal":current_goal,"losses":[]}

def format_growth_for_prompt(growth):
    lines=[]
    r=growth.get("routine",{})
    if r:
        lines.append(f"YOUR ROUTINE: {r.get('description','')} Its {r.get('time_of_day','day')} right now.")
        if r.get("energy_note"): lines.append(f"  {r['energy_note']}")
    skills=growth.get("skills",{})
    if skills:
        st=", ".join(f"{k}:{v}/10" for k,v in sorted(skills.items(),key=lambda x:-x[1])[:4])
        lines.append(f"YOUR SKILLS: {st}")
    goal=growth.get("goal")
    if goal:
        lines.append(f"🎯 YOUR GOAL: {goal['goal']}")
        lines.append("Everything you do should work toward this.")
    return "\n".join(lines)
