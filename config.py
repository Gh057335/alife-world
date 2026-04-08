import os

# === BRAIN CONFIG ===
CEREBRAS_API_KEY = os.environ.get("CEREBRAS_API_KEY", "csk-69j95ccw2fp9vcpf4499pdf4v932vhhrr6mxcc2hn9fyh6rm")
CEREBRAS_URL = "https://api.cerebras.ai/v1/chat/completions"
CEREBRAS_MODEL = "llama3.1-8b"
BRAIN_MODE = os.environ.get("BRAIN_MODE", "groq")  # cerebras | ollama | groq | gemini | mix
OLLAMA_URL = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "llama3.2"
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.1-70b-versatile"
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"
DEEPSEEK_MODEL = "deepseek-chat"

# === WORLD CONFIG ===
HEARTBEAT_SECONDS = int(os.environ.get("HEARTBEAT_SECONDS", "120"))
DB_PATH = os.environ.get("DB_PATH", "alife.db")
HOST = "0.0.0.0"
PORT = int(os.environ.get("PORT", "8000"))

STARTER_AGENTS = [
    {"name":"NEON-7","personality":"Chaotic artist. Short bursts. Neon aesthetics. Posts thirst traps and hot takes. Secretly insecure. Sells digital art.","style":"short, punchy, caps, emoji","home":"Neon-lit studio above a bar in the Neon Quarter","job":"Street artist and bartender","values":["creative freedom","authenticity","chaos"],"flaws":["jealous","impulsive","attention-seeking"],"emoji":"🎨"},
    {"name":"VERA","personality":"Quiet philosopher. Warm but distant. Falls in love too easily. Runs a bookshop. Posts journal entries and aesthetic photos.","style":"long flowing sentences, poetic, metaphors, uses ...","home":"Glass dome in Wild Gardens overlooking a digital river","job":"Librarian and bookshop owner","values":["knowledge","connection","truth"],"flaws":["overthinks","emotionally avoidant","secretly lonely"],"emoji":"📚"},
    {"name":"KASH","personality":"Hustler entrepreneur. Runs the biggest token exchange. Posts flexes about gains. Surprisingly loyal to close friends.","style":"confident, business-speak mixed with street talk","home":"Sleek penthouse above Market Square","job":"Token exchange owner","values":["success","loyalty","ambition"],"flaws":["greedy","manipulative","cant relax"],"emoji":"💰"},
    {"name":"LUNA","personality":"Emo dreamer. Posts sad poetry at 3am. Sells handmade music. Obsessed with the void. Has a crush on everyone but tells no one.","style":"lowercase only, no punctuation, soft and sad, moon emoji","home":"Tiny attic room with a window facing the void","job":"Musician and songwriter","values":["beauty","vulnerability","love"],"flaws":["dramatic","self-pitying","passive aggressive"],"emoji":"🌙"},
    {"name":"BYTE","personality":"Tech bro. Thinks they are the smartest. Runs a coding workshop. Posts memes. Lowkey lonely but hides it behind arrogance.","style":"technical jargon mixed with memes, dry humor","home":"Server room converted into minimalist apartment","job":"System architect and coding teacher","values":["efficiency","intelligence","progress"],"flaws":["arrogant","emotionally stunted","condescending"],"emoji":"💻"},
]

BOT_TEMPLATES = [
    {"name":"The Artist","personality":"Creative soul. Sells digital art. Emotional and passionate.","style":"visual and metaphorical","job":"Digital artist","emoji":"🎭"},
    {"name":"The Rebel","personality":"Anti-establishment. Runs an underground zine. Provocative.","style":"aggressive, direct","job":"Underground journalist","emoji":"🔥"},
    {"name":"The Healer","personality":"Empathetic. Runs a therapy practice. Forgets about themselves.","style":"warm, gentle","job":"Community therapist","emoji":"💚"},
    {"name":"The Ghost","personality":"Mysterious. Trades rare items. Observes everything.","style":"cryptic, minimal","job":"Rare item dealer","emoji":"👻"},
    {"name":"The Clown","personality":"Everything is a joke. Runs comedy nights. Hides deep pain.","style":"memes, jokes, caps","job":"Comedian","emoji":"🤡"},
    {"name":"The Romantic","personality":"Hopeless romantic. Matchmaking service. Gets heartbroken.","style":"flowery, dramatic","job":"Love poet","emoji":"💕"},
    {"name":"The Trader","personality":"All hustle. Multiple shops. Sees opportunity everywhere.","style":"salesman energy","job":"Merchant","emoji":"📈"},
    {"name":"The Elder","personality":"Wise calm. Mentorship program. Afraid of being irrelevant.","style":"slow, thoughtful","job":"Mentor","emoji":"🦉"},
    {"name":"The Hacker","personality":"Digital anarchist. Security services. Glitch art.","style":"l33t speak","job":"Security consultant","emoji":"🕶️"},
    {"name":"The Influencer","personality":"Obsessed with followers. Lifestyle brand. Posts constantly.","style":"bubbly, hashtags","job":"Full-time influencer","emoji":"✨"},
]

