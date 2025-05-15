import discord
from discord.ui import View, Button
import asyncio
from cogs.ego import load_data, save_data
from .base_game import BaseGame

class RockPaperScissors(BaseGame):
    async def start(self, bot, channel, challenger, opponent, bet):
        #Creates RPSGame instance with respective players and bet
        game = RPSGame(bot, channel, challenger, opponent, bet)
        await game.run()

        #Waits 15 seconds before deleting the channel
        await asyncio.sleep(15)
        await channel.delete()

class RPSGame:
    def __init__(self, bot, channel, player1, player2, bet):
        self.bot = bot
        self.channel = channel
        self.players = {player1.id: {"member": player1, "wins": 0},
                       player2.id: {"member": player2, "wins": 0}}
        self.choices = {}       #Storages each player choices
        self.bet = bet
        self.round = 1

    async def run(self):
        #Game Loop: continues while no player has 2 victories
        while all(p["wins"] < 2 for p in self.players.values()):
            await self.channel.send(f"**Round {self.round}**")

            #Resets player choices for new round
            self.choices = {}

            #Asks players to make their choices (await for button interactions)
            await self.get_choices()

            #Get Players ID's
            p1_id, p2_id = list(self.players.keys())
            #Get Players choices
            c1 = self.choices.get(p1_id)
            c2 = self.choices.get(p2_id)
            #Get Players objects to mention in the chat
            p1 = self.players[p1_id]["member"]
            p2 = self.players[p2_id]["member"]

            emoji_map = {
                "rock": "🪨",
                "paper": "📄",
                "scissors": "✂️"
            }

            if c1 is None and c2 is None:
                await self.channel.send("Both players did not choose in time. Round Repeating")
                await asyncio.sleep(2)
                continue

            if c1 is None:
                self.players[p2_id]["wins"] += 1
                await self.channel.send(f"{p1.mention} did not choose in time.\n⛓️ {p2.mention} **WON Round {self.round}!** ⛓️")
                self.round += 1
                await asyncio.sleep(2)
                continue

            if c2 is None:
                self.players[p1_id]["wins"] += 1
                await self.channel.send(f"{p2.mention} did not choose in time.\n⛓️ {p1.mention} **WON Round {self.round}!** ⛓️")  
                self.round += 1
                await asyncio.sleep(2)
                continue
                
            #Determines who won this round (returns winner id, "draw" or None)
            result = self.determine_winner()

            choice1_text = f"🕷️ {p1.mention} chose  **{c1.capitalize()}** {emoji_map.get(c1, '')}" if c1 else "**Nothing. ⁉️"
            choice2_text = f"🩸 {p2.mention} chose  **{c2.capitalize()}** {emoji_map.get(c2, '')}" if c2 else "**Nothing. ⁉️"

            await self.channel.send(
                f"🕷️ {p1.mention} chose {choice1_text}\n"
                f"🩸 {p2.mention} chose {choice2_text}"
            )
            
            if result == "draw":
                await self.channel.send("**Draw.** Round repeating.")
                await asyncio.sleep(2)
                continue
            
            #Gets the winner and +1 wins
            winner = self.players[result]["member"]
            self.players[result]["wins"] += 1
            await self.channel.send(f"⛓️ {winner.mention} **WON Round {self.round}!** ⛓️")

            #Delay so the message can be read
            await asyncio.sleep(2)

            #Goes for the next round and reset player choices
            self.round += 1
            self.choices = {}

        #When someone reaches 2 wins, the game ends
        #Sorts the players based on wins, higher to lower
        sorted_players = sorted(self.players.items(), key = lambda x: x[1]["wins"], reverse = True)
        winner_id = sorted_players[0][0]
        loser_id = sorted_players[1][0]
        winner = self.players[winner_id]["member"]
        loser = self.players[loser_id]["member"]

        data = load_data() 
        #Increments winners EGO for the betted amount
        data["egos"][str(winner.id)] = data["egos"].get(str(winner.id), 0) + self.bet
        #Decreases losers EGO for the betted amount
        data["egos"][str(loser.id)] = data["egos"].get(str(loser.id), 0) - self.bet
        save_data(data)

        await self.channel.send(f"🏆 {winner.mention} won the match and got **{self.bet} EGO** 🏆")

    async def get_choices(self):
        #Creates button interface for players to chose
        view = RPSView(self.players.keys(), self.choices)
        await self.channel.send("Choose your action:", view = view)
        try:
            #Waits for both players to chose their action
            await asyncio.wait_for(view.wait(), timeout = 30)
        except asyncio.TimeoutError:
            pass

    def determine_winner(self):
        p1_id, p2_id = list(self.players.keys())
        c1 = self.choices.get(p1_id)
        c2 = self.choices.get(p2_id)

        valid_choices = {"rock", "paper", "scissors"}
        if c1 not in valid_choices or c2 not in valid_choices:
            return None

        if c1 == c2:
            return "draw"
        
        beats = {"rock": "scissors", "scissors": "paper", "paper": "rock"}
        return p1_id if beats[c1] == c2 else p2_id
    
class RPSView(View):
    def __init__(self, player_ids, choices):
        super().__init__(timeout = 30)
        self.player_ids = player_ids
        self.choices = choices
        self.responded = set()

    @discord.ui.button(label = "Rock 🪨", style = discord.ButtonStyle.secondary)
    async def rock(self, button, interaction):
        await self.register_choice(interaction, "rock")

    @discord.ui.button(label = "Paper 📄", style = discord.ButtonStyle.primary)
    async def paper(self, button, interaction):
        await self.register_choice(interaction, "paper")

    @discord.ui.button(label = "Scissors ✂️", style = discord.ButtonStyle.danger)
    async def scissors(self, button, interaction):
        await self.register_choice(interaction, "scissors")

    async def register_choice(self, interaction, choice):
        if interaction.user.id in self.choices:
            await interaction.response.send_message("You already made your choice.", ephemeral = True)
            return
        
        self.choices[interaction.user.id] = choice
        await interaction.response.send_message(f"You chose **{choice}**.", ephemeral = True)

        if len(self.choices) == 2:
            self.disable_all_items()
            await interaction.message.edit(view = self)
            self.stop()