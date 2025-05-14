import discord
from discord.ext import commands
from PIL import Image
import io
from discord import Option
from cogs.ego import EgoCog
from cogs.challenge import ChallengeCog
from config import TOKEN

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="/", intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    await bot.sync_commands()

bot.add_cog(EgoCog(bot)) #Loading EgoCog

bot.add_cog(ChallengeCog(bot)) #Loading ChallengeCog

@bot.slash_command(name="yo", description = "hi for whoever is using this command")
async def yo(ctx, arg: str = None):
    author = ctx.author.name
    if arg:
        await ctx.respond(f'yo {arg}')
    else:
        await ctx.respond(f'yo {author}')

@bot.slash_command(name = "convertimg", description= "Convert an image type to another")
async def convertImg(ctx, file: discord.Attachment, format = Option(str, "Choose output format", choices = ["png", "jpeg", "webp"])):
     img_bytes = await file.read()
     image = Image.open(io.BytesIO(img_bytes))
     converted = io.BytesIO()
     if format == "jpeg":
         if image.mode == "RGBA":
             background = Image.new("RGB", image.size, (255, 255, 255))
             background.paste(image, mask=image.split()[3])
             image = background
         else:
             image = image.convert("RGB")
     fmt = format.upper()
     image.save(converted, format=fmt)
     converted.seek(0)
     await ctx.respond(file = discord.File(converted, filename=f"converted.{format.lower()}"))
        
bot.run(TOKEN) #Bot Start