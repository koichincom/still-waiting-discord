"""
Tests for the database module (db.py).
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from google.cloud.firestore_v1.base_query import FieldFilter


class TestFirestoreReminderCollection:
    """Test cases for FirestoreReminderCollection."""

    @patch('db.db')
    def test_init(self, mock_db):
        """Test FirestoreReminderCollection initialization."""
        from db import FirestoreReminderCollection
        
        collection = FirestoreReminderCollection()
        assert collection.db == mock_db
        mock_db.collection.assert_called_once()

    @patch('db.db')
    def test_make_data(self, mock_db):
        """Test _make_data method creates correct data structure."""
        from db import FirestoreReminderCollection
        
        collection = FirestoreReminderCollection()
        data = collection._make_data(123, 456, 789)
        
        assert data['message_id'] == 123
        assert data['channel_id'] == 456
        assert data['mentioned_user_id'] == 789
        assert 'created_at' in data

    @patch('db.db')
    def test_save_message(self, mock_db):
        """Test save_message method."""
        from db import FirestoreReminderCollection
        
        mock_collection = Mock()
        mock_db.collection.return_value = mock_collection
        
        collection = FirestoreReminderCollection()
        collection.save_message(123, 456, 789)
        
        mock_collection.add.assert_called_once()
        call_args = mock_collection.add.call_args[0][0]
        assert call_args['message_id'] == 123
        assert call_args['channel_id'] == 456
        assert call_args['mentioned_user_id'] == 789

    @patch('db.db')
    def test_delete_message_by_message_and_user_id_success(self, mock_db):
        """Test delete_message_by_message_and_user_id returns True when message exists."""
        from db import FirestoreReminderCollection
        
        mock_collection = Mock()
        mock_query = Mock()
        mock_doc = Mock()
        mock_doc_ref = Mock()
        
        mock_db.collection.return_value = mock_collection
        mock_collection.where.return_value = mock_query
        mock_query.where.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.stream.return_value = [mock_doc]
        mock_doc.reference = mock_doc_ref
        
        collection = FirestoreReminderCollection()
        result = collection.delete_message_by_message_and_user_id(123, 789)
        
        mock_doc_ref.delete.assert_called_once()

    @patch('db.db')
    def test_delete_message_by_message_and_user_id_not_found(self, mock_db):
        """Test delete_message_by_message_and_user_id returns False when message doesn't exist."""
        from db import FirestoreReminderCollection
        
        mock_collection = Mock()
        mock_query = Mock()
        
        mock_db.collection.return_value = mock_collection
        mock_collection.where.return_value = mock_query
        mock_query.where.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.stream.return_value = []
        
        collection = FirestoreReminderCollection()
        result = collection.delete_message_by_message_and_user_id(123, 789)
        
        assert result is False

    @patch('db.db')
    def test_get_expired_messages(self, mock_db):
        """Test get_expired_messages returns correct data."""
        from db import FirestoreReminderCollection
        
        mock_collection = Mock()
        mock_query = Mock()
        mock_doc = Mock()
        
        mock_db.collection.return_value = mock_collection
        mock_collection.where.return_value = mock_query
        mock_query.stream.return_value = [mock_doc]
        mock_doc.to_dict.return_value = {'message_id': 123, 'user_id': 789}
        
        collection = FirestoreReminderCollection()
        result = collection.get_expired_messages(3600)
        
        assert len(result) == 1
        assert result[0]['message_id'] == 123
        assert result[0]['user_id'] == 789


class TestFirestoreStatsCollection:
    """Test cases for FirestoreStatsCollection."""

    @patch('db.db')
    def test_init(self, mock_db):
        """Test FirestoreStatsCollection initialization."""
        from db import FirestoreStatsCollection
        
        collection = FirestoreStatsCollection()
        assert collection.db == mock_db
        mock_db.collection.assert_called_once()

    @patch('db.db')
    def test_make_data(self, mock_db):
        """Test _make_data method creates correct data structure."""
        from db import FirestoreStatsCollection
        
        collection = FirestoreStatsCollection()
        data = collection._make_data("test_metric", 100)
        
        assert data['platform'] == "discord"
        assert data['metric'] == "test_metric"
        assert data['count'] == 100
        assert 'updated_at' in data

    @patch('db.db')
    def test_update_guild_count(self, mock_db):
        """Test update_guild_count method."""
        from db import FirestoreStatsCollection
        
        mock_collection = Mock()
        mock_doc_ref = Mock()
        
        mock_db.collection.return_value = mock_collection
        mock_collection.document.return_value = mock_doc_ref
        
        collection = FirestoreStatsCollection()
        collection.update_guild_count(50)
        
        mock_collection.document.assert_called_with("discord_guilds")
        mock_doc_ref.set.assert_called_once()

    @patch('db.db')
    def test_update_user_count(self, mock_db):
        """Test update_user_count method."""
        from db import FirestoreStatsCollection
        
        mock_collection = Mock()
        mock_doc_ref = Mock()
        
        mock_db.collection.return_value = mock_collection
        mock_collection.document.return_value = mock_doc_ref
        
        collection = FirestoreStatsCollection()
        collection.update_user_count(1000)
        
        mock_collection.document.assert_called_with("discord_users")
        mock_doc_ref.set.assert_called_once()

    @patch('db.db')
    def test_increment_message_count(self, mock_db):
        """Test increment_message_count method."""
        from db import FirestoreStatsCollection
        
        mock_collection = Mock()
        mock_doc_ref = Mock()
        
        mock_db.collection.return_value = mock_collection
        mock_collection.document.return_value = mock_doc_ref
        
        collection = FirestoreStatsCollection()
        collection.increment_message_count()
        
        mock_collection.document.assert_called_with("discord_messages")
        mock_doc_ref.set.assert_called_once()
