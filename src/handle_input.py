import logging
import discord
from db import get_pool, save_message, if_message_exists, delete_message
from config import config

logger = logging.getLogger(__name__)

async def register_db(message):
    # Collect all mentioned members
    all_members = []
    
    # Handle @everyone and @here mentions
    if message.mention_everyone:
        if "@everyone" in message.content:
            # Add all channel members for @everyone
            all_members.extend(message.channel.members)
            if len(all_members) > config.MAX_ROLE_MEMBERS:
                logger.warning(f"Message {message.id} has too many members for @everyone mention ({len(all_members)}). Skipping.")
                await message.reply(config.ROLE_SIZE_ERROR.format(limit=config.MAX_ROLE_MEMBERS))
                all_members = []  # Reset to avoid saving too many members
    
        elif "@here" in message.content:
            # Add only online members for @here
            for member in message.channel.members:
                if member.status == discord.Status.online:
                    all_members.append(member)
            if len(all_members) > config.MAX_ROLE_MEMBERS:
                logger.warning(f"Message {message.id} has too many members for @here mention ({len(all_members)}). Skipping.")
                await message.reply(config.ROLE_SIZE_ERROR.format(limit=config.MAX_ROLE_MEMBERS))
                all_members = []  # Reset to avoid saving too many members
        else:
            logger.warning(f"Unknown mention type in message {message.id}")
    
    # Handle role mentions
    for role in message.role_mentions:
        all_members.extend(role.members)
        if len(all_members) > config.MAX_ROLE_MEMBERS:
            logger.warning(f"Message {message.id} has too many members for role mention ({len(all_members)}). Skipping.")
            await message.reply(config.ROLE_SIZE_ERROR.format(limit=config.MAX_ROLE_MEMBERS))
            all_members = []  # Reset to avoid saving too many members

    # Handle individual user mentions
    all_members.extend(message.mentions)
    
    # Filter to only human users (not bots, not the message author) and remove duplicates
    all_mentioned_ids = set()
    human_mentions = []
    
    for user in all_members:
        if (not user.bot and 
            user != message.author and 
            user.id not in all_mentioned_ids):
            all_mentioned_ids.add(user.id)
            human_mentions.append(user)

    # If no human mentions found, exit early
    if not human_mentions:
        return

    try:
        pool = await get_pool()

        # Save the message for each mentioned user
        for mentioned_user in human_mentions:
            saved = await save_message(
                pool,
                message_id=message.id,
                channel_id=message.channel.id,
                mentioned_user_id=mentioned_user.id
            )
            if saved:
                logger.info(f"Saved waiting message for {mentioned_user.name} (ID: {saved['id']})")
            else:
                logger.warning(f"Failed to save message for {mentioned_user.name}")
    except Exception as e:
        logger.error(f"Failed to save message: {e}", exc_info=True)

async def observe_reply(message):
    if not message.reference:
        return # Ignore messages that are not replies
        
    try:
        pool = await get_pool()
        target_message_id = message.reference.message_id
        user_id = message.author.id
        
        if await if_message_exists(pool, target_message_id, user_id):
            await delete_message(pool, target_message_id, user_id)
            logger.info(f"Message {target_message_id} for user {user_id} deleted from database after reply")
        else:
            return # This means it was a reply but not to a message we are tracking
    except Exception as e:
        logger.error(f"Failed to process reply: {e}", exc_info=True)

async def observe_reaction(payload):
    try:
        pool = await get_pool()
        target_message_id = payload.message_id
        user_id = payload.user_id
        
        if await if_message_exists(pool, target_message_id, user_id):
            await delete_message(pool, target_message_id, user_id)
            logger.info(f"Message {target_message_id} for user {user_id} deleted from database after reaction")
        else:
            return # This means it was a reaction but not to a message we are tracking
    except Exception as e:
        logger.error(f"Failed to process reply: {e}", exc_info=True)