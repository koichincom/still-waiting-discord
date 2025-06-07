from dataclasses import dataclass

@dataclass
class Config:
    # Application settings
    COMMAND_PREFIX: str = '/'
    MAX_ROLE_MEMBERS: int = 1
    REMINDER_THRESHOLD: int = 60 * 60 * 24 # seconds (1 day)
    REMINDER_INTERVAL: int = 60 * 60  # seconds (1 hour)
    
    REMINDER_THRESHOLD: int = 10 # Testing purposes
    REMINDER_INTERVAL: int = 10 # Testing purposes

    # Database settings
    DB_TABLE_NAME: str = "waiting_messages"
    DB_MIN_POOL_SIZE: int = 1
    DB_MAX_POOL_SIZE: int = 5

    # Web server settings
    PORT: int = 8080

    # Message templates
    ROLE_SIZE_ERROR: str = "Number of role members to be notified is limited to {limit}. These members will not be notified."
    LOG_MESSAGE_SAVED: str = "Saved waiting message for {name} (ID: {id})"
    LOG_MESSAGE_FAILED: str = "Failed to save message for {name}"
    REMINDER_MESSAGE: str = "{user_mention} You haven't replied yet! We're STILL WAITING for your response!"
    
    # Log messages
    LOG_NO_REMINDERS: str = "No messages to remind at this time."
    LOG_REMINDER_SENT: str = "Sent reminder to {user_name} for message ID {message_id}."
    LOG_REMINDER_DELETED: str = "Deleted reminder message {message_id} for user {user_name} after sending."
    LOG_CHANNEL_USER_NOT_FOUND: str = "Could not find channel {channel_id} or user {user_id}"
    LOG_REMINDER_FAILED: str = "Failed to send reminder for message ID {message_id}: {error}"
    LOG_BOT_READY: str = "Bot is ready. Logged in as {bot_name}"
    LOG_HEALTH_SERVER: str = "Health server running on port {port}"
    LOG_DB_INITIALIZED: str = "Database initialized"
    LOG_REPLY_DELETED: str = "Message {message_id} for user {user_id} deleted from database after reply"
    LOG_REACTION_DELETED: str = "Message {message_id} for user {user_id} deleted from database after reaction"

config = Config()
