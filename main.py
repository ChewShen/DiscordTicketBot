import discord  
import os
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone

# Load environment variables from the .env file
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")

# Initialize the Discord Bot with default intents
intents = discord.Intents.default()
bot = discord.Bot(intents=intents)

# Initialize the MongoDB Async Client
# Server Selection Timeout is set to 5 seconds so it doesn't hang forever if the password is wrong
db_client = AsyncIOMotorClient(MONGO_URI, serverSelectionTimeoutMS=5000)
db = db_client.helpdesk_db  # This creates/connects to a database named 'helpdesk_db'
tickets_collection = db.tickets  # This creates/connects to a collection named 'tickets'

@bot.event
async def on_ready():
    print(f"✅ Logged in to Discord as {bot.user}")
    
    # Ping the MongoDB database to test the connection
    try:
        await db_client.admin.command('ping')
        print("✅ Successfully connected to MongoDB Atlas!")
    except Exception as e:
        print(f"❌ Failed to connect to MongoDB. Error: {e}")

@bot.event
async def on_application_command_error(ctx: discord.ApplicationContext, error: discord.DiscordException):
    # This triggers anytime ANY slash command fails
    
    # 1. Log the actual error to your terminal so you can fix it later
    print(f"⚠️ CRITICAL COMMAND ERROR in /{ctx.command.name}: {error}")
    
    # 2. Build a graceful, professional apology for the user
    error_embed = discord.Embed(
        title="🔧 System Error",
        description="Our ticketing system encountered an unexpected issue while processing your request. The IT team has been automatically notified.",
        color=discord.Color.dark_red()
    )
    
    # 3. Send it to the user. We use a try/except here just in case the error 
    # was caused by Discord not allowing us to send messages!
    try:
        if ctx.interaction.response.is_done():
            await ctx.followup.send(embed=error_embed, ephemeral=True)
        else:
            await ctx.respond(embed=error_embed, ephemeral=True)
    except Exception as fallback_error:
        print(f"Could not send error message to user: {fallback_error}")

# --- THE MODAL (The Pop-up Form) ---
class TicketModal(discord.ui.Modal):                              
    def __init__(self, *args, **kwargs):                         
        super().__init__(*args, **kwargs)
        
        # Add a text input field to the modal
        self.add_item(discord.ui.InputText(
            label="What is the IT issue?",
            style=discord.InputTextStyle.long, # Makes it a large paragraph box
            placeholder="E.g., My monitor won't turn on, or I need VPN access...",
            required=True
        ))

    # This 'callback' runs the moment the user clicks "Submit" on the modal
    async def callback(self, interaction: discord.Interaction):
        # 1. Grab what the user typed into the box
        issue_description = self.children[0].value
        
        # 2. Generate a simple Ticket ID (Count existing tickets + 1)
        ticket_count = await tickets_collection.count_documents({})
        new_ticket_id = ticket_count + 1
        
        # 3. Construct our JSON Document
        ticket_doc = {
            "ticket_id": new_ticket_id,
            "author_id": str(interaction.user.id), # Save as string to prevent math errors
            "author_name": interaction.user.name,
            "issue_description": issue_description,
            "status": "Open",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "resolved_by": None,
            "resolved_at": None
        }
        
        # 4. Insert the document into MongoDB Atlas
        await tickets_collection.insert_one(ticket_doc)
        
        # 5. Build a nice visual response (Embed) for the user
        embed = discord.Embed(
            title=f"🎫 Ticket #{new_ticket_id} Created",
            description="Your IT support ticket has been submitted to the database.",
            color=discord.Color.red() # Red signifies an "Open" state
        )
        embed.add_field(name="Issue Details", value=issue_description)
        embed.set_footer(text="An IT admin will review this shortly.")
        
        # Send the embed back to the user. 'ephemeral=True' means only they can see this message.
        await interaction.response.send_message(embed=embed, ephemeral=True)


# --- THE SLASH COMMAND (The Trigger) ---
@bot.slash_command(name="ticket_create", description="Open a new IT Support ticket")
async def ticket_create(ctx: discord.ApplicationContext):
    # When the user types /ticket_create, show them the Modal
    modal = TicketModal(title="Create IT Ticket")
    await ctx.send_modal(modal)

