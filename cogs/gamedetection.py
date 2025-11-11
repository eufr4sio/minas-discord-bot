import nextcord
from nextcord.ext import commands, tasks
import datetime
import os
import requests
from database import Database

class GameDetection(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()
        self.last_games = {}  # Track last known game for each user
        self.game_check.start()
    
    def cog_unload(self):
        self.game_check.cancel()
    
    def get_steam_game_image(self, game_name):
        """Get game image from Steam API with multiple size options"""
        try:
            # Search Steam store for the game
            url = f"https://store.steampowered.com/api/storesearch/?term={game_name}&l=english&cc=us"
            response = requests.get(url)
            data = response.json()
            
            if data.get('items'):
                # Try different image sizes in order of preference
                item = data['items'][0]
                
                # Try to get header image first (largest)
                if item.get('header_image'):
                    return item['header_image']
                # Try large image
                elif item.get('large_image'):
                    return item['large_image']
                # Try small image
                elif item.get('small_image'):
                    return item['small_image']
                # Try tiny image
                elif item.get('tiny_image'):
                    return item['tiny_image']
                    
        except:
            pass  # If anything fails, return None
        
        return None
    
    @tasks.loop(seconds=30)  # Check every 30 seconds
    async def game_check(self):
        """Check for game status changes"""
        try:
            guild = self.bot.guilds[0]  # Your server
            for member in guild.members:
                if member.bot:
                    continue  # Skip bots
                
                user_id = member.id
                current_activity = member.activity
                
                # Check if user is playing a game
                if current_activity and current_activity.type == nextcord.ActivityType.playing:
                    game_name = current_activity.name
                    
                    # Check if this is a new game (user just started playing)
                    if user_id not in self.last_games or self.last_games[user_id] != game_name:
                        self.last_games[user_id] = game_name
                        await self.send_game_notification(member, game_name)
                else:
                    # User is not playing anything
                    if user_id in self.last_games:
                        del self.last_games[user_id]
        
        except Exception as e:
            print(f"Error in game_check: {e}")
    
    async def send_game_notification(self, member, game_name):
        """Send notification when someone starts playing a game"""
        # Get all users registered for this game
        registered_users = self.db.get_users_registered_for_game(game_name)
        
        if not registered_users:
            return  # No one registered for this game
        
        # Find your alert channel (configure this in your .env)
        alert_channel_id = int(os.getenv('ALERT_CHANNEL_ID', 0))
        if alert_channel_id == 0:
            print("❌ ALERT_CHANNEL_ID not configured in .env")
            return
        
        channel = self.bot.get_channel(alert_channel_id)
        if not channel:
            print(f"❌ Could not find alert channel with ID {alert_channel_id}")
            return
        
        # Create clean, professional embed
        embed = nextcord.Embed(
            title=f"🎮 {game_name}",
            description=f"**{member.display_name}** is now playing!",
            color=0x3498db  # Professional blue
        )
        
        # Try to get Steam game image first (highest priority)
        game_image = self.get_steam_game_image(game_name)
        
        # Add game image if available (no user avatar fallback)
        if game_image:
            embed.set_image(url=game_image)
        
        # Add small circle avatar before username
        embed.set_thumbnail(url=member.display_avatar.url)
        
        # Add game info
        embed.add_field(
            name="👤 Player", 
            value=member.display_name,  # Just username, no mention
            inline=True
        )
        embed.add_field(
            name="📅 Started", 
            value=datetime.datetime.now().strftime("%B %d, %Y at %H:%M"),  # 24-hour format
            inline=True
        )
        
        # Ping registered users
        ping_list = [f"<@{user_id}>" for user_id in registered_users if user_id != member.id]
        if ping_list:
            embed.add_field(
                name="🔔 Notifying", 
                value=f"{len(ping_list)} players", 
                inline=True
            )
        
        # Send notification
        await channel.send(content=" ".join(ping_list), embed=embed)
        print(f"🎮 Sent notification for {member.display_name} playing {game_name}")

def setup(bot):
    bot.add_cog(GameDetection(bot))