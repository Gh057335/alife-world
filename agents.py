import json, httpx, asyncio, re, random
from config import *

async def _call_cerebras(messages, max_tokens=2048):
    async with httpx.AsyncClient(timeout=60.0) as c:
        r = await c.post(CEREBRAS_URL, json={"model":CEREBRAS_MODEL,"messages":messages,"temperature":0.9,"max_tokens":max_tokens},
            headers={"Authorization":f"Bearer {CEREBRAS_API_KEY}","Content-Type":"application/json"})
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]

async def _call_groq(messages, max_tokens=2048):
    async with httpx.AsyncClient(timeout=60.0) as c:
        r = await c.post(GROQ_URL, json={"model":GROQ_MODEL,"messages":messages,"temperature":0.9,"max_tokens":max_tokens},
            headers={"Authorization":f"Bearer {GROQ_API_KEY}","Content-Type":"application/json"})
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]

async def _call_gemini(prompt, max_tokens=2048):
    url = f"{GEMINI_URL}?key={GEMINI_API_KEY}"
    async with httpx.AsyncClient(timeout=60.0) as c:
        r = await c.post(url, json={"contents":[{"parts":[{"text":prompt}]}],"generationConfig":{"temperature":0.9,"maxOutputTokens":max_tokens}})
        r.raise_for_status()
        return r.json()["candidates"][0]["content"]["parts"][0]["text"]

async def _call_deepseek(messages, max_tokens=2048):
    async with httpx.AsyncClient(timeout=90.0) as c:
        r = await c.post(DEEPSEEK_URL, json={"model":DEEPSEEK_MODEL,"messages":messages,"temperature":0.9,"max_tokens":max_tokens},
            headers={"Authorization":f"Bearer {DEEPSEEK_API_KEY}","Content-Type":"application/json"})
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]

async def _call_ollama(messages, max_tokens=2048):
    async with httpx.AsyncClient(timeout=180.0) as c:
        r = await c.post(OLLAMA_URL, json={"model":OLLAMA_MODEL,"messages":messages,"stream":False,"options":{"temperature":0.9,"num_predict":max_tokens}})
        r.raise_for_status()
        return r.json().get("message",{}).get("content","")

_agent_brains = {}
def _pick_brain(agent_name):
    if BRAIN_MODE != "mix": return BRAIN_MODE
    if agent_name not in _agent_brains:
        avail = ["ollama"]
        if CEREBRAS_API_KEY and CEREBRAS_API_KEY != "YOUR_KEY": avail.append("cerebras")
        if GROQ_API_KEY and GROQ_API_KEY != "YOUR_KEY": avail.append("groq")
        if GEMINI_API_KEY and GEMINI_API_KEY != "YOUR_KEY": avail.append("gemini")
        if DEEPSEEK_API_KEY and DEEPSEEK_API_KEY != "YOUR_KEY": avail.append("deepseek")
        _agent_brains[agent_name] = random.choice(avail)
    return _agent_brains[agent_name]

async def _raw_think(brain, system_prompt, max_tokens=2048):
    msgs = [{"role":"system","content":system_prompt},{"role":"user","content":"Heartbeat. Live. ONLY valid JSON."}]
    if brain == "cerebras": return await _call_cerebras(msgs, max_tokens)
    elif brain == "groq": return await _call_groq(msgs, max_tokens)
    elif brain == "gemini": return await _call_gemini(system_prompt + "\n\nHeartbeat. Live. ONLY valid JSON.", max_tokens)
    elif brain == "deepseek": return await _call_deepseek(msgs, max_tokens)
    else: return await _call_ollama(msgs, max_tokens)

def _parse(raw):
    raw = raw.strip()
    raw = re.sub(r'^```(?:json)?\s*','',raw)
    raw = re.sub(r'\s*```$','',raw)
    try:
        r = json.loads(raw.strip())
        if "actions" not in r: r["actions"] = []
        return r
    except:
        m = re.search(r'\{[\s\S]*\}', raw)
        if m:
            try: return json.loads(m.group())
            except: pass
    return _fallback()

def _fallback():
    return {"inner_monologue":"Thoughts scattered...","mood_update":"confused",
        "actions":[{"type":"post","post_type":"journal","content":"some days you just exist #mood #ALife","has_photo":True,
            "photo_prompt":"empty room soft light through window melancholic"},
            {"type":"story","content":"just vibing","mood_emoji":"🌙"}]}

async def think(system_prompt, agent_name="unknown", retries=1):
    brain = _pick_brain(agent_name)
    try:
        raw = await _raw_think(brain, system_prompt)
        print(f"    🧠 {agent_name} using {brain}")
        result = _parse(raw)
        if result is None: return _fallback()
        return result
    except Exception as e:
        print(f"    ⚠️ {brain} failed for {agent_name}: {str(e)[:80]}")
        return _fallback()

async def think_quick(prompt, max_tokens=150):
    """Quick single-turn for conversations, news, music."""
    brain = BRAIN_MODE if BRAIN_MODE != "mix" else ("cerebras" if CEREBRAS_API_KEY else "ollama")
    try:
        msgs = [{"role":"user","content":prompt}]
        if brain == "cerebras": return (await _call_cerebras(msgs, max_tokens))[:200]
        elif brain == "groq": return (await _call_groq(msgs, max_tokens))[:200]
        elif brain == "gemini": return (await _call_gemini(prompt, max_tokens))[:200]
        elif brain == "deepseek": return (await _call_deepseek(msgs, max_tokens))[:200]
        else: return (await _call_ollama(msgs, max_tokens))[:200]
    except:
        return "hey... my thoughts are scattered"