# --- THE READ COMMAND (Viewing the Queue) ---
@bot.slash_command(name="ticket_view_open", description="[Admin] View all open IT tickets", default_member_permissions=discord.Permissions(administrator=True)) # <-- The Security Lock
async def ticket_view_open(ctx: discord.ApplicationContext):
    # 1. "Defer" the response. Discord requires the bot to reply within 3 seconds.
    # Since database searches can sometimes take a moment, we tell Discord to show a "bot is thinking..." message.
    await ctx.defer(ephemeral=True)

    # 2. Query MongoDB: Find EVERY document where the status is exactly "Open"
    # We use .to_list(length=None) to grab all of them at once.
    open_tickets = await tickets_collection.find({"status": "Open"}).to_list(length=None)

    # 3. Handle the scenario where the queue is empty
    if not open_tickets:
        await ctx.followup.send("🎉 There are no open tickets! The IT queue is clear.", ephemeral=True)
        return

    # 4. Build a master Embed to hold all the tickets
    embed = discord.Embed(
        title="📋 Open IT Support Tickets",
        description=f"There are currently **{len(open_tickets)}** open tickets.",
        color=discord.Color.orange() # Orange for pending queue
    )

   # 5. Loop through the database results and add each one to the Embed
    for ticket in open_tickets:
        raw_date = datetime.fromisoformat(ticket["created_at"])
        
        # Convert the datetime into a Unix integer (e.g., 1679845300)
        unix_timestamp = int(raw_date.timestamp())
        
        # Use Discord's special syntax: <t:TIMESTAMP:f>
        discord_time = f"<t:{unix_timestamp}:f>"

        # Add a block of text for this specific ticket
        embed.add_field(
            name=f"Ticket #{ticket['ticket_id']} | User: {ticket['author_name']}",
            value=f"**Issue:** {ticket['issue_description']}\n**Opened:** {discord_time}",
            inline=False
        )

    # 6. Send the final, populated Embed to the channel
    await ctx.followup.send(embed=embed, ephemeral=True)

# --- THE UPDATE COMMAND (Resolving a Ticket) ---
@bot.slash_command(name="ticket_resolve", description="[Admin] Mark an open IT ticket as resolved", default_member_permissions=discord.Permissions(administrator=True))
async def ticket_resolve(
    ctx: discord.ApplicationContext,
    ticket_id: discord.Option(int, "The ID of the ticket to close (e.g., 1)", required=True) # type: ignore
):
    await ctx.defer(ephemeral=True)

    # 1. Search the database for this specific ticket ID
    ticket = await tickets_collection.find_one({"ticket_id": ticket_id})

    # 2. Validation: Does the ticket exist?
    if not ticket:
        await ctx.followup.send(f"❌ Error: Ticket #{ticket_id} does not exist in the database.", ephemeral=True)
        return

    # 3. Validation: Is it already closed?
    if ticket["status"] == "Closed":
        await ctx.followup.send(f"⚠️ Ticket #{ticket_id} is already marked as Closed.", ephemeral=True)
        return

    # 4. The Update Operation in MongoDB
    # We use $set to only update specific fields, leaving the rest of the document untouched
    current_time = datetime.now(timezone.utc).isoformat()
    await tickets_collection.update_one(
        {"ticket_id": ticket_id},
        {"$set": {
            "status": "Closed",
            "resolved_by": ctx.author.name,
            "resolved_at": current_time
        }}
    )

    # 5. Notify the Admin in the channel
    admin_embed = discord.Embed(title=f"✅ Ticket #{ticket_id} Resolved", description=f"The status has been updated in the database. A notification has been sent to the user.", color=discord.Color.green()) # Green for success/closed)
    await ctx.followup.send(embed=admin_embed, ephemeral=True)

    # 6. Notify the Original User via Direct Message (DM)
    try:
        # We stored the author_id as a string, but Discord needs it as an integer to find the user
        user = await bot.fetch_user(int(ticket["author_id"]))
        
        user_embed = discord.Embed(
            title="✅ Your IT Ticket has been Resolved",
            description=f"**Ticket #{ticket_id}** has been marked as closed by the IT team.",
            color=discord.Color.green()
        )
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
@bot.slash_command(name="ticket_lookup", description="[Admin] Search for any ticket (Open or Closed) by its ID",
    default_member_permissions=discord.Permissions(administrator=True))

async def ticket_lookup(
    ctx: discord.ApplicationContext,
    ticket_id: discord.Option(int, "The ID of the ticket to lookup", required=True) # type: ignore
):
    await ctx.defer(ephemeral=True)

    # Fetch the specific document
    ticket = await tickets_collection.find_one({"ticket_id": ticket_id})

    if not ticket:
        await ctx.followup.send(f"❌ Error: Ticket #{ticket_id} could not be found.", ephemeral=True)
        return

    # Determine the color and status text based on the database state
    is_open = ticket["status"] == "Open"
    embed_color = discord.Color.red() if is_open else discord.Color.green()
    status_icon = "🔴" if is_open else "🟢"

    embed = discord.Embed(
        title=f"{status_icon} Ticket #{ticket['ticket_id']} Audit Log",
        color=embed_color
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

# Run the bot
if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)