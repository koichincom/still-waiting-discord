# Still Waiting - Discord Reminder Bot

A Discord bot that automatically monitors mentions and replies, then sends **dual reminders** (channel + DM) if users don't respond within a specified time. Features smart monitoring, memory management, and comprehensive user tracking.

## 🚀 Quick Start

1. **[Invite Still Waiting to your server](INVITE_LINK_HERE)** *(Link will be added when deployed)*
2. Grant the required permissions during invitation
3. Start mentioning users or replying to messages
4. The bot automatically monitors and reminds users with both channel mentions and DMs!

## ✨ Features

### Core Functionality

- **Automatic Monitoring**: Works without commands - simply mention users or reply to messages
- **Dual Reminder System**: Sends both channel mentions AND direct messages (configurable)
- **User Mentions**: Monitors individual user mentions (`@username`)
- **Role Mentions**: Monitors all members when a role is mentioned (`@role`)
- **Reply Monitoring**: Monitors users when you reply to their messages (respects Discord's mention suppression)
- **Reaction Support**: Optionally accepts reactions as valid responses
- **Message Links**: All reminders include clickable links to the original message

### Advanced Features

- **Memory Management**: Automatic cleanup of stale monitoring entries every 30 minutes
- **Rate Limiting**: Prevents Discord API limits with intelligent message queuing
- **Concurrent Limits**: Configurable maximum concurrent monitoring (default: 1000)
- **Duplicate Prevention**: Prevents multiple reminders for the same user/message combination
- **Smart Logging**: Comprehensive logging system for debugging and monitoring
- **Error Recovery**: Robust error handling with graceful fallbacks

## 🔧 How It Works

### User Mentions

```text
User: @john hey, can you check this?
Bot: [Starts monitoring john's activity]
[After wait time if no response]
Bot (Channel): @john, you did not respond to this message. Please reply!
Bot (DM): Hi john! You haven't responded to a message in #general.
         Original message: [link]
         Please consider replying when you have a chance.
```

### Role Mentions

```text
User: @developers please review this code
Bot: [Starts monitoring all members of the @developers role individually]
[Sends dual reminders (channel + DM) to each member who doesn't respond]
```

### Reply Monitoring

```text
Original: "Has anyone seen the new update?"
Reply: "@john yes, it looks great!" (mentions john)
Bot: [Starts monitoring john for response to the reply]
[Sends dual reminders if john doesn't respond]
```

## 💬 DM Reminder System

The bot features a **dual reminder system** that sends both channel mentions and direct messages:

### Channel Reminders

- Posted in the original channel where the mention occurred
- Uses @mention to notify the user
- Includes clickable link to the original message
- Visible to all channel members

### Direct Message Reminders

- Sent privately to the user's DMs
- More personal and harder to miss
- Includes channel context and original message link
- Respects user privacy settings

### DM Fallback Behavior

- If DM fails (user has DMs disabled), channel reminder still works
- If channel reminder fails (no permissions), DM still works
- Logs all delivery attempts for debugging
- Graceful handling of blocked/unavailable users

## 📋 Required Permissions

When inviting the bot to your server, make sure it has these permissions:

- **Read Messages** - To see mentions and replies
- **Send Messages** - To send reminder messages in channels
- **Read Message History** - To check for responses and fetch original messages
- **Add Reactions** - For reaction response support (optional)
- **Send Direct Messages** - To send DM reminders (handled automatically by Discord)

**Note**: The bot will automatically request DM permissions when trying to send DMs. Users can allow or deny these on an individual basis.

## 💡 Example Usage

### Basic Mention with Dual Reminders

```text
User: @sarah can you help with this bug?
Bot: [Starts monitoring sarah]
[After wait time if no response]
Bot (Channel): @sarah, you did not respond to this message. Please reply!
Bot (DM): Hi sarah! You haven't responded to a message in #development.
         Original message: [clickable link]
         Please consider replying when you have a chance.
```

### Role Mention

```text
User: @moderators we need help in #general
Bot: [Starts monitoring all moderator role members individually]
[Sends dual reminders (channel + DM) to each member who doesn't respond]
```

### Reply with Mention

```text
Original: "Has anyone seen the new update?"
Reply: "@john yes, it looks great!" (mentions john)
Bot: [Starts monitoring john for response to the reply]
[Sends dual reminders if john doesn't respond]
```

## ⚙️ Configuration Settings

The bot uses environment variables for configuration:

### Core Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `DISCORD_TOKEN` | **Required** | Your Discord bot token |
| `WAIT_TIME` | `86400` | Time to wait before sending reminder (seconds, default: 24 hours) |
| `ALLOW_REACTIONS` | `true` | Accept reactions as valid responses |
| `ENABLE_NOTIFY` | `true` | Enable/disable all monitoring functionality |

### DM Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `ENABLE_DM_REMINDERS` | `true` | Enable/disable DM reminders (channel reminders still work) |

### Performance Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `MAX_CONCURRENT_MONITORING` | `1000` | Maximum number of simultaneous monitoring tasks |

### Example .env file

```env
DISCORD_TOKEN=your_bot_token_here
WAIT_TIME=86400
ALLOW_REACTIONS=true
ENABLE_NOTIFY=true
ENABLE_DM_REMINDERS=true
MAX_CONCURRENT_MONITORING=1000
```

## 🤖 Bot Behavior

### Smart Monitoring

- **Ignores bots**: Won't monitor or remind other bots
- **Ignores self-mentions**: Won't monitor users mentioning themselves  
- **Prevents duplicates**: Won't send multiple reminders for the same interaction
- **Respects mention suppression**: Only monitors replies that actually notify users
- **Memory management**: Automatically cleans up stale monitoring entries every 30 minutes

### Dual Reminder System

- **Channel reminders**: Uses @mentions in the original channel with message links
- **DM reminders**: Sends private direct messages with context and links
- **Graceful fallbacks**: Works even if one delivery method fails
- **Configurable**: DM reminders can be disabled while keeping channel reminders

### Rate Limiting & Performance

- **API compliance**: Automatically rate limits messages to prevent Discord API limits
- **Concurrent limits**: Configurable maximum concurrent monitoring to prevent resource exhaustion
- **Resource cleanup**: Periodic cleanup prevents memory leaks from long-running instances
- **Error recovery**: Comprehensive error handling with detailed logging

### User Privacy

- **DM consent**: Respects user DM settings (some users may have DMs disabled)
- **No data persistence**: All monitoring is in-memory only (no database)
- **Minimal logging**: Only logs essential information for debugging

## 🆘 Support & Troubleshooting

### Common Issues

**DM reminders not working?**

- Check if the user has DMs enabled in their Discord settings
- Some users block DMs from server members - this is normal behavior
- Channel reminders will still work even if DMs fail

**Bot not responding to mentions?**

- Verify the bot has "Read Messages" and "Read Message History" permissions
- Ensure the bot can see the channel where you're testing
- Check that the bot is online and properly invited to your server

**No reminder sent?**

- The user may have responded (message or reaction) before the wait time expired
- Check bot logs for any permission or API errors
- Verify monitoring is enabled (`ENABLE_NOTIFY=true`)

### Getting Help

If you encounter persistent issues:

1. Verify the bot has all required permissions in your server
2. Check the console logs for error messages
3. Ensure the bot is online and properly invited to your server

For additional support, please open an issue on GitHub.

## 🔍 How to Self-Host (Advanced Users)

If you prefer to host your own instance:

### Prerequisites

- Python 3.8+
- Discord bot token

### Setup

1. Clone this repository
2. Create a virtual environment: `python -m venv venv`
3. Activate virtual environment:
   - Linux/Mac: `source venv/bin/activate`
   - Windows: `venv\Scripts\activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Create `.env` file with your Discord token
6. Run: `python main.py`

### Environment Variables

| Variable | Required | Description | Default |
|----------|----------|-------------|---------|
| `DISCORD_TOKEN` | **Yes** | Your Discord bot token | None |
| `WAIT_TIME` | No | Time to wait before sending reminder (seconds) | `86400` (24 hours) |
| `ALLOW_REACTIONS` | No | Accept reactions as valid responses | `true` |
| `ENABLE_NOTIFY` | No | Enable/disable all monitoring | `true` |
| `ENABLE_DM_REMINDERS` | No | Enable/disable DM reminders | `true` |
| `MAX_CONCURRENT_MONITORING` | No | Maximum concurrent monitoring tasks | `1000` |

### Example .env file for self-hosting

```env
DISCORD_TOKEN=your_actual_bot_token_here
WAIT_TIME=86400
ALLOW_REACTIONS=true
ENABLE_NOTIFY=true
ENABLE_DM_REMINDERS=true
MAX_CONCURRENT_MONITORING=1000
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details. MIT License provides you the freedom to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the software.
