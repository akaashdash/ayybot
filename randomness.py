import discord
import random
from discord.ext import commands


# A class with commands related to randomness
class Randomness:
    """
    Commands related to randomness
    """
    def __init__(self, bot):
        self.bot = bot

    @commands.command(pass_context=True)
    async def rand(self, ctx, limit: int):
        result = random.randint(1, limit)
        embed = discord.Embed(description=":small_orange_diamond:Randomly selected **{0}** from 1 to {1}.".format(result, limit), color=0xFFA500)
        await self.bot.send_message(ctx.message.channel, embed=embed)

    @commands.command(pass_context=True)
    async def roll(self, ctx):
        result = random.randint(1, 6)
        embed = discord.Embed(description=":small_orange_diamond:Rolled a die and got **{0}**.".format(result), color=0xFFA500)
        await self.bot.send_message(ctx.message.channel, embed=embed)

    @commands.command(pass_context=True)
    async def choose(self, ctx, *choices: str):
        """Chooses between multiple choices."""
        embed = discord.Embed(description=":small_orange_diamond:Chose **{0}**.".format(random.choice(choices)), color=0xFFA500)
        await self.bot.send_message(ctx.message.channel, embed=embed)

    @commands.command(pass_context=True)
    async def r6attacker(self, ctx):
        """Chooses between multiple choices."""
        choices = ["Lion", "Finka", "Dokkaebi", "Zofia", "Ying", "Jackal", "Hibana", "Capitao", "Blackbeard", "Buck",
                   "Sledge", "Thatcher", "Ash", "Thermite", "Montagne", "Twitch", "Blitz", "Iq", "Fuze", "Glaz"]
        embed = discord.Embed(description=":small_orange_diamond:**{0}** is your attacker.".format(random.choice(choices)), color=0xFFA500)
        await self.bot.send_message(ctx.message.channel, embed=embed)

    @commands.command(pass_context=True)
    async def r6defender(self, ctx):
        """Chooses between multiple choices."""
        choices = ["Vigil", "Ela", "Lesion", "Mira", "Echo", "Caveira", "Valkyrie", "Frost", "Mute", "Smoke",
                   "Castle", "Pulse", "Doc", "Rook", "Jager", "Bandit", "Tachanka", "Kapkan"]
        embed = discord.Embed(description=":small_orange_diamond:**{0}** is your defender.".format(random.choice(choices)), color=0xFFA500)
        await self.bot.send_message(ctx.message.channel, embed=embed)


# Sets up the extension and adds the cog
def setup(bot):
    bot.add_cog(Randomness(bot))