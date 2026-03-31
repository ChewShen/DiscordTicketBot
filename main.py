import discord  
import os
import sys
from dotenv import load_dotenv
from keep_alive import keep_alive
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone

# Load environment variables from the .env file
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")
RAW_IT_LOG = os.getenv("IT_LOG")

missing_vars = []
if not DISCORD_TOKEN: missing_vars.append("DISCORD_TOKEN")
if not MONGO_URI: missing_vars.append("MONGO_URI")
if not RAW_IT_LOG: missing_vars.append("IT_LOG")

if missing_vars:
    print(f"❌ FATAL STARTUP ERROR: Missing environment variables: {', '.join(missing_vars)}")
    print("👉 Please check your .env file and ensure all required variables are set.")
    sys.exit(1) # 1 means the script exited because of an error

# 3. Since it exist, it is safe to convert IT_LOG to an integer
try:
    IT_LOG = int(RAW_IT_LOG)
except ValueError:
    print("❌ FATAL STARTUP ERROR: IT_LOG must be a valid Discord Channel ID (numbers only).")
    sys.exit(1)

# Initialize the Discord Bot with default intents
intents = discord.Intents.default()
bot = discord.Bot(intents=intents)

# Initialize the MongoDB Async Client
# Server Selection Timeout is set to 5 seconds so it doesn't hang forever if the password is wrong
db_client = AsyncIOMotorClient(MONGO_URI, serverSelectionTimeoutMS=5000)
bot.db = db_client.helpdesk_db  # Now every Cog can access self.bot.db!
bot.admin_channel_id = IT_LOG   # Pass the channel ID in the backpack too

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
    # 1. Print to the Render console for the Developer (You)
    print(f"⚠️ CRITICAL COMMAND ERROR in /{ctx.command.name}: {error}")
    
    # 2. Build the graceful, professional apology for the User
    user_error_embed = discord.Embed(
        title="🔧 System Error",
        description="Our ticketing system encountered an unexpected issue while processing your request. The IT team has been automatically notified.",
        color=discord.Color.dark_red()
    )
    
    # Send the apology to the user (ephemeral so only they see it)
    # Note: We use respond() because an error might happen before the bot defers
    try:
        await ctx.respond(embed=user_error_embed, ephemeral=True)
    except discord.errors.InteractionResponded:
        await ctx.followup.send(embed=user_error_embed, ephemeral=True)

    # 3. ACTUALLY notify the IT Department in the #it-logs channel!
    try:
        RAW_IT_LOG = os.getenv("IT_LOG")
        if RAW_IT_LOG:
            log_channel = await bot.fetch_channel(int(RAW_IT_LOG))
            
            admin_alert_embed = discord.Embed(
                title="🚨 Application Command Error",
                description=f"A user triggered a critical error while using `/{ctx.command.name}`.",
                color=discord.Color.red()
            )
            admin_alert_embed.add_field(name="User Experiencing Error", value=ctx.author.mention, inline=True)
            admin_alert_embed.add_field(name="Channel", value=ctx.channel.mention, inline=True)
            admin_alert_embed.add_field(name="Raw Error Traceback", value=f"```py\n{error}\n```", inline=False)
            
            await log_channel.send(embed=admin_alert_embed)
    except Exception as e:
        # If the bot fails to send the Discord message, print this final warning to Render
        print(f"❌ FATAL: Could not send error report to IT channel. Reason: {e}")

# Load the Cogs ---
cogs_list = [
    "cogs.tickets",
    "cogs.admin"
]

for cog in cogs_list:
    bot.load_extension(cog)
    print(f"⚙️ Loaded Sub-module: {cog}")

if __name__ == "__main__":
    keep_alive()
    bot.run(DISCORD_TOKEN)