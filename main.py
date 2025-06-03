import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
import os
import asyncio
import time
import logging
from datetime import datetime, timedelta
from collections import deque

import webserver

load_dotenv()
token = os.getenv('DISCORD_TOKEN')

# Load settings from .env file
WAIT_TIME = int(os.getenv('WAIT_TIME', '86400'))
ALLOW_REACTIONS = os.getenv('ALLOW_REACTIONS', 'true').lower() == 'true'
ENABLE_NOTIFY = os.getenv('ENABLE_NOTIFY', 'true').lower() == 'true'
ENABLE_DM_REMINDERS = os.getenv('ENABLE_DM_REMINDERS', 'true').lower() == 'true'
MAX_CONCURRENT_MONITORING = int(os.getenv('MAX_CONCURRENT_MONITORING', '1000'))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Track active monitoring tasks to prevent duplicates
active_monitoring = set()
# Track monitoring start times for cleanup
monitoring_start_times = {}

# Message send queue for rate limiting
message_queue = deque()
last_message_time = 0

# Periodic cleanup task
@tasks.loop(minutes=30)
async def cleanup_task():
    """Clean up stale monitoring entries every 30 minutes"""
    current_time = time.time()
    stale_keys = []
    
    for key, start_time in monitoring_start_times.items():
        # Remove monitoring entries that are older than WAIT_TIME + 1 hour buffer
        if current_time - start_time > WAIT_TIME + 3600:
            stale_keys.append(key)
    
    for key in stale_keys:
        active_monitoring.discard(key)
        monitoring_start_times.pop(key, None)
    
    if stale_keys:
        logger.info(f"Cleaned up {len(stale_keys)} stale monitoring entries")

@cleanup_task.before_loop
async def before_cleanup():
    await bot.wait_until_ready()

async def rate_limited_send(channel, content):
    """Send message with rate limiting to prevent Discord API limits"""
    global last_message_time
    current_time = time.time()
    
    # Ensure at least 1 second between messages
    time_since_last = current_time - last_message_time
    if time_since_last < 1.0:
        await asyncio.sleep(1.0 - time_since_last)
    
    try:
        await channel.send(content)
        last_message_time = time.time()
        return True
    except discord.Forbidden:
        logger.error(f"No permission to send message in channel {channel.name}")
        return False
    except discord.HTTPException as e:
        logger.error(f"Failed to send message: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error sending message: {e}")
        return False

async def send_dm_reminder(user, original_message, channel):
    """Send a DM reminder to the user"""
    try:
        dm_content = (
            f"Hi {user.name}! You haven't responded to a message in #{channel.name}.\n"
            f"Original message: {original_message.jump_url}\n"
            f"Please consider replying when you have a chance."
        )
        await user.send(dm_content)
        logger.info(f"DM reminder sent to {user.name}")
        return True
    except discord.Forbidden:
        logger.warning(f"Cannot send DM to {user.name} - DMs disabled or blocked")
        return False
    except discord.HTTPException as e:
        logger.error(f"Failed to send DM to {user.name}: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error sending DM to {user.name}: {e}")
        return False

@bot.event
async def on_ready():
    bot_status['is_ready'] = True
    bot_status['last_activity'] = time.time()
    logger.info(f"Bot is ready. Logged in as {bot.user.name}")
    logger.info(f"Settings from .env - Wait time: {WAIT_TIME} seconds")
    logger.info(f"Reactions allowed: {ALLOW_REACTIONS}")
    logger.info(f"Monitoring enabled: {ENABLE_NOTIFY}")
    logger.info(f"DM reminders enabled: {ENABLE_DM_REMINDERS}")
    logger.info(f"Max concurrent monitoring: {MAX_CONCURRENT_MONITORING}")
    logger.info(f"Health server running on port {PORT}")
    
    # Start periodic cleanup task
    cleanup_task.start()

