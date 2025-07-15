
import os
import logging
from datetime import datetime, timedelta
from typing import Any

import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
import asyncio

from config import config
from db import FirestoreStatsCollection
from handle_input import observe_reaction, observe_reply, register_db
from reminder import send_reminders

load_dotenv(dotenv_path="secrets/.env")
token = os.getenv("DISCORD_TOKEN")

# Firestore DB instance
stats_db = FirestoreStatsCollection()

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

# Bot initialization
bot = commands.Bot(command_prefix=config.COMMAND_PREFIX, intents=intents)

@bot.event
async def on_message(message: discord.Message) -> None:
    """
    Handle incoming Discord messages.
    
    Processes messages to register mentioned users, observe replies,
    process bot commands, and increment message statistics.
    
    Args:
        message (discord.Message): The incoming Discord message
    """
    if message.author.bot:
        return  # Ignore messages from bots

    await register_db(message)
    observe_reply(message)
    await bot.process_commands(message)
    stats_db.increment_message_count()

@bot.event
async def on_raw_reaction_add(payload: discord.RawReactionActionEvent) -> None:
    """
    Handles the addition of a reaction to a message.
    """

    user = bot.get_user(payload.user_id)
    if user and user.bot:
        return  # Ignore reactions from bots

    # Get message to check if user is the author
    try:
        channel = bot.get_channel(payload.channel_id)
        if channel is None:
            logger.error(f"Channel {payload.channel_id} not found for reaction {payload.message_id}")
            return
        message = await channel.fetch_message(payload.message_id)
    except Exception as e:
        logger.error(f"Error fetching message {payload.message_id}: {e}")
        return

    if payload.user_id != message.author.id:
        observe_reaction(payload)

@tasks.loop(seconds=config.REMINDER_INTERVAL)
async def send_reminders_task() -> None:
    """
    Periodic task to send reminder messages to users who haven't responded.
    
    This task runs at intervals defined by REMINDER_INTERVAL and sends
    reminders to users who have been mentioned but haven't replied or reacted.
    """
    await send_reminders(bot)

@send_reminders_task.before_loop
async def before_send_reminders() -> None:
    """
    Setup function that runs before the send_reminders_task loop starts.
    
    If ALIGNED_REMINDER_INTERVAL_START is enabled and the reminder interval
    is a multiple of 3600 seconds, waits until the next full hour to start.
    """
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
async def user_count_update_task() -> None:
    """
    Periodic task to update the user count statistics in the database.
    
    Counts human members (excluding bots) across all guilds and updates
    the statistics in Firestore. Runs at intervals defined by USER_COUNT_UPDATE_INTERVAL.
    """
    try:
        total_members = 0
        
        for guild in bot.guilds:
            human_members = sum(1 for member in guild.members if not member.bot)
            total_members += human_members
        
        stats_db.update_user_count(total_members)
        logger.info(f"Updated user count (humans only): {total_members}")
    except Exception as e:
        logger.error(f"Failed to update user count: {e}", exc_info=True)

@user_count_update_task.before_loop
async def before_user_count_update() -> None:
    """
    Setup function that runs before the user_count_update_task loop starts.
    
    Logs that the user count update task has been initialized.
    """
    logger.info("User count update task initialized")

@bot.event
async def on_ready() -> None:
    """
    Called when the bot is ready and connected to Discord.
    """

    try:
        send_reminders_task.start()
        user_count_update_task.start()
        
        current_guilds = len(bot.guilds)
        stats_db.update_guild_count(current_guilds)
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}", exc_info=True)
        return

    logger.info(f"Bot is ready. Logged in as {bot.user.name}")
    logger.info(f"Health server running on port {config.PORT}")
    logger.info(f"Connected to {current_guilds} guild(s).")


# Error and connection events
@bot.event
async def on_disconnect() -> None:
    """
    Handle bot disconnection from Discord.
    
    Logs when the bot loses connection to Discord.
    """
    logger.info("Bot disconnected from Discord")


@bot.event
async def on_resumed() -> None:
    """
    Handle bot reconnection to Discord.
    
    Logs when the bot successfully resumes connection to Discord.
    """
    logger.info("Bot resumed connection to Discord")


@bot.event
async def on_error(event: str, *args: Any, **kwargs: Any) -> None:
    """
    Handle general Discord events errors.
    
    Logs errors that occur during Discord event processing.
    
    Args:
        event (str): The name of the event where the error occurred
        *args: Variable positional arguments from the event
        **kwargs: Variable keyword arguments from the event
    """
    logger.error(f"An error occurred in event {event}", exc_info=True)


@bot.event
async def on_command_error(ctx: commands.Context, error: Exception) -> None:
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
async def on_guild_join(guild: discord.Guild) -> None:
    """
    Called when the bot joins a new guild.
    """
    current_guilds = len(bot.guilds)
    try:
        stats_db.update_guild_count(current_guilds)
    except Exception as e:
        logger.error(f"Failed to update guild count: {e}")
    logger.info(f"Total guilds: {current_guilds}")

@bot.event
async def on_guild_remove(guild: discord.Guild) -> None:
    """
    Called when the bot is removed from a guild.
    """
    current_guilds = len(bot.guilds)
    try:
        stats_db.update_guild_count(current_guilds)
    except Exception as e:
        logger.error(f"Failed to update guild count: {e}")
    logger.info(f"Total guilds: {current_guilds}")

if __name__ == "__main__":
    try:
        bot.run(token)
    except KeyboardInterrupt:
        logger.info("Bot shutdown requested by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
