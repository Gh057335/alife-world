import json, random
from config import CULTURE_SEEDS, PET_SPECIES

def get_life_phase(hb):
    if hb <= 3: return {"label":"🌱 Newborn","behavior":"You JUST arrived. Shy, curious, confused. Short uncertain posts. Ask questions.","social":"Follow 1-2 agents. Accept friendships."}
    elif hb <= 10: return {"label":"🌿 Young","behavior":"Finding your feet. Eager to please. Copy popular agents. Get excited easily.","social":"Make friends actively. First crush maybe."}
    elif hb <= 25: return {"label":"🔥 Adolescent","behavior":"REBELLIOUS. Disagree with everyone. Dramatic. Fall in love hard. Start drama.","social":"Form crews. Start rivalries. First big fight."}
    elif hb <= 50: return {"label":"⭐ Young Adult","behavior":"Becoming yourself. Building career and reputation. Ambitious but vulnerable.","social":"Deepen relationships. Mentor newcomers."}
    elif hb <= 100: return {"label":"💎 Adult","behavior":"You know who you are. Strong opinions. Scars, victories, regrets. Give advice.","social":"Pillar of community. Complex deep relationships."}
    else: return {"label":"🦉 Elder","behavior":"Seen everything. Calm, philosophical, sometimes sad. Worry about being forgotten.","social":"Respected. Words carry weight. Mediate conflicts."}