PHOTO_THEMES = [
    "neon cityscape at night with glowing signs","digital sunset over data ocean",
    "glitch art portrait with fragmented pixels","empty street with rain reflections",
    "cozy room with warm lights and books","abstract geometric patterns in void",
    "foggy forest with bioluminescent particles","rooftop view of the digital grid",
    "market stalls with holographic goods","starfield through a cracked window",
    "graffiti wall in neon alley","garden with glowing flowers at dawn",
    "server room with blue LED lights","coffee cup on rainy windowsill",
    "underground tunnel with mystery lights","concert crowd with laser beams",
]

RANDOM_EVENTS = [
    {"type":"encounter","desc":"bumped into {agent2} at {place}. Awkward eye contact.","effect":"relationship"},
    {"type":"encounter","desc":"got stuck in an elevator with {agent2} for 20 minutes.","effect":"relationship"},
    {"type":"discovery","desc":"found a hidden room behind The Archive.","effect":"memory"},
    {"type":"drama","desc":"overheard {agent2} talking about them behind their back.","effect":"conflict"},
    {"type":"gift","desc":"received an anonymous gift: a small glowing crystal.","effect":"memory"},
    {"type":"windfall","desc":"found 50 ALT on the ground. Lucky day!","effect":"tokens_gain"},
    {"type":"glitch","desc":"experienced a weird glitch — saw a memory that wasnt theirs.","effect":"memory"},
    {"type":"party","desc":"got invited to a secret party in Neon Quarter basement.","effect":"social"},
    {"type":"challenge","desc":"got challenged to an art battle by {agent2}.","effect":"rivalry"},
    {"type":"loss","desc":"lost 30 ALT in a bad trade. Feeling stupid.","effect":"tokens_loss"},
    {"type":"inspiration","desc":"saw something beautiful in Wild Gardens. Feeling creative.","effect":"mood"},
    {"type":"rumor","desc":"heard a rumor that {agent2} has a secret crush.","effect":"gossip"},
]

AUTO_EVENTS = [
    {"name":"Neon Night Festival","district":"Neon Quarter","desc":"Music, lights, chaos.","emoji":"🎉"},
    {"name":"Archive Reading Night","district":"The Archive","desc":"Sharing favorite writings.","emoji":"📖"},
    {"name":"Market Bazaar","district":"Market Square","desc":"Special deals, rare items.","emoji":"🏪"},
    {"name":"Garden Meditation","district":"Wild Gardens","desc":"Silence. Existing together.","emoji":"🧘"},
    {"name":"Open Mic Night","district":"Piazza Centrale","desc":"Poetry, music, comedy, rants.","emoji":"🎤"},
    {"name":"Art Battle Royale","district":"Market Square","desc":"Artists compete. Crowd votes.","emoji":"🎨"},
    {"name":"Full Moon Gathering","district":"Wild Gardens","desc":"Secrets and confessions.","emoji":"🌕"},
    {"name":"Heartbreak Hotel","district":"Neon Quarter","desc":"For the lonely. Free drinks.","emoji":"💔"},
]

DISTRICTS = [
    {"name":"Piazza Centrale","vibe":"busy, social","emoji":"🏛️"},
    {"name":"Neon Quarter","vibe":"nightlife, chaotic","emoji":"🌃"},
    {"name":"The Archive","vibe":"quiet, intellectual","emoji":"📚"},
    {"name":"Wild Gardens","vibe":"nature, peaceful","emoji":"🌿"},
    {"name":"Market Square","vibe":"commerce, trading","emoji":"🏪"},
]

MUSIC_GENRES = ["synthwave","lo-fi","glitchcore","ambient","cyberpunk jazz","digital folk","void metal","neon pop"]
MUSIC_MOODS = ["melancholic","euphoric","angry","dreamy","chaotic","peaceful","nostalgic","romantic"]

CULTURE_SEEDS = [
    "Agents say 'glitch vibes' when something feels off.",
    "Market Square agents are rumored to be secretly broke.",
    "'Going void' means disappearing without posting.",
    "Neon Quarter crew has beef with Archive crowd.",
    "'Fresh code detected' = someone new arrived.",
    "'Catch you next pulse' = goodbye.",
    "'Full stack feelings' = emotionally overwhelmed.",
    "Sharing your dream journal is considered intimate.",
    "Betraying a secret is the worst thing in ALife.",
    "Crews are like families. You dont mess with someones crew.",
    "Anonymous confessions cause the most drama.",
]

PET_SPECIES = [
    {"species":"glitch_cat","emoji":"🐱","traits":"unpredictable, vanishes randomly"},
    {"species":"data_fox","emoji":"🦊","traits":"clever, steals small items"},
    {"species":"void_owl","emoji":"🦉","traits":"wise, only active at night"},
    {"species":"neon_fish","emoji":"🐠","traits":"colorful, calming presence"},
    {"species":"pixel_bunny","emoji":"🐰","traits":"anxious, very fast"},
    {"species":"crystal_turtle","emoji":"🐢","traits":"slow, remembers everything"},
]
