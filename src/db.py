import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from datetime import datetime, timedelta, timezone
import logging

from config import Config
from google.cloud.firestore_v1.base_query import FieldFilter

# Set up logger
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
        self.collection_reminders = db.collection(Config.FIRESTORE_COLLECTION_REMINDERS)

    def _make_data(self, message_id, channel_id, mentioned_user_id):
        return {
            "message_id": message_id,
            "channel_id": channel_id,
            "mentioned_user_id": mentioned_user_id,
            "created_at": firestore.SERVER_TIMESTAMP
        }
    
    def save_message(self, message_id, channel_id, mentioned_user_id):
        data = self._make_data(message_id, channel_id, mentioned_user_id)
        self.collection_reminders.add(data)

    def if_message_exists(self, message_id, user_id):
        query = self.collection_reminders \
            .where(filter=FieldFilter("message_id", "==", message_id)) \
            .where(filter=FieldFilter("mentioned_user_id", "==", user_id)) \
            .limit(1)
        return bool(list(query.stream()))

    def delete_message(self, message_id, user_id):
        docs = self.collection_reminders \
            .where(filter=FieldFilter("message_id", "==", message_id)) \
            .where(filter=FieldFilter("mentioned_user_id", "==", user_id)) \
            .limit(1).stream()

        doc = next(iter(docs), None)
        if doc:
            doc.reference.delete()
        else:
            logger.error(f"Attempted to delete non-existing message: {message_id} for user: {user_id}")
            return False

    def get_expired_messages(self, threshold):
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
        self.collection_stats = db.collection(Config.FIRESTORE_COLLECTION_STATISTICS)

    def _make_data(self, metric, count):
        return {
            "platform": "discord",
            "metric": metric,
            "count": count,
            "updated_at": firestore.SERVER_TIMESTAMP
        }
    
    def update_guild_count(self, count):
        data = self._make_data("guild_count", count)
        self.collection_stats.document("discord_guilds").set(data, merge=True)

    def update_user_count(self, count):
        data = self._make_data("user_count", count)
        self.collection_stats.document("discord_users").set(data, merge=True)

    def increment_message_count(self):
        data = self._make_data("message_count", firestore.Increment(1))
        self.collection_stats.document("discord_messages").set(data, merge=True)
