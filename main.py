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

feedback_cooldowns = {}  
wip_cooldowns = {}       
help_cooldowns = {}      

# ---------------- Ticket Views ----------------
class CloseButtons(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.red)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Ticket closed", ephemeral=True)
        await interaction.channel.delete()   # FIX: pridane ()

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
            color=discord.Colour.dark_blue()
        )
        # keď klikne na Close → pošle embed s Confirm/Cancel
        await interaction.response.send_message(embed=embed, view=CloseButtons(), ephemeral=True)


class TicketCategory(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Partnership", description="Open this only if your server follows our guidelines", emoji="🎫"),
            discord.SelectOption(label="Role Request", description="Open this ticket to apply for an artist rankup", emoji="⭐"),
            discord.SelectOption(label="Support", description="Open this ticket if you have any general queries", emoji="📩")
        ]
        super().__init__(placeholder="Select a topic", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True) 

        category = self.values[0]
        user = interaction.user

        categories = {
            "Partnership": {
                "title": "Partnership Ticket",
                "description":"Thanks {user.name} for contacting the partnership team of **Thumbnailers**!\n"
                "Send your server's ad, and the ping you're expecting with any other additional details.\n"
                "Our team will respond to you shortly.",
                "ping": [1136118197725171813, 1102975816062730291]
            },
            "Role Request":{
                "title": "Role Request Ticket",
                "description": "Thank you for contacting support.\n"
                "Please refer to <#1102968475925876876> and make sure you send the amount"
                "of thumbnails required for the rank you're applying for, as and when you open the"
                "ticket. Make sure you link 5 minecraft based thumbnails at MINIMUM if you apply"
                "for one of the artist roles.",
                "ping": [1156543738861064192]
            },
            "Support": {
                "title":"Support Ticket",
                "description": "Thanks {user.name} for contacting the support team of **Thumbnailers**!\n"
                "Please explain your case so we can help you as quickly as possible!",
                "ping": [1102976554759368818, 1102975816062730291]
            }
        }

        ticket_channel = discord.utils.get(interaction.guild.channels, name=f"ticket-{user.name}")
        if ticket_channel:
            await interaction.followup.send(f"You already have a ticket - {ticket_channel.mention}", ephemeral=True)
            return

        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            interaction.guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)
        }

        channel = await interaction.guild.create_text_channel(
            name=f"ticket-{user.name}",
            overwrites=overwrites,
            reason=f"Ticket opened by {user} for {category}"
        )

        config = categories[category]

        embed = discord.Embed(
            title=config["title"],
            description=config["description"].format(user=user),
            color=discord.Color.blue()
        )

        view = CloseButton()
        ping_roles = " ".join(f"<@&{rid}>" for rid in config["ping"])
        await channel.send(content=f"{user.mention}, {ping_roles}", embed=embed, view=view)

        await interaction.followup.send(f"Ticket created - {channel.mention}", ephemeral=True)


class TicketDropdownView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketCategory())


# --------------------- Commands ---------------------


# ------------ Feedback ------------
@bot.command()
async def feedback(ctx):
    now = time.time()
    user_id = ctx.author.id
    last_used = feedback_cooldowns.get(user_id, 0)
    cooldown_seconds = 7200  

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
    await ctx.send("<@&1135502050575261758>")  

# ------------ WIP ------------

@bot.command()
async def wip(ctx):
    now = time.time()
    user_id = ctx.author.id
    last_used = wip_cooldowns.get(user_id, 0)
    cooldown_seconds = 7200  

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
    await ctx.send("<@&1282267309477728317>")  

# ------------ Help ------------

@bot.command()
async def help(ctx):
    now = time.time()
    user_id = ctx.author.id
    last_used = help_cooldowns.get(user_id, 0)
    cooldown_seconds = 7200  

    if now - last_used < cooldown_seconds:
        remaining = cooldown_seconds - (now - last_used)
        hours = int(remaining // 3600)
        minutes = int((remaining % 3600) // 60)
        seconds = int(remaining % 60)
        await ctx.send(f"You can use Help again in {hours}h {minutes}m {seconds}s!")
        return

    help_cooldowns[user_id] = now
    await ctx.send("<@&1135502182825852988>")  

# ------------ Purge command ------------

@commands.has_permissions(administrator=True)
@bot.command(aliases=["purge"])
async def delete(ctx, amount: int):
    await ctx.channel.purge(limit=amount+1)
    await ctx.send(f"Purged {amount} messages", delete_after=3)

# ------------ Ticket setup command ------------

@bot.command(name="ticket")
async def ticket_command(ctx):
    embed = discord.Embed(
        title="Open a ticket!",
        description=(
            "Welcome! You can create a ticket for any of the categories listed below. "
            "Please ensure you select the appropriate category for your issue. "
            "If your concern doesn't align with any of the options provided, feel free to create a general support ticket. Thank you!\n\n"
            "**Warn system for wrong tickets.**\n"
            "A straight warning will be issued for opening incorrect tickets for incorrect reasons. "
            "It is quite clear what ticket you need to open for what problem."
        ),
        color=discord.Color.blue()
    )
    await ctx.send(embed=embed, view=TicketDropdownView())

# ---------------- Run bot + web ----------------
if __name__ == "__main__":
    Thread(target=run_web).start()
    bot.run(TOKEN)