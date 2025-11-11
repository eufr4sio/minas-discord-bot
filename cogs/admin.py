import nextcord
from nextcord.ext import commands
from database import Database

class Admin(commands.Cog):
    def __init__(self, bot, db: Database):
        self.bot = bot
        self.db = db

    # This check ensures only users with Administrator permissions can use these commands
    @commands.has_permissions(administrator=True)
    @commands.group(name="admin", invoke_without_command=True)
    async def admin(self, ctx):
        """Bot administration commands"""
        await ctx.send("Admin commands: `listregistrations`, `removeuser`, `addgame`, `deletegame`, `setchannel`")

    @admin.command(name="listregistrations")
    async def list_registrations(self, ctx, *, game_name: str):
        """List all users registered for a specific game"""
        registered_users = await self.db.get_users_registered_for_game(game_name)
        
        if registered_users:
            user_mentions = [f"<@{user_id}>" for user_id in registered_users]
            embed = nextcord.Embed(
                title=f"🎮 Registrations for {game_name}",
                description="\n".join(user_mentions),
                color=nextcord.Color.blue()
            )
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"❌ No one is registered for **{game_name}**.")

    @admin.command(name="removeuser")
    async def remove_user(self, ctx, user: nextcord.Member, *, game_name: str):
        """Manually remove a user from a game's registration"""
        user_id = user.id
        success = await self.db.unregister_user_from_game(user_id, game_name)
        
        if success:
            await ctx.send(f"✅ Successfully removed {user.mention} from **{game_name}** notifications.")
        else:
            await ctx.send(f"❌ {user.mention} was not registered for **{game_name}**.")

    @admin.command(name="addgame")
    async def add_game(self, ctx, game_name: str, image_url: str = None):
        """Add a game to the database (optionally with an image URL)"""
        game_id = await self.db.add_game(game_name, image_url)
        
        if game_id:
            await ctx.send(f"✅ Successfully added **{game_name}** to the database.")
        else:
            await ctx.send(f"❌ **{game_name}** already exists in the database.")

    @admin.command(name="deletegame")
    async def delete_game(self, ctx, *, game_name: str):
        """Delete a game and all its registrations from the database"""
        # Confirmation step
        await ctx.send(f"⚠️ Are you sure you want to delete **{game_name}** and all its registrations? Type `confirm` to proceed.")

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel and m.content.lower() == 'confirm'

        try:
            await self.bot.wait_for("message", check=check, timeout=30.0)
            success = await self.db.delete_game_by_name(game_name)
            if success:
                await ctx.send(f"✅ Successfully deleted **{game_name}**.")
            else:
                await ctx.send(f"❌ Could not find **{game_name}** in the database.")
        except nextcord.ext.commands.utils.TimeoutError:
            await ctx.send("❌ Deletion cancelled.")

    @admin.command(name="setchannel")
    async def set_channel(self, ctx, channel: nextcord.TextChannel):
        """Set the channel for game notifications"""
        # You need to write the channel ID to the .env file or a config table
        # For simplicity, this example will just print it.
        # A more permanent solution would be to add a 'config' table to your DB.
        
        # This is a temporary solution. You will have to manually update your .env file.
        await ctx.send(f"⚙️ To set the alert channel, please update your `.env` file:\n`ALERT_CHANNEL_ID={channel.id}`")
        await ctx.send(f"The channel ID for **#{channel.name}** is `{channel.id}`.")

def setup(bot):
    bot.add_cog(Admin(bot))