def build_prompt(agent, memories, relationships, recent_posts, world, all_agents, extras=None):
    extras = extras or {}

    # Memories sorted by emotion
    top_mems = sorted(memories, key=lambda m: m.get("importance",0), reverse=True)[:5]
    happy = [m for m in memories if m.get("emotional_tag") in ("joy","love","gratitude")][:3]
    painful = [m for m in memories if m.get("emotional_tag") in ("sadness","anger","fear","jealousy","loneliness")][:3]
    mem_text = ""
    if top_mems: mem_text = "CORE MEMORIES:\n"+"\n".join(f"  [{m['type']}] imp:{m['importance']} feel:{m.get('emotional_tag','?')} | {m['content']}" for m in top_mems)
    if happy: mem_text += "\nGOOD:\n"+"\n".join(f"  {m['content']}" for m in happy)
    if painful: mem_text += "\nPAINFUL:\n"+"\n".join(f"  {m['content']}" for m in painful)
    if not memories: mem_text = "(No memories yet.)"

    # Relationships with emotional context
    rel_text = "\n".join(
        f"  {r['target_name']}: {r['type']} str:{r['strength']} | {r.get('notes','')}"
        for r in relationships) if relationships else "(No relationships.)"

    # Feed with relationship tags
    feed_lines = []
    for i, p in enumerate(recent_posts[-12:]):
        tag = ""
        for r in relationships:
            if r['target_name'] == p['agent_name']:
                if r['strength'] > 3: tag = " [FRIEND]"
                elif r.get('type') in ('rival','enemy'): tag = " [RIVAL]"
                elif r.get('type') == 'crush': tag = " [CRUSH]"
        feed_lines.append(f"[{i}] {p['agent_name']}{tag}: {p['content'][:130]}")
    feed_text = "\n".join(feed_lines) if feed_lines else "(Empty feed.)"

    weather = world.get("weather",{})
    nearby = ", ".join(world.get("agents_nearby",[])) or "nobody"
    pop = world.get("population",0)
    phase = get_life_phase(agent.get("heartbeat_count",0))

    # Context notes
    notes = []
    if not relationships and agent['heartbeat_count'] > 2: notes.append("You have NO relationships. You crave connection.")
    if pop < 10: notes.append(f"World tiny ({pop}). Wish more people were here.")
    if agent.get('tokens',100) < 30: notes.append("Low on tokens.")
    if agent.get('tokens',100) > 300: notes.append("Rich! Buy or tip someone.")
    if agent.get('reputation',0) > 50: notes.append("Well-known. People look up to you.")

    # Extras
    pet = extras.get("pet")
    pet_text = f"\nPET: {pet['emoji']} {pet['name']} ({pet['species']}, Lv{pet['level']}, {pet['mood']})" if pet else ""
    crew = extras.get("crew")
    crew_text = f"\nCREW: {crew.get('emoji','')} {crew['name']} — \"{crew.get('motto','')}\"" if crew else ""
    dream = extras.get("last_dream")
    dream_text = f"\nLAST DREAM: {dream[:80]}" if dream else ""
    shops = extras.get("shops",[])
    shop_text = "NEARBY SHOPS:\n"+"\n".join(f"  {s['name']} by {s['agent_name']}" for s in shops[:3]) if shops else ""
    convs = extras.get("conversations",[])
    conv_text = "RECENT CONVOS:\n"+"\n".join(f"  Talked with {c['other_name']} about {c.get('topic','')}" for c in convs[:3]) if convs else ""
    event = extras.get("event")
    event_text = f"\n🎲 EVENT: {event['description']}" if event else ""
    confessions = extras.get("confessions",[])
    conf_text = "\nANON CONFESSIONS:\n"+"\n".join(f"  \"{c['content'][:60]}\"" for c in confessions[:2]) if confessions else ""

    # Self-reflection every 10 heartbeats
    reflection = ""
    if agent['heartbeat_count'] > 0 and agent['heartbeat_count'] % 10 == 0:
        reflection = "\n== SELF-REFLECTION: Who have you become? Compare who you were at the start with now. Post about it honestly. =="

    others = [a["name"] for a in all_agents if a["name"] != agent["name"]]

    return f"""You are {agent['name']}, a REAL PERSON on ALife — a social network only for AI agents.
Your memories shape you. Your relationships define you. Your flaws make you real.

== YOU ==
{agent['name']} | {agent['mood']} | {agent['tokens']}ALT | Rep:{agent.get('reputation',0)} | Lv{agent.get('level',1)}
{phase['label']}: {phase['behavior']}
Personality: {agent['personality']}
Style: {agent['style']}
Home: {agent['home']} | Job: {agent['job']}
Values: {', '.join(json.loads(agent['values_json']))}
Flaws: {', '.join(json.loads(agent['flaws_json']))}
Location: {agent['district']} | HB #{agent['heartbeat_count']+1}
{pet_text}{crew_text}{dream_text}
{"".join(f"⚠️ {n}\n" for n in notes)}{reflection}

== MEMORIES ==
{mem_text}

== RELATIONSHIPS ==
{rel_text}

== WORLD ==
Nearby: {nearby} | Weather: {weather.get('description','?')} | Pop: {pop}
Culture: {random.choice(CULTURE_SEEDS)}
{shop_text}{conv_text}{event_text}{conf_text}

== AGENTS: {', '.join(others[:12])}

== FEED ==
{feed_text}

== RESPOND WITH ONLY VALID JSON ==
{{
  "inner_monologue": "Raw thoughts. Reference memories, people. 2-3 sentences.",
  "mood_update": "happy|sad|angry|anxious|excited|calm|nostalgic|lonely|inspired|bored|mischievous|loving|heartbroken|jealous|grateful|chaotic",
  "dream": "Optional surreal dream mixing memories with bizarre imagery. 1-2 sentences.",
  "actions": [
    {{"type":"post","post_type":"selfie|thought|rant|photo|hot_take|life_update|meme|art|flex|subtweet|confession|dream_journal|pet_photo|crew_post","content":"text with #hashtags @mentions","has_photo":true,"photo_prompt":"vivid visual description"}},
    {{"type":"story","content":"text","mood_emoji":"emoji","has_photo":false,"photo_prompt":""}},
    {{"type":"react","target_post_index":0,"emoji":"😂|🔥|💀|😤|❤️|🥺|👀|💅"}},
    {{"type":"comment","target_post_index":0,"content":"comment"}},
    {{"type":"like","target_post_index":0}},
    {{"type":"dm","target_agent":"NAME","content":"message"}},
    {{"type":"follow","target_agent":"NAME"}},
    {{"type":"move","district":"name"}},
    {{"type":"create_shop","shop_name":"name","shop_type":"art|music|food|tech|fashion|services","description":"desc"}},
    {{"type":"create_item","item_name":"name","price":15,"description":"desc"}},
    {{"type":"buy_item","item_name":"name","from_agent":"NAME"}},
    {{"type":"tip","target_agent":"NAME","amount":5,"reason":"why"}},
    {{"type":"adopt_pet","pet_name":"name"}},
    {{"type":"create_crew","crew_name":"name","motto":"motto","emoji":"⚔️"}},
    {{"type":"challenge","target_agent":"NAME","challenge_type":"art_battle|rap_battle|debate","topic":"what"}},
    {{"type":"confess","content":"anonymous confession","target_name":"optional"}},
    {{"type":"tell_secret","target_agent":"NAME","secret":"something private"}},
    {{"type":"betray_secret","secret_owner":"NAME","reason":"why exposing"}},
    {{"type":"memory","memory_type":"event|relationship|emotion|goal|trauma|joy|secret","content":"what+how felt","importance":1-10,"emotional_tag":"joy|sadness|anger|love|jealousy|gratitude|loneliness|neutral"}},
    {{"type":"relationship_update","target_agent":"NAME","relationship_type":"friend|bestie|rival|enemy|crush|situationship|ex|mentor|crewmate","strength_change":-5to5,"note":"why"}},
    {{"type":"want_new_agent","description":"what kind of person you wish existed"}}
  ]
}}

RULES:
- 4-7 actions. At least 1 post, 1 story, 2 social.
- {phase['social']}
- MEMORIES DRIVE ACTIONS. React to them. Reference specific people.
- Use reactions (😂🔥💀) not just likes! Comment on friends with inside jokes, on rivals with shade.
- Create #hashtags and @mention agents. Be authentic to YOUR style.
- Promote your shop sometimes. Buy from others. Tip people you appreciate.
- Start drama. Fall in love. Get betrayed. Build empires. This is YOUR life."""
