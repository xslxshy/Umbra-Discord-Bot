import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

@bot.command()
async def yo(ctx):
    author = ctx.author.name
    await ctx.send(f'yo {author}')

bot.run('MTM3MDk3MDg1MjUyMjMyODA3NA.GQ7Cuk.Nh2QVm7_sA_I4kDz0C74HLbqYw1yRVyHBmhsJY')