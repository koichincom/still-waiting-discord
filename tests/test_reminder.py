"""
Tests for the reminder module (reminder.py).
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta
import discord
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


class TestSendReminders:
    """Test cases for send_reminders function."""

    @patch('reminder.config')
    @patch('reminder.FirestoreReminderCollection')
    @pytest.mark.asyncio
    async def test_send_reminders_no_expired_messages(self, mock_db_class, mock_config):
        """Test send_reminders when no expired messages exist."""
        from reminder import send_reminders
        
        mock_config.REMINDER_THRESHOLD = 3600
        mock_db = Mock()
        mock_db_class.return_value = mock_db
        mock_db.get_expired_messages.return_value = []
        
        bot = Mock(spec=discord.Client)
        
        await send_reminders(bot)
        
        mock_db.get_expired_messages.assert_called_once_with(3600)
        bot.get_channel.assert_not_called()

    @patch('reminder.config')
    @patch('reminder.FirestoreReminderCollection')
    @pytest.mark.asyncio
    async def test_send_reminders_single_valid_reminder(self, mock_db_class, mock_config):
        """Test send_reminders with a single valid reminder."""
        from reminder import send_reminders
        
        mock_config.REMINDER_THRESHOLD = 3600
        mock_config.REMINDER_MESSAGE_START = "## Reminders\n"
        mock_config.REMINDER_MESSAGE_MAIN = "- {user_mention} reply to {message_link}\n"
        mock_config.REMINDER_MESSAGE_END = "Please reply!"
        
        mock_db = Mock()
        mock_db_class.return_value = mock_db
        
        # Mock expired message
        expired_message = {
            'message_id': 123456789,
            'channel_id': 987654321,
            'mentioned_user_id': 222222222
        }
        mock_db.get_expired_messages.return_value = [expired_message]
        
        # Mock bot and Discord objects
        bot = Mock(spec=discord.Client)
        
        # Mock channel
        channel = Mock(spec=discord.TextChannel)
        channel.id = 987654321
        channel.name = "test-channel"
        channel.guild = Mock(spec=discord.Guild)
        channel.guild.id = 555555555
        channel.send = AsyncMock()
        bot.get_channel.return_value = channel
        
        # Mock user
        user = Mock(spec=discord.User)
        user.id = 222222222
        user.name = "test_user"
        bot.get_user.return_value = user
        
        # Mock message
        message = Mock(spec=discord.Message)
        message.id = 123456789
        channel.fetch_message = AsyncMock(return_value=message)
        
        # Mock member permissions
        member = Mock(spec=discord.Member)
        member.id = 222222222
        channel.guild.get_member.return_value = member
        permissions = Mock()
        permissions.read_messages = True
        channel.permissions_for.return_value = permissions
        
        await send_reminders(bot)
        
        mock_db.get_expired_messages.assert_called_once_with(3600)
        bot.get_channel.assert_called_with(987654321)
        bot.get_user.assert_called_with(222222222)
        channel.fetch_message.assert_called_with(123456789)
        channel.send.assert_called_once()
        mock_db.delete_message_by_message_and_user_id.assert_called_once_with(123456789, 222222222)

    @patch('reminder.config')
    @patch('reminder.FirestoreReminderCollection')
    @patch('reminder.logger')
    @pytest.mark.asyncio
    async def test_send_reminders_invalid_channel(self, mock_logger, mock_db_class, mock_config):
        """Test send_reminders with invalid channel."""
        from reminder import send_reminders
        
        mock_config.REMINDER_THRESHOLD = 3600
        
        mock_db = Mock()
        mock_db_class.return_value = mock_db
        
        expired_message = {
            'message_id': 123456789,
            'channel_id': 987654321,
            'mentioned_user_id': 222222222
        }
        mock_db.get_expired_messages.return_value = [expired_message]
        
        bot = Mock(spec=discord.Client)
        bot.get_channel.return_value = None  # Channel not found
        bot.get_user.return_value = Mock(spec=discord.User)
        
        await send_reminders(bot)
        
        mock_db.delete_message_by_message_and_user_id.assert_called_once_with(123456789, 222222222)

    @patch('reminder.config')
    @patch('reminder.FirestoreReminderCollection')
    @patch('reminder.logger')
    @pytest.mark.asyncio
    async def test_send_reminders_invalid_user(self, mock_logger, mock_db_class, mock_config):
        """Test send_reminders with invalid user."""
        from reminder import send_reminders
        
        mock_config.REMINDER_THRESHOLD = 3600
        
        mock_db = Mock()
        mock_db_class.return_value = mock_db
        
        expired_message = {
            'message_id': 123456789,
            'channel_id': 987654321,
            'mentioned_user_id': 222222222
        }
        mock_db.get_expired_messages.return_value = [expired_message]
        
        bot = Mock(spec=discord.Client)
        bot.get_channel.return_value = Mock(spec=discord.TextChannel)
        bot.get_user.return_value = None  # User not found
        
        await send_reminders(bot)
        
        mock_db.delete_message_by_message_and_user_id.assert_called_once_with(123456789, 222222222)

    @patch('reminder.config')
    @patch('reminder.FirestoreReminderCollection')
    @pytest.mark.asyncio
    async def test_send_reminders_message_not_found(self, mock_db_class, mock_config):
        """Test send_reminders when message is not found."""
        from reminder import send_reminders
        
        mock_config.REMINDER_THRESHOLD = 3600
        
        mock_db = Mock()
        mock_db_class.return_value = mock_db
        
        expired_message = {
            'message_id': 123456789,
            'channel_id': 987654321,
            'mentioned_user_id': 222222222
        }
        mock_db.get_expired_messages.return_value = [expired_message]
        
        bot = Mock(spec=discord.Client)
        
        channel = Mock(spec=discord.TextChannel)
        bot.get_channel.return_value = channel
        
        user = Mock(spec=discord.User)
        bot.get_user.return_value = user
        
        # Message not found
        channel.fetch_message = AsyncMock(side_effect=discord.NotFound(Mock(), "Message not found"))
        
        await send_reminders(bot)
        
        mock_db.delete_message_by_message_and_user_id.assert_called_once_with(123456789, 222222222)

    @patch('reminder.config')
    @patch('reminder.FirestoreReminderCollection')
    @pytest.mark.asyncio
    async def test_send_reminders_no_read_permissions(self, mock_db_class, mock_config):
        """Test send_reminders when user has no read permissions."""
        from reminder import send_reminders
        
        mock_config.REMINDER_THRESHOLD = 3600
        
        mock_db = Mock()
        mock_db_class.return_value = mock_db
        
        expired_message = {
            'message_id': 123456789,
            'channel_id': 987654321,
            'mentioned_user_id': 222222222
        }
        mock_db.get_expired_messages.return_value = [expired_message]
        
        bot = Mock(spec=discord.Client)
        
        # Mock channel
        channel = Mock(spec=discord.TextChannel)
        channel.guild = Mock(spec=discord.Guild)
        bot.get_channel.return_value = channel
        
        # Mock user
        user = Mock(spec=discord.User)
        bot.get_user.return_value = user
        
        # Mock message
        message = Mock(spec=discord.Message)
        channel.fetch_message = AsyncMock(return_value=message)
        
        # Mock member with no read permissions
        member = Mock(spec=discord.Member)
        channel.guild.get_member.return_value = member
        permissions = Mock()
        permissions.read_messages = False
        channel.permissions_for.return_value = permissions
        
        await send_reminders(bot)
        
        mock_db.delete_message_by_message_and_user_id.assert_called_once_with(123456789, 222222222)

    @patch('reminder.config')
    @patch('reminder.FirestoreReminderCollection')
    @pytest.mark.asyncio
    async def test_send_reminders_multiple_reminders_same_channel(self, mock_db_class, mock_config):
        """Test send_reminders with multiple reminders in same channel."""
        from reminder import send_reminders
        
        mock_config.REMINDER_THRESHOLD = 3600
        mock_config.REMINDER_MESSAGE_START = "## Reminders\n"
        mock_config.REMINDER_MESSAGE_MAIN = "- {user_mention} reply to {message_link}\n"
        mock_config.REMINDER_MESSAGE_END = "Please reply!"
        
        mock_db = Mock()
        mock_db_class.return_value = mock_db
        
        # Mock multiple expired messages in same channel
        expired_messages = [
            {
                'message_id': 123456789,
                'channel_id': 987654321,
                'mentioned_user_id': 222222222
            },
            {
                'message_id': 123456790,
                'channel_id': 987654321,
                'mentioned_user_id': 333333333
            }
        ]
        mock_db.get_expired_messages.return_value = expired_messages
        
        bot = Mock(spec=discord.Client)
        
        # Mock channel
        channel = Mock(spec=discord.TextChannel)
        channel.id = 987654321
        channel.guild = Mock(spec=discord.Guild)
        channel.guild.id = 555555555
        channel.send = AsyncMock()
        bot.get_channel.return_value = channel
        
        # Mock users
        def get_user_side_effect(user_id):
            user = Mock(spec=discord.User)
            user.id = user_id
            return user
        
        bot.get_user.side_effect = get_user_side_effect
        
        # Mock messages
        def fetch_message_side_effect(message_id):
            message = Mock(spec=discord.Message)
            message.id = message_id
            return message
        
        channel.fetch_message.side_effect = fetch_message_side_effect
        
        # Mock member permissions
        def get_member_side_effect(user_id):
            member = Mock(spec=discord.Member)
            member.id = user_id
            return member
        
        channel.guild.get_member.side_effect = get_member_side_effect
        permissions = Mock()
        permissions.read_messages = True
        channel.permissions_for.return_value = permissions
        
        await send_reminders(bot)
        
        # Should send one message containing both reminders
        channel.send.assert_called_once()
        assert mock_db.delete_message_by_message_and_user_id.call_count == 2

    @patch('reminder.config')
    @patch('reminder.FirestoreReminderCollection')
    @patch('reminder.logger')
    @pytest.mark.asyncio
    async def test_send_reminders_send_message_error(self, mock_logger, mock_db_class, mock_config):
        """Test send_reminders when sending message fails."""
        from reminder import send_reminders
        
        mock_config.REMINDER_THRESHOLD = 3600
        mock_config.REMINDER_MESSAGE_START = "## Reminders\n"
        mock_config.REMINDER_MESSAGE_MAIN = "- {user_mention} reply to {message_link}\n"
        mock_config.REMINDER_MESSAGE_END = "Please reply!"
        
        mock_db = Mock()
        mock_db_class.return_value = mock_db
        
        expired_message = {
            'message_id': 123456789,
            'channel_id': 987654321,
            'mentioned_user_id': 222222222
        }
        mock_db.get_expired_messages.return_value = [expired_message]
        
        bot = Mock(spec=discord.Client)
        
        # Mock channel that fails to send
        channel = Mock(spec=discord.TextChannel)
        channel.id = 987654321
        channel.name = "test-channel"
        channel.guild = Mock(spec=discord.Guild)
        channel.guild.id = 555555555
        channel.send = AsyncMock(side_effect=Exception("Send failed"))
        bot.get_channel.return_value = channel
        
        # Mock user
        user = Mock(spec=discord.User)
        bot.get_user.return_value = user
        
        # Mock message
        message = Mock(spec=discord.Message)
        channel.fetch_message = AsyncMock(return_value=message)
        
        # Mock member permissions
        member = Mock(spec=discord.Member)
        channel.guild.get_member.return_value = member
        permissions = Mock()
        permissions.read_messages = True
        channel.permissions_for.return_value = permissions
        
        await send_reminders(bot)
        
        mock_logger.error.assert_called()
        mock_db.delete_message_by_message_and_user_id.assert_called_once_with(123456789, 222222222)

    @patch('reminder.config')
    @patch('reminder.FirestoreReminderCollection')
    @patch('reminder.logger')
    @pytest.mark.asyncio
    async def test_send_reminders_general_exception(self, mock_logger, mock_db_class, mock_config):
        """Test send_reminders handles general exceptions."""
        from reminder import send_reminders
        
        mock_config.REMINDER_THRESHOLD = 3600
        mock_db_class.side_effect = Exception("Database connection failed")
        
        bot = Mock(spec=discord.Client)
        
        await send_reminders(bot)
        
        mock_logger.error.assert_called_with("Error in send_reminders(): Database connection failed")

    @patch('reminder.config')
    @patch('reminder.FirestoreReminderCollection')
    @pytest.mark.asyncio
    async def test_send_reminders_duplicate_reminders(self, mock_db_class, mock_config):
        """Test send_reminders handles duplicate reminders correctly."""
        from reminder import send_reminders
        
        mock_config.REMINDER_THRESHOLD = 3600
        mock_config.REMINDER_MESSAGE_START = "## Reminders\n"
        mock_config.REMINDER_MESSAGE_MAIN = "- {user_mention} reply to {message_link}\n"
        mock_config.REMINDER_MESSAGE_END = "Please reply!"
        
        mock_db = Mock()
        mock_db_class.return_value = mock_db
        
        # Mock duplicate expired messages
        expired_messages = [
            {
                'message_id': 123456789,
                'channel_id': 987654321,
                'mentioned_user_id': 222222222
            },
            {
                'message_id': 123456789,  # Same message
                'channel_id': 987654321,  # Same channel
                'mentioned_user_id': 222222222  # Same user
            }
        ]
        mock_db.get_expired_messages.return_value = expired_messages
        
        bot = Mock(spec=discord.Client)
        
        # Mock channel
        channel = Mock(spec=discord.TextChannel)
        channel.id = 987654321
        channel.guild = Mock(spec=discord.Guild)
        channel.guild.id = 555555555
        channel.send = AsyncMock()
        bot.get_channel.return_value = channel
        
        # Mock user
        user = Mock(spec=discord.User)
        bot.get_user.return_value = user
        
        # Mock message
        message = Mock(spec=discord.Message)
        channel.fetch_message = AsyncMock(return_value=message)
        
        # Mock member permissions
        member = Mock(spec=discord.Member)
        channel.guild.get_member.return_value = member
        permissions = Mock()
        permissions.read_messages = True
        channel.permissions_for.return_value = permissions
        
        await send_reminders(bot)
        
        # Should only delete once due to deduplication
        mock_db.delete_message_by_message_and_user_id.assert_called_once_with(123456789, 222222222)
