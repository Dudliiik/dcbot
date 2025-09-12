import discord
from discord.ext import commands
import time
import os
from flask import Flask
from threading import Thread
from dotenv import load_dotenv

# ---------------- Load .env ----------------
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    raise ValueError("DISCORD_TOKEN environment variable not set")

# ---------------- Flask server ----------------
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running!"

def run_web():
    port = int(os.environ.get("PORT", 10000))  # Render poskytuje PORT
    app.run(host="0.0.0.0", port=port)

# ---------------- Discord bot ----------------
intents = discord.Intents.default()
intents.message_content = True 

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# ---------------- Cooldowns ----------------
feedback_cooldowns = {}  
wip_cooldowns = {}       
help_cooldowns = {}      

# ---------------- Commands ----------------
@bot.event
async def on_ready():
    print(f"✅ User logged as {bot.user}")

@bot.command()
async def feedback(ctx):
    now = time.time()
    user_id = ctx.author.id
    last_used = feedback_cooldowns.get(user_id, 0)
    cooldown_seconds = 7200  # 2 hodiny

    if now - last_used < cooldown_seconds:
        remaining = cooldown_seconds - (now - last_used)
        hours = int(remaining // 3600)
        minutes = int((remaining % 3600) // 60)
        seconds = int(remaining % 60)
        await ctx.send(f"You can ping Feedback again in {hours}h {minutes}m {seconds}s!")
        return

    if len(ctx.message.attachments) == 0:
        await ctx.send("You have to attach an image to ping Feedback!")
        return

    feedback_cooldowns[user_id] = now
    await ctx.send("<@&1415013619246039085>")  # ID Feedback role

@bot.command()
async def wip(ctx):
    now = time.time()
    user_id = ctx.author.id
    last_used = wip_cooldowns.get(user_id, 0)
    cooldown_seconds = 7200  # 2 hodiny

    if now - last_used < cooldown_seconds:
        remaining = cooldown_seconds - (now - last_used)
        hours = int(remaining // 3600)
        minutes = int((remaining % 3600) // 60)
        seconds = int(remaining % 60)
        await ctx.send(f"You can ping WIP again in {hours}h {minutes}m {seconds}s!")
        return

    if len(ctx.message.attachments) == 0:
        await ctx.send("You have to attach an image to ping WIP!")
        return

    wip_cooldowns[user_id] = now
    await ctx.send("<@&1415013619246039083>")  # ID WIP role

@bot.command()
async def help(ctx):
    now = time.time()
    user_id = ctx.author.id
    last_used = help_cooldowns.get(user_id, 0)
    cooldown_seconds = 7200  # 2 hodiny

    if now - last_used < cooldown_seconds:
        remaining = cooldown_seconds - (now - last_used)
        hours = int(remaining // 3600)
        minutes = int((remaining % 3600) // 60)
        seconds = int(remaining % 60)
        await ctx.send(f"You can use Help again in {hours}h {minutes}m {seconds}s!")
        return

    help_cooldowns[user_id] = now
    await ctx.send("<@&1415013619246039084>")  # ID Help role

# ---------------- Run bot + web ----------------
if __name__ == "__main__":
    Thread(target=run_web).start()
    bot.run(TOKEN)
