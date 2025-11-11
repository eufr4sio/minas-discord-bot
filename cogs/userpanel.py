import nextcord
from nextcord.ext import commands
from nextcord.ui import Button, View, Select
from database import Database

# --- The main view for the shared user panel ---
class SharedUserPanelView(View):
    def __init__(self, cog: 'UserPanel'):
        super().__init__(timeout=None) # Persistent view
        self.cog = cog
        self._add_components()

    def _add_components(self):
        self.clear_items()
        
        # Get all games for the dropdowns
        games = self.cog.db.get_all_games_for_panel_sync()
        game_options = [nextcord.SelectOption(label=game['name'], value=str(game['id'])) for game in games]

        # Handle the case where there are no games
        if not game_options:
            self.add_item(Button(label="No games available", style=nextcord.ButtonStyle.grey, disabled=True, row=0, custom_id="no_games_button"))
            return

        # Handle Discord's 25 option limit
        if len(game_options) > 25:
            game_options = game_options[:25]

        # Dropdown for registering
        self.add_item(Select(placeholder="➕ Select a game to register for...", options=game_options, row=0, custom_id="shared_register_select"))
        
        # Button for registering
        self.add_item(Button(label="✅ Confirm Registration", style=nextcord.ButtonStyle.success, row=1, custom_id="shared_register_button"))
        self.children[-1].callback = self.register_button_callback

        # Dropdown for unregistering
        self.add_item(Select(placeholder="❌ Select a game to unregister from...", options=game_options, row=2, custom_id="shared_unregister_select"))

        # Button for unregistering
        self.add_item(Button(label="❌ Confirm Unregistration", style=nextcord.ButtonStyle.danger, row=3, custom_id="shared_unregister_button"))
        self.children[-1].callback = self.unregister_button_callback

        # Button for checking registrations
        self.add_item(Button(label="📋 Check My Registrations", style=nextcord.ButtonStyle.secondary, row=4, custom_id="user_check_registrations_button"))
        self.children[-1].callback = self.check_registrations_button_callback

    async def register_button_callback(self, interaction: nextcord.Interaction):
        # Find the dropdown for registration (it's the first Select component)
        register_select = self.children[0]
        if not register_select.values:
            return await interaction.response.send_message("❌ Please select a game from the dropdown first.", ephemeral=True)
        
        game_id = int(register_select.values[0])
        game_name = await self.cog.db.get_game_name_by_id(game_id)
        
        success = await self.cog.db.register_user_for_game(interaction.user.id, game_name)
        
        if success:
            await interaction.response.send_message(f"✅ You have been registered for **{game_name}**!", ephemeral=True)
        else:
            await interaction.response.send_message(f"❌ You are already registered for **{game_name}**.", ephemeral=True)

    async def unregister_button_callback(self, interaction: nextcord.Interaction):
        # Find the dropdown for unregistration (it's the second Select component)
        unregister_select = self.children[2]
        if not unregister_select.values:
            return await interaction.response.send_message("❌ Please select a game from the dropdown first.", ephemeral=True)

        game_id = int(unregister_select.values[0])
        game_name = await self.cog.db.get_game_name_by_id(game_id)
        
        success = await self.cog.db.unregister_user_from_game(interaction.user.id, game_name)

        if success:
            await interaction.response.send_message(f"✅ You have been unregistered from **{game_name}**.", ephemeral=True)
        else:
            await interaction.response.send_message(f"❌ You were not registered for **{game_name}**.", ephemeral=True)

    async def check_registrations_button_callback(self, interaction: nextcord.Interaction):
        user_id = interaction.user.id
        registered_games = await self.cog.db.get_user_registered_games(user_id)

        if registered_games:
            game_list = "\n".join(f"🔹 {game}" for game in registered_games)
            embed = nextcord.Embed(
                title="🎮 Your Game Registrations",
                description=game_list,
                color=nextcord.Color.green()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            embed = nextcord.Embed(
                title="🎮 Your Game Registrations",
                description="You are not registered for any games yet. Use the buttons above to get started!",
                color=nextcord.Color.orange()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)


# --- The User Panel Cog ---
class UserPanel(commands.Cog):
    def __init__(self, bot: commands.Bot, db: Database):
        self.bot = bot
        self.db = db
        self.shared_panel_message = None
        # Register the persistent view so buttons work after a restart
        self.bot.add_view(SharedUserPanelView(self))

    @commands.command(name="createuserpanel")
    @commands.has_permissions(administrator=True)
    async def createuserpanel(self, ctx: commands.Context):
        """Creates the shared user panel in the current channel."""
        if self.shared_panel_message:
            return await ctx.send("A user panel is already active. Delete the old one or restart the bot to create a new one.", ephemeral=True)

        view = SharedUserPanelView(self)
        embed = nextcord.Embed(
            title="🎮 Game Notification Center",
            description="Select a game from the dropdown and click the corresponding button to manage your subscriptions.",
            color=nextcord.Color.blue()
        )
        embed.set_footer(text="All actions are private and only you can see the confirmation.")
        
        self.shared_panel_message = await ctx.send(embed=embed, view=view)
        await ctx.message.delete() # Clean up the command message

    # THIS is the function the admin panel will call
    async def refresh_shared_panel(self):
        """Edits the shared user panel message with an updated game list."""
        if self.shared_panel_message:
            new_view = SharedUserPanelView(self)
            embed = nextcord.Embed(
                title="🎮 Game Notification Center",
                description="Select a game from the dropdown and click the corresponding button to manage your subscriptions.",
                color=nextcord.Color.blue()
            )
            embed.set_footer(text="All actions are private and only you can see the confirmation.")
            await self.shared_panel_message.edit(embed=embed, view=new_view)

def setup(bot):
    bot.add_cog(UserPanel(bot))