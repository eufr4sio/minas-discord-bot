import nextcord
from nextcord.ext import commands
import datetime
import os
from database import Database

class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()
    
    @commands.group(name="event", invoke_without_command=True)
    async def event(self, ctx):
        """Event management commands"""
        await ctx.send("Use `!event create <title>` to create a game event or `!event list` to see upcoming events.")
    
    @event.command(name="create")
    async def create(self, ctx, title: str, *, description: str = "No description provided"):
        """Create a new game event"""
        # Create event in database
        event_id = self.db.create_event(title, description, ctx.author.id)
        
        if event_id:
            embed = nextcord.Embed(
                title="🎉 Event Created!",
                description=f"Event **{title}** has been created successfully!",
                color=nextcord.Color.green()
            )
            embed.add_field(name="📝 Description", value=description, inline=False)
            embed.add_field(name="👤 Creator", value=ctx.author.mention, inline=True)
            embed.add_field(name="🆔 Event ID", value=f"#{event_id}", inline=True)
            embed.set_footer(text=f"Created by {ctx.author.name}")
            await ctx.send(embed=embed)
            
            # Also send to events channel if configured
            await self.announce_event(event_id, title, description, ctx.author)
        else:
            embed = nextcord.Embed(
                title="❌ Event Creation Failed",
                description="Could not create the event. Please try again.",
                color=nextcord.Color.red()
            )
            await ctx.send(embed=embed)
    
    @event.command(name="list")
    async def list(self, ctx):
        """List all upcoming events"""
        events = self.db.get_upcoming_events()
        
        if events:
            embed = nextcord.Embed(
                title="📅 Upcoming Events",
                description="Here are the upcoming game events:",
                color=nextcord.Color.blue()
            )
            
            for event in events:
                event_time = event[3] if event[3] else "No time set"
                embed.add_field(
                    name=f"🎮 {event[1]} (#{event[0]})",
                    value=f"📝 {event[2][:50]}{'...' if len(event[2]) > 50 else ''}\n👤 Created by <@{event[4]}>\n📅 {event_time}",
                    inline=False
                )
            
            embed.set_footer(text=f"Requested by {ctx.author.name}")
            await ctx.send(embed=embed)
        else:
            embed = nextcord.Embed(
                title="📅 No Events",
                description="No upcoming events found. Create one with `!event create <title>`!",
                color=nextcord.Color.orange()
            )
            embed.set_footer(text=f"Requested by {ctx.author.name}")
            await ctx.send(embed=embed)
    
    @event.command(name="rsvp")
    async def rsvp(self, ctx, event_id: int, status: str = "attending"):
        """RSVP to an event (attending/declined/maybe)"""
        valid_statuses = ["attending", "declined", "maybe"]
        if status.lower() not in valid_statuses:
            await ctx.send(f"❌ Invalid status. Use: {', '.join(valid_statuses)}")
            return
        
        success = self.db.update_event_rsvp(event_id, ctx.author.id, status.lower())
        
        if success:
            embed = nextcord.Embed(
                title="✅ RSVP Updated",
                description=f"You've marked yourself as **{status.lower()}** for event #{event_id}",
                color=nextcord.Color.green()
            )
            embed.set_footer(text=f"Updated by {ctx.author.name}")
            await ctx.send(embed=embed)
        else:
            embed = nextcord.Embed(
                title="❌ Event Not Found",
                description=f"Event #{event_id} doesn't exist or has ended.",
                color=nextcord.Color.red()
            )
            await ctx.send(embed=embed)
    
    async def announce_event(self, event_id, title, description, creator):
        """Announce new event to the server"""
        # You can configure this channel in .env or use a default
        events_channel_id = int(os.getenv('EVENTS_CHANNEL_ID', 0))
        if events_channel_id == 0:
            return  # No events channel configured
        
        channel = self.bot.get_channel(events_channel_id)
        if not channel:
            return
        
        embed = nextcord.Embed(
            title="🎉 New Game Event!",
            description=f"**{title}**",
            color=nextcord.Color.purple(),
            timestamp=datetime.datetime.now()
        )
        
        embed.add_field(name="📝 Description", value=description, inline=False)
        embed.add_field(name="👤 Creator", value=creator.mention, inline=True)
        embed.add_field(name="🆔 Event ID", value=f"#{event_id}", inline=True)
        embed.add_field(name="📋 RSVP", value="Use `!event rsvp {event_id} attending/declined/maybe`", inline=False)
        
        embed.set_thumbnail(url=creator.display_avatar.url)
        embed.set_footer(text="React to this event to RSVP!")
        
        await channel.send(embed=embed)

def setup(bot):
    bot.add_cog(Events(bot))