import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Configuration class for the bot"""
    
    # Discord Configuration
    DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
    PREFIX = os.getenv('PREFIX', '!')
    GUILD_ID = int(os.getenv('GUILD_ID', 0))
    CONTROL_CHANNEL_ID = int(os.getenv('CONTROL_CHANNEL_ID', 0))
    ALERT_CHANNEL_ID = int(os.getenv('ALERT_CHANNEL_ID', 0))
    
    # Database Configuration
    DATABASE_PATH = 'bot.db'
    
    # Web UI Configuration
    WEB_HOST = '0.0.0.0'
    WEB_PORT = 5000
    
    # Game Detection Configuration
    GAME_CHECK_INTERVAL = 30  # seconds