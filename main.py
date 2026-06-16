import discord
from discord.ext import commands
import asyncio
from dotenv import load_dotenv
import logging
from pathlib import Path
from datetime import datetime, timezone

from utils.config import Config

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('BlastBot')


class BlastBot(commands.Bot):
    """Main bot class với custom initialization"""
    
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True

        self.logger = logging.getLogger('BlastBot')
        
        super().__init__(
            command_prefix=Config.DEFAULT_PREFIX,
            intents=intents,
            help_command=None  # Disable default help command
        )
        
        # Auto-discover extensions from cogs folder
        self.initial_extensions = self._discover_extensions()
        
        # Thời gian khởi động bot
        self.start_time = None
        
        # Shared database connection
        self.db = None
        self._persistent_views_registered = False
    
    async def setup_hook(self):
        """Called when the bot is starting up"""
        logger.info("Đang tải extensions...")

        from utils.database import Database
        self.db = Database()
        await self.db.connect()
        
        # Set up tree error handler
        self.tree.on_error = self.on_app_command_error
        
        # Load all cogs
        for ext in self.initial_extensions:
            try:
                await self.load_extension(ext)
                logger.info(f"✅ Đã tải {ext}")
            except Exception as e:
                logger.error(f"❌ Không thể tải {ext}: {e}")

        # Sync commands (global hoặc guild-specific cho testing)
        guild_id = Config.GUILD_ID
        if guild_id and guild_id.strip():
            try:
                gid = int(guild_id.strip())
            except ValueError:
                logger.error(f"GUILD_ID không hợp lệ ('{guild_id}'), sẽ sync global.")
                gid = None

            if gid:
                guild = discord.Object(id=gid)
                self.tree.copy_global_to(guild=guild)
                synced = await self.tree.sync(guild=guild)
                logger.info(f"Đã sync {len(synced)} commands cho guild {gid}")
            else:
                synced = await self.tree.sync()
                logger.info(f"Đã sync {len(synced)} commands globally")
        else:
            synced = await self.tree.sync()
            logger.info(f"Đã sync {len(synced)} commands globally")

    def _discover_modules(self, base_path: Path, package: str) -> list[str]:
        modules = []
        if not base_path.exists():
            return modules

        for item in base_path.iterdir():
            if item.name.startswith('_') or item.name.startswith('.'):
                continue

            if item.is_dir():
                init_file = item / '__init__.py'
                if init_file.exists():
                    modules.append(f'{package}.{item.name}')
            elif item.is_file() and item.suffix == '.py' and item.stem != '__init__':
                modules.append(f'{package}.{item.stem}')

        return modules

    def _discover_extensions(self) -> list[str]:
        """Tự động tìm và load tất cả extension modules."""
        extensions = []
        base_path = Path(__file__).parent

        extensions.extend(self._discover_modules(base_path / 'cogs', 'cogs'))
        extensions.extend(self._discover_modules(base_path / 'events', 'events'))

        logger.info(f"Đã phát hiện {len(extensions)} extensions: {', '.join(extensions)}")
        return extensions

    async def _register_persistent_views(self):
        """Đăng ký lại các persistent role menu views đã lưu trong DB."""
        if self._persistent_views_registered or not self.db:
            return

        try:
            from cogs.utilities.roles import RoleMenuView

            menus = await self.db.get_role_menus()
            registered = 0

            for menu in menus:
                guild = self.get_guild(menu['guild_id'])
                if not guild:
                    continue

                roles = [guild.get_role(rid) for rid in menu['role_ids']]
                roles = [r for r in roles if r is not None]

                if not roles:
                    await self.db.delete_role_menu(menu['message_id'])
                    continue

                view = RoleMenuView(
                    roles=roles,
                    mode=menu['mode'],
                    message_id=menu['message_id']
                )

                channel = self.get_channel(menu['channel_id'])
                if channel and hasattr(channel, 'fetch_message'):
                    try:
                        message = await channel.fetch_message(menu['message_id'])
                        await message.edit(view=view)
                    except discord.NotFound:
                        await self.db.delete_role_menu(menu['message_id'])
                        continue
                    except discord.Forbidden:
                        logger.warning(
                            f"Không đủ quyền cập nhật role menu {menu['message_id']} trong channel {menu['channel_id']}"
                        )
                    except discord.HTTPException as e:
                        logger.warning(
                            f"Không thể cập nhật role menu {menu['message_id']}: {e}"
                        )

                self.add_view(view, message_id=menu['message_id'])
                registered += 1

            from utils.modals import SuggestionVotingView
            self.add_view(SuggestionVotingView(self.db))

            self._persistent_views_registered = True
            logger.info(f"Đã đăng ký lại {registered} persistent role menu views")
        except Exception as e:
            logger.error(f"❌ Không thể đăng ký persistent views: {e}", exc_info=True)
    
    async def on_ready(self):
        """Called when bot is ready"""
        if self.user:
            logger.info(f"🚀 Bot đã sẵn sàng! Đăng nhập với tên: {self.user.name}")
        logger.info(f"📊 Đang hoạt động trên {len(self.guilds)} servers")
        
        # Lưu thời gian khởi động
        self.start_time = datetime.now(timezone.utc)
        logger.info(f"⏰ Bot khởi động lúc: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")

        await self._register_persistent_views()
        
        # Set bot status
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="your server"
            )
        )
    
    async def close(self):
        """Graceful shutdown"""
        logger.info("🛑 Đang tắt bot...")

        if getattr(self, 'db', None):
            try:
                await self.db.close()
                logger.info("✅ Đã đóng database")
            except Exception as e:
                logger.error(f"❌ Lỗi khi đóng database: {e}", exc_info=True)
        
        # Call parent close
        await super().close()
        logger.info("✅ Bot đã tắt hoàn toàn")
    
    async def on_app_command_error(
        self,
        interaction: discord.Interaction,
        error: discord.app_commands.AppCommandError
    ):
        """Global error handler for slash commands"""
        from utils.error_handler import handle_command_error
        
        # Handle CommandNotFound separately (cache issue)
        if isinstance(error, discord.app_commands.CommandNotFound):
            logger.warning(
                f"Command '{error.name}' không tồn tại nhưng vẫn được gọi bởi {interaction.user}. "
                f"Discord đang cache command cũ. Đã tự động clear trong lần sync tiếp theo."
            )
            try:
                await interaction.response.send_message(
                    "⚠️ Lệnh này đã bị xóa. Vui lòng reload Discord (Ctrl+R) để cập nhật danh sách lệnh.",
                    ephemeral=True
                )
            except (discord.InteractionResponded, discord.HTTPException):
                pass
            return
        
        # Unwrap the error if it's wrapped
        original_error = getattr(error, 'original', error)
        
        await handle_command_error(interaction, original_error)
    
