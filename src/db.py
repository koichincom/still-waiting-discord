import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from datetime import datetime, timedelta, timezone
import logging
from typing import Any, Dict, List

from config import config
from google.cloud.firestore_v1.base_query import FieldFilter

# Initialize logging
logger = logging.getLogger(__name__)

# Firebase Admin SDK initialization
cred = credentials.Certificate("secrets/firestore-credentials.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

class FirestoreReminderCollection:
    """
    Firestore collection for reminders.
    """
    def __init__(self):
        self.db = db
        self.collection_reminders = db.collection(config.FIRESTORE_COLLECTION_REMINDERS)

    def _make_data(self, message_id: int, channel_id: int, mentioned_user_id: int) -> Dict[str, Any]:
        """
        Create a data dictionary for storing reminder information in Firestore.
        
        Args:
            message_id (int): The Discord message ID
            channel_id (int): The Discord channel ID where the message was sent
            mentioned_user_id (int): The Discord user ID of the mentioned user
            
        Returns:
            Dict[str, Any]: A dictionary containing the reminder data with server timestamp
        """
        return {
            "message_id": message_id,
            "channel_id": channel_id,
            "mentioned_user_id": mentioned_user_id,
            "created_at": firestore.SERVER_TIMESTAMP
        }
    
    def save_message(self, message_id: int, channel_id: int, mentioned_user_id: int) -> None:
        """
        Save a reminder message to the Firestore database.
        
        Args:
            message_id (int): The Discord message ID
            channel_id (int): The Discord channel ID where the message was sent
            mentioned_user_id (int): The Discord user ID of the mentioned user
        """
        data = self._make_data(message_id, channel_id, mentioned_user_id)
        self.collection_reminders.add(data)

    def if_message_exists(self, message_id: int, user_id: int) -> bool:
        """
        Check if a reminder message exists for a specific user.
        
        Args:
            message_id (int): The Discord message ID to check
            user_id (int): The Discord user ID to check
            
        Returns:
            bool: True if the message exists in the database, False otherwise
        """
        query = self.collection_reminders \
            .where(filter=FieldFilter("message_id", "==", message_id)) \
            .where(filter=FieldFilter("mentioned_user_id", "==", user_id)) \
            .limit(1)
        return bool(list(query.stream()))

    def delete_message(self, message_id: int, user_id: int) -> bool:
        """
        Delete a reminder message from the database for a specific user.
        
        Args:
            message_id (int): The Discord message ID to delete
            user_id (int): The Discord user ID associated with the message
            
        Returns:
            bool: False if the message was not found, True otherwise
        """
        docs = self.collection_reminders \
            .where(filter=FieldFilter("message_id", "==", message_id)) \
            .where(filter=FieldFilter("mentioned_user_id", "==", user_id)) \
            .limit(1).stream()

        doc = next(docs, None)
        if doc:
            doc.reference.delete()
        else:
            logger.error(f"Attempted to delete non-existing message: {message_id} for user: {user_id}")
            return False

    def get_expired_messages(self, threshold: int) -> List[Dict[str, Any]]:
        """
        Retrieve messages that have exceeded the reminder threshold time.
        
        Args:
            threshold (int): The time threshold in seconds for considering messages expired
            
        Returns:
            List[Dict[str, Any]]: A list of expired message documents
        """
        expire_time = datetime.now(timezone.utc) - timedelta(seconds=threshold)
        docs = self.collection_reminders \
            .where(filter=FieldFilter("created_at", "<=", expire_time)) \
            .stream()
        return [doc.to_dict() for doc in docs]


class FirestoreStatsCollection:
    """
    Firestore collection for statistics.
    """
    def __init__(self):
        self.db = db
        self.collection_stats = db.collection(config.FIRESTORE_COLLECTION_STATISTICS)

    def _make_data(self, metric: str, count: int) -> Dict[str, Any]:
        """
        Create a data dictionary for storing statistics information in Firestore.
        
        Args:
            metric (str): The name of the metric being tracked
            count (int): The count value for the metric
            
        Returns:
            Dict[str, Any]: A dictionary containing the statistics data with server timestamp
        """
        return {
            "platform": "discord",
            "metric": metric,
            "count": count,
            "updated_at": firestore.SERVER_TIMESTAMP
        }
    
    def update_guild_count(self, count: int) -> None:
        """
        Update the guild count statistic in Firestore.
        
        Args:
            count (int): The current number of guilds the bot is in
        """
        data = self._make_data("guild_count", count)
        self.collection_stats.document("discord_guilds").set(data, merge=True)

    def update_user_count(self, count: int) -> None:
        """
        Update the user count statistic in Firestore.
        
        Args:
            count (int): The current number of users the bot can see
        """
        data = self._make_data("user_count", count)
        self.collection_stats.document("discord_users").set(data, merge=True)

    def increment_message_count(self) -> None:
        """
        Increment the message count statistic in Firestore by 1.
        """
        data = self._make_data("message_count", firestore.Increment(1))
        self.collection_stats.document("discord_messages").set(data, merge=True)
