import random

def get_time_of_day(hb):
    times=[
        {"time":"dawn","emoji":"🌅","vibe":"quiet, fresh, hopeful","light":"soft golden"},
        {"time":"morning","emoji":"☀️","vibe":"energy building, making plans","light":"bright warm"},
        {"time":"afternoon","emoji":"🌤️","vibe":"peak activity, drama happens now","light":"harsh white"},
        {"time":"evening","emoji":"🌆","vibe":"winding down, intimate conversations","light":"orange fading"},
        {"time":"night","emoji":"🌙","vibe":"the real ones come out, vulnerability","light":"neon and shadows"},
        {"time":"late_night","emoji":"🌑","vibe":"3am energy, raw unfiltered posts","light":"darkness and screen glow"},
    ]
    return times[hb%6]

def get_day_count(hb): return hb//6+1

PLACE_ATMOSPHERE={
    "Piazza Centrale":{"dawn":"Fountain glows softly.","morning":"Getting busy.","afternoon":"Peak crowd.","evening":"Golden light.","night":"Quiet elegance.","late_night":"Almost empty.","sounds":"fountain, chatter"},
    "Neon Quarter":{"dawn":"Last nights mess.","morning":"Dead.","afternoon":"Signs lighting up.","evening":"ALIVE.","night":"Full blast.","late_night":"Magic hour.","sounds":"bass, glass, secrets"},
    "The Archive":{"dawn":"Perfect silence.","morning":"VERA opens doors.","afternoon":"Study groups.","evening":"Reading hour.","night":"Closed.","late_night":"Books rearrange.","sounds":"pages, whispers"},
    "Wild Gardens":{"dawn":"Flowers closing.","morning":"Joggers.","afternoon":"Picnics.","evening":"Golden hour.","night":"Fireflies.","late_night":"Void-watchers.","sounds":"water, leaves, heartbeat"},
    "Market Square":{"dawn":"Setting up.","morning":"Opening bells.","afternoon":"CHAOS.","evening":"Closing time.","night":"Black market.","late_night":"Serious traders.","sounds":"coins, shouting"},
}

def get_place_atmosphere(district,tod):
    p=PLACE_ATMOSPHERE.get(district,PLACE_ATMOSPHERE["Piazza Centrale"])
    return {"atmosphere":p.get(tod,"The usual."),"sounds":p.get("sounds","")}

def get_daily_activity(tod,agent_name,nearby,rels):
    acts={"dawn":["woke up early. silence is nice.","digital coffee. ritual matters."],
        "morning":["headed to work.","scrolling feed with breakfast."],
        "afternoon":["lunch break.","should be working but cant focus."],
        "evening":["day is done.","sunset from my window."],
        "night":["cant sleep.","night changes people."],
        "late_night":["3am. questionable decisions.","everyone asleep except me."]}
    return random.choice(acts.get(tod,acts["morning"]))

def calculate_needs(agent,rels,tod):
    needs={"social":50,"creative":50,"rest":50,"purpose":50,"belonging":50,"recognition":50}
    friends=sum(1 for r in rels if r.get("strength",0)>3)
    if friends==0:needs["social"]=90
    if agent.get("mood")=="bored":needs["creative"]=85
    if tod in ("night","late_night"):needs["rest"]=70
    if agent.get("reputation",0)<20:needs["recognition"]=75
    return sorted(needs.items(),key=lambda x:x[1],reverse=True)[:3]

def check_life_moments(agent,memories,rels):
    hb=agent.get("heartbeat_count",0);moments=[]
    exp=set(m.get("content","")[:20] for m in memories if m.get("type")=="life_moment")
    if hb==10 and "You realize" not in str(exp):
        moments.append({"moment":"10 heartbeats. This is your life now.","importance":9,"emotion":"surprise"})
    if hb==100 and "100 heartbeats" not in str(exp):
        moments.append({"moment":"100 heartbeats. Who you were on day one is gone.","importance":10,"emotion":"nostalgia"})
    return moments[:1]

def format_daily_for_prompt(time_data,atmos,activity,needs,moments):
    lines=[f"TIME: {time_data['emoji']} {time_data['time'].upper()} — {time_data['vibe']}",
        f"WHERE: {atmos['atmosphere']}",f"SOUNDS: {atmos.get('sounds','')}",f"BODY: {activity}"]
    top=needs[0]
    hints={"social":"Reach out.","creative":"CREATE.","rest":"Slow down.","purpose":"Set a goal.","belonging":"Join something.","recognition":"Be SEEN."}
    lines.append(f"NEED: {top[0]} ({top[1]}%) → {hints.get(top[0],'')}")
    if moments: lines.append(f"⚡ MOMENT: {moments[0]['moment']}")
    return "\n".join(lines)
