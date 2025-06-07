import logging
from datetime import datetime, timedelta
from src.db import get_pool, delete_message, has_message_expires
from src.config import config

logger = logging.getLogger(__name__)

async def send_reminders(bot):
    try:
        pool = await get_pool()
        threshold = config.REMINDER_THRESHOLD
        rows = await has_message_expires(pool, threshold)
        
        if not rows:
            logger.info(config.LOG_NO_REMINDERS)
            return
        
        for row in rows:
            try:
                # Extract data from the row
                message_id = row['message_id']
                channel_id = row['channel_id']
                mentioned_user_id = row['mentioned_user_id']
                
                # Turn IDs into appropriate types
                channel = bot.get_channel(channel_id)
                user = bot.get_user(mentioned_user_id)
                
                if channel and user:
                    # Get original message and reply to it
                    original_message = await channel.fetch_message(message_id)
                    await original_message.reply(config.REMINDER_MESSAGE.format(user_mention=user.mention))
                    logger.info(config.LOG_REMINDER_SENT.format(user_name=user.name, message_id=message_id))
                    
                    # Delete from DB after sending reminder
                    await delete_message(pool, message_id, mentioned_user_id)
                    logger.info(config.LOG_REMINDER_DELETED.format(message_id=message_id, user_name=user.name))
                else:
                    logger.warning(config.LOG_CHANNEL_USER_NOT_FOUND.format(channel_id=channel_id, user_id=mentioned_user_id))
                    
            except Exception as e:
                logger.error(config.LOG_REMINDER_FAILED.format(message_id=message_id, error=str(e)))
                
    except Exception as e:
        logger.error(f"Error in send_reminders: {e}")