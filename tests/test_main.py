"""
Tests for the main module (main.py).
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
import discord
from discord.ext import commands
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


class TestBotEvents:
    """Test cases for bot event handlers."""

    @patch('main.register_db')
    @patch('main.observe_message')
    @patch('main.stats_db')
    @pytest.mark.asyncio
    async def test_on_message_human_user(self, mock_stats_db, mock_observe_message, mock_register_db):
        """Test on_message with human user message."""
        # Import here to avoid circular imports during patching
        import main
        
        # Create a mock message from human user
        message = Mock(spec=discord.Message)
        message.author = Mock(spec=discord.User)
        message.author.bot = False
        
        # Create a mock bot
        bot = Mock(spec=commands.Bot)
        bot.process_commands = AsyncMock()
        
        # Replace the global bot with our mock
        original_bot = main.bot
        main.bot = bot
        
        try:
            await main.on_message(message)
            
            mock_register_db.assert_called_once_with(message)
            mock_observe_message.assert_called_once_with(message)
            bot.process_commands.assert_called_once_with(message)
            mock_stats_db.increment_message_count.assert_called_once()
        finally:
            # Restore original bot
            main.bot = original_bot

    @patch('main.register_db')
    @patch('main.observe_message')
    @patch('main.stats_db')
    @pytest.mark.asyncio
    async def test_on_message_bot_user(self, mock_stats_db, mock_observe_message, mock_register_db):
        """Test on_message ignores bot messages."""
        import main
        
        # Create a mock message from bot user
        message = Mock(spec=discord.Message)
        message.author = Mock(spec=discord.User)
        message.author.bot = True
        
        bot = Mock(spec=commands.Bot)
        bot.process_commands = AsyncMock()
        
        original_bot = main.bot
        main.bot = bot
        
        try:
            await main.on_message(message)
            
            # Should not call any functions for bot messages
            mock_register_db.assert_not_called()
            mock_observe_message.assert_not_called()
            bot.process_commands.assert_not_called()
            mock_stats_db.increment_message_count.assert_not_called()
        finally:
            main.bot = original_bot

    @patch('main.observe_reaction')
    @patch('main.logger')
    @pytest.mark.asyncio
    async def test_on_raw_reaction_add_valid_reaction(self, mock_logger, mock_observe_reaction):
        """Test on_raw_reaction_add with valid reaction."""
        import main
        
        # Create mock payload
        payload = Mock(spec=discord.RawReactionActionEvent)
        payload.user_id = 222222222
        payload.message_id = 123456789
        payload.channel_id = 987654321
        
        # Create mock user (not bot)
        user = Mock(spec=discord.User)
        user.bot = False
        
        # Create mock message and channel
        message = Mock(spec=discord.Message)
        message.author = Mock(spec=discord.User)
        message.author.id = 111111111  # Different from reaction user
        
        channel = Mock(spec=discord.TextChannel)
        channel.fetch_message = AsyncMock(return_value=message)
        
        # Create mock bot
        bot = Mock(spec=commands.Bot)
        bot.get_user.return_value = user
        bot.get_channel.return_value = channel
        
        original_bot = main.bot
        main.bot = bot
        
        try:
            await main.on_raw_reaction_add(payload)
            
            bot.get_user.assert_called_once_with(222222222)
            bot.get_channel.assert_called_once_with(987654321)
            channel.fetch_message.assert_called_once_with(123456789)
            mock_observe_reaction.assert_called_once_with(payload)
        finally:
            main.bot = original_bot

    @patch('main.observe_reaction')
    @patch('main.logger')
    @pytest.mark.asyncio
    async def test_on_raw_reaction_add_bot_user(self, mock_logger, mock_observe_reaction):
        """Test on_raw_reaction_add ignores bot reactions."""
        import main
        
        payload = Mock(spec=discord.RawReactionActionEvent)
        payload.user_id = 222222222
        
        # Create mock bot user
        user = Mock(spec=discord.User)
        user.bot = True
        
        bot = Mock(spec=commands.Bot)
        bot.get_user.return_value = user
        
        original_bot = main.bot
        main.bot = bot
        
        try:
            await main.on_raw_reaction_add(payload)
            
            mock_observe_reaction.assert_not_called()
        finally:
            main.bot = original_bot

    @patch('main.observe_reaction')
    @patch('main.logger')
    @pytest.mark.asyncio
    async def test_on_raw_reaction_add_self_reaction(self, mock_logger, mock_observe_reaction):
        """Test on_raw_reaction_add ignores self-reactions."""
        import main
        
        payload = Mock(spec=discord.RawReactionActionEvent)
        payload.user_id = 222222222
        payload.message_id = 123456789
        payload.channel_id = 987654321
        
        user = Mock(spec=discord.User)
        user.bot = False
        
        # Message author is same as reaction user
        message = Mock(spec=discord.Message)
        message.author = Mock(spec=discord.User)
        message.author.id = 222222222
        
        channel = Mock(spec=discord.TextChannel)
        channel.fetch_message = AsyncMock(return_value=message)
        
        bot = Mock(spec=commands.Bot)
        bot.get_user.return_value = user
        bot.get_channel.return_value = channel
        
        original_bot = main.bot
        main.bot = bot
        
        try:
            await main.on_raw_reaction_add(payload)
            
            # Should not call observe_reaction for self-reactions
            mock_observe_reaction.assert_not_called()
        finally:
            main.bot = original_bot

    @patch('main.observe_reaction')
    @patch('main.logger')
    @pytest.mark.asyncio
    async def test_on_raw_reaction_add_channel_not_found(self, mock_logger, mock_observe_reaction):
        """Test on_raw_reaction_add when channel is not found."""
        import main
        
        payload = Mock(spec=discord.RawReactionActionEvent)
        payload.user_id = 222222222
        payload.channel_id = 987654321
        
        user = Mock(spec=discord.User)
        user.bot = False
        
        bot = Mock(spec=commands.Bot)
        bot.get_user.return_value = user
        bot.get_channel.return_value = None  # Channel not found
        
        original_bot = main.bot
        main.bot = bot
        
        try:
            await main.on_raw_reaction_add(payload)
            
            mock_logger.error.assert_called_once()
            mock_observe_reaction.assert_not_called()
        finally:
            main.bot = original_bot

    @patch('main.observe_reaction')
    @patch('main.logger')
    @pytest.mark.asyncio
    async def test_on_raw_reaction_add_message_fetch_error(self, mock_logger, mock_observe_reaction):
        """Test on_raw_reaction_add when message fetch fails."""
        import main
        
        payload = Mock(spec=discord.RawReactionActionEvent)
        payload.user_id = 222222222
        payload.message_id = 123456789
        payload.channel_id = 987654321
        
        user = Mock(spec=discord.User)
        user.bot = False
        
        channel = Mock(spec=discord.TextChannel)
        channel.fetch_message = AsyncMock(side_effect=Exception("Message fetch failed"))
        
        bot = Mock(spec=commands.Bot)
        bot.get_user.return_value = user
        bot.get_channel.return_value = channel
        
        original_bot = main.bot
        main.bot = bot
        
        try:
            await main.on_raw_reaction_add(payload)
            
            mock_logger.error.assert_called_once()
            mock_observe_reaction.assert_not_called()
        finally:
            main.bot = original_bot


class TestPeriodicTasks:
    """Test cases for periodic tasks."""

    @patch('main.send_reminders')
    @pytest.mark.asyncio
    async def test_send_reminders_task(self, mock_send_reminders):
        """Test send_reminders_task calls send_reminders with bot."""
        import main
        
        bot = Mock(spec=commands.Bot)
        original_bot = main.bot
        main.bot = bot
        
        try:
            await main.send_reminders_task()
            mock_send_reminders.assert_called_once_with(bot)
        finally:
            main.bot = original_bot

    @patch('main.config')
    @patch('main.datetime')
    @pytest.mark.asyncio
    async def test_before_send_reminders_aligned(self, mock_datetime, mock_config):
        """Test before_send_reminders with aligned interval start."""
        import main
        from datetime import datetime, timedelta
        
        mock_config.REMINDER_INTERVAL = 3600  # 1 hour
        mock_config.ALIGNED_REMINDER_INTERVAL_START = True
        
        # Mock current time as 30 minutes past the hour
        current_time = datetime(2024, 1, 1, 12, 30, 0)
        next_hour = datetime(2024, 1, 1, 13, 0, 0)
        
        mock_datetime.now.return_value = current_time
        
        with patch('asyncio.sleep') as mock_sleep:
            await main.before_send_reminders()
            
            # Should sleep for 30 minutes (1800 seconds)
            expected_sleep = (next_hour - current_time).total_seconds()
            mock_sleep.assert_called_once_with(expected_sleep)

    @patch('main.config')
    @patch('main.datetime')
    @pytest.mark.asyncio
    async def test_before_send_reminders_not_aligned(self, mock_datetime, mock_config):
        """Test before_send_reminders without aligned interval start."""
        import main
        
        mock_config.REMINDER_INTERVAL = 60  # 1 minute (not multiple of 3600)
        mock_config.ALIGNED_REMINDER_INTERVAL_START = True
        
        with patch('asyncio.sleep') as mock_sleep:
            await main.before_send_reminders()
            
            # Should not sleep when interval is not multiple of 3600
            mock_sleep.assert_not_called()

    @patch('main.config')
    @pytest.mark.asyncio
    async def test_before_send_reminders_disabled(self, mock_config):
        """Test before_send_reminders when alignment is disabled."""
        import main
        
        mock_config.REMINDER_INTERVAL = 3600
        mock_config.ALIGNED_REMINDER_INTERVAL_START = False
        
        with patch('asyncio.sleep') as mock_sleep:
            await main.before_send_reminders()
            
            # Should not sleep when alignment is disabled
            mock_sleep.assert_not_called()


class TestBotInitialization:
    """Test cases for bot initialization and configuration."""

    @patch.dict(os.environ, {'DISCORD_TOKEN': 'test_token_123'})
    def test_token_loading(self):
        """Test Discord token is loaded from environment."""
        # Patch load_dotenv before importing main
        with patch('dotenv.load_dotenv') as mock_load_dotenv:
            import importlib
            import main
            importlib.reload(main)
            
            # Check that load_dotenv was called with the correct path
            mock_load_dotenv.assert_called_with(dotenv_path='secrets/.env')

    def test_bot_intents_configuration(self):
        """Test bot intents are properly configured."""
        import main
        
        # Check that required intents are enabled
        assert main.intents.message_content is True
        assert main.intents.members is True
        assert main.intents.presences is True

    def test_bot_command_prefix(self):
        """Test bot command prefix is set correctly."""
        import main
        
        assert main.bot.command_prefix == main.config.COMMAND_PREFIX

    def test_stats_db_initialization(self):
        """Test stats database is initialized."""
        with patch('db.FirestoreStatsCollection') as mock_stats_import:
            import importlib
            import main
            importlib.reload(main)
            
            mock_stats_import.assert_called_once()
