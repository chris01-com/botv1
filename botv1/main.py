import discord
from discord.ext import commands
import os
import asyncio
import json
from bot.commands import QuestCommands
from bot.json_database import JSONDatabase
from bot.quest_manager import QuestManager
from bot.config import ChannelConfig
from bot.user_stats import UserStatsManager

from flask import Flask
from threading import Thread
import logging

logging.basicConfig(level=logging.INFO)
logging.info("Bot is starting...")

# --- Flask ping server setup ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot and pinger are alive!"

def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)

def start_flask():
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()

# --- Discord bot setup ---

# Bot configuration
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.guild_messages = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Initialize components
database = None
quest_manager = None
channel_config = None
user_stats_manager = None

@bot.event
async def on_ready():
    """Bot startup event"""
    print(f'{bot.user} has connected to Discord!')
    print(f'Bot is in {len(bot.guilds)} guilds')

    # Sync slash commands
    try:
        synced = await bot.tree.sync()
        print(f'Synced {len(synced)} command(s)')
    except Exception as e:
        print(f'Failed to sync commands: {e}')

@bot.event
async def on_guild_join(guild):
    """Event when bot joins a new guild"""
    print(f'Joined guild: {guild.name} (ID: {guild.id})')

@bot.event
async def on_command_error(ctx, error):
    """Global error handler"""
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ You don't have permission to use this command.")
    elif isinstance(error, commands.CommandNotFound):
        pass  # Ignore command not found errors
    else:
        print(f'Error in command {ctx.command}: {error}')
        await ctx.send("❌ An error occurred while processing your command.")

# JSON database with auto-git commits

async def main():
    """Main async function"""
    global database, quest_manager, channel_config, user_stats_manager

    try:
        # Setup git repository for auto-commits
        import subprocess
        subprocess.run(['python', 'setup_git.py'], check=False)
        
        # Initialize JSON database
        database = JSONDatabase()
        await database.initialize()

        # Initialize other components
        quest_manager = QuestManager(database)
        channel_config = ChannelConfig(database)
        await channel_config.initialize()
        user_stats_manager = UserStatsManager(database)

        # Add the quest commands cog
        await bot.add_cog(QuestCommands(bot, quest_manager, channel_config, user_stats_manager))

        print("All components initialized successfully")

        # Get Discord token from environment
        discord_token = os.getenv('DISCORD_TOKEN')
        if not discord_token:
            raise ValueError("DISCORD_TOKEN environment variable is required!")

        # Start the bot
        await bot.start(discord_token)

    except Exception as e:
        print(f"Error during initialization: {e}")
        raise

if __name__ == "__main__":
    try:
        # Start Flask server
        start_flask()

        # Run the async main function and bot
        asyncio.run(main())

    except Exception as e:
        print(f"Critical error: {e}")