import nextcord
from nextcord.ext import commands
from nextcord.ui import Button, View, Select, Modal, TextInput
from database import Database

# --- Helper function to find a user ---
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

# --- Modal for Managing a User (Text Input Only) ---
class ManageUserModal(Modal):
    def __init__(self, cog: 'ControlPanel'):
        super().__init__(title="Manage a User")
        self.cog = cog

        # Add the text input for any user. This is the only component.
        self.add_item(TextInput(
            label="User (ID, @mention, or Name#1234)",
            placeholder="e.g., @Mina or Mina#1234",
            required=True # Make it required since it's the only way
        ))

    async def callback(self, interaction: nextcord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        target_user = None
        text_input_value = self.children[0].value

        # Find the user from the text input
        if text_input_value:
            target_user = find_user(interaction.guild, text_input_value)

        if not target_user:
            return await interaction.followup.send(f"❌ Could not find a user from your input. Please check the ID/mention/name.", ephemeral=True)
        
        view = UserActionView(self.cog, target_user)
        embed = nextcord.Embed(title=f"Managing {target_user.display_name}", description="Select a game and an action below.", color=nextcord.Color.blue())
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)


# --- View for User Actions (Register/Unregister) ---
class UserActionView(View):
    def __init__(self, cog: 'ControlPanel', target_user: nextcord.Member):
        super().__init__(timeout=120)
        self.cog = cog
        self.target_user = target_user
        self._add_components()

    def _add_components(self):
        self.clear_items()
        
        games = self.cog.db.get_all_games_for_panel_sync()
        if not games:
            self.add_item(Button(label="No games found in bot", style=nextcord.ButtonStyle.grey, disabled=True, row=0))
            return

        game_options = [nextcord.SelectOption(label=game['name'], value=str(game['id'])) for game in games]
        self.add_item(Select(placeholder="Select a game for this user...", options=game_options, row=0))
        
        self.add_item(Button(label="✅ Register User", style=nextcord.ButtonStyle.success, row=1))
        self.children[-1].callback = self.register_button_callback
        
        self.add_item(Button(label="❌ Unregister User", style=nextcord.ButtonStyle.danger, row=1))
        self.children[-1].callback = self.unregister_button_callback

    async def register_button_callback(self, interaction: nextcord.Interaction):
        game_id = int(self.children[0].values[0])
        game_name = await self.cog.db.get_game_name_by_id(game_id)
        success = await self.cog.db.register_user_for_game(self.target_user.id, game_name)
        
        if success:
            await interaction.response.send_message(f"✅ Registered {self.target_user.mention} for **{game_name}**.", ephemeral=True)
        else:
            await interaction.response.send_message(f"❌ {self.target_user.mention} is already registered for **{game_name}**.", ephemeral=True)
        
        await self.cog.refresh_panel()

    async def unregister_button_callback(self, interaction: nextcord.Interaction):
        game_id = int(self.children[0].values[0])
        game_name = await self.cog.db.get_game_name_by_id(game_id)
        success = await self.cog.db.unregister_user_from_game(self.target_user.id, game_name)

        if success:
            await interaction.response.send_message(f"✅ Unregistered {self.target_user.mention} from **{game_name}**.", ephemeral=True)
        else:
            await interaction.response.send_message(f"❌ {self.target_user.mention} was not registered for **{game_name}**.", ephemeral=True)

        await self.cog.refresh_panel()


# --- (Keep all the other classes from before: AddGameModal, ConfirmView, etc.) ---

# --- Modal for Adding a New Game ---
class AddGameModal(Modal):
    def __init__(self, cog: 'ControlPanel'):
        super().__init__(title="Add a New Game")
        self.cog = cog
        self.add_item(TextInput(label="Game Name", placeholder="e.g., Battlefield 6", required=True))
        self.add_item(TextInput(label="Image URL (Optional)", placeholder="https://...", required=False))
        self.add_item(TextInput(label="Aliases (Optional)", placeholder="e.g., BF6, BF (comma-separated)", required=False))

    async def callback(self, interaction: nextcord.Interaction):
        game_name = self.children[0].value
        image_url = self.children[1].value or None
        aliases_str = self.children[2].value
        await interaction.response.defer(ephemeral=True)
        try:
            game_id = await self.cog.db.add_game(game_name, image_url, aliases_str)
            if game_id:
                await interaction.followup.send(f"✅ Successfully added game **{game_name}**!", ephemeral=True)
                await self.cog.refresh_panel()
            else:
                await interaction.followup.send(f"❌ A game named **{game_name}** or one of its aliases already exists.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Error adding game: {e}", ephemeral=True)

# --- View for Confirmation Prompts ---
class ConfirmView(View):
    def __init__(self, cog: 'ControlPanel', action_type: str, target_id: int, target_name: str):
        super().__init__(timeout=60.0)
        self.cog = cog
        self.action_type = action_type
        self.target_id = target_id
        self.target_name = target_name

    @nextcord.ui.button(label="Confirm", style=nextcord.ButtonStyle.danger, row=0)
    async def confirm(self, button: Button, interaction: nextcord.Interaction):
        await interaction.response.defer(ephemeral=True)
        try:
            if self.action_type == "delete_game":
                success = await self.cog.db.delete_game(self.target_id)
                if success:
                    await interaction.followup.send(f"✅ Game **{self.target_name}** has been deleted.", ephemeral=True)
                else:
                    await interaction.followup.send(f"❌ Could not find **{self.target_name}**.", ephemeral=True)
                    return
            elif self.action_type == "set_channel":
                await self.cog.db.set_config("ALERT_CHANNEL_ID", self.target_id)
                channel = self.cog.bot.get_channel(self.target_id)
                await interaction.followup.send(f"✅ Alert channel set to **{channel.mention}**.", ephemeral=True)
            await self.cog.refresh_panel()
        except Exception as e:
            await interaction.followup.send(f"❌ Error: {e}", ephemeral=True)
        self.stop()

    @nextcord.ui.button(label="Cancel", style=nextcord.ButtonStyle.secondary, row=0)
    async def cancel(self, button: Button, interaction: nextcord.Interaction):
        await interaction.response.send_message("Action cancelled.", ephemeral=True)
        self.stop()

