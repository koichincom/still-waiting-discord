import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
import os
import asyncio
import time
import logging

from src import webserver
from src.db import get_pool, init_db, save_message
from src.config import config
from src.handle_input import register_db, observe_reply, observe_reaction
from src.reminder import send_reminders

load_dotenv()
token = os.getenv('DISCORD_TOKEN')

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Discord intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

# Bot initialization
bot = commands.Bot(command_prefix=config.COMMAND_PREFIX, intents=intents)

@bot.event
async def on_message(message):
    if message.author.bot:
        return # Ignore messages from bots
    
    await register_db(message)
    await observe_reply(message)
    await bot.process_commands(message)

@bot.event
async def on_raw_reaction_add(payload):
    user = bot.get_user(payload.user_id)
    if user and user.bot:
        return # Ignore reactions from bots
    
    # Get message to check if user is the author
    channel = bot.get_channel(payload.channel_id)
    message = await channel.fetch_message(payload.message_id)
    if payload.user_id == message.author.id:
        return # Ignore reactions from the author of the message

    await observe_reaction(payload)

@tasks.loop(seconds=config.REMINDER_INTERVAL)
async def send_reminders_task():
    await send_reminders(bot)

@send_reminders_task.before_loop
async def before_send_reminders():
    await bot.wait_until_ready()

@bot.event
async def on_ready():
    try:
        pool = await get_pool()
        await init_db(pool)
        await send_reminders_task.start()  # Updated to match new name
        logger.info(config.LOG_DB_INITIALIZED)
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}", exc_info=True)
    
    logger.info(config.LOG_BOT_READY.format(bot_name=bot.user.name))
    logger.info(config.LOG_HEALTH_SERVER.format(port=config.PORT))

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
    if isinstance(error, commands.CommandNotFound):
        logger.warning(f"Unknown command used: {ctx.message.content}")
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("You don't have permission to use this command.")
    elif isinstance(error, commands.BotMissingPermissions):
        await ctx.send("I don't have the required permissions to execute this command.")
    else:
        logger.error(f"Command error in {ctx.command}: {error}", exc_info=True)
        await ctx.send("An error occurred while processing your command.")

if __name__ == "__main__":
    webserver.keep_alive()

    try:
        bot.run(token)
    except KeyboardInterrupt:
        logger.info("Bot shutdown requested by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
