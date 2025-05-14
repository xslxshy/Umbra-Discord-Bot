import discord
from discord.ext import commands
from discord import Option
import json
import os
from datetime import datetime

DATA_FILE = "data/ego_data.json"

#Loads ego.json data
def load_data():
    if not os.path.exists(DATA_FILE):
        return {"egos": {}, "last_give": {}}
    with open (DATA_FILE, "r") as f:
        return json.load(f)
    
#Saves data on ego.json
def save_data(data):
    #Open the file in write mode and sava data as formatted JSON
    with open (DATA_FILE, "w") as f:
        json.dump(data, f, indent = 4)

#Main Cog class
class ChallengeCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.pending_challenges = {} #Storages the pending challenges

    #Creates /challenge cmd
    @commands.slash_command(name = "challenge", description = "Challenge someone for a game betting your EGO")
    async def challenge(self, ctx, opponent: discord.Member,
                         game = Option(str, "Choose the game of the challenge", choices = ["rock_paper_scissors"]),
                         bet = Option(int, "How much EGO you want to bet?")):
        
        challenger = ctx.author
        opponent = opponent

        print(f"{challenger.name} challenged {opponent.name}")

        #Checks if is challenging himself
        if challenger.id == opponent.id:
            await ctx.respond("You cant challenge yourself", ephemeral = True)
            return
        
        #Loads EGO data from ego.json
        data = load_data()
        challenger_ego = data["egos"].get(str(challenger.id), 0)
        opponent_ego = data["egos"].get(str(opponent.id), 0)

        #Checks if both have enough ego to bet
        if challenger_ego < bet or opponent_ego < bet:
            await ctx.respond("One of the players dont have enough **EGO** to this bet.")
            return
        
        #Storage pending challenge
        self.pending_challenges[opponent.id] = {
            "challenger": challenger,
            "game": game,
            "bet": bet
        }

        #Creates the view with "Accept" and "Decline" buttons
        view = ChallengeResponseView(self.bot, self.pending_challenges, opponent.id, ctx.guild)
        try:
            #Sends DM to opponent
            await opponent.send(
                f"{opponent.mention}, you have been challenged by {challenger.mention} for a game of **{game}** with **{bet} EGO** on the line.",
                view = view
            )
            await ctx.respond("Challenge sent successfully.", ephemeral = True)
        except discord.Forbidden:
            await ctx.respond("Couldn't DM the opponent. Check if they have DMs disabled.", ephemeral = True)

#Class that defines "Accept" and "Decline" buttons
class ChallengeResponseView(discord.ui.View):
    def __init__(self, bot, pending_challenges, opponent_id, guild):
        super().__init__(timeout = 60) #60 seconds of time limit to accept or decline
        self.bot = bot
        self.pending_challenges = pending_challenges
        self.opponent_id = opponent_id
        self.guild = guild

    #Accept challenge button
    @discord.ui.button(label = "Accept")
    async def accept(self, button, interaction):
        #Removes it from pending_challenges
        challenge = self.pending_challenges.pop(self.opponent_id, None)
        if not challenge:
            #If challenge doesnt exists for whatever reason
            await interaction.response.send_message("This challenge doesnt exist anymore", ephemeral = True)
            return
        
        #Create private channel for challenge
        guild = self.guild
        if guild is None:
            await interaction.response.send_message("Erro: Servidor não encontrado.", ephemeral = True)
            return

        challenger = challenge["challenger"]
        opponent = interaction.user

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel = False),
            challenger: discord.PermissionOverwrite(view_channel = True, send_messages = True),
            opponent: discord.PermissionOverwrite(view_channel = True, send_messages = True),
            guild.me: discord.PermissionOverwrite(view_channel = True, send_messages = True)
        }

        channel = await guild.create_text_channel(
            f"challenge-{challenger.name}-vs-{opponent.name}",
            overwrites = overwrites,
            reason = "Temporary Challenge Channel"
        )

        await interaction.response.send_message("Challange Accepted. Channel Created", ephemeral = True)
        await channel.send(
            f"{challenger.mention} vs {opponent.mention} - **{challenge['game']}** betting **{challenge['bet']} EGO**"
        )

    #Decline challenge button
    @discord.ui.button(label = "Decline")
    async def decline(self, button, interaction):
        self.pending_challenges.pop(self.opponent_id, None)
        await interaction.response.send_message("Challenge **declined.**", ephemeral = True)