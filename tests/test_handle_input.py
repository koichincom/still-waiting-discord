"""
Tests for the handle_input module (handle_input.py).
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
import discord
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


class TestRegisterDb:
    """Test cases for register_db function."""

    @patch('handle_input.reminder_db')
    @patch('handle_input.config')
    @pytest.mark.asyncio
    async def test_register_db_single_mention(self, mock_config, mock_db):
        """Test register_db with a single user mention."""
        from handle_input import register_db
        
        mock_config.MAX_ROLE_MEMBERS = 20
        
        # Create mock message with single mention
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
        
        # Create mentioned user
        mentioned_user = Mock(spec=discord.User)
        mentioned_user.id = 222222222
        mentioned_user.bot = False
        mentioned_user.name = "mentioned_user"
        message.mentions = [mentioned_user]
        
        await register_db(message)
        
        mock_db.save_message.assert_called_once_with(
            message_id=123456789,
            channel_id=987654321,
            mentioned_user_id=222222222
        )

    @patch('handle_input.reminder_db')
    @patch('handle_input.config')
    @pytest.mark.asyncio
    async def test_register_db_ignore_bots(self, mock_config, mock_db):
        """Test register_db ignores bot mentions."""
        from handle_input import register_db
        
        mock_config.MAX_ROLE_MEMBERS = 20
        
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
        
        # Create bot user
        bot_user = Mock(spec=discord.User)
        bot_user.id = 333333333
        bot_user.bot = True
        bot_user.name = "bot_user"
        message.mentions = [bot_user]
        
        await register_db(message)
        
        mock_db.save_message.assert_not_called()

    @patch('handle_input.reminder_db')
    @patch('handle_input.config')
    @pytest.mark.asyncio
    async def test_register_db_ignore_self_mention(self, mock_config, mock_db):
        """Test register_db ignores self-mentions."""
        from handle_input import register_db
        
        mock_config.MAX_ROLE_MEMBERS = 20
        
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
        
        # User mentions themselves
        message.mentions = [message.author]
        
        await register_db(message)
        
        mock_db.save_message.assert_not_called()

    @patch('handle_input.reminder_db')
    @patch('handle_input.config')
    @pytest.mark.asyncio
    async def test_register_db_everyone_mention(self, mock_config, mock_db):
        """Test register_db with @everyone mention."""
        from handle_input import register_db
        
        mock_config.MAX_ROLE_MEMBERS = 20
        
        message = Mock(spec=discord.Message)
        message.id = 123456789
        message.channel = Mock(spec=discord.TextChannel)
        message.channel.id = 987654321
        message.author = Mock(spec=discord.Member)
        message.author.id = 111111111
        message.author.bot = False
        message.content = "Hello @everyone"
        message.mention_everyone = True
        message.role_mentions = []
        message.mentions = []
        
        # Create channel members
        user1 = Mock(spec=discord.Member)
        user1.id = 222222222
        user1.bot = False
        user1.name = "user1"
        
        user2 = Mock(spec=discord.Member)
        user2.id = 333333333
        user2.bot = False
        user2.name = "user2"
        
        message.channel.members = [user1, user2]
        
        await register_db(message)
        
        assert mock_db.save_message.call_count == 2

    @patch('handle_input.reminder_db')
    @patch('handle_input.config')
    @pytest.mark.asyncio
    async def test_register_db_role_size_limit(self, mock_config, mock_db):
        """Test register_db respects role size limits."""
        from handle_input import register_db
        
        mock_config.MAX_ROLE_MEMBERS = 2
        mock_config.ROLE_SIZE_ERROR = "Too many members: {limit}"
        
        message = Mock(spec=discord.Message)
        message.id = 123456789
        message.channel = Mock(spec=discord.TextChannel)
        message.channel.id = 987654321
        message.author = Mock(spec=discord.Member)
        message.author.id = 111111111
        message.author.bot = False
        message.content = "Hello @everyone"
        message.mention_everyone = True
        message.role_mentions = []
        message.mentions = []
        message.reply = AsyncMock()
        
        # Create too many channel members
        members = []
        for i in range(5):
            user = Mock(spec=discord.Member)
            user.id = 222222222 + i
            user.bot = False
            user.name = f"user{i}"
            members.append(user)
        
        message.channel.members = members
        
        await register_db(message)
        
        mock_db.save_message.assert_not_called()
        message.reply.assert_called_once()

    @patch('handle_input.reminder_db')
    @patch('handle_input.config')
    @patch('handle_input.logger')
    @pytest.mark.asyncio
    async def test_register_db_database_error(self, mock_logger, mock_config, mock_db):
        """Test register_db handles database errors gracefully."""
        from handle_input import register_db
        
        mock_config.MAX_ROLE_MEMBERS = 20
        mock_db.save_message.side_effect = Exception("Database error")
        
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
        
        mock_logger.error.assert_called_once()


class TestObserveMessage:
    """Test cases for observe_message function."""

    @patch('handle_input.reminder_db')
    def test_observe_message_valid_response(self, mock_db):
        """Test observe_message with valid message in tracked channel."""
        from handle_input import observe_message
        
        mock_db.search_reminders.return_value = ['doc1']
        
        message = Mock(spec=discord.Message)
        message.channel.id = 987654321
        message.author.id = 222222222
        
        observe_message(message)
        
        mock_db.search_reminders.assert_called_once_with(987654321, 222222222)
        mock_db.delete_messages_by_doc_ids.assert_called_once_with(['doc1'])

    @patch('handle_input.reminder_db')
    def test_observe_message_no_reminders(self, mock_db):
        """Test observe_message when no reminders are found."""
        from handle_input import observe_message
        
        mock_db.search_reminders.return_value = []
        
        message = Mock(spec=discord.Message)
        message.channel.id = 987654321
        message.author.id = 222222222
        
        observe_message(message)
        
        mock_db.search_reminders.assert_called_once_with(987654321, 222222222)
        mock_db.delete_messages_by_doc_ids.assert_not_called()

    @patch('handle_input.reminder_db')
    @patch('handle_input.logger')
    def test_observe_message_exception_handling(self, mock_logger, mock_db):
        """Test observe_message handles exceptions gracefully."""
        from handle_input import observe_message
        
        mock_db.search_reminders.side_effect = Exception("Database error")
        
        message = Mock(spec=discord.Message)
        message.channel.id = 987654321
        message.author.id = 222222222
        
        observe_message(message)
        
        mock_logger.error.assert_called_once()


class TestObserveReaction:
    """Test cases for observe_reaction function."""

    @patch('handle_input.reminder_db')
    def test_observe_reaction_valid_reaction(self, mock_db):
        """Test observe_reaction with valid reaction payload."""
        from handle_input import observe_reaction
        
        mock_db.delete_message_by_message_and_user_id.return_value = True
        
        payload = Mock()
        payload.message_id = 123456789
        payload.user_id = 222222222
        
        observe_reaction(payload)
        
        mock_db.delete_message_by_message_and_user_id.assert_called_once_with(123456789, 222222222)

    @patch('handle_input.reminder_db')
    def test_observe_reaction_message_not_tracked(self, mock_db):
        """Test observe_reaction when message is not being tracked."""
        from handle_input import observe_reaction
        
        mock_db.delete_message_by_message_and_user_id.return_value = False
        
        payload = Mock()
        payload.message_id = 123456789
        payload.user_id = 222222222
        
        observe_reaction(payload)
        
        mock_db.delete_message_by_message_and_user_id.assert_called_once_with(123456789, 222222222)

    @patch('handle_input.reminder_db')
    @patch('handle_input.logger')
    def test_observe_reaction_exception_handling(self, mock_logger, mock_db):
        """Test observe_reaction handles exceptions gracefully."""
        from handle_input import observe_reaction
        
        mock_db.delete_message_by_message_and_user_id.side_effect = Exception("Database error")
        
        payload = Mock()
        payload.message_id = 123456789
        payload.user_id = 222222222
        
        observe_reaction(payload)
        
        mock_logger.error.assert_called_once()
