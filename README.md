# Still Waiting - Discord Reminder Bot

A Discord bot that automatically monitors mentions and replies, then sends reminders if users don't respond within a specified time. Perfect for keeping track of important messages and ensuring nothing gets forgotten!

## 🚀 **Quick Start - Add to Your Server (FREE)**

**[Add Still Waiting to Your Discord Server](https://discord.com/oauth2/authorize?client_id=YOUR_CLIENT_ID&permissions=292057852928&integration_type=0&scope=bot)**

- **Completely FREE to use**  
- **No setup required** - works immediately after adding  
- **Minimal data storage** - only stores message IDs, user IDs, and timestamps temporarily  
- **Open source** - full transparency  

Simply click the link above, select your server, and start using the bot immediately!

---

## How It Works

### 1. Mention Someone

```
You: "@alice can you check this bug report?"
Bot: [Starts monitoring alice's activity]
```

### 2. Automatic Reminders

```
[After 24 hours if no response]
Bot: "@alice You haven't replied yet! We're STILL WAITING for your response!"
```

### 3. Smart Response Detection

- **Replies** to the original message remove the reminder
- **Reactions** to the message also count as responses
- **No spam** - only one reminder per person per message

---

## Features

### Core Functionality

- **Automatic monitoring** - No commands needed, just mention users
- **24-hour reminders** - Configurable wait time
- **Reply detection** - Removes monitoring when users respond
- **Reaction support** - Emoji reactions count as responses
- **Message links** - Reminders include links to original messages
- **Role mentions** - Monitor entire roles (with limits)

### Smart Features

- **Bot protection** - Ignores messages from other bots
- **Self-mention protection** - Won't monitor users mentioning themselves
- **Duplicate prevention** - No multiple reminders for the same interaction
- **Comprehensive logging** - Full activity tracking for server admins

---

## Self-Hosting (Advanced Users)

Want to host your own instance? Still Waiting is **100% open source**!

### Quick Deploy Options

#### Option 1: Render (Recommended)
[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com)

1. Fork this repository
2. Connect to Render
3. Set environment variables
4. Deploy!

#### Option 2: Railway
[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app)

#### Option 3: Local/VPS
```bash
git clone https://github.com/yourusername/still-waiting.git
cd still-waiting
pip install -r requirements.txt
python main.py
```

### Environment Variables
Create a `.env` file with these settings:

```env
# Required
DISCORD_TOKEN=your_bot_token_here
DB_USER=your_postgres_user
DB_PASSWORD=your_postgres_password
DB_NAME=your_postgres_database
DB_HOST=your_postgres_host
DB_PORT=5432

# Optional (defaults shown)
REMINDER_THRESHOLD=86400  # 24 hours in seconds
REMINDER_INTERVAL=3600    # Check every hour
MAX_ROLE_MEMBERS=1        # Max users in role mentions
```

### Database Setup

Still Waiting requires **PostgreSQL**:

```sql
-- The bot creates this table automatically
CREATE TABLE waiting_messages (
    id SERIAL PRIMARY KEY,
    message_id BIGINT NOT NULL,
    channel_id BIGINT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    mentioned_user_id BIGINT NOT NULL,
    UNIQUE(message_id, mentioned_user_id)
);
```

---

## Privacy & Data Storage

Still Waiting stores minimal data required for functionality:

### Data Collected
- **Message IDs** - To identify which messages contain mentions
- **Channel IDs** - To know where to send reminders  
- **User IDs** - To track who was mentioned and who responded
- **Timestamps** - To determine when reminders should be sent

### Data Retention
- Data is automatically deleted when users respond to mentions
- Reminder data is removed after reminders are sent
- No message content, usernames, or other personal information is stored
- All data is temporary and functional only

### Data Usage
- Data is used solely to provide reminder functionality
- No data is shared with third parties
- No analytics or tracking beyond core bot operation

---

## Technical Details

### Tech Stack

- **Language**: Python 3.8+
- **Discord Library**: discord.py 2.5+
- **Database**: PostgreSQL with asyncpg
- **Web Framework**: Flask (health check endpoint)
- **Async**: Full async/await implementation

### Key Libraries

```txt
discord.py==2.5.2      # Discord API interaction
asyncpg==0.30.0        # PostgreSQL async driver
Flask==3.1.1           # Web server for health checks
python-dotenv==1.1.0   # Environment variable management
```

### Configuration Options

Located in `src/config.py`:

```python
# Timing settings
REMINDER_THRESHOLD: int = 60 * 60 * 24  # 24 hours
REMINDER_INTERVAL: int = 60 * 60        # 1 hour

# Role mention limits
MAX_ROLE_MEMBERS: int = 1  # Limit role mentions

# Database settings
DB_TABLE_NAME: str = "waiting_messages"
DB_MIN_POOL_SIZE: int = 1
DB_MAX_POOL_SIZE: int = 5

# Message templates (customizable)
REMINDER_MESSAGE: str = "{user_mention} You haven't replied yet! We're STILL WAITING for your response!"
ROLE_SIZE_ERROR: str = "Number of role members to be notified is limited to {limit}."
```

### Architecture Overview

```
main.py              # Bot initialization and event handling
├── src/
│   ├── config.py    # Configuration and message templates
│   ├── db.py        # PostgreSQL database operations
│   ├── handle_input.py  # Message and reaction processing
│   ├── reminder.py  # Reminder sending logic
│   └── webserver.py # Health check endpoint
```

---

## Required Permissions

When adding the bot, ensure it has these Discord permissions:

- **Read Messages** - To see mentions and replies
- **Send Messages** - To send reminder messages
- **Read Message History** - To check for responses
- **Add Reactions** - For reaction-based responses (optional)

---

## Usage Examples

### Individual Mentions

```
You: "@john can you review this PR?"
Bot: [Monitors john for 24 hours]
[If john doesn't respond]
Bot: "@john You haven't replied yet! We're STILL WAITING for your response!"
```

### Role Mentions (Limited)

```
You: "@developers please check the deployment"
Bot: [Monitors up to 1 developer - configurable limit]
```

### Response Detection

```
Original: "@sarah what do you think about this?"
Sarah: "Looks good to me!" [Bot stops monitoring]
# OR
Sarah: [Reacts with 👍] [Bot stops monitoring]
```

---

## Support & Issues

### Common Issues

- **Bot not responding?** Check permissions and bot status
- **No reminders sent?** Verify database connection and settings
- **Role mentions not working?** Check `MAX_ROLE_MEMBERS` limit

### Getting Help

1. Check the [Issues](https://github.com/yourusername/still-waiting/issues) page
2. Create a new issue with detailed information
3. Join our Discord Support Server *(link to be added)*

---

## License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

**MIT License provides you the freedom to:**

- Use commercially
- Modify and distribute
- Private use
- Include in other projects

---

## Contributing

We welcome contributions! Here's how to get started:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup

```bash
git clone https://github.com/yourusername/still-waiting.git
cd still-waiting
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env      # Configure your environment
python main.py
```

---

**If you find Still Waiting useful, please star this repository!**
