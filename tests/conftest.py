"""
Fixtures and utilities for testing the Discord bot.
"""

import pytest
from unittest.mock import Mock, AsyncMock, MagicMock
import discord
from datetime import datetime, timedelta

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from config import Config

@pytest.fixture
def mock_config():
    """Mock configuration for testing."""
    config = Config()
    config.REMINDER_THRESHOLD = 60
    config.REMINDER_INTERVAL = 60
    config.MAX_ROLE_MEMBERS = 20
    config.FIRESTORE_COLLECTION_REMINDERS = 'test_reminders'
    config.FIRESTORE_COLLECTION_STATISTICS = 'test_statistics'
    return config

@pytest.fixture
def mock_message():
    """Mock Discord message for testing."""
    message = Mock(spec=discord.Message)
    message.id = 123456789
    message.channel = Mock(spec=discord.TextChannel)
    message.channel.id = 987654321
    message.channel.name = "test-channel"
    message.channel.members = []
    message.author = Mock(spec=discord.Member)
    message.author.id = 111111111
    message.author.bot = False
    message.author.name = "test_user"
    message.content = "Hello @mentioned_user"
    message.mentions = []
    message.role_mentions = []
    message.mention_everyone = False
    message.reference = None
    message.reply = AsyncMock()
    return message

@pytest.fixture
def mock_user():
    """Mock Discord user for testing."""
    user = Mock(spec=discord.User)
    user.id = 222222222
    user.name = "mentioned_user"
    user.bot = False
    user.status = discord.Status.online
    return user

@pytest.fixture
def mock_member():
    """Mock Discord member for testing."""
    member = Mock(spec=discord.Member)
    member.id = 222222222
    member.name = "mentioned_user"
    member.bot = False
    member.status = discord.Status.online
    return member

@pytest.fixture
def mock_channel():
    """Mock Discord channel for testing."""
    channel = Mock(spec=discord.TextChannel)
    channel.id = 987654321
    channel.name = "test-channel"
    channel.guild = Mock(spec=discord.Guild)
    channel.guild.id = 555555555
    channel.send = AsyncMock()
    channel.fetch_message = AsyncMock()
    channel.members = []
    channel.permissions_for = Mock(return_value=Mock(read_messages=True))
    return channel

@pytest.fixture
def mock_guild():
    """Mock Discord guild for testing."""
    guild = Mock(spec=discord.Guild)
    guild.id = 555555555
    guild.name = "Test Guild"
    guild.get_member = Mock()
    return guild

@pytest.fixture
def mock_bot():
    """Mock Discord bot for testing."""
    bot = Mock(spec=discord.Client)
    bot.get_channel = Mock()
    bot.get_user = Mock()
    bot.process_commands = AsyncMock()
    return bot

@pytest.fixture
def mock_reaction_payload():
    """Mock Discord reaction payload for testing."""
    payload = Mock()
    payload.message_id = 123456789
    payload.user_id = 222222222
    payload.channel_id = 987654321
    return payload

@pytest.fixture
def sample_reminder_data():
    """Sample reminder data for testing."""
    return {
        'message_id': 123456789,
        'channel_id': 987654321,
        'mentioned_user_id': 222222222,
        'created_at': datetime.utcnow() - timedelta(hours=25)
    }

@pytest.fixture
def mock_firestore_client():
    """Mock Firestore client for testing."""
    mock_client = Mock()
    mock_collection = Mock()
    mock_doc_ref = Mock()
    mock_doc = Mock()
    
    # Setup collection chain
    mock_client.collection.return_value = mock_collection
    mock_collection.add = Mock()
    mock_collection.where.return_value = mock_collection
    mock_collection.limit.return_value = mock_collection
    mock_collection.stream.return_value = []
    mock_collection.document.return_value = mock_doc_ref
    
    # Setup document operations
    mock_doc_ref.set = Mock()
    mock_doc_ref.delete = Mock()
    mock_doc.to_dict.return_value = {}
    mock_doc.reference = mock_doc_ref
    
    return mock_client
