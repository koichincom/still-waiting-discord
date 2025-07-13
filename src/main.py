import logging
import os
import asyncio
from dotenv import load_dotenv
from config import config
from webserver import keep_alive
import discord
from discord.ext import commands, tasks
from datetime import datetime, timedelta

from db import get_pool, init_db_discord, init_db_stats, update_guild_count, update_user_count, increment_message_count
from handle_input import observe_reaction, observe_reply, register_db
from reminder import send_reminders

load_dotenv()
token = os.getenv("DISCORD_TOKEN")

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Discord intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True
intents.presences = True


# Bot initialization
bot = commands.Bot(command_prefix=config.COMMAND_PREFIX, intents=intents)


@bot.event
async def on_message(message): 
    if message.author.bot:
        return  # Ignore messages from bots

    await register_db(message)
    await observe_reply(message)
    await bot.process_commands(message)
    if hasattr(bot, 'db_pool'):
        await increment_message_count(bot.db_pool)

@bot.event
async def on_raw_reaction_add(payload):
    """
    Handles the addition of a reaction to a message.
    """

    user = bot.get_user(payload.user_id)
    if user and user.bot:
        return  # Ignore reactions from bots

    # Get message to check if user is the author
    channel = bot.get_channel(payload.channel_id)
    message = await channel.fetch_message(payload.message_id)
    if payload.user_id == message.author.id:
        return  # Ignore reactions from the author of the message

    await observe_reaction(payload)


@tasks.loop(seconds=config.REMINDER_INTERVAL)
async def send_reminders_task():
    await send_reminders(bot)

@send_reminders_task.before_loop
async def before_send_reminders():
    if config.REMINDER_INTERVAL % 3600 == 0 and config.ALIGNED_REMINDER_INTERVAL_START:
        now = datetime.now()
        next_hour = (now + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
        wait_seconds = (next_hour - now).total_seconds()
        logger.info(f"Waiting {wait_seconds:.0f} seconds until next full hour to start reminders loop.")
        await asyncio.sleep(wait_seconds)
        logger.info("Starting reminders task.")
    else:
        logger.info("Starting reminders task without waiting for the next hour.")

@tasks.loop(seconds=config.USER_COUNT_UPDATE_INTERVAL)
async def user_count_update_task():
    try:
        total_members = 0
        
        for guild in bot.guilds:
            human_members = sum(1 for member in guild.members if not member.bot)
            total_members += human_members
        
        if hasattr(bot, 'db_pool'):
            await update_user_count(bot.db_pool, total_members)
            logger.info(f"Updated user count (humans only): {total_members}")
    except Exception as e:
        logger.error(f"Failed to update user count: {e}", exc_info=True)

@user_count_update_task.before_loop
async def before_user_count_update():
    logger.info("User count update task initialized")

@bot.event
async def on_ready():
    """
    Called when the bot is ready and connected to Discord.
    """

    try:
        # Initialize global pool once
        bot.db_pool = await get_pool()
        await init_db_discord(bot.db_pool)
        await init_db_stats(bot.db_pool)

        send_reminders_task.start()
        user_count_update_task.start()
        
        current_guilds = len(bot.guilds)
        await update_guild_count(bot.db_pool, current_guilds)
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}", exc_info=True)
        return

    logger.info(f"Bot is ready. Logged in as {bot.user.name}")
    logger.info(f"Health server running on port {config.PORT}")
    logger.info(f"Connected to {current_guilds} guild(s).")


# Error and connection events
@bot.event
async def on_disconnect():
    logger.info("Bot disconnected from Discord")


@bot.event
async def on_resumed():
    logger.info("Bot resumed connection to Discord")


@bot.event
async def on_error(event, *args, **kwargs):
    logger.error(f"An error occurred in event {event}", exc_info=True)


@bot.event
async def on_command_error(ctx, error):
    """
    Handles errors that occur during command execution.
    """

    if isinstance(error, commands.CommandNotFound):
        logger.warning(f"Unknown command used: {ctx.message.content}")
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("You don't have permission to use this command.")
    elif isinstance(error, commands.BotMissingPermissions):
        await ctx.send("I don't have the required permissions to execute this command.")
    else:
        logger.error(f"Command error in {ctx.command}: {error}", exc_info=True)
        await ctx.send("An error occurred while processing your command.")

@bot.event
async def on_guild_join(guild):
    """
    Called when the bot joins a new guild.
    """
    current_guilds = len(bot.guilds)
    try:
        if hasattr(bot, 'db_pool'):
            await update_guild_count(bot.db_pool, current_guilds)
    except Exception as e:
        logger.error(f"Failed to update guild count: {e}")
    logger.info(f"Total guilds: {current_guilds}")

@bot.event
async def on_guild_remove(guild):
    """
    Called when the bot is removed from a guild.
    """
    current_guilds = len(bot.guilds)
    try:
        if hasattr(bot, 'db_pool'):
            await update_guild_count(bot.db_pool, current_guilds)
    except Exception as e:
        logger.error(f"Failed to update guild count: {e}")
    logger.info(f"Total guilds: {current_guilds}")

if __name__ == "__main__":
    keep_alive()

    try:
        bot.run(token)
    except KeyboardInterrupt:
        logger.info("Bot shutdown requested by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)

    # Caution: Discord.py is more like a framework and internally handles the event loop,
    # so we don't need to explicitly close the loop or the bot even though we are using asyncio.
