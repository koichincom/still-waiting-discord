import logging
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Any
import discord

from db import FirestoreReminderCollection
from config import config

logger = logging.getLogger(__name__)

async def send_reminders(bot: discord.Client) -> None:
    try:
        # All the ingredients for sending reminders
        threshold = config.REMINDER_THRESHOLD
        reminder_db = FirestoreReminderCollection()
        reminders = reminder_db.get_expired_messages(threshold)

        # Return early if there are no reminders to send
        if not reminders:
            return

        # Verify the channels, users, and messages in the reminders exist
        # Use set() just in case
        verified_reminders = []
        unique_reminders = set()

        invalid_channels = set()
        invalid_mentioned_users = set()
        invalid_messages = set()
        invalid_permissions = set()

        for i in range(len(reminders)):
            instant_invalid = False
            if not reminders[i]['channel_id'] in invalid_channels:
                if not reminders[i]['mentioned_user_id'] in invalid_mentioned_users:
                    if not reminders[i]['message_id'] in invalid_messages:
                        if not (reminders[i]['channel_id'], reminders[i]['mentioned_user_id']) in invalid_permissions:
                            # Obtain the channel, user, and message
                            channel = bot.get_channel(reminders[i]['channel_id'])
                            user = bot.get_user(reminders[i]['mentioned_user_id'])
                            try:
                                message = await channel.fetch_message(reminders[i]['message_id'])
                            except discord.NotFound:
                                message = None
                            except Exception as e:
                                logger.error(f"Error fetching message {reminders[i]['message_id']}: {e}")
                                message = None

                            # Append to invalid lists if each of the component is missing
                            if not channel:
                                invalid_channels.add(reminders[i]['channel_id'])
                                instant_invalid = True
                            if not user:
                                invalid_mentioned_users.add(reminders[i]['mentioned_user_id'])
                                instant_invalid = True
                            if not message:
                                invalid_messages.add(reminders[i]['message_id'])
                                instant_invalid = True

                            guild = channel.guild
                            member = guild.get_member(reminders[i]['mentioned_user_id'])
                            if not channel.permissions_for(member).read_messages:
                                invalid_permissions.add((reminders[i]['channel_id'], reminders[i]['mentioned_user_id']))
                                instant_invalid = True

                            # If all components are valid, append to verified reminders
                            if not instant_invalid:
                                tuple_reminder = (reminders[i]['message_id'], reminders[i]['mentioned_user_id'])
                                if tuple_reminder not in unique_reminders:
                                    unique_reminders.add(tuple_reminder)
                                    verified_reminders.append(reminders[i])
                            else:
                                reminder_db.delete_message(reminders[i]['message_id'], reminders[i]['mentioned_user_id'])
                                logger.info(f"Invalid reminder is ignored and deleted from DB: user {reminders[i]['mentioned_user_id']} / {reminders[i]['channel_id']} / {reminders[i]['message_id']}")

        # Group verified reminders by channel_id
        grouped_reminders = defaultdict(list)
        for verified_reminder in verified_reminders:
            grouped_reminders[verified_reminder['channel_id']].append(verified_reminder)
        grouped_verified_reminders = list(grouped_reminders.values())

        # Send reminders
        for group in grouped_verified_reminders:
            message = config.REMINDER_MESSAGE_START
            channel = bot.get_channel(group[0]['channel_id'])
            guild_id = channel.guild.id

            for item in group:
                user_mention = f"<@{item['mentioned_user_id']}>"
                message_link = f"https://discord.com/channels/{guild_id}/{channel.id}/{item['message_id']}"
                message += config.REMINDER_MESSAGE_MAIN.format(
                    user_mention=user_mention,
                    message_link=message_link
                )
                reminder_db.delete_message(item['message_id'], item['mentioned_user_id'])
                logger.info(f"Deleted reminder: message_id={item['message_id']}, mentioned_user_id={item['mentioned_user_id']}")
            
            message += config.REMINDER_MESSAGE_END
            try:
                await channel.send(message)
                logger.info(f"{len(group)} reminders sent to {channel.name} ({channel.id})")
            except Exception as e:
                logger.error(f"Failed to send reminders to {channel.name} ({channel.id}): {e}")

    except Exception as e:
        logger.error(f"Error in send_reminders(): {e}")