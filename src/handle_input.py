import logging
from typing import Any

import discord

from config import config
from db import FirestoreReminderCollection

reminder_db = FirestoreReminderCollection()

logger = logging.getLogger(__name__)


async def register_db(message: discord.Message) -> None:
    """
    Register mentioned users in a Discord message to the reminder database.

    Processes @everyone, @here, role mentions, and individual user mentions,
    filtering out bots and the message author. Also handles role size limits
    to prevent spam.

    Args:
        message (discord.Message): The Discord message containing mentions
    """
    # Collect all mentioned members
    all_members = []
    instant_role_size_error = False

    # Handle @everyone and @here mentions
    if message.mention_everyone:
        if "@everyone" in message.content:
            # Add all channel members for @everyone
            all_members.extend(message.channel.members)
            if len(all_members) > config.MAX_ROLE_MEMBERS:
                logger.warning(
                    f"Message {message.id} has too many members for @everyone mention ({len(all_members)}). Skipping."
                )
                if not instant_role_size_error:
                    instant_role_size_error = True
                    await message.reply(
                        config.ROLE_SIZE_ERROR.format(limit=config.MAX_ROLE_MEMBERS)
                    )
                all_members = []  # Reset to avoid saving too many members

        elif "@here" in message.content:
            # Add only online members for @here
            for member in message.channel.members:
                if member.status == discord.Status.online:
                    all_members.append(member)
            if len(all_members) > config.MAX_ROLE_MEMBERS:
                logger.warning(
                    f"Message {message.id} has too many members for @here mention ({len(all_members)}). Skipping."
                )
                if not instant_role_size_error:
                    instant_role_size_error = True
                    await message.reply(
                        config.ROLE_SIZE_ERROR.format(limit=config.MAX_ROLE_MEMBERS)
                    )
                all_members = []  # Reset to avoid saving too many members
        else:
            logger.warning(f"Unknown mention type in message {message.id}")

    # Handle role mentions
    for role in message.role_mentions:
        all_members.extend(role.members)
        if len(all_members) > config.MAX_ROLE_MEMBERS:
            logger.warning(
                f"Message {message.id} has too many members for role mention ({len(all_members)}). Skipping."
            )
            if not instant_role_size_error:
                instant_role_size_error = True
                await message.reply(
                    config.ROLE_SIZE_ERROR.format(limit=config.MAX_ROLE_MEMBERS)
                )
            all_members = []  # Reset to avoid saving too many members

    # Handle individual user mentions
    all_members.extend(message.mentions)

    # Filter to only human users (not bots, not the message author) and remove duplicates
    all_mentioned_ids = set()
    human_mentions = []

    for user in all_members:
        if not user.bot and user != message.author and user.id not in all_mentioned_ids:
            all_mentioned_ids.add(user.id)
            human_mentions.append(user)

    # If no human mentions found, exit early
    if not human_mentions:
        logging.info(f"No human mentions found in message {message.id}. Skipping.")
        return

    try:

        # Save the message for each mentioned user
        for mentioned_user in human_mentions:
            reminder_db.save_message(
                message_id=message.id,
                channel_id=message.channel.id,
                mentioned_user_id=mentioned_user.id,
            )
            logger.info(f"Saved waiting message for {mentioned_user.name}")
    except Exception as e:
        logger.error(f"Failed to save message: {e}", exc_info=True)


def observe_message(message: discord.Message) -> None:
    """
    Observe the channel of the message and if the channel is being tracked,
    remove corresponding reminders from the database.

    When a user sends any message in the same channel or thread where they were mentioned,
    this function removes the corresponding reminder from the database since they have responded.

    Args:
        message (discord.Message): The Discord message to check for responses in the channel/thread
    """

    try:
        channel_id = message.channel.id
        user_id = message.author.id

        matched_message_ids = reminder_db.search_reminders(
            channel_id, user_id
        )  # list of reminders
        if matched_message_ids:
            reminder_db.delete_messages_by_doc_ids(matched_message_ids)
            logger.info(
                f"{len(matched_message_ids)} reminders in {channel_id} for user {user_id} deleted from database after message in channel/thread"
            )
        else:
            return  # The coming messages is not in a channel we are tracking
    except Exception as e:
        logger.error(f"Failed to process message: {e}", exc_info=True)


def observe_reaction(payload: Any) -> None:
    """
    Observe Discord message reactions and remove corresponding reminders from the database.

    When a user reacts to a message they were mentioned in, this function
    removes the corresponding reminder from the database since they have acknowledged it.

    Args:
        payload (Any): The Discord reaction payload containing message and user information
    """
    try:
        target_message_id = payload.message_id
        user_id = payload.user_id

        if reminder_db.delete_message_by_message_and_user_id(target_message_id, user_id):
            logger.info(
                f"Message {target_message_id} for user {user_id} deleted from database after reaction"
            )
        else:
            return  # This means it was a reaction but not to a message we are tracking
    except Exception as e:
        logger.error(f"Failed to process reply: {e}", exc_info=True)

