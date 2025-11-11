import nextcord
from nextcord.ext import commands
import os
import asyncio
from database import Database

class InteractivePanel(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()
        self.control_channel_id = int(os.getenv('CONTROL_CHANNEL_ID', 0))
        self.panel_message_id = None  # Will store the panel message ID
    
    @commands.group(name="panel", invoke_without_command=True)
    async def panel(self, ctx):
        """Interactive panel commands"""
        await ctx.send("🎮 Interactive Panel - Use `!panel spawn` to create a control panel in Discord")
    
    @panel.command(name="spawn")
    async def spawn_panel(self, ctx):
        """Spawn an interactive control panel in Discord"""
        # Check if user has admin permissions
        if not any(role.name == "Admin" for role in ctx.author.roles):
            await ctx.send("❌ You need Admin role to spawn a control panel.")
            return
        
        # Create the panel message
        embed = nextcord.Embed(
            title="🎮 Interactive Control Panel",
            description="Creating an interactive control panel...",
            color=nextcord.Color.blue()
        )
        
        try:
            # Create the panel message with buttons
            panel_message = await ctx.send(
                content="🎮 **Interactive Control Panel**\n\nClick the buttons below to manage the bot:",
                embed=embed
            )
            
            # Store the message ID for button interactions
            self.panel_message_id = panel_message.id
            
            # Add buttons
            view = nextcord.ui.View()
            view.add_item(nextcord.ui.Button(
                label="➕ Add Game",
                style=nextcord.ButtonStyle.success,
                custom_id="add_game"
            ))
            view.add_item(nextcord.ui.Button(
                label="🗑️ Remove Game",
                style=nextcord.ButtonStyle.danger,
                custom_id="remove_game"
            ))
            view.add_item(nextcord.ui.Button(
                label="👥 User Management",
                style=nextcord.ButtonStyle.primary,
                custom_id="user_management"
            ))
            view.add_item(nextcord.ui.Button(
                label="📊 Statistics",
                style=nextcord.ButtonStyle.secondary,
                custom_id="show_stats"
            ))
            
            # Add a timeout for the view (30 seconds)
            view.timeout = 30
            
            await panel_message.edit(
                view=view,
                content="🎮 **Interactive Control Panel** - Click the buttons below to manage the bot"
            )
            
            await ctx.send(f"✅ Panel spawned! Message ID: {self.panel_message_id}")
            
        except Exception as e:
            await ctx.send(f"❌ Error spawning panel: {e}")

def setup(bot):
    bot.add_cog(InteractivePanel(bot))