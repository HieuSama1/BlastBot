# BlastBot 🚀

Modern Discord bot with slash commands và các công cụ moderation/feedback thực tế.

## ✨ Features

- **Slash Commands** - Modern Discord interactions with autocomplete
- **Moderation Suite** - Kick, ban, timeout, and message management
- **Role Management** - Interactive role menus with button/select controls
- **Context Menus** - Right-click actions on users and messages
- **Feedback** - Suggestion modal với voting persistent
- **Moderation Warnings** - Warn và warnings tracking
- **Database** - SQLite with async operations and smart caching
- **Error Handling** - Comprehensive error handling with user-friendly messages
- **Logging** - Console output and UTF-8 file logging

## 🏗️ Architecture

```
BlastBot/
├── main.py              # Main entry point with BlastBot class
├── cogs/                # Modular command groups
│   ├── core/           # Help and core functionality
│   ├── interactions/   # Context menus
│   ├── moderation/     # Mod commands (kick, ban, timeout, clear)
│   └── utilities/      # Role management
├── events/             # Event handlers
├── utils/              # Helper modules
│   ├── database.py     # Async database with caching
│   ├── embeds.py       # Embed builders
│   ├── views.py        # Interactive UI components
│   └── error_handler.py
└── data/               # Database storage
```

## 📦 Installation

### Prerequisites
- Python 3.12 or higher
- Discord Bot Token ([Get one here](https://discord.com/developers/applications))

### Setup Steps

1. **Clone the repository:**
```bash
git clone <repository-url>
cd BlastBot
```

2. **Create virtual environment (recommended):**
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables:**
```bash
# Copy the example file
cp .env.example .env

# Edit .env with your values
DISCORD_TOKEN=your_discord_bot_token_here
GUILD_ID=your_test_guild_id  # Optional, for faster testing
BOT_PREFIX=!
DB_PATH=./data/bot.db
OWNER_ID=your_user_id  # Optional
```

5. **Run the bot:**
```bash
python main.py
```

## 🎮 Commands

### Moderation
- `/kick <member> [reason]` - Kick a member from the server
- `/ban <member> [reason] [delete_messages]` - Ban a member
- `/timeout <member> <duration> [reason]` - Timeout a member
- `/clear <amount>` - Clear messages from channel
- `/warn <member> [reason]` - Cảnh cáo một thành viên
- `/warnings <member>` - Xem số cảnh cáo của thành viên

### Roles
- `/rolemenu` - Create an interactive role selection menu
- `/roleinfo <role>` - Display detailed role information
- `/roleadd <role>` - Add a role to yourself or others
- `/roleremove <role>` - Remove a role

### Core
- `/help [command]` - Show available commands or specific command info
- `/suggest` - Gửi góp ý cho server

### Context Menus
Right-click on users or messages for quick actions:
- **User Info** - View detailed user information
- **Avatar** - Display user's avatar in full size
- **Report User** - Open a report modal for a user
- **Report Message** - Open a report modal for a message
- **Bookmark Message** - Send a message bookmark to DM

## ⚙️ Configuration

### Required Environment Variables
- `DISCORD_TOKEN` - Your Discord bot token
- `DB_PATH` - Path to SQLite database file (default: `./data/bot.db`)

### Optional Environment Variables
- `GUILD_ID` - Guild ID for testing (enables instant command sync)
- `BOT_PREFIX` - Command prefix for hybrid commands (default: `!`)
- `DEBUG_MODE` - Enable debug logging (default: `False`)
- `OWNER_ID` - Your Discord user ID cho các lệnh owner-only

## 🗃️ Database

BlastBot uses **async SQLite** via `aiosqlite` with the following features:
- **Guild configurations** - Per-server settings and preferences
- **User data** - Warnings tracking
- **Smart caching** - 5-minute TTL cache for frequently accessed data
- **Automatic initialization** - Tables created on first run

### Cache Management
```python
from utils.database import Database

# Invalidate cache for specific guild
Database.invalidate_cache(guild_id)

# Clear all cache
Database.invalidate_cache()

# Get cache statistics
stats = Database.get_cache_stats()
```

## 🛠️ Development

### Project Structure
- **Cogs** - All commands are organized as cogs in `cogs/` folder
- **Auto-discovery** - Cogs are automatically discovered and loaded
- **Base Classes** - `BaseModerationCog` provides shared functionality
- **Utils** - Reusable components in `utils/` (embeds, views, constants)

### Adding New Commands

1. Create a new cog in appropriate subfolder:
```python
# cogs/utilities/example.py
from discord.ext import commands
from discord import app_commands

class Example(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="example")
    async def example(self, interaction: discord.Interaction):
        await interaction.response.send_message("Hello!")

async def setup(bot):
    await bot.add_cog(Example(bot))
```

2. The cog will be automatically loaded on next restart!

### Testing
For faster testing, set `GUILD_ID` in `.env` to your test server ID. This enables instant command sync instead of the 1-hour global sync delay.

## 📝 Logging

Logs are stored in:
- **Console** - Real-time output
- **bot.log** - UTF-8 file log

Lưu ý: hiện chưa bật log rotation.

Log levels:
- `INFO` - Normal operations
- `WARNING` - Non-critical issues
- `ERROR` - Errors with stack traces
- `DEBUG` - Detailed debug information

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

This project is licensed under the GNU Affero General Public License v3.0 (AGPL-3.0) - see the [LICENSE](LICENSE) file for details.

**Note:** AGPL-3.0 requires that if you run a modified version of this software as a network service, you must make the complete source code available to users of that service.

## 🐛 Troubleshooting

### Commands not appearing?
- Check that `GUILD_ID` is set correctly in `.env`
- Wait up to 1 hour for global command sync
- Reload Discord client (Ctrl+R)

### Database errors?
- Ensure `data/` folder exists and is writable
- Check `DB_PATH` in `.env`
- Delete `data/bot.db` to reset (will lose data)

### Bot not responding?
- Verify `DISCORD_TOKEN` is correct
- Check bot has required permissions in server
- Review `bot.log` for error messages

## 🔗 Links

- [Discord.py Documentation](https://discordpy.readthedocs.io/)
- [Discord Developer Portal](https://discord.com/developers/applications)

---

Made with ❤️ using discord.py
