import discord
from discord.ext import commands
import traceback
import logging

class ErrorHandler(commands.Cog):
    """A Cog that handles various command execution errors in the Discord bot.
    This cog implements error handling for common command errors like missing permissions,
    command not found, cooldowns etc. It catches exceptions raised during command execution
    and sends appropriate error messages to users.
    Attributes:
        bot: The Discord bot instance this cog is attached to
    Error types handled:
        - CommandNotFound: When an invalid command is used
        - MissingPermissions: When user lacks required permissions
        - BotMissingPermissions: When bot lacks required permissions 
        - MissingRequiredArgument: When required command parameters are missing
        - CommandOnCooldown: When command is used before cooldown expires
        - DisabledCommand: When trying to use a disabled command
        - NoPrivateMessage: When using server-only commands in DM
        - NotOwner: When non-owner tries to use owner-only commands
    Unhandled errors are logged to the bot's logger with full traceback.
    """

    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger('BlastBot.ErrorHandler')

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: Exception):
        """Handles command errors in the bot.
        This event handler catches various command-related errors and responds with appropriate error messages.
        It handles the following error types:
        - CommandNotFound: When the command doesn't exist
        - MissingPermissions: When user lacks required permissions
        - BotMissingPermissions: When bot lacks required permissions
        - MissingRequiredArgument: When a required argument is missing
        - CommandOnCooldown: When command is on cooldown
        - DisabledCommand: When command is disabled
        - NoPrivateMessage: When command can't be used in DMs
        - NotOwner: When command requires bot owner
        - Unhandled errors are logged to the bot's logger
            ctx (commands.Context): The invocation context
            error (Exception): The error that was raised
        Returns:
            None
        """
        if isinstance(error, commands.CommandNotFound):
            await ctx.send("❌ Lệnh không tồn tại!")
            return
            
        if isinstance(error, commands.MissingPermissions):
            perms = ", ".join(error.missing_permissions)
            await ctx.send(f"❌ Bạn cần quyền {perms} để thực hiện lệnh này!")
            return
            
        if isinstance(error, commands.BotMissingPermissions):
            perms = ", ".join(error.missing_permissions)
            await ctx.send(f"❌ Bot cần quyền {perms} để thực hiện lệnh này!")
            return
            
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ Thiếu tham số: {error.param.name}")
            return
            
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"⏳ Vui lòng đợi {error.retry_after:.1f}s để dùng lại lệnh này!")
            return
        
        if isinstance(error, commands.DisabledCommand):
            await ctx.send("❌ Lệnh này đã bị vô hiệu hóa")
            return
            
        if isinstance(error, commands.NoPrivateMessage):
            await ctx.send("❌ Lệnh này chỉ có thể dùng trong server")
            return

        if isinstance(error, commands.NotOwner):
            await ctx.send("❌ Chỉ chủ bot mới dùng được lệnh này")
            return

        # Log lỗi không xác định
        self.logger.error(f"Lỗi trong lệnh {ctx.command}:")
        self.logger.error("".join(traceback.format_exception(type(error), error, error.__traceback__)))

async def setup(bot):
    await bot.add_cog(ErrorHandler(bot))
