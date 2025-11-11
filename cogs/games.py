import nextcord
from nextcord.ext import commands
from database import Database

class Games(commands.Cog):
    def __init__(self, bot, db: Database):
        self.bot = bot
        self.db = db
    
    @commands.group(name="game", invoke_without_command=True)
    async def game(self, ctx):
        """Game registration commands"""
        await ctx.send("Use `!game register <game>` to register for a game or `!game list` to see registered games.")
    
    @game.command(name="register")
    async def register(self, ctx, *, game_name: str):
        """Register for notifications when someone plays a game"""
        user_id = ctx.author.id
        success = await self.db.register_user_for_game(user_id, game_name)
        
        if success:
            embed = nextcord.Embed(title="✅ Game Registration Successful", description=f"You've been registered for notifications when someone plays **{game_name}**!", color=nextcord.Color.green())
            embed.set_footer(text=f"Requested by {ctx.author.name}")
            await ctx.send(embed=embed)
        else:
            embed = nextcord.Embed(title="❌ Already Registered", description=f"You're already registered for **{game_name}** notifications.", color=nextcord.Color.red())
            embed.set_footer(text=f"Requested by {ctx.author.name}")
            await ctx.send(embed=embed)
    
    @game.command(name="unregister")
    async def unregister(self, ctx, *, game_name: str):
        """Unregister from game notifications"""
        user_id = ctx.author.id
        success = await self.db.unregister_user_from_game(user_id, game_name)
        
        if success:
            embed = nextcord.Embed(title="✅ Game Unregistration Successful", description=f"You've been unregistered from **{game_name}** notifications.", color=nextcord.Color.green())
            embed.set_footer(text=f"Requested by {ctx.author.name}")
            await ctx.send(embed=embed)
        else:
            embed = nextcord.Embed(title="❌ Not Registered", description=f"You weren't registered for **{game_name}** notifications.", color=nextcord.Color.red())
            embed.set_footer(text=f"Requested by {ctx.author.name}")
            await ctx.send(embed=embed)
    
    @game.command(name="list")
    async def list(self, ctx):
        """List all games you're registered for"""
        user_id = ctx.author.id
        games = await self.db.get_user_registered_games(user_id)
        
        if games:
            embed = nextcord.Embed(title="🎮 Your Registered Games", description="You'll receive notifications when someone starts playing these games:", color=nextcord.Color.blue())
            for game in games:
                embed.add_field(name=game, value="✅ Registered", inline=True)
            embed.set_footer(text=f"Requested by {ctx.author.name}")
            await ctx.send(embed=embed)
        else:
            embed = nextcord.Embed(title="🎮 No Registered Games", description="You haven't registered for any game notifications yet. Use `!game register <game>` to get started!", color=nextcord.Color.orange())
            embed.set_footer(text=f"Requested by {ctx.author.name}")
            await ctx.send(embed=embed)