async def main():
    """Main entry point"""
    # Check for token
    token = Config.TOKEN
    if not token:
        logger.error("❌ Không tìm thấy DISCORD_TOKEN trong file .env!")
        logger.error("Vui lòng tạo file .env và thêm token của bạn.")
        return
    
    # Validate token format (basic check)
    from utils.constants import BOT_CONFIG
    
    if not token.strip() or len(token) < BOT_CONFIG['min_token_length']:
        logger.error(f"❌ DISCORD_TOKEN không hợp lệ! Token phải có ít nhất {BOT_CONFIG['min_token_length']} ký tự.")
        logger.error("Vui lòng kiểm tra lại token trong file .env")
        return
    
    # Create data directory if not exists
    Path('data').mkdir(exist_ok=True)

    bot = BlastBot()
    async with bot:
        try:
            await bot.start(token)
        except KeyboardInterrupt:
            logger.info("⚠️ Nhận tín hiệu KeyboardInterrupt (Ctrl+C)")
        except discord.LoginFailure:
            logger.error("❌ Token không hợp lệ! Không thể đăng nhập vào Discord.")
        except Exception as e:
            logger.error(f"❌ Lỗi khi chạy bot: {e}", exc_info=True)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("✅ Bot đã được tắt bởi người dùng")
    except Exception as e:
        logger.error(f"❌ Lỗi nghiêm trọng: {e}", exc_info=True)
