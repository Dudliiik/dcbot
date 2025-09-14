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

# ---------------- Flask ----------------
app = Flask(__name__)
@app.route("/")
def home():
    return "Bot is running"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# ---------------- Discord bot ----------------
intents = discord.Intents.default()
intents.message_content = True 
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# ---------------- Bot event ----------------
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

# ---------------- Cooldowns ----------------
cooldowns = {"feedback": {}, "wip": {}, "help": {}}

# ---------------- Ticket Views ----------------
class CloseButtons(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.red)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Ticket closed", ephemeral=True)
        await interaction.channel.delete()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.gray)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Close canceled", ephemeral=True)
        self.stop()

class CloseButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Close", emoji="🔒", style=discord.ButtonStyle.gray)
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="Sure?",
            description="Are you sure about closing this ticket?",
            color=discord.Color.dark_blue()
        )
        await interaction.response.send_message(embed=embed, view=CloseButtons(), ephemeral=True)

# ---------------- Ticket Logic ----------------
categories = {
    "Partnership": {"title":"Partnership Ticket", "desc":"Thanks {user} for contacting partnership team!", "ping":[1136118197725171813,1102975816062730291], "ping_user":True},
    "Role Request": {"title":"Role Request Ticket", "desc":"Send your role request details.", "ping":[1156543738861064192], "ping_user":False},
    "Support": {"title":"Support Ticket", "desc":"Please explain your support request.", "ping":[1102976554759368818,1102975816062730291], "ping_user":True}
}

class TicketCategory(discord.ui.Select):
    def __init__(self):
        options = [discord.SelectOption(label=k) for k in categories]
        super().__init__(placeholder="Select a topic", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        category = self.values[0]
        user = interaction.user
        channel_name = f"{category.lower().replace(' ','-')}-{user.name}"

        # ❌ len 1 ticket okrem Support
        if category != "Support" and discord.utils.get(interaction.guild.channels, name=channel_name):
            await interaction.followup.send(f"You already have a ticket in {category} category.", ephemeral=True)
            return

        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            interaction.guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)
        }

        channel = await interaction.guild.create_text_channel(
            name=channel_name,
            overwrites=overwrites,
            reason=f"Ticket opened by {user} for {category}"
        )

        cfg = categories[category]
        embed = discord.Embed(title=cfg["title"], description=cfg["desc"].format(user=user), color=discord.Color.blue())
        view = CloseButton()
        ping_roles = " ".join(f"<@&{rid}>" for rid in cfg["ping"])
        content = f"{user.mention} {ping_roles}" if cfg["ping_user"] else ping_roles

        await channel.send(content=content, embed=embed, view=view)
        await interaction.followup.send(f"Ticket created - {channel.mention}", ephemeral=True)

class TicketDropdownView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketCategory())

# ---------------- Commands ----------------
def check_cooldown(user_id, name, seconds=7200):
    now = time.time()
    last = cooldowns[name].get(user_id, 0)
    if now - last < seconds:
        remaining = seconds - (now - last)
        h = int(remaining // 3600)
        m = int((remaining % 3600) // 60)
        s = int(remaining % 60)
        return f"You can use {name.capitalize()} again in {h}h {m}m {s}s!"
    cooldowns[name][user_id] = now
    return None

async def send_ping(ctx, role_id, cd_name):
    msg = check_cooldown(ctx.author.id, cd_name)
    if msg:
        await ctx.send(msg)
        return
    if not ctx.message.attachments:
        await ctx.send("You must attach an image!")
        return
    await ctx.send(f"<@&{role_id}>")

@bot.command()  
async def feedback(ctx): await send_ping(ctx, 1135502050575261758, "feedback")
@bot.command()
async def wip(ctx): await send_ping(ctx, 1282267309477728317, "wip")
@bot.command()
async def help(ctx): await send_ping(ctx, 1135502182825852988, "help")

@commands.has_permissions(administrator=True)
@bot.command(aliases=["purge"])
async def delete(ctx, amount: int):
    await ctx.channel.purge(limit=amount+1)
    await ctx.send(f"Purged {amount} messages", delete_after=3)

@commands.has_permissions(administrator=True)
@bot.command(aliases=["ticket"])
async def ticket_command(ctx):
    embed = discord.Embed(title="Open a ticket!", description="Select a category below.", color=discord.Color.blue())
    await ctx.send(embed=embed, view=TicketDropdownView())

# ---------------- Run ----------------
if __name__ == "__main__":
    Thread(target=run_web).start()
    bot.run(TOKEN)
