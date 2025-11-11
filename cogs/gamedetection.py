import nextcord
from nextcord.ext import commands, tasks
import datetime
import os
import requests
from database import Database

class GameDetection(commands.Cog):
    def __init__(self, bot, db: Database):
        self.bot = bot
        self.db = db
        self.last_games = {}
        self.game_check.start()
    
    def cog_unload(self):
        self.game_check.cancel()
    
    def get_steam_game_image(self, game_name):
        try:
            url = f"https://store.steampowered.com/api/storesearch/?term={game_name}&l=english&cc=us"
            response = requests.get(url)
            data = response.json()
            if data.get('items'):
                item = data['items'][0]
                if item.get('header_image'): return item['header_image']
                elif item.get('large_image'): return item['large_image']
                elif item.get('small_image'): return item['small_image']
                elif item.get('tiny_image'): return item['tiny_image']
        except:
            pass
        return None
    
    @tasks.loop(seconds=30)
    async def game_check(self):
        try:
            if not self.bot.is_ready(): return
            guild = self.bot.guilds[0]
            for member in guild.members:
                if member.bot: continue
                
                user_id = member.id
                current_activity = member.activity
                
                if current_activity and current_activity.type == nextcord.ActivityType.playing:
                    game_name = current_activity.name
                    if user_id not in self.last_games or self.last_games[user_id] != game_name:
                        self.last_games[user_id] = game_name
                        await self.send_game_notification(member, game_name)
                else:
                    if user_id in self.last_games:
                        del self.last_games[user_id]
        except Exception as e:
            print(f"Error in game_check: {e}")
    
    async def send_game_notification(self, member, game_name):
        registered_users = await self.db.get_users_registered_for_game(game_name)
        if not registered_users: return
        
        alert_channel_id_str = os.getenv('ALERT_CHANNEL_ID')
        if not alert_channel_id_str:
            print("❌ ALERT_CHANNEL_ID not configured in .env")
            return
        
        alert_channel_id = int(alert_channel_id_str)
        channel = self.bot.get_channel(alert_channel_id)
        if not channel:
            print(f"❌ Could not find alert channel with ID {alert_channel_id}")
            return
        
        embed = nextcord.Embed(title=f"🎮 {game_name}", description=f"**{member.display_name}** is now playing!", color=0x3498db)
        game_image = self.get_steam_game_image(game_name)
        if game_image: embed.set_image(url=game_image)
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="👤 Player", value=member.display_name, inline=True)
        embed.add_field(name="📅 Started", value=datetime.datetime.now().strftime("%B %d, %Y at %H:%M"), inline=True)
        
        ping_list = [f"<@{user_id}>" for user_id in registered_users if user_id != member.id]
        if ping_list:
            embed.add_field(name="🔔 Notifying", value=f"{len(ping_list)} players", inline=True)
        
        await channel.send(content=" ".join(ping_list), embed=embed)
        print(f"🎮 Sent notification for {member.display_name} playing {game_name}")