import os
import nextcord
from nextcord.ext import commands
from dotenv import load_dotenv

load_dotenv()

intents = nextcord.Intents.default()
intents.presences = True
intents.members = True
intents.guilds = True
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'✅ {bot.user} has connected to Discord!')
    print(f'🎯 Running on server: {bot.guilds[0].name if bot.guilds else "No servers"}')
    
    # Set bot status
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
    embed.set_footer(text=f"Requested by {ctx.author.name}")
    await ctx.send(embed=embed)

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
if DISCORD_TOKEN:
    bot.run(DISCORD_TOKEN)
else:
    print("❌ Error: DISCORD_TOKEN not found in environment variables!")
    print("Please set your Discord token in the .env file.")