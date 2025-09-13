import discord
from discord.ext import commands
from discord import app_commands, utils
import time
import os
from flask import Flask
from threading import Thread
from dotenv import load_dotenv

class ticket_launcher(discord.ui.View):
    def __init__(self) -> None:
        super().__init__(timeout=None)

@discord.ui.button(label = "Open a ticket!", style = discord.ButtonStyle.blurple, custom_id="ticket_button")
async def ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
    ticket = utils.get(interaction.guild.text_channels, name = f"ticket-{interaction.user.name}-{interaction.user.discriminator}")
    if ticket is not None: await interaction.response.send_message(f"You already have a ticket open at {ticket.mention}", ephemeral=True)
    else:
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(view_channel = False),
            interaction.user: discord.PermissionOverwrite(view_channel = True, send_messages = True, attach_files = True, embed_links = True),
            interaction.guild.me: discord.PermissionOverwrite(view_channel = True, send_messages = True, read_message_history = True)
        }
        channel = await interaction.guild.create_text_channel(name = f"ticket-{interaction.user.name}-{interaction.user.discriminator}", 
        overwrites=overwrites, reason=f"Ticket-{interaction.user}")
        await interaction.response.send_message(f"Ticket opened - {channel.mention}", ephemeral=True)

# ---------------- Load .env ----------------
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# ---------------- Flask server ----------------
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running"

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
class aclient(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.default())
        self.synced = True

client = aclient()
tree=app_commands.CommandTree(client)

@tree.command(name='ticket')
async def ticketing(interaction:discord.Interaction):
    embed = discord.Embed(title="Welcome! You can create a ticket for any of the categories listed below. Please ensure you select the appropriate category for your issue. If your concern doesn't align with any of the options provided, feel free to create a general support ticket. Thank you!" \
    "Warn system for wrong tickets. " \
    "A straight warning will be issued for opening incorrect tickets for incorrect reasons. It is quite clear what ticket you need to open for what problem.", color=discord.Colour.dark_blue())
    await interaction.channel.send(embed=embed, view = ticket)
    await interaction.response.send_message("Ticket system launched!", ephemeral=True)


@bot.event
async def on_ready():
    print(f"User logged as {bot.user}")

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
    await ctx.send("<@&1135502050575261758>")  # ID Feedback role

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
    await ctx.send("<@&1282267309477728317>")  # ID WIP role

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
    await ctx.send("<@&1135502182825852988>")  # ID Help role


@commands.has_permissions(administrator = True)
@bot.command(aliases = ["purge"])
async def delete(ctx, amount : int):
    await ctx.channel.purge(limit=amount+1)
    confirmation = await ctx.send(f"Purged {amount} messages", delete_after = 3)

# ---------------- Run bot + web ----------------
if __name__ == "__main__":
    Thread(target=run_web).start()
    bot.run(TOKEN)