async def monitor_user_response(channel, target_user, original_message):
    """
    Monitor a user's response (message or reaction) to the original message.
    """
    # Create unique monitoring key
    monitoring_key = (channel.id, target_user.id, original_message.id)
    
    # Check if already monitoring this combination
    if monitoring_key in active_monitoring:
        logger.info(f"Already monitoring {target_user.name} for message {original_message.id}, skipping duplicate")
        return

    # Check if we've reached max concurrent monitoring limit
    if len(active_monitoring) >= MAX_CONCURRENT_MONITORING:
        logger.warning(f"Maximum concurrent monitoring limit ({MAX_CONCURRENT_MONITORING}) reached, skipping new monitoring")
        return

    # Add to active monitoring
    active_monitoring.add(monitoring_key)
    monitoring_start_times[monitoring_key] = time.time()
    
    try:
        start_time = time.time()
        logger.info(f"Starting monitoring for {target_user.name} (ID: {target_user.id}) in #{channel.name}, wait: {WAIT_TIME}s for message {original_message.id}")

        def check_reply(message):
            # Only consider messages after monitoring started
            message_time = message.created_at.timestamp()
            is_after_start = message_time > start_time
            is_correct_user = message.author == target_user
            is_correct_channel = message.channel == channel
            is_match = is_correct_user and is_correct_channel and is_after_start
            
            if is_match:
                logger.info(f"Response detected from {target_user.name}: '{message.content[:50]}...'")
            return is_match

        def check_reaction(reaction, user):
            # Only consider reactions after monitoring started
            reaction_time = time.time()
            is_after_start = reaction_time > start_time
            is_correct_user = user == target_user
            is_correct_message = reaction.message.id == original_message.id
            is_match = is_correct_user and is_correct_message and is_after_start
            
            if is_match:
                logger.info(f"Reaction detected from {target_user.name}: {reaction.emoji}")
            return is_match

        # Start monitoring based on global settings
        try:
            if ALLOW_REACTIONS:
                done, pending = await asyncio.wait([
                    asyncio.create_task(bot.wait_for("message", check=check_reply)),
                    asyncio.create_task(bot.wait_for("reaction_add", check=check_reaction))
                ], timeout=WAIT_TIME, return_when=asyncio.FIRST_COMPLETED)

                # Cancel pending tasks properly
                for task in pending:
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass

                # If no tasks completed (timeout), send reminder
                if not done:
                    logger.info(f"Timeout reached, sending reminder to {target_user.name}")
                    # Send channel reminder first
                    channel_sent = await rate_limited_send(
                        channel,
                        f"{target_user.mention}, you did not respond to [this message]({original_message.jump_url}). Please reply!"
                    )
                    
                    # Also send DM reminder if enabled
                    dm_sent = False
                    if ENABLE_DM_REMINDERS:
                        dm_sent = await send_dm_reminder(target_user, original_message, channel)
                    
                    if channel_sent and dm_sent:
                        logger.info(f"Both channel and DM reminders sent to {target_user.name}")
                    elif channel_sent and ENABLE_DM_REMINDERS:
                        logger.info(f"Only channel reminder sent to {target_user.name} (DM failed)")
                    elif channel_sent:
                        logger.info(f"Channel reminder sent to {target_user.name} (DM disabled)")
                    elif dm_sent:
                        logger.info(f"Only DM reminder sent to {target_user.name} (channel failed)")
                    else:
                        logger.warning(f"All reminder methods failed for {target_user.name}")
                else:
                    logger.info(f"Response detected from {target_user.name}, monitoring stopped")
            else:
                try:
                    await bot.wait_for("message", timeout=WAIT_TIME, check=check_reply)
                    logger.info(f"Response detected from {target_user.name}, monitoring stopped")
                except asyncio.TimeoutError:
                    logger.info(f"Timeout reached, sending reminder to {target_user.name}")
                    # Send channel reminder first
                    channel_sent = await rate_limited_send(
                        channel,
                        f"{target_user.mention}, you did not respond to [this message]({original_message.jump_url}). Please reply!"
                    )
                    
                    # Also send DM reminder if enabled
                    dm_sent = False
                    if ENABLE_DM_REMINDERS:
                        dm_sent = await send_dm_reminder(target_user, original_message, channel)
                    
                    if channel_sent and dm_sent:
                        logger.info(f"Both channel and DM reminders sent to {target_user.name}")
                    elif channel_sent and ENABLE_DM_REMINDERS:
                        logger.info(f"Only channel reminder sent to {target_user.name} (DM failed)")
                    elif channel_sent:
                        logger.info(f"Channel reminder sent to {target_user.name} (DM disabled)")
                    elif dm_sent:
                        logger.info(f"Only DM reminder sent to {target_user.name} (channel failed)")
                    else:
                        logger.warning(f"All reminder methods failed for {target_user.name}")
        except asyncio.TimeoutError:
            logger.info(f"Timeout reached, sending reminder to {target_user.name}")
            # Send channel reminder first
            channel_sent = await rate_limited_send(
                channel,
                f"{target_user.mention}, you did not respond to [this message]({original_message.jump_url}). Please reply!"
            )
            
            # Also send DM reminder if enabled
            dm_sent = False
            if ENABLE_DM_REMINDERS:
                dm_sent = await send_dm_reminder(target_user, original_message, channel)
            
            if channel_sent and dm_sent:
                logger.info(f"Both channel and DM reminders sent to {target_user.name}")
            elif channel_sent and ENABLE_DM_REMINDERS:
                logger.info(f"Only channel reminder sent to {target_user.name} (DM failed)")
            elif channel_sent:
                logger.info(f"Channel reminder sent to {target_user.name} (DM disabled)")
            elif dm_sent:
                logger.info(f"Only DM reminder sent to {target_user.name} (channel failed)")
            else:
                logger.warning(f"All reminder methods failed for {target_user.name}")
    except Exception as e:
        logger.error(f"Error in monitoring {target_user.name}: {e}")
    finally:
        # Always remove from active monitoring when done
        active_monitoring.discard(monitoring_key)
        monitoring_start_times.pop(monitoring_key, None)
        logger.info(f"Monitoring ended for {target_user.name} on message {original_message.id}")

