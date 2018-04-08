import asyncio
import discord
import requests
import os
import sys
from datetime import datetime
from bs4 import BeautifulSoup
from discord.ext import commands

# Loads the 'libopus' library, required for discord voice to work
if not discord.opus.is_loaded():
    discord.opus.load_opus('opus')


# A data class for items in the queue
class QueueEntry:
    def __init__(self, message, player):
        self.requester = message.author
        self.channel = message.channel
        self.player = player


# A class used to store information about the VoiceState of the bot in a server/guild
class VoiceState:
    def __init__(self, bot):
        self.volume = 0.2
        self.current = None
        self.voice = None
        self.bot = bot
        self.play_next_song = asyncio.Event()
        self.songs = asyncio.Queue()
        self.skip_votes = set()
        self.audio_player = self.bot.loop.create_task(self.audio_player_task())

    # Returns whether the bot is currently playing or not
    def is_playing(self):
        if self.voice is None or self.current is None:
            return False

        return not self.current.player.is_done()

    # Shortcut to access player
    @property
    def player(self):
        return self.current.player

    # Skips the currently playing song and clears the votes
    def skip(self):
        self.skip_votes.clear()
        if self.is_playing():
            self.player.stop()

    # Toggles to the next song in the queue
    def toggle_next(self):
        self.bot.loop.call_soon_threadsafe(self.play_next_song.set)

    # Looped task to play audio
    async def audio_player_task(self):
        # Inifnite loop
        while True:
            # Stops the ongoing event
            self.play_next_song.clear()
            # Gets the next song from the queue
            self.current = await self.songs.get()
            # Reconnects to the source - fixes connectivity issues
            opts = {
                'default_search': 'auto',
                'quiet': True,
            }
            before_args = "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"
            self.current.player = await self.voice.create_ytdl_player(self.current.player.url, ytdl_options=opts, before_options=before_args, after=self.toggle_next)
            # Adjusts the volume
            self.current.player.volume = self.volume
            # Starts streaming
            self.current.player.start()
            playing = self.current.player
            requester = self.current.requester
            embed = discord.Embed(title="Now Playing", url=playing.url, timestamp=datetime.now(), color=0xFFA500)
            embed.add_field(name="Title", value=playing.title, inline=True)
            embed.add_field(name="By", value=playing.uploader, inline=True)
            embed.add_field(name="Length", value="{0[0]}m {0[1]}s".format(divmod(playing.duration, 60)), inline=True)
            embed.set_footer(text="Queued by @{0.name}".format(requester), icon_url=requester.avatar_url)
            await self.bot.send_message(self.current.channel, embed=embed)
            await self.play_next_song.wait()


