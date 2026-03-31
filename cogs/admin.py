import discord
import os
from discord.ext import commands
from datetime import datetime, timezone

RAW_IT_LOG = os.getenv("IT_LOG")

class AdminCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # --- THE READ COMMAND (Viewing the Queue) ---
    @discord.slash_command(
            name="ticket_view_open",
            description="[Admin] View all open IT tickets",
            default_member_permissions=discord.Permissions(administrator=True)
            )
    
    async def ticket_view_open(self, ctx: discord.ApplicationContext):
        
        # 1. "Defer" the response. Discord requires the bot to reply within 3 seconds.
        # Since database searches can sometimes take a moment, we tell Discord to show a "bot is thinking..." message.
        await ctx.defer(ephemeral=True)

        # 2. Query MongoDB: Find EVERY document where the status is exactly "Open"
        # We use .to_list(length=None) to grab all of them at once.
        open_tickets = await self.bot.db.tickets.find({"status": "Open"}).to_list(length=None)

        # 3. Handle the scenario where the queue is empty
        if not open_tickets:
            await ctx.followup.send("🎉 There are no open tickets! The IT queue is clear.", ephemeral=True)
            return
         
        # 4. Build a master Embed to hold all the tickets
        embed = discord.Embed(title="📋 Open IT Support Tickets", description=f"There are currently **{len(open_tickets)}** open tickets.", color=discord.Color.orange())
        
        # 5. Loop through the database results and add each one to the Embed
        for ticket in open_tickets:
            
            unix_timestamp = int(datetime.fromisoformat(ticket["created_at"]).timestamp())
            # Convert the datetime into a Unix integer (e.g., 1679845300)

            # Use Discord's special syntax: <t:TIMESTAMP:f>
            discord_time = f"<t:{unix_timestamp}:f>"
            
            embed.add_field(
                name=f"Ticket #{ticket['ticket_id']} | User: {ticket['author_name']}",
                value=f"**Issue:** {ticket['issue_description']}\n**Opened:** <t:{discord_time}:f>",
                inline=False
            )
        
        # 6. Send the final, populated Embed to the channel
        await ctx.followup.send(embed=embed, ephemeral=True)

    # --- THE UPDATE COMMAND (Resolving a Ticket) ---
    @discord.slash_command(
            name="ticket_resolve",
            description="[Admin] Mark an open IT ticket as resolved",
            default_member_permissions=discord.Permissions(administrator=True)
            )
    
    async def ticket_resolve(self, ctx: discord.ApplicationContext, ticket_id: discord.Option(int, "The ID of the ticket to close", required=True)): # type: ignore
        await ctx.defer(ephemeral=True)

        # 1. Search the database for this specific ticket ID
        ticket = await self.bot.db.tickets.find_one({"ticket_id": ticket_id})

        # 2. Validation: Does the ticket exist?
        if not ticket:
            await ctx.followup.send(f"❌ Error: Ticket #{ticket_id} does not exist in the database.", ephemeral=True)
            return
        
        # 3. Validation: Is it already closed?
        if ticket["status"] == "Closed":
            await ctx.followup.send(f"⚠️ Ticket #{ticket_id} is already marked as Closed.", ephemeral=True)
            return
        
        # 4. The Update Operation in MongoDB
        # use $set to only update specific fields, leaving the rest of the document untouched
        current_time = datetime.now(timezone.utc).isoformat()
        await self.bot.db.tickets.update_one(
            {"ticket_id": ticket_id},
            {"$set": {"status": "Closed", "resolved_by": ctx.author.name, "resolved_at": current_time}}
        )

        # 5. Notify the Admin in the channel
        admin_embed = discord.Embed(title=f"✅ Ticket #{ticket_id} Resolved", description="Database updated. User notified.", color=discord.Color.green())
        await ctx.followup.send(embed=admin_embed, ephemeral=True)

        # Fetch the channel directly from Discord using self.bot
        try:
            log_channel = await self.bot.fetch_channel(int(RAW_IT_LOG))
            await log_channel.send(f"🔒 **Ticket Resolved:** Ticket #{ticket_id} was closed by {ctx.author.mention}.")
        except Exception as e:
            print(f"⚠️ Audit Log Error: Could not find channel {RAW_IT_LOG}. Error: {e}")

        # 6. Notify the Original User via Direct Message (DM)
        try:
             # We stored the author_id as a string, but Discord needs it as an integer to find the user
            user = await self.bot.fetch_user(int(ticket["author_id"]))

            user_embed = discord.Embed(title="✅ Your IT Ticket has been Resolved", description=f"**Ticket #{ticket_id}** has been marked as closed.", color=discord.Color.green())
            user_embed.add_field(name="Original Issue", value=ticket["issue_description"], inline=False)
            user_embed.add_field(name="Resolved By", value=ctx.author.name, inline=False)

            await user.send(embed=user_embed)

        except discord.Forbidden:
            # This catches the error if the user has DMs disabled
            print(f"Could not send DM to user {ticket['author_id']}. DMs are closed.")
        except discord.NotFound:
            # This catches the error if the user left the server
            print(f"Could not find user {ticket['author_id']}.")


    # --- THE AUDIT COMMAND (Looking up any ticket) ---
    @discord.slash_command(
            name="ticket_lookup",
            description="[Admin] Search for any ticket by ID",
            default_member_permissions=discord.Permissions(administrator=True)
            )
    
    async def ticket_lookup(self, ctx: discord.ApplicationContext, ticket_id: discord.Option(int, "Ticket ID", required=True)): # type: ignore
        await ctx.defer(ephemeral=True)

        # Fetch the specific document
        ticket = await self.bot.db.tickets.find_one({"ticket_id": ticket_id})

        if not ticket:
            await ctx.followup.send(f"❌ Error: Ticket #{ticket_id} could not be found.", ephemeral=True)
            return

        # Determine the color and status text based on the database state
        is_open = ticket["status"] == "Open"
        embed = discord.Embed(
            title=f"{'🔴' if is_open else '🟢'} Ticket #{ticket['ticket_id']} Audit Log",
            color=discord.Color.red() if is_open else discord.Color.green()
        )
        
        # Format the creation date
        created_unix = int(datetime.fromisoformat(ticket["created_at"]).timestamp())
        embed.add_field(name="Reported By", value=ticket["author_name"], inline=True)
        embed.add_field(name="Status", value=ticket["status"], inline=True)
        embed.add_field(name="Opened At", value=f"<t:{created_unix}:f>", inline=False)
        embed.add_field(name="Issue Description", value=f"```\n{ticket['issue_description']}\n```", inline=False)

        # If it is closed, show who closed it and when
        if not is_open and ticket["resolved_at"]:
            resolved_unix = int(datetime.fromisoformat(ticket["resolved_at"]).timestamp())
            embed.add_field(name="Resolved By", value=ticket["resolved_by"], inline=True)
            embed.add_field(name="Resolved At", value=f"<t:{resolved_unix}:f>", inline=True)

        await ctx.followup.send(embed=embed, ephemeral=True)


    @discord.slash_command(
            name="ticket_history", 
            description="[Admin] View the 5 most recently closed tickets",
            default_member_permissions=discord.Permissions(administrator=True)
            )
    
    async def ticket_history(self, ctx: discord.ApplicationContext):
        await ctx.defer(ephemeral=True)
        
        # Search for closed tickets, sort them by resolved_at (instead of ticket_id)000000000, and limit to 5
        closed_tickets = await self.bot.db.tickets.find({"status": "Closed"}).sort("resolved_at", -1).limit(5).to_list(length=5)

        if not closed_tickets:
            await ctx.followup.send("No closed tickets found in the database.", ephemeral=True)
            return

        embed = discord.Embed(title="📚 Recently Closed Tickets", color=discord.Color.blue())
        for ticket in closed_tickets:
            resolved_unix = int(datetime.fromisoformat(ticket["resolved_at"]).timestamp())
            embed.add_field(
                name=f"Ticket #{ticket['ticket_id']} | User: {ticket['author_name']}",
                value=f"**Issue:** {ticket['issue_description']}\n**Closed:** <t:{resolved_unix}:R> by {ticket['resolved_by']}",
                inline=False
            )
        await ctx.followup.send(embed=embed, ephemeral=True)

def setup(bot):
    bot.add_cog(AdminCog(bot))