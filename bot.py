import discord
from discord.ext import commands
import asyncio
import sys
import os

# Get the token from the file 'token.txt'
token = open("token.txt").read()

# Create the instance of the command bot
description = 'A bot made by Akaash Dash.'
bot = commands.Bot(command_prefix='!', description=description)
extensions = ["music", "randomness", "search"]


# Declare when the bot has started
@bot.event
async def on_ready():
    print('ayybot started')


# Default command check for any command
# Checks to ensure executor is not the bot and the command was executed in the right channel
@bot.check
def command_check(context):
    # Checks if the command executor is the bot itself
    if context.message.author == bot.user:
        return False

    # Checks if the command wasn't executed in the 'bot' channel
    if context.message.channel.name != 'bot':
        return False

    return True


# Runs whenever a command is executed
# Similar to command check, but completes an action if the checks aren't passed
@bot.event
@asyncio.coroutine
async def on_command(command, context):
    message = context.message
    # Does nothing if executor is the bot itself
    if message.author == bot.user:
        return

    # Alerts the user that they must only execute bot commands in the 'bot' channel if it was not already
    if message.channel.name != 'bot':
        await bot.delete_message(message)
        channel = next(
            (channel for channel in message.server.channels if channel.name == 'bot'), None)
        say = "You may only use bot commands in this channel, **{0.mention}**."
        await bot.send_message(channel, say.format(message.author))
        return

    return

# Runs when the bot starts
if __name__ == "__main__":
    # Changes the presence of the bot to the name of the group
    bot.change_presence(game=discord.Game(name="Ayy Gang"))
    # Loads the list of extensions
    for extension in extensions:
        bot.load_extension(extension)

# Start the bot
bot.run(token)

# Restarts the bot on a crash/close
python = sys.executable
os.execl(python, python, * sys.argv)
