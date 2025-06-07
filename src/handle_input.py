import logging
from src.db import get_pool, save_message, if_message_exists, delete_message
from src.config import config

logger = logging.getLogger(__name__)

async def register_db(message):
    # Get members from role mentions
    human_role_members = []
    for role in message.role_mentions:
        for member in role.members:
            if not member.bot and member != message.author:
                human_role_members.append(member)
        if len(human_role_members) > config.MAX_ROLE_MEMBERS:
            logger.warning(f"Message {message.id} has too many role mentions ({len(human_role_members)}). Skipping.")
            await message.reply(config.ROLE_SIZE_ERROR.format(limit=config.MAX_ROLE_MEMBERS))
            human_role_members = []
    
    human_non_role_mentions = [user for user in message.mentions
                             if not user.bot and user != message.author]
    
    all_mentioned_ids = set()
    human_mentions = []
    
    # Collect unique human mentions from both role and non-role mentions
    for user in human_role_members + human_non_role_mentions:
        if user.id not in all_mentioned_ids:
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
                logger.info(config.LOG_MESSAGE_SAVED.format(
                    name=mentioned_user.name,
                    id=saved['id']
                ))
            else:
                logger.warning(config.LOG_MESSAGE_FAILED.format(
                    name=mentioned_user.name
                ))
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
            logger.info(config.LOG_REPLY_DELETED.format(message_id=target_message_id, user_id=user_id))
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
            logger.info(config.LOG_REACTION_DELETED.format(message_id=target_message_id, user_id=user_id))
        else:
            return # This means it was a reaction but not to a message we are tracking
    except Exception as e:
        logger.error(f"Failed to process reply: {e}", exc_info=True)