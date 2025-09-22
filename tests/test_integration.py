"""
Integration tests for the Discord bot.

These tests verify that different components work together correctly.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
import discord
from datetime import datetime, timedelta
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


class TestBotIntegration:
    """Integration tests for the bot workflow."""

    @patch('handle_input.reminder_db')
    @patch('handle_input.config')
    @patch('reminder.FirestoreReminderCollection')
    @patch('reminder.config')
    @pytest.mark.asyncio
    async def test_full_reminder_workflow(self, mock_reminder_config, mock_reminder_db_class, 
                                         mock_handle_config, mock_handle_db):
        """Test the complete workflow from mention to reminder."""
        from handle_input import register_db
        from reminder import send_reminders
        
        # Setup configs
        mock_handle_config.MAX_ROLE_MEMBERS = 20
        mock_reminder_config.REMINDER_THRESHOLD = 3600
        mock_reminder_config.REMINDER_MESSAGE_START = "## Reminders\n"
        mock_reminder_config.REMINDER_MESSAGE_MAIN = "- {user_mention} reply to {message_link}\n"
        mock_reminder_config.REMINDER_MESSAGE_END = "Please reply!"
        
        # Setup database mocks
        mock_reminder_db = Mock()
        mock_reminder_db_class.return_value = mock_reminder_db
        
        # Step 1: Register a mention
        message = Mock(spec=discord.Message)
        message.id = 123456789
        message.channel = Mock(spec=discord.TextChannel)
        message.channel.id = 987654321
        message.channel.members = []
        message.author = Mock(spec=discord.Member)
        message.author.id = 111111111
        message.author.bot = False
        message.mention_everyone = False
        message.role_mentions = []
        
        mentioned_user = Mock(spec=discord.User)
        mentioned_user.id = 222222222
        mentioned_user.bot = False
        mentioned_user.name = "mentioned_user"
        message.mentions = [mentioned_user]
        
        await register_db(message)
        
        # Verify mention was saved
        mock_handle_db.save_message.assert_called_once_with(
            message_id=123456789,
            channel_id=987654321,
            mentioned_user_id=222222222
        )
        
        # Step 2: Simulate expired reminder
        expired_reminder = {
            'message_id': 123456789,
            'channel_id': 987654321,
            'mentioned_user_id': 222222222
        }
        mock_reminder_db.get_expired_messages.return_value = [expired_reminder]
        
        # Setup bot for sending reminder
        bot = Mock(spec=discord.Client)
        
        channel = Mock(spec=discord.TextChannel)
        channel.id = 987654321
        channel.guild = Mock(spec=discord.Guild)
        channel.guild.id = 555555555
        channel.send = AsyncMock()
        bot.get_channel.return_value = channel
        
        user = Mock(spec=discord.User)
        bot.get_user.return_value = user
        
        original_message = Mock(spec=discord.Message)
        channel.fetch_message = AsyncMock(return_value=original_message)
        
        member = Mock(spec=discord.Member)
        channel.guild.get_member.return_value = member
        permissions = Mock()
        permissions.read_messages = True
        channel.permissions_for.return_value = permissions
        
        await send_reminders(bot)
        
        # Verify reminder was sent and deleted
        channel.send.assert_called_once()
        mock_reminder_db.delete_message_by_message_and_user_id.assert_called_once_with(123456789, 222222222)

    @patch('handle_input.reminder_db')
    @pytest.mark.asyncio
    async def test_message_in_channel_removes_reminder(self, mock_db):
        """Test that sending a message in the channel removes the reminder."""
        from handle_input import observe_message
        
        mock_db.search_reminders.return_value = ['doc1']
        
        # Create message in channel
        message = Mock(spec=discord.Message)
        message.channel.id = 987654321
        message.author.id = 222222222
        
        observe_message(message)
        
        # Verify reminder was removed
        mock_db.search_reminders.assert_called_once_with(987654321, 222222222)
        mock_db.delete_messages_by_doc_ids.assert_called_once_with(['doc1'])

    @patch('handle_input.reminder_db')
    def test_reaction_removes_reminder(self, mock_db):
        """Test that reacting to a message removes the reminder."""
        from handle_input import observe_reaction
        
        mock_db.delete_message_by_message_and_user_id.return_value = True
        
        # Create reaction payload
        payload = Mock()
        payload.message_id = 123456789
        payload.user_id = 222222222
        
        observe_reaction(payload)
        
        # Verify reminder was removed
        mock_db.delete_message_by_message_and_user_id.assert_called_once_with(123456789, 222222222)

    @patch('handle_input.reminder_db')
    @patch('handle_input.config')
    @pytest.mark.asyncio
    async def test_role_mention_size_limit_integration(self, mock_config, mock_db):
        """Test integration of role mention size limits."""
        from handle_input import register_db
        
        mock_config.MAX_ROLE_MEMBERS = 2
        mock_config.ROLE_SIZE_ERROR = "Too many members: {limit}"
        
        # Create message with large role mention
        message = Mock(spec=discord.Message)
        message.id = 123456789
        message.channel = Mock(spec=discord.TextChannel)
        message.channel.id = 987654321
        message.author = Mock(spec=discord.Member)
        message.author.id = 111111111
        message.author.bot = False
        message.content = "Hello @testrole"
        message.mention_everyone = False
        message.mentions = []
        message.reply = AsyncMock()
        
        # Create role with too many members
        role = Mock(spec=discord.Role)
        role.id = 444444444
        role.name = "testrole"
        
        # Create many members
        members = []
        for i in range(5):  # More than MAX_ROLE_MEMBERS
            member = Mock(spec=discord.Member)
            member.id = 555555555 + i
            member.bot = False
            member.name = f"user{i}"
            members.append(member)
        
        role.members = members
        message.role_mentions = [role]
        
        await register_db(message)
        
        # Should not save any messages due to size limit
        mock_db.save_message.assert_not_called()
        
        # Should send error message
        message.reply.assert_called_once()

    @patch('reminder.FirestoreReminderCollection')
    @patch('reminder.config')
    @pytest.mark.asyncio
    async def test_multiple_reminders_grouping(self, mock_config, mock_db_class):
        """Test that multiple reminders in same channel are grouped."""
        from reminder import send_reminders
        
        mock_config.REMINDER_THRESHOLD = 3600
        mock_config.REMINDER_MESSAGE_START = "## Reminders\n"
        mock_config.REMINDER_MESSAGE_MAIN = "- {user_mention} reply to {message_link}\n"
        mock_config.REMINDER_MESSAGE_END = "Please reply!"
        
        mock_db = Mock()
        mock_db_class.return_value = mock_db
        
        # Multiple expired reminders in same channel
        expired_reminders = [
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
        mock_db.get_expired_messages.return_value = expired_reminders
        
        bot = Mock(spec=discord.Client)
        
        # Setup channel
        channel = Mock(spec=discord.TextChannel)
        channel.id = 987654321
        channel.guild = Mock(spec=discord.Guild)
        channel.guild.id = 555555555
        channel.send = AsyncMock()
        bot.get_channel.return_value = channel
        
        # Setup users
        def get_user_side_effect(user_id):
            user = Mock(spec=discord.User)
            user.id = user_id
            return user
        bot.get_user.side_effect = get_user_side_effect
        
        # Setup messages
        def fetch_message_side_effect(message_id):
            message = Mock(spec=discord.Message)
            message.id = message_id
            return message
        channel.fetch_message.side_effect = fetch_message_side_effect
        
        # Setup permissions
        def get_member_side_effect(user_id):
            member = Mock(spec=discord.Member)
            member.id = user_id
            return member
        channel.guild.get_member.side_effect = get_member_side_effect
        
        permissions = Mock()
        permissions.read_messages = True
        channel.permissions_for.return_value = permissions
        
        await send_reminders(bot)
        
        # Should send only one message containing both reminders
        channel.send.assert_called_once()
        
        # Should delete both reminders
        assert mock_db.delete_message_by_message_and_user_id.call_count == 2


class TestErrorHandlingIntegration:
    """Integration tests for error handling across components."""

    @patch('handle_input.reminder_db')
    @patch('handle_input.logger')
    @pytest.mark.asyncio
    async def test_database_error_handling_in_registration(self, mock_logger, mock_db):
        """Test database error handling during message registration."""
        from handle_input import register_db
        
        mock_db.save_message.side_effect = Exception("Database connection failed")
        
        message = Mock(spec=discord.Message)
        message.id = 123456789
        message.channel = Mock(spec=discord.TextChannel)
        message.channel.id = 987654321
        message.channel.members = []
        message.author = Mock(spec=discord.Member)
        message.author.id = 111111111
        message.author.bot = False
        message.mention_everyone = False
        message.role_mentions = []
        
        mentioned_user = Mock(spec=discord.User)
        mentioned_user.id = 222222222
        mentioned_user.bot = False
        mentioned_user.name = "mentioned_user"
        message.mentions = [mentioned_user]
        
        await register_db(message)
        
        # Should log the error
        mock_logger.error.assert_called_once()

    @patch('reminder.FirestoreReminderCollection')
    @patch('reminder.logger')
    @pytest.mark.asyncio
    async def test_reminder_sending_error_handling(self, mock_logger, mock_db_class):
        """Test error handling when sending reminders fails."""
        from reminder import send_reminders
        
        mock_db_class.side_effect = Exception("Database initialization failed")
        
        bot = Mock(spec=discord.Client)
        
        await send_reminders(bot)
        
        # Should log the error
        mock_logger.error.assert_called_with("Error in send_reminders(): Database initialization failed")
