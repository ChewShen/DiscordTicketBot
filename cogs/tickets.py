import discord
from discord.ext import commands
from datetime import datetime, timezone


# --- THE MODAL (The Pop-up Form) ---
class TicketModal(discord.ui.Modal):
    # We pass the bot into the modal so we can access the database
    def __init__(self, bot, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bot = bot
        
        # Add a text input field to the modal
        self.add_item(discord.ui.InputText(
            label="What is the IT issue?",
            style=discord.InputTextStyle.long,
            placeholder="E.g., My monitor won't turn on...",
            required=True
        ))

    # This 'callback' runs the moment the user clicks "Submit" on the modal
    async def callback(self, interaction: discord.Interaction):
        # 1. Grab what the user typed into the box
        issue_description = self.children[0].value
        # Access the DB from the bot's backpack
        tickets_collection = self.bot.db.tickets
        counters_collection = self.bot.db.counters
        
        # 2. Generate a simple Ticket ID (Count existing tickets + 1)
        # ticket_count = await tickets_collection.count_documents({})
        # new_ticket_id = ticket_count + 1

        # This securely increments the 'ticket_id' counter by 1. If the counter doesn't exist yet, 'upsert=True' creates it.
        counter_doc = await counters_collection.find_one_and_update(
            {"_id": "ticket_id"},
            {"$inc": {"sequence_value": 1}},
            return_document=True,
            upsert=True
        )
        new_ticket_id = counter_doc["sequence_value"]
        
        # 3. Construct our JSON Document
        ticket_doc = {
            "ticket_id": new_ticket_id,
            "author_id": str(interaction.user.id),
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
            description="Your IT support ticket has been submitted.",
            color=discord.Color.red()
        )
        embed.add_field(name="Issue Details", value=issue_description)

        # Send the embed back to the user. 'ephemeral=True' means only they can see this message.
        await interaction.response.send_message(embed=embed, ephemeral=True)

        # --- SEND ALERT TO ADMIN CHANNEL ---
        admin_channel = self.bot.get_channel(self.bot.admin_channel_id)
         # A quick note so admins know who to contact
        if admin_channel:
            # 1. Create the independent clone
            admin_alert_embed = embed.copy()
            # 2. Change the title and color for the admins
            admin_alert_embed.title = f"🚨 NEW TICKET ALERT: #{new_ticket_id}"
            admin_alert_embed.color = discord.Color.orange() #color fix!

            # 3. Create a Unicode separation line
            separator = "━━━━━━━━━━━━━━━━━━━━━━━━━━━"

            # 4. Get the exact current time as a Unix Timestamp integer
            unix_timestamp = int(datetime.now(timezone.utc).timestamp())
            
            # 5. Completely overwrite the description with the new Audit Log data
            # Using [interaction.user.mention] will make their name clickable in the channel!
            admin_alert_embed.description = (
                f"{separator}\n"
                f"**Reported By:** {interaction.user.mention}\n"
                f"**Opened At:** <t:{unix_timestamp}:f>\n"
            
            )
            # Note: No need to add the issue description here
            
            # 6. Send it to the logs
            await admin_channel.send(embed=admin_alert_embed)

# Trigger (For User)
class TicketsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # When the user types /ticket_create, show them the Modal
    @discord.slash_command(
                            name="ticket_create",
                            description="Open a new IT Support ticket"
                           )
    
    async def ticket_create(self, ctx: discord.ApplicationContext):
        modal = TicketModal(bot=self.bot, title="Create IT Ticket")
        await ctx.send_modal(modal)

# This function is required by Discord to load the Cog
def setup(bot):
    bot.add_cog(TicketsCog(bot))