class Music:
    """
    Commands to control the music bot.
    """

    def __init__(self, bot):
        self.bot = bot
        self.voice_states = {}

    def get_voice_state(self, server):
        state = self.voice_states.get(server.id)
        if state is None:
            state = VoiceState(self.bot)
            self.voice_states[server.id] = state

        return state

    async def create_voice_client(self, channel):
        voice = await self.bot.join_voice_channel(channel)
        state = self.get_voice_state(channel.server)
        state.voice = voice

    def __unload(self):
        for state in self.voice_states.values():
            try:
                state.audio_player.cancel()
                if state.voice:
                    self.bot.loop.create_task(state.voice.disconnect())
            except:
                pass

    @commands.command(pass_context=True, no_pm=True)
    async def join(self, ctx, *, channel: discord.Channel):
        """
        Joins a voice channel.
        """
        try:
            await self.create_voice_client(channel)
        except discord.ClientException:
            embed = discord.Embed(description="Music is already playing in a voice channel.", color=0xFF0000)
            await self.bot.send_message(ctx.message.channel, embed=embed)
        except discord.InvalidArgument:
            embed = discord.Embed(description="Invalid channel specified.", color=0xFF0000)
            await self.bot.send_message(ctx.message.channel, embed=embed)
        else:
            embed = discord.Embed(description="Now playing music in **{0.name}**.".format(channel), color=0xFFA500)
            await self.bot.send_message(ctx.message.channel, embed=embed)

    @commands.command(pass_context=True, no_pm=True)
    async def summon(self, ctx):
        """Summons the bot to join your voice channel."""
        summoned_channel = ctx.message.author.voice_channel
        if summoned_channel is None:
            embed = discord.Embed(description="You are not in a voice channel.", color=0xFF0000)
            await self.bot.send_message(ctx.message.channel, embed=embed)
            return False

        state = self.get_voice_state(ctx.message.server)
        if state.voice is None:
            state.voice = await self.bot.join_voice_channel(summoned_channel)
        else:
            await state.voice.move_to(summoned_channel)

        return True

    @commands.command(pass_context=True, no_pm=True)
    async def play(self, ctx, *, song: str):
        """Plays a song."""
        name = str(ctx.message.author)
        server = ctx.message.author.server
        message = ctx.message

        def youtube(query: str, num: int = 0):
            isNotAVideo = True
            url = 'https://youtube.com/results?search_query=' + query.replace(" ", "+")
            r = requests.get(url).text
            soup = BeautifulSoup(r, "html.parser")
            yt = soup.find_all("div", {"class": "yt-lockup-content"})
            num = 0
            while isNotAVideo:
                try:
                    if (not 'list' in yt[num].a.get('href') and 'watch' in yt[num].a.get('href') and len(
                            yt[num].get('class')) < 2):
                        isNotAVideo = False
                    else:
                        num = num + 1
                except AttributeError:
                    num = num + 1

            link = yt[num].a.get('href')
            page = 'https://youtube.com' + link
            return page

        def restart_program():
            python = sys.executable
            os.execl(python, python, *sys.argv)

        state = self.get_voice_state(ctx.message.server)
        opts = {
            'default_search': 'auto',
            'quiet': True,
        }
        link = song.split(':')
        if link[0] == 'https':
            ytsearch = song
        elif link[0] == 'http':
            ytsearch = song
        else:
            ytsearch = youtube(song)

        if state.voice is None:
            success = await ctx.invoke(self.summon)
            if not success:
                return

        try:
            player = await state.voice.create_ytdl_player(ytsearch, ytdl_options=opts, after=state.toggle_next)
        except Exception as e:
            fmt = 'An error occurred while processing this request: ```py\n{}: {}\n```'
            await self.bot.send_message(ctx.message.channel, fmt.format(type(e).__name__, e))
            # IF BREAK RESTART
            #restart_program()
        else:
            entry = QueueEntry(ctx.message, player)
            playing = entry.player
            requester = entry.requester
            embed = discord.Embed(title="Added To Queue", url=playing.url, timestamp=datetime.now(), color=0xFFA500)
            embed.add_field(name="Title", value=playing.title, inline=True)
            embed.add_field(name="By", value=playing.uploader, inline=True)
            embed.add_field(name="Length", value="{0[0]}m {0[1]}s".format(divmod(playing.duration, 60)), inline=True)
            embed.set_footer(text="Added by @{0.name}!".format(requester), icon_url=requester.avatar_url)
            await self.bot.send_message(entry.channel, embed=embed)
            await state.songs.put(entry)

    @commands.command(aliases=["vol"], pass_context=True, no_pm=True)
    async def volume(self, ctx, value: int):
        """Sets the volume of the currently playing song."""

        if ctx.message.author:
            state = self.get_voice_state(ctx.message.server)
            if value > 200:
                value = 200
            volume = value / 100
            state.volume = volume
            if state.is_playing():
                state.player.volume = volume
            embed = discord.Embed(description="Set the volume to **{:.0%}**.".format(volume), color=0xFFA500)
            await self.bot.send_message(ctx.message.channel, embed=embed)
        else:
            embed = discord.Embed(description="There was an error while attempting to change the volume.", color=0xFF0000)
            await self.bot.send_message(ctx.message.channel, embed=embed)

    @commands.command(pass_context=True, no_pm=True)
    async def pause(self, ctx):
        """Pauses the currently played song."""
        state = self.get_voice_state(ctx.message.server)
        if state.is_playing():
            player = state.player
            player.pause()
            embed = discord.Embed(description="Music has been **paused**.", color=0xFFA500)
            await self.bot.send_message(ctx.message.channel, embed=embed)

    @commands.command(aliases=["unpause"], pass_context=True, no_pm=True)
    async def resume(self, ctx):
        """Resumes the currently played song."""
        state = self.get_voice_state(ctx.message.server)
        if state.is_playing():
            player = state.player
            player.resume()
            embed = discord.Embed(description="Music has been **resumed**.", color=0xFFA500)
            await self.bot.send_message(ctx.message.channel, embed=embed)

    @commands.command(pass_context=True, no_pm=True)
    async def stop(self, ctx):
        """Stops playing audio and leaves the voice channel.
        This also clears the queue.
        """
        server = ctx.message.server
        state = self.get_voice_state(server)
        summoned_channel = ctx.message.author.voice_channel

        if state.is_playing():
            player = state.player
            player.stop()
        try:
            state.audio_player.cancel()
            del self.voice_states[server.id]
            await state.voice.disconnect()
            if summoned_channel is None:
                return False
            else:
                if state.voice is None:
                    success = await ctx.invoke(self.summon)
                if not success:
                    return
        except:
            pass

    @commands.command(pass_context=True, no_pm=True)
    async def leave(self, ctx):
        """Bot Leaves Voice Channel"""
        server = ctx.message.server
        state = self.get_voice_state(server)
        if state.is_playing():
            player = state.player
            player.stop()
        try:
            state.audio_player.cancel()
            del self.voice_states[server.id]
            await state.voice.disconnect()
        except:
            pass

    @commands.command(pass_context=True, no_pm=True)
    async def skip(self, ctx):
        """
        Skips Song
        """
        state = self.get_voice_state(ctx.message.server)
        if not state.is_playing():
            embed = discord.Embed(description="No music is currently playing.", color=0xFF0000)
            await self.bot.send_message(ctx.message.channel, embed=embed)
            return

        voter = ctx.message.author
        if voter == state.current.requester:
            embed = discord.Embed(description="The person who queued the song skipped the song.", color=0xFFA500)
            await self.bot.send_message(ctx.message.channel, embed=embed)
            state.skip()
        elif ctx.message.channel.permissions_for(voter).administrator:
            embed = discord.Embed(description="An admin has skipped the song.", color=0xFFA500)
            await self.bot.send_message(ctx.message.channel, embed=embed)
            state.skip()
        elif voter not in state.skip_votes:
            state.skip_votes.add(voter)
            for member in state.skip_votes:
                if member not in state.voice.channel.voice_members:
                    state.skip_votes.discard(member)
            count = len(state.skip_votes)
            total = len(state.voice.channel.voice_members)
            if total % 2 == 1:
                total = total + 1
            required = int(total / 2)
            if count >= required:
                embed = discord.Embed(description="Majority has voted to skip the song.", color=0xFFA500)
                await self.bot.send_message(ctx.message.channel, embed=embed)
                state.skip()
            else:
                embed = discord.Embed(description="Voted to skip, current votes: **{0}/{1}**.".format(count, required), color=0xFFA500)
                await self.bot.send_message(ctx.message.channel, embed=embed)
        else:
            embed = discord.Embed(description="You have already voted to skip the song.", color=0xFF0000)
            await self.bot.send_message(ctx.message.channel, embed=embed)

    @commands.command(pass_context=True, no_pm=True)
    async def playing(self, ctx):
        """Shows info about the currently played song."""

        state = self.get_voice_state(ctx.message.server)
        if state.current is None:
            embed = discord.Embed(description="No music is currently playing.", color=0xFF0000)
            await self.bot.send_message(ctx.message.channel, embed=embed)
        else:
            skip_count = len(state.skip_votes)
            playing = state.player
            requester = state.current.requester
            embed = discord.Embed(title="Now Playing", url=playing.url, timestamp=datetime.now(), color=0xFFA500)
            embed.add_field(name="Title", value=playing.title, inline=True)
            embed.add_field(name="By", value=playing.uploader, inline=True)
            embed.add_field(name="Length", value="{0[0]}m {0[1]}s".format(divmod(playing.duration, 60)), inline=True)
            embed.set_footer(text="Queued by @{0.name}".format(requester), icon_url=requester.avatar_url)
            await self.bot.send_message(state.current.channel, embed=embed)


# Sets up the extension and adds the cog
def setup(bot):
    bot.add_cog(Music(bot))