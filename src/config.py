from dataclasses import dataclass


@dataclass
class Config:
    # General
    COMMAND_PREFIX: str = "/"
    PORT: int = 8080
    MAX_ROLE_MEMBERS: int = 20  # Maximum number of role members to notify

    # Thresholds and intervals
    # The below are for testing (uncomment and adjust as needed)
    REMINDER_THRESHOLD: int = 5
    REMINDER_INTERVAL: int = 5
    # REMINDER_THRESHOLD: int = 60 * 60 * 24  # seconds (24 hours)
    # REMINDER_INTERVAL: int = 60 * 60  # seconds (1 hour) - how often to check for reminders
    ALIGNED_REMINDER_INTERVAL_START: bool = (
        True  # Whether to align the start of the reminder interval to the next hour. This only works if REMINDER_INTERVAL is a multiple of 3600 seconds.
    )
    USER_COUNT_UPDATE_INTERVAL: int = 60 * 60 * 24  # seconds (1 day)

    # Firestore
    FIRESTORE_COLLECTION_REMINDERS: str = "discord_reminders"
    FIRESTORE_COLLECTION_STATISTICS: str = "statistics"
    FIRESTORE_DOCUMENT_DISCORD_GUILDS: str = "discord_guilds"
    FIRESTORE_DOCUMENT_DISCORD_USERS: str = "discord_users"
    FIRESTORE_DOCUMENT_DISCORD_MESSAGES: str = "discord_messages"

    # Message templates
    REMINDER_MESSAGE_START: str = "## Still Waiting Reminders\n"
    REMINDER_MESSAGE_MAIN: str = (
        "- {user_mention} You haven't responded in {message_link}'s channel/thread\n"
    )
    REMINDER_MESSAGE_END: str = (
        "To avoid being reminded next time, please send a message in the channel/thread or leave a stamp directly on the mentioned message."
    )
    ROLE_SIZE_ERROR: str = (
        "The reminders will not be sent to these members even if they don't reply, since the number of the role members exceeds the limit of {limit}."
    )


config = Config()
