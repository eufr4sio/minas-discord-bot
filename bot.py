import os
import nextcord
from nextcord.ext import commands
import asyncio
from dotenv import load_dotenv
from database import Database

# Import all your cogs
from cogs.games import Games
from cogs.gamedetection import GameDetection
from cogs.admin import Admin
from cogs.controlpanel import ControlPanel
from cogs.userpanel import UserPanel

# Load environment variables from .env file
load_dotenv()

# --- Bot Setup ---
intents = nextcord.Intents.default()
intents.message_content = True
intents.presences = True
intents.members = True
bot = commands.Bot(command_prefix='!', intents=intents)

# --- Database Setup ---
db = Database()

@bot.event
async def on_ready():
    print(f'✅ {bot.user} has connected to Discord!')
    print(f'🎯 Running on server: {bot.guilds[0].name if bot.guilds else "No servers"}')
    
    # Initialize the database tables
    await db.init_db()
    await db.init_config_table()
    
    # Load all cogs and pass the database instance to them
    bot.add_cog(Games(bot, db))
    bot.add_cog(GameDetection(bot, db))
    bot.add_cog(Admin(bot, db))
    bot.add_cog(ControlPanel(bot, db))
    bot.add_cog(UserPanel(bot, db))
    
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
    embed.add_field(name="Features", value="✅ Game Registration\n✅ Game Detection\n✅ Admin Controls\n✅ Interactive Panel", inline=True)
    embed.set_footer(text=f"Requested by {ctx.author.name}")
    await ctx.send(embed=embed)

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
if DISCORD_TOKEN:
    bot.run(DISCORD_TOKEN)
else:
    print("❌ Error: DISCORD_TOKEN not found in environment variables!")
    print("Please set your Discord token in the .env file.")
    # In bot.py, add this helper function

def find_user(guild, user_identifier):
    """Finds a user in a guild by ID, mention, or name#discriminator."""
    # Try to get user by ID
    try:
        user_id = int(user_identifier.strip('<@!>'))
        return guild.get_member(user_id)
    except ValueError:
        pass # Not an ID, continue to other methods

    # Try to get user by mention
    if user_identifier.startswith('<@') and user_identifier.endswith('>'):
        user_id = int(user_identifier.strip('<@!>'))
        return guild.get_member(user_id)

    # Try to get user by name#discriminator or just name
    for member in guild.members:
        if str(member) == user_identifier or member.name == user_identifier:
            return member
            
    return None