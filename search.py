import discord
from discord.ext import commands
import wikipedia
import urllib
import re
import requests
from bs4 import BeautifulSoup


# A class with commands related to randomness
class Search:
    """
    Commands related to randomness
    """
    def __init__(self, bot):
        self.bot = bot

    @commands.command(pass_context=True)
    async def wikipedia(self, ctx, *, query: str):
        summary = wikipedia.summary(query)
        page = wikipedia.page(query)
        embed = discord.Embed(title=page.title, url=page.url, color=0xFFA500, description=summary)
        await self.bot.send_message(ctx.message.channel, embed=embed)

    #@commands.command(pass_context=True)
    #async def image(self, ctx, *, query: str):
    #    """Returns the first image from the google search"""
    #    # Taken from https://stackoverflow.com/questions/32884439/how-to-get-all-videos-from-youtube-playlist-with-youtubeapi-for-java
    #   token = "AIzaSyCg3WitBUQl5ifC2QygQaZUPOSRMKfSD5E"
    #    webpage = "https://www.googleapis.com/customsearch/v1?cx=013629950505680552901%3Axac8ijijt08&searchType=image&key=" + token + "&q=" + query.replace(" ", "+")
    #    html_content = urllib.request.urlopen(webpage)
    #    str_html = html_content.read().decode("utf-8")
    #    match = re.findall(r'link": "?([^\'" >]+)', str_html)
    #    if match:
    #        await self.bot.send_message(ctx.message.channel, match[0])
    #    else:
    #        embed = discord.Embed(description="No image found.", color=0xFF0000)
    #        await self.bot.send_message(ctx.message.channel, embed=embed)

    @commands.command(aliases=["joke"], pass_context=True)
    async def dad(self, ctx):
        r = requests.get('https://icanhazdadjoke.com', headers={"Accept":"application/json"})
        contents = r.json()['joke']
        embed = discord.Embed(description=contents, color=0xFFA500)
        await self.bot.send_message(ctx.message.channel, embed=embed)

    @commands.command(pass_context=True)
    async def ub(self, ctx, query: str = "random"):
        """Returns the first Urban Dictionary result"""
        if query == "random":
            webpage = "https://www.urbandictionary.com/random.php"
        else:
            webpage = "http://www.urbandictionary.com/define.php?term=" + query.replace(" ", "+")
        r = requests.get(webpage).text
        soup = BeautifulSoup(r)
        title = soup.find_all("div", {"class": "def-header"})[0].find_all("a")[0].text
        meaning = soup.find_all("div", {"class": "meaning"})[0].text.replace("&apos;", "'")
        example = soup.find_all("div", {"class": "example"})[0].text
        embed = discord.Embed(title=title, url=webpage, color=0xFFA500, description=meaning)
        embed.add_field(name="Example", value=example, inline=True)
        await self.bot.send_message(ctx.message.channel, embed=embed)


def setup(bot):
    bot.add_cog(Search(bot))
