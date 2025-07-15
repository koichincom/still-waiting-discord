"""
Tests for the config module (config.py).
"""

import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


class TestConfig:
    """Test cases for Config class and configuration values."""

    def test_config_default_values(self):
        """Test that config has correct default values."""
        from config import Config
        
        config = Config()
        
        # General settings
        assert config.COMMAND_PREFIX == '/'
        assert config.PORT == 8080
        assert config.MAX_ROLE_MEMBERS == 20
        
        # Timing settings
        assert config.REMINDER_THRESHOLD == 60
        assert config.REMINDER_INTERVAL == 60
        assert config.ALIGNED_REMINDER_INTERVAL_START is True
        assert config.USER_COUNT_UPDATE_INTERVAL == 60 * 60 * 24
        
        # Firestore collection names
        assert config.FIRESTORE_COLLECTION_REMINDERS == 'reminders'
        assert config.FIRESTORE_COLLECTION_STATISTICS == 'statistics'
        assert config.FIRESTORE_DOCUMENT_DISCORD_GUILDS == 'discord_guilds'
        assert config.FIRESTORE_DOCUMENT_DISCORD_USERS == 'discord_users'
        assert config.FIRESTORE_DOCUMENT_DISCORD_MESSAGES == 'discord_messages'

    def test_config_message_templates(self):
        """Test that message templates are properly defined."""
        from config import Config
        
        config = Config()
        
        # Check message templates exist and are strings
        assert isinstance(config.REMINDER_MESSAGE_START, str)
        assert isinstance(config.REMINDER_MESSAGE_MAIN, str)
        assert isinstance(config.REMINDER_MESSAGE_END, str)
        assert isinstance(config.ROLE_SIZE_ERROR, str)
        
        # Check message templates have expected placeholders
        assert '{user_mention}' in config.REMINDER_MESSAGE_MAIN
        assert '{message_link}' in config.REMINDER_MESSAGE_MAIN
        assert '{limit}' in config.ROLE_SIZE_ERROR

    def test_config_singleton_instance(self):
        """Test that config singleton works correctly."""
        from config import config
        
        # Test that the singleton instance exists
        assert config is not None
        assert hasattr(config, 'COMMAND_PREFIX')
        assert hasattr(config, 'REMINDER_THRESHOLD')

    def test_config_dataclass_structure(self):
        """Test that Config is properly structured as a dataclass."""
        from config import Config
        import dataclasses
        
        # Check that Config is a dataclass
        assert dataclasses.is_dataclass(Config)
        
        # Check that all fields have types
        fields = dataclasses.fields(Config)
        assert len(fields) > 0
        
        for field in fields:
            assert field.type is not None

    def test_config_field_types(self):
        """Test that config fields have correct types."""
        from config import Config
        
        config = Config()
        
        # String fields
        assert isinstance(config.COMMAND_PREFIX, str)
        assert isinstance(config.FIRESTORE_COLLECTION_REMINDERS, str)
        assert isinstance(config.FIRESTORE_COLLECTION_STATISTICS, str)
        assert isinstance(config.REMINDER_MESSAGE_START, str)
        assert isinstance(config.REMINDER_MESSAGE_MAIN, str)
        assert isinstance(config.REMINDER_MESSAGE_END, str)
        assert isinstance(config.ROLE_SIZE_ERROR, str)
        
        # Integer fields
        assert isinstance(config.PORT, int)
        assert isinstance(config.MAX_ROLE_MEMBERS, int)
        assert isinstance(config.REMINDER_THRESHOLD, int)
        assert isinstance(config.REMINDER_INTERVAL, int)
        assert isinstance(config.USER_COUNT_UPDATE_INTERVAL, int)
        
        # Boolean fields
        assert isinstance(config.ALIGNED_REMINDER_INTERVAL_START, bool)

    def test_config_timing_values_are_positive(self):
        """Test that timing-related config values are positive."""
        from config import Config
        
        config = Config()
        
        assert config.REMINDER_THRESHOLD > 0
        assert config.REMINDER_INTERVAL > 0
        assert config.USER_COUNT_UPDATE_INTERVAL > 0
        assert config.MAX_ROLE_MEMBERS > 0
        assert config.PORT > 0

    def test_config_message_formatting(self):
        """Test that message templates can be formatted correctly."""
        from config import Config
        
        config = Config()
        
        # Test REMINDER_MESSAGE_MAIN formatting
        formatted_main = config.REMINDER_MESSAGE_MAIN.format(
            user_mention="<@123456789>",
            message_link="https://discord.com/channels/111/222/333"
        )
        assert "<@123456789>" in formatted_main
        assert "https://discord.com/channels/111/222/333" in formatted_main
        
        # Test ROLE_SIZE_ERROR formatting
        formatted_error = config.ROLE_SIZE_ERROR.format(limit=20)
        assert "20" in formatted_error

    def test_config_immutability_after_creation(self):
        """Test that config values can be modified (since it's not frozen)."""
        from config import Config
        
        config = Config()
        original_threshold = config.REMINDER_THRESHOLD
        
        # Should be able to modify values (useful for testing)
        config.REMINDER_THRESHOLD = 3600
        assert config.REMINDER_THRESHOLD == 3600
        
        # Restore original value
        config.REMINDER_THRESHOLD = original_threshold

    def test_config_production_vs_testing_values(self):
        """Test that config has reasonable values for both testing and production."""
        from config import Config
        
        config = Config()
        
        # Current values are set for testing (60 seconds)
        # This test documents that behavior
        assert config.REMINDER_THRESHOLD == 60  # Testing value
        assert config.REMINDER_INTERVAL == 60   # Testing value
        
        # Production values would be:
        # REMINDER_THRESHOLD = 60 * 60 * 24  # 24 hours
        # REMINDER_INTERVAL = 60 * 60        # 1 hour

    def test_config_firestore_collection_names_are_valid(self):
        """Test that Firestore collection names follow naming conventions."""
        from config import Config
        
        config = Config()
        
        # Collection names should be strings without special characters
        collections = [
            config.FIRESTORE_COLLECTION_REMINDERS,
            config.FIRESTORE_COLLECTION_STATISTICS
        ]
        
        for collection_name in collections:
            assert isinstance(collection_name, str)
            assert len(collection_name) > 0
            # Firestore collection names should not start with a period
            assert not collection_name.startswith('.')
            # Should not contain forward slashes
            assert '/' not in collection_name

    def test_config_document_names_are_valid(self):
        """Test that Firestore document names follow naming conventions."""
        from config import Config
        
        config = Config()
        
        document_names = [
            config.FIRESTORE_DOCUMENT_DISCORD_GUILDS,
            config.FIRESTORE_DOCUMENT_DISCORD_USERS,
            config.FIRESTORE_DOCUMENT_DISCORD_MESSAGES
        ]
        
        for doc_name in document_names:
            assert isinstance(doc_name, str)
            assert len(doc_name) > 0
            # Document names should not start with a period
            assert not doc_name.startswith('.')
            # Should not contain forward slashes
            assert '/' not in doc_name
