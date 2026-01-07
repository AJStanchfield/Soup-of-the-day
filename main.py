import discord
from discord.ext import commands
import logging
from dotenv import load_dotenv
import os
import asyncio
import datetime
from zoneinfo import ZoneInfo
import random
import re

load_dotenv()
token = os.getenv('DISCORD_TOKEN')

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)
soups = [
    'Tomato Basil',
    'Chicken Noodle',
    'Minestrone',
    'Clam Chowder',
    'Butternut Squash',
    'French Onion',
    'Broccoli Cheddar',
    'Lentil',
    'Beef Barley',
    'Miso',
    'Split Pea',
    'Potato Leek',
    'Gazpacho',
    'Wonton',
    'Vegetable',
    'Tortilla',
    'Pumpkin',
    'Egg Drop',
    'Pho',
    'Ramen',
    'Gumbo',
    'Avgolemono',
    'Hot and Sour',
    'Chicken and Rice',
    'Cabbage Soup',
    'Cauliflower Soup',
    'Gabagool Soup',
    "Monty's Gay Queer Soup",
    ]


def GenerateSoupOfTheDay():
    today = datetime.date.today()
    index = today.toordinal() % len(soups)
    return soups[index]



@bot.event
async def on_ready():

    print(f'Logged in as {bot.user.name} - {bot.user.id}')
    # start background task to announce noon Eastern
    if not hasattr(bot, "_noon_task_started"):
        bot.loop.create_task(_noon_announcer())
        bot._noon_task_started = True



@bot.event
async def on_member_join(member):
    channel = discord.utils.get(member.guild.text_channels, name='anousements')
    if channel:
        await channel.send(f'Lets get soupin, {member.mention}!')

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return


    if message.content.lstrip().startswith(bot.command_prefix):
        await bot.process_commands(message)
        return


    if re.search(r"(?<!\!)\bsoup\b", message.content, re.IGNORECASE):
        await message.channel.send('Did someone say soup? 🍲')

    await bot.process_commands(message)
    


async def _noon_announcer():
    """Background task: sleep until the next 12:00 PM Eastern and send a message.

    It uses the system event loop and will run as long as the bot is connected.
    Configure the destination channel by setting the environment variable
    TARGET_CHANNEL_ID to a channel ID (integer). If not set, the task will
    look for a text channel named 'anousements' (existing typo) or
    'announcements' in the bot's guilds and send the message there.
    """
    tz = ZoneInfo("America/New_York")
    await bot.wait_until_ready()
    while not bot.is_closed():
        now = datetime.datetime.now(tz)
        target = now.replace(hour=12, minute=0, second=0, microsecond=0)
        if now >= target:
            target = target + datetime.timedelta(days=1)
        seconds = (target - now).total_seconds()
        # sleep until target
        try:
            await asyncio.sleep(seconds)
        except asyncio.CancelledError:
            return

        # determine channel (env override or named channel)
        channel = None
        cid_env = os.getenv("TARGET_CHANNEL_ID")
        if cid_env:
            try:
                cid = int(cid_env)
                channel = bot.get_channel(cid)
            except Exception:
                logging.exception("Invalid TARGET_CHANNEL_ID environment variable")

        if not channel:
            for guild in bot.guilds:
                channel = discord.utils.get(guild.text_channels, name='soup-of-the-day')
                if channel:
                    break
                channel = discord.utils.get(guild.text_channels, name='anousements')
                if channel:
                    break
                channel = discord.utils.get(guild.text_channels, name='announcements')
                if channel:
                    break

        if channel:
            try:
                await channel.send("ITS THAT TIME OF THE DAY AGAIN:")
                await channel.send(f"Soup of the day is: {GenerateSoupOfTheDay()} 🍲")
                logging.info(f"Sent noon message to {channel} ({channel.id})")
            except Exception:
                logging.exception("Failed to send noon message")
        else:
            logging.warning("No target channel found for noon message. Set TARGET_CHANNEL_ID or create a channel named 'soup-of-the-day', 'announcements' or 'anousements'.")


@bot.command(name='soup')
async def soup(ctx, mode: str = None):
    """Send the soup of the day.

    Usage:
      !soup          -> deterministic soup of the day (changes daily)
      !soup random   -> random soup from the list
    """


    if mode and mode.lower() == 'random':
        choice = random.choice(soups)
        await ctx.send(f"Today's (random) soup is: {choice} 🍲")
        return


    if mode and mode.lower() == 'funny':
        await ctx.send(f"Today's soup is Monty's Gay Queer Soup 🍲")
        return

    # deterministic daily selection via GenerateSoupOfTheDay()
    await ctx.send(f"Soup of the day: {GenerateSoupOfTheDay()} 🍲")


if __name__ == '__main__':
    # Start the bot after all commands and background tasks are defined
    bot.run(token, log_handler=handler, log_level=logging.DEBUG)