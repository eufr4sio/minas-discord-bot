import os
import nextcord
from nextcord.ext import commands
import asyncio
from dotenv import load_dotenv
from database import Database

# Add this line after bot = commands.Bot(...)

bot = commands.Bot(command_prefix='!', intents=nextcord.Intents.default())
bot.load_extension("cogs.games")
bot.load_extension("cogs.gamedetection")
bot.load_extension("cogs.events")

@bot.event
async def on_ready():
    print(f'✅ {bot.user} has connected to Discord!')
    print(f'🎯 Running on server: {bot.guilds[0].name if bot.guilds else "No servers"}')
    
    await bot.change_presence(
        activity=nextcord.Activity(
            type=nextcord.ActivityType.watching,
            name="for gamers 🎮"
        )
    )

@bot.command(name='ping')
async def ping(ctx):
    """Check if the bot is responding"""
    latency = round(bot.latency * 1000)
    await ctx.send(f'🏓 Pong! Latency: {latency}ms')

@bot.command(name='info')
async def info(ctx):
    """Show information about the bot"""
    embed = nextcord.Embed(
        title="🎮 Game Notification Bot",
        description="A bot for game notifications and events!",
        color=nextcord.Color.blue()
    )
    embed.add_field(name="Prefix", value="`!`")
    embed.add_field(name="Version", value="1.0.0")
    embed.add_field(name="Features", value="✅ Game Registration\n✅ Game Detection\n✅ Event System", inline=True)
    embed.set_footer(text=f"Requested by {ctx.author.name}")
    await ctx.send(embed=embed)

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
if DISCORD_TOKEN:
    bot.run(DISCORD_TOKEN)
else:
    print("❌ Error: DISCORD_TOKEN not found in environment variables!")
    print("Please set your Discord token in the .env file.")