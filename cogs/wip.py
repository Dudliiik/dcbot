import time
from discord.ext import commands

wip_cooldowns={}

class WIP(commands.Cog):
    def __init__(self, client):
        self.client = client

    
    @commands.command()
    async def wip(self, ctx):
        now = time.time()
        user_id = ctx.author.id
        last_used = wip_cooldowns.get(user_id, 0)
        cooldown_seconds = 7200

        if now - last_used < cooldown_seconds:
            remaining = cooldown_seconds - (now - last_used)
            
            h = int(remaining // 3600)
            m = int(remaining % 3600 // 60)
            s = int(remaining % 60)
            await ctx.send(f"You can ping WIP again in {h}h {m}m {s}s!")
            return
        
        if len(ctx.message.attachments) == 0:
            await ctx.send("You have to attach an image to ping WIP!")
            return
        
        attachment = ctx.message.attachments[0]
        if not attachment.filename.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".webp")):
            await ctx.send("You have to attach an image to ping WIP!")
            return
        
        wip_cooldowns[user_id] = now
        await ctx.send("<@&1282267309477728317>")

async def setup(client):
    await client.add_cog(WIP(client))