@bot.event
async def on_message(message):
    logger.debug(f"Message received from {message.author.name}: {message.content[:50]}...")
    
    # Ignore bot messages
    if message.author.bot:
        logger.debug("Ignoring bot message")
        return
    
    # Check if monitoring is globally disabled
    if not ENABLE_NOTIFY:
        logger.debug("Monitoring disabled via ENABLE_NOTIFY")
        return
    
    # Process commands first
    await bot.process_commands(message)

    # Handle replies first, then exit to prevent double-handling
    if message.reference and message.reference.message_id:
        logger.debug(f"Found reply to message {message.reference.message_id}")
        try:
            # Fetch the replied message
            replied_message = await message.channel.fetch_message(message.reference.message_id)
            replied_user = replied_message.author
            # Ignore self-replies or bot replies
            if replied_user == message.author or replied_user.bot:
                logger.debug("Ignoring self or bot reply")
                return
            # Only proceed if the reply actually mentioned (not suppressed)
            if replied_user not in message.mentions:
                logger.debug("Reply did not ping the user (mention suppressed), skipping monitoring")
                return
            logger.info(f"Starting monitoring for reply target {replied_user.name}")
            asyncio.create_task(monitor_user_response(message.channel, replied_user, message))
        except discord.NotFound:
            logger.warning("Reply target message not found")
        except Exception as e:
            logger.error(f"Error handling reply: {e}")
        return

    # If there are user mentions
    if message.mentions:
        logger.debug(f"Found {len(message.mentions)} user mentions")
        for mentioned_user in message.mentions:
            # Ignore self-mentions
            if mentioned_user == message.author:
                logger.debug("Ignoring self-mention")
                continue
            # Ignore bot mentions
            if mentioned_user.bot:
                logger.debug("Ignoring bot mention")
                continue
            
            logger.info(f"Starting monitoring for {mentioned_user.name}")
            # Start monitoring response
            asyncio.create_task(monitor_user_response(message.channel, mentioned_user, message))
    
    # If there are role mentions
    if message.role_mentions:
        logger.debug(f"Found {len(message.role_mentions)} role mentions")
        for role in message.role_mentions:
            # Get all members except the sender (excluding bots)
            targets = [member for member in role.members if member != message.author and not member.bot]
            logger.info(f"Role {role.name} has {len(targets)} target members")
            
            # Check if role mention would exceed monitoring limit
            if len(active_monitoring) + len(targets) > MAX_CONCURRENT_MONITORING:
                logger.warning(f"Role mention would exceed monitoring limit. Skipping {role.name}")
                continue
            
            # Monitor each member individually
            for member in targets:
                logger.info(f"Starting monitoring for role member {member.name}")
                asyncio.create_task(monitor_user_response(message.channel, member, message))

@bot.command(name='my_reminders')
async def my_reminders(ctx):
    """Show user's active reminders"""
    user_reminders = []
    current_time = time.time()
    
    for (channel_id, user_id, message_id), start_time in monitoring_start_times.items():
        if user_id == ctx.author.id:
            remaining_time = WAIT_TIME - (current_time - start_time)
            if remaining_time > 0:
                try:
                    channel = bot.get_channel(channel_id)
                    if channel:
                        message = await channel.fetch_message(message_id)
                        user_reminders.append({
                            'channel': channel.name,
                            'message_url': message.jump_url,
                            'remaining_minutes': int(remaining_time / 60),
                            'content': message.content[:50] + '...' if len(message.content) > 50 else message.content
                        })
                except Exception as e:
                    logger.warning(f"Failed to fetch reminder info: {e}")
    
    if not user_reminders:
        await ctx.send("You have no active reminders waiting for responses.")
        return
    
    embed = discord.Embed(title="Your Active Reminders", color=0x3498db)
    for reminder in user_reminders[:10]:  # Limit to 10 reminders
        embed.add_field(
            name=f"#{reminder['channel']} - {reminder['remaining_minutes']} minutes left",
            value=f"[{reminder['content']}]({reminder['message_url']})",
            inline=False
        )
    
    if len(user_reminders) > 10:
        embed.set_footer(text=f"Showing 10 of {len(user_reminders)} active reminders")
    
    await ctx.send(embed=embed)

@bot.command(name='status')
async def status(ctx):
    """Show bot status and statistics"""
    embed = discord.Embed(title="Still Waiting - Bot Status", color=0x2ecc71)
    embed.add_field(name="Active Monitoring", value=len(active_monitoring), inline=True)
    embed.add_field(name="Wait Time", value=f"{WAIT_TIME / 3600:.1f} hours", inline=True)
    embed.add_field(name="Max Concurrent", value=MAX_CONCURRENT_MONITORING, inline=True)
    embed.add_field(name="Reactions Enabled", value="✅" if ALLOW_REACTIONS else "❌", inline=True)
    embed.add_field(name="Monitoring Enabled", value="✅" if ENABLE_NOTIFY else "❌", inline=True)
    embed.add_field(name="DM Reminders", value="✅" if ENABLE_DM_REMINDERS else "❌", inline=True)
    embed.add_field(name="Servers", value=len(bot.guilds), inline=True)
    
    await ctx.send(embed=embed)

# Error handling
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
        return  # Ignore unknown commands
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