# --- The Main Control Panel View ---
class ControlPanelView(View):
    def __init__(self, cog: 'ControlPanel'):
        super().__init__(timeout=None)
        self.cog = cog
        self._add_components()

    def _add_components(self):
        self.clear_items()
        
        # Row 0: Add Game & Manage User
        self.add_item(Button(label="➕ Add Game", style=nextcord.ButtonStyle.success, row=0, custom_id="add_game_button"))
        self.children[0].callback = self.add_game_button_callback
        
        self.add_item(Button(label="👤 Manage User", style=nextcord.ButtonStyle.primary, row=0, custom_id="manage_user_button"))
        self.children[1].callback = self.manage_user_button_callback

        # Row 1: Game Dropdowns
        games = self.cog.db.get_all_games_for_panel_sync()
        game_options = [nextcord.SelectOption(label=game['name'], value=str(game['id'])) for game in games]
        if game_options:
            if len(game_options) > 25: game_options = game_options[:25]
            self.add_item(Select(placeholder="🗑️ Delete a Game...", options=game_options, row=1, custom_id="delete_game_select"))
            self.children[-1].callback = self.delete_game_select_callback
            self.add_item(Select(placeholder="👥 View Registrations...", options=game_options, row=2, custom_id="view_registrations_select"))
            self.children[-1].callback = self.view_registrations_select_callback

        # Row 3: Channel Dropdown
        channels = [c for c in self.cog.bot.get_all_channels() if isinstance(c, nextcord.TextChannel)]
        channel_options = [nextcord.SelectOption(label=f"#{c.name}", value=str(c.id)) for c in channels]
        if channel_options:
            if len(channel_options) > 25: channel_options = channel_options[:25]
            self.add_item(Select(placeholder="📢 Set Alert Channel...", options=channel_options, row=3, custom_id="set_channel_select"))
            self.children[-1].callback = self.set_channel_select_callback

    async def add_game_button_callback(self, interaction: nextcord.Interaction):
        await interaction.response.send_modal(AddGameModal(self.cog))

    async def manage_user_button_callback(self, interaction: nextcord.Interaction):
        await interaction.response.send_modal(ManageUserModal(self.cog))

    async def delete_game_select_callback(self, interaction: nextcord.Interaction):
        game_id = int(interaction.data['values'][0])
        game_name = await self.cog.db.get_game_name_by_id(game_id)
        confirm_view = ConfirmView(self.cog, "delete_game", game_id, game_name)
        await interaction.response.send_message(f"Are you sure you want to delete **{game_name}**?", view=confirm_view, ephemeral=True)

    async def view_registrations_select_callback(self, interaction: nextcord.Interaction):
        game_id = int(interaction.data['values'][0])
        game_name = await self.cog.db.get_game_name_by_id(game_id)
        registrations = await self.cog.db.get_registrations_for_game_id(game_id)
        if not registrations:
            return await interaction.response.send_message(f"No users are registered for **{game_name}**.", ephemeral=True)
        user_mentions = [f"<@{user_id}>" for user_id in registrations]
        embed = nextcord.Embed(title=f"Registrations for {game_name}", description="\n".join(user_mentions), color=nextcord.Color.blue())
        await interaction.response.send_message(embed=embed, ephemeral=True)

    async def set_channel_select_callback(self, interaction: nextcord.Interaction):
        channel_id = int(interaction.data['values'][0])
        channel = self.cog.bot.get_channel(channel_id)
        confirm_view = ConfirmView(self.cog, "set_channel", channel_id, channel.name)
        await interaction.response.send_message(f"Set **{channel.mention}** as the new alert channel?", view=confirm_view, ephemeral=True)

# --- The Main Cog ---
class ControlPanel(commands.Cog):
    def __init__(self, bot: commands.Bot, db: Database):
        self.bot = bot
        self.db = db
        self.message = None
        self.bot.add_view(ControlPanelView(self))

    @commands.command(name="controlpanel")
    @commands.has_permissions(administrator=True)
    async def controlpanel(self, ctx: commands.Context):
        if self.message:
            return await ctx.send("A control panel is already active.", ephemeral=True)
        view = ControlPanelView(self)
        embed = await self._build_embed()
        self.message = await ctx.send(embed=embed, view=view)

    async def _build_embed(self):
        embed = nextcord.Embed(title="🛠️ Mina's Bot Control Panel", description="Use the components below to manage the bot.", color=nextcord.Color.gold())
        alert_channel_id = await self.db.get_config("ALERT_CHANNEL_ID")
        if alert_channel_id:
            channel = self.bot.get_channel(alert_channel_id)
            if channel:
                embed.add_field(name="Current Alert Channel", value=channel.mention, inline=False)
        return embed

    async def refresh_panel(self):
        if self.message:
            new_view = ControlPanelView(self)
            new_embed = await self._build_embed()
            await self.message.edit(embed=new_embed, view=new_view)

        user_panel_cog = self.bot.get_cog('UserPanel')
        if user_panel_cog:
            await user_panel_cog.refresh_shared_panel()