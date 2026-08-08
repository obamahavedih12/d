import discord
import asyncio
import random
import time
import os
from discord.ext import commands
from datetime import datetime, timedelta

TOKEN = os.getenv("DISCORD_TOKEN")
TRIGGER_CHANNEL = int(os.getenv("TRIGGER_CHANNEL", "1513571358292971550"))
STATUS_CHANNEL = int(os.getenv("STATUS_CHANNEL", "1513571359953780767"))
QUESTION_CHANNEL = int(os.getenv("QUESTION_CHANNEL", "1513571360989905094"))

# ====== FIX: Add intents ======
intents = discord.Intents.default()
intents.message_content = True
intents.messages = True

bot = commands.Bot(command_prefix="!", self_bot=True, help_command=None, intents=intents)

status_cache = {"value": None, "timestamp": 0, "last_up": None, "last_down": None}
response_history = {"up": [], "down": [], "error": []}
user_cooldown = {}
message_counter = {}

# ====== MASSIVE RESPONSE POOLS ======
UP_RESPONSES = [
    "up. smooth sailing.",
    "up. all green, nexomia live.",
    "up. running fine, devs might tweak later.",
    "up. online and stable.",
    "up. no issues detected.",
    "up. good to go.",
    "up. nexus active.",
    "up. working as intended.",
    "up. all systems nominal.",
    "up. ready when you are.",
    "up. nexus is live, enjoy.",
    "up. everything's operational.",
    "up. devs say it's stable.",
    "up. no downtime reported.",
    "up. fresh and working.",
    "up. nexus online, go ahead.",
    "up. confirmed working.",
    "up. all good on this end.",
    "up. should be fine.",
    "up. positive status.",
    "up. live and kicking.",
    "up. nexus is awake.",
    "up. working perfectly.",
    "up. no problems found.",
    "up. status: online.",
    "up. feel free to use it.",
    "up. devs are monitoring.",
    "up. stable build running.",
    "up. everything checks out.",
    "up. you're good to go."
]

DOWN_RESPONSES = [
    "down. devs are on it. wait for update.",
    "down. hotfix incoming. hold tight.",
    "down. nexus is being patched. check soon.",
    "down. devs cooking a fix. stand by.",
    "down. e.t.a unknown. devs notified.",
    "down. priority queue. wait for push.",
    "down. service interrupted. devs working.",
    "down. temporary outage. devs aware.",
    "down. patch in progress. stay tuned.",
    "down. nexus offline. devs handling it.",
    "down. devs are debugging now.",
    "down. backend issues. wait for fix.",
    "down. rollback happening. give it time.",
    "down. nexus took a nap. wake it later.",
    "down. devs pushing emergency patch.",
    "down. server migration? wait for notice.",
    "down. auth issues. devs fixing.",
    "down. database being repaired.",
    "down. nexus is down, devs know.",
    "down. hotfix rolling out soon.",
    "down. check back in 15.",
    "down. maintenance window. hold tight.",
    "down. nexus crashed. devs rebooting.",
    "down. api timeout. devs on it.",
    "down. deployment failed. retrying.",
    "down. wait for devs to greenlight.",
    "down. nexus offline, stay tuned.",
    "down. issues reported. devs investigating.",
    "down. fixing as we speak.",
    "down. should be back shortly."
]

ERROR_RESPONSES = [
    "can't fetch status. check manual.",
    "status unknown. check yourself.",
    "couldn't reach status channel.",
    "no status found. ask devs.",
    "status check failed. try later.",
    "maybe check the status channel?",
    "unable to read status. manual check.",
    "status api offline? check manually.",
    "can't determine. verify yourself.",
    "status unavailable. ping devs."
]

CONVERSATIONAL = [
    "how's your day?",
    "nexus is a vibe today.",
    "devs are sleeping btw.",
    "patience, young padawan.",
    "i'm just a bot, don't shoot.",
    "checking... beep boop.",
    "nexus or nexomia? pick one.",
    "devs said 'soon' ™",
    "imagine having uptime.",
    "this is fine. 🔥",
    "good question. next question.",
    "i don't make the rules.",
    "tell the devs to fix it.",
    "your guess is as good as mine.",
    "i'm the messenger, not the dev.",
    "nexus = love, nexus = life.",
    "wrong roblox version? oh no.",
    "client 7484? oof.",
    "live version required btw.",
    "did you try turning it off?",
    "maybe reinstall? just saying.",
    "devs hate this one trick.",
    "update your client, bro.",
    "7484 is old. get live.",
    "wrong version alert! 🚨",
]

ROBLOX_TRIGGERS = [
    "wrong roblox version",
    "make sure to download the latest LIVE version of Roblox",
    "client: 7484",
    "roblox version mismatch",
    "live version required",
    "update roblox",
    "wrong client version",
    "roblox outdated",
]

CONVERSATIONAL_TRIGGERS = [
    "when is it back",
    "how long",
    "eta",
    "estimated time",
    "when fix",
    "any update",
    "is it gonna be up soon",
    "how much longer",
    "devs said anything"
]

def get_status():
    now = time.time()
    if now - status_cache["timestamp"] < 60 and status_cache["value"] is not None:
        return status_cache["value"]
    
    try:
        channel = bot.get_channel(STATUS_CHANNEL)
        if not channel:
            return None
        
        async def fetch():
            async for msg in channel.history(limit=20):
                content = msg.content.lower()
                if "up" in content and "down" not in content:
                    status_cache["last_up"] = msg.created_at
                    return "up"
                if "down" in content and "up" not in content:
                    status_cache["last_down"] = msg.created_at
                    return "down"
            return None
        
        status = asyncio.run_coroutine_threadsafe(fetch(), bot.loop).result()
        status_cache["value"] = status
        status_cache["timestamp"] = now
        return status
    except Exception as e:
        print(f"Status fetch error: {e}")
        return None

def get_response(status, trigger_type="status"):
    if status == "up":
        pool = UP_RESPONSES
    elif status == "down":
        pool = DOWN_RESPONSES
    else:
        pool = ERROR_RESPONSES
    
    used_key = "down" if status == "down" else "up"
    available = [r for r in pool if r not in response_history.get(used_key, [])]
    if not available:
        response_history[used_key] = []
        available = pool
    
    chosen = random.choice(available)
    response_history.setdefault(used_key, []).append(chosen)
    if len(response_history[used_key]) > 15:
        response_history[used_key] = response_history[used_key][-10:]
    
    if random.random() > 0.6:
        conv = random.choice(CONVERSATIONAL)
        chosen = f"{chosen} {conv}"
    
    return chosen

def get_roblox_response():
    return random.choice([
        "wrong version. download LIVE from roblox.com.",
        "client 7484? update to latest live.",
        "roblox version mismatch. grab the live build.",
        "outdated client. get the latest version.",
        "7484 isn't live. update roblox.",
        "wrong roblox version. devs said use live.",
        "your client is old. get the latest roblox.",
        "roblox needs updating. live version required."
    ])

def get_eta_response():
    return random.choice([
        "no eta yet. devs working.",
        "devs haven't given a time.",
        "could be minutes. could be hours.",
        "check back later. no eta.",
        "devs are silent on eta.",
        "unknown. watch the status channel.",
        "soon™ as always.",
        "when it's ready.",
        "devs will announce when fixed."
    ])

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    print(f"📡 Monitoring: {TRIGGER_CHANNEL}, {QUESTION_CHANNEL}")
    print(f"📊 Status channel: {STATUS_CHANNEL}")
    print(f"🟢 Bot is ready and listening!")

@bot.event
async def on_message(message):
    # Debug: print every message received
    print(f"📨 Message from {message.author}: {message.content[:50]}")
    
    if message.author == bot.user:
        return
    
    if message.content.startswith("!"):
        return
    
    user_id = message.author.id
    message_counter[user_id] = message_counter.get(user_id, 0) + 1
    
    content = message.content.lower()
    
    # ====== ROBLOX VERSION TRIGGER ======
    if any(trigger in content for trigger in ROBLOX_TRIGGERS):
        if message.channel.id in [QUESTION_CHANNEL, TRIGGER_CHANNEL]:
            print("🔴 Roblox trigger detected!")
            roblox_response = get_roblox_response()
            await message.channel.send(roblox_response)
            await asyncio.sleep(0.5)
            try:
                await message.add_reaction(random.choice(["✅", "👍", "💀", "🔥"]))
            except:
                pass
            return
    
    # ====== ETA / WHEN BACK TRIGGER ======
    if any(trigger in content for trigger in CONVERSATIONAL_TRIGGERS):
        if message.channel.id in [QUESTION_CHANNEL, TRIGGER_CHANNEL]:
            print("⏳ ETA trigger detected!")
            eta_response = get_eta_response()
            await message.channel.send(eta_response)
            try:
                await message.add_reaction("⏳")
            except:
                pass
            return
    
    # ====== MAIN NEXOMIA STATUS TRIGGER ======
    if message.channel.id in [QUESTION_CHANNEL, TRIGGER_CHANNEL]:
        if any(phrase in content for phrase in ["nexomia", "nexus", "up?", "working?", "is it up", "status", "what's the status"]):
            print("🟢 Nexomia status trigger detected!")
            
            now = time.time()
            if user_id in user_cooldown and now - user_cooldown[user_id] < 25:
                print(f"⏱️ Cooldown for user {user_id}")
                return
            user_cooldown[user_id] = now
            
            status = get_status()
            print(f"📊 Status fetched: {status}")
            
            if status == "down":
                response = get_response(status)
            elif status == "up":
                response = get_response(status)
            else:
                response = random.choice(ERROR_RESPONSES)
            
            if message_counter.get(user_id, 0) > 5 and random.random() > 0.7:
                conv = random.choice(CONVERSATIONAL)
                response = f"{response} {conv}"
            
            prefixes = ["hey ", "yo ", "just fyi ", "quick update: ", "checkin: ", ""]
            if random.random() > 0.5:
                response = random.choice(prefixes) + response
            
            await message.channel.send(response)
            await asyncio.sleep(0.5)
            try:
                await message.add_reaction(random.choice(["✅", "👍", "👀", "🔥", "💀", "⏳"]))
            except:
                pass

async def keep_alive():
    while True:
        await asyncio.sleep(300)
        status_cache["timestamp"] = 0
        print("🔄 Status cache refreshed")

@bot.event
async def on_connect():
    print("🔌 Bot connected to Discord!")
    bot.loop.create_task(keep_alive())

if not TOKEN:
    print("❌ ERROR: DISCORD_TOKEN not set")
    exit(1)

print("🚀 Starting bot...")
bot.run(TOKEN, bot=False)
