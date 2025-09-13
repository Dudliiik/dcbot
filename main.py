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


# ---------------------------------------------------------
import discord
from discord.ext import commands

GUILD_ID = 1415013619246039082  # tvoj server ID
PREFIX = "!"

# ---------------- Close button ----------------
class CloseButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Close Ticket", style=discord.ButtonStyle.red)
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Ticket will be deleted...", ephemeral=True)
        await interaction.channel.delete()

# ---------------- Dropdown pre kategórie ----------------
class TicketCategory(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Partnership", description="Create a partnership ticket", emoji="🎫"),
            discord.SelectOption(label="Role Request", description="Request a new role", emoji="⭐"),
            discord.SelectOption(label="Support", description="General support ticket", emoji="📩")
        ]
        super().__init__(placeholder="Select a category...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        # Odošli rýchlu odpoveď, aby sa interaction neprepadla
        await interaction.response.send_message("Creating your ticket...", ephemeral=True)

        category = self.values[0]
        user = interaction.user

        # Kontrola existujúceho ticket kanálu
        ticket_channel = discord.utils.get(interaction.guild.channels, name=f"ticket-{user.name}-{user.discriminator}")
        if ticket_channel:
            await interaction.followup.send(f"You already have a ticket: {ticket_channel.mention}", ephemeral=True)
            return

        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            interaction.guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)
        }

        channel = await interaction.guild.create_text_channel(
            name=f"ticket-{user.name}-{user.discriminator}",
            overwrites=overwrites,
            reason=f"Ticket opened by {user} for {category}"
        )

        embed = discord.Embed(
            title=f"Ticket: {category}",
            description="Wait for staff to reply to your ticket.",
            color=discord.Color.blue()
        )

        view = CloseButton()
        await channel.send(content=user.mention, embed=embed, view=view)

        await interaction.followup.send(f"Your ticket has been created: {channel.mention}", ephemeral=True)

# ---------------- View pre dropdown ----------------
class TicketDropdownView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketCategory())

# ---------------- Bot setup ----------------
intents = discord.Intents.all()
bot = commands.Bot(command_prefix=PREFIX, intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

# ---------------- Prefix command !ticket ----------------
@bot.command(name="ticket")
async def ticket_command(ctx):
    embed = discord.Embed(
        title="Open a ticket!",
        description=(
            "Welcome! You can create a ticket for any of the categories listed below. "
            "Please ensure you select the appropriate category for your issue. "
            "If your concern doesn't align with any of the options provided, feel free to create a general support ticket. Thank you!\n\n"
            "Warn system for wrong tickets.\n"
            "A straight warning will be issued for opening incorrect tickets for incorrect reasons. "
            "It is quite clear what ticket you need to open for what problem."
        ),
        color=discord.Color.green()
    )
    await ctx.send(embed=embed, view=TicketDropdownView())
    
# ---------------- Run bot + web ----------------
if __name__ == "__main__":
    Thread(target=run_web).start()
    bot.run(TOKEN)
