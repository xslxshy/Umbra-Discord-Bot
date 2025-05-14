import discord
from discord.ext import commands
import json
import os
from datetime import datetime, timedelta
from discord import Option

DATA_FILE = "data/ego_data.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        return {"egos": {}, "last_give": {}}
    with open (DATA_FILE, "r") as f:
        return json.load(f)
    
def save_data(data):
    #Open the file in write mode and sava data as formatted JSON
    with open (DATA_FILE, "w") as f:
        json.dump(data, f, indent = 4)

#Cog class that will be added to the bot
class EgoCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name = "ego", description = "Give 1 ego to someone")
    async def ego(self, ctx, user: discord.Member):
        if user.id == ctx.author.id:
            await ctx.respond("You cant give ego to yourself", ephemeral = True)
            return
        
        #Load data from file
        data = load_data()
        author_id = str(ctx.author.id) #Convert ID's to strings for JSON keys
        target_id = str(user.id)

        now = datetime.now()
        last_used = data["last_give"].get(author_id)

        #Cooldown Handler
        if last_used:
            last_time = datetime.fromisoformat(last_used)
            cooldown = timedelta(days = 1)
            remaining = (last_time + cooldown) - now

            if remaining.total_seconds() > 0:
                hours, remaining = divmod(int(remaining.total_seconds()), 3600)
                minutes, seconds = divmod(remaining, 60)
                time_left = f"{hours}h {minutes}m {seconds}s"
                await ctx.respond(f"You already gave **ego** today. Try again in **{time_left}**.", ephemeral = True)
                return
            
        #Increment ego count for target user
        data["egos"][target_id] = data["egos"].get(target_id, 0) + 1

        #Update last_give time for the author
        data["last_give"][author_id] = now.isoformat()
        save_data(data)

        #Role Handler
        ego_amount = data["egos"][target_id]
        guild = ctx.guild
        member = user

        for role in member.roles:
            if role.name.startswith("EGO:"):
                await member.remove_roles(role)

        new_role_name = f"EGO: {ego_amount} "
        role = discord.utils.get(guild.roles, name = new_role_name)
        if role is None:
            role = await guild.create_role(
                name = new_role_name,
                colour = discord.Colour.from_rgb(1,1,1)
                )

        await member.add_roles(role)

        await ctx.respond(f"You gave **+1** ego to {user.mention}")

    @commands.slash_command(name="egocheck", description = "Check how much ego someone has")
    async def egocheck(self, ctx, user: discord.Member = None):
        data = load_data()
        target = user or ctx.author
        target_id = str(target.id)
        ego = data["egos"].get(target_id, 0)
        await ctx.respond(f"{target.mention} has **{ego} ego**")