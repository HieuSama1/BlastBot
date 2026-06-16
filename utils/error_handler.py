"""Error handling utilities và custom exceptions"""

import discord
from discord import app_commands
import logging
from typing import Optional
from functools import wraps

logger = logging.getLogger('BlastBot.ErrorHandler')


class BotError(Exception):
    """Base exception cho bot"""
    def __init__(self, message: str, user_message: Optional[str] = None):
        self.message = message
        self.user_message = user_message or message
        super().__init__(message)


class DatabaseError(BotError):
    """Exception cho database errors"""
    pass


class ValidationError(BotError):
    """Exception cho validation errors"""
    pass


class BotPermissionError(BotError):
    """Exception cho permission errors"""
    pass


# Centralized error messages
ERROR_MESSAGES = {
    'api_error': '❌ Lỗi kết nối với Discord API. Vui lòng thử lại sau.',
    'database_error': '❌ Lỗi database. Thao tác không thành công.',
    'rate_limit': '⏰ Bạn đang dùng lệnh quá nhanh! Vui lòng đợi {remaining:.1f}s.',
    'missing_permissions': '🔒 Bạn không có quyền thực hiện lệnh này!',
    'bot_missing_permissions': '🔒 Bot không có đủ quyền để thực hiện hành động này!',
    'invalid_input': '❌ Dữ liệu đầu vào không hợp lệ.',
    'user_not_found': '❌ Không tìm thấy người dùng.',
    'guild_only': '❌ Lệnh này chỉ có thể sử dụng trong server!',
    'dm_only': '❌ Lệnh này chỉ có thể sử dụng trong tin nhắn riêng!',
    'unknown_error': '❌ Đã xảy ra lỗi không xác định. Vui lòng thử lại sau.',
}


def get_error_message(error_type: str, **kwargs) -> str:
    """Lấy error message với format"""
    message = ERROR_MESSAGES.get(error_type, ERROR_MESSAGES['unknown_error'])
    return message.format(**kwargs) if kwargs else message


async def send_error_embed(
    interaction: discord.Interaction,
    title: str,
    description: str,
    ephemeral: bool = True
):
    """Gửi error embed đến user"""
    embed = discord.Embed(
        title=title,
        description=description,
        color=0xED4245  # Red
    )
    
    try:
        if interaction.response.is_done():
            await interaction.followup.send(embed=embed, ephemeral=ephemeral)
        else:
            await interaction.response.send_message(embed=embed, ephemeral=ephemeral)
    except discord.HTTPException as e:
        logger.error(f"Failed to send error message: {e}")


async def handle_command_error(interaction: discord.Interaction, error: Exception):
    """Xử lý lỗi command với logging và user feedback"""
    # Log error với context
    command_name = interaction.command.name if interaction.command else "Unknown"
    logger.error(
        f"Error in command '{command_name}' by {interaction.user} "
        f"in guild {interaction.guild_id}: {error}",
        exc_info=True
    )
    
    # Xác định error type và message
    if isinstance(error, app_commands.CommandOnCooldown):
        message = get_error_message('rate_limit', remaining=error.retry_after)
        await send_error_embed(interaction, "Cooldown", message)
    
    elif isinstance(error, app_commands.MissingPermissions):
        message = get_error_message('missing_permissions')
        await send_error_embed(interaction, "Thiếu quyền", message)
    
    elif isinstance(error, app_commands.BotMissingPermissions):
        message = get_error_message('bot_missing_permissions')
        await send_error_embed(interaction, "Bot thiếu quyền", message)
    
    elif isinstance(error, app_commands.CheckFailure):
        message = "❌ Bạn không thể sử dụng lệnh này!"
        await send_error_embed(interaction, "Kiểm tra thất bại", message)
    
    elif isinstance(error, discord.Forbidden):
        message = get_error_message('bot_missing_permissions')
        await send_error_embed(interaction, "Forbidden", message)
    
    elif isinstance(error, discord.NotFound):
        message = "❌ Không tìm thấy tài nguyên được yêu cầu."
        await send_error_embed(interaction, "Not Found", message)
    
    elif isinstance(error, discord.HTTPException):
        if error.status == 429:  # Rate limited
            message = "⏰ Discord API đang rate limit. Vui lòng đợi giây lát."
        else:
            message = get_error_message('api_error')
        await send_error_embed(interaction, "Discord API Error", message)
    
    elif isinstance(error, DatabaseError):
        message = get_error_message('database_error')
        await send_error_embed(interaction, "Database Error", message)
    
    elif isinstance(error, ValidationError):
        message = error.user_message
        await send_error_embed(interaction, "Validation Error", message)
    
    else:
        message = get_error_message('unknown_error')
        await send_error_embed(interaction, "Unknown Error", message)


def with_error_handling(func):
    """Decorator để wrap command với error handling"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            # Tìm interaction từ args
            interaction = None
            for arg in args:
                if isinstance(arg, discord.Interaction):
                    interaction = arg
                    break
            
            if interaction:
                await handle_command_error(interaction, e)
            else:
                logger.error(f"Error in {func.__name__}: {e}", exc_info=True)
            raise
    
    return wrapper


# Validation helpers
def validate_string_length(text: str, min_len: int = 1, max_len: int = 2000) -> str:
    """Validate và sanitize string input"""
    text = text.strip()
    if len(text) < min_len:
        raise ValidationError(
            f"Text too short (min {min_len} characters)",
            f"❌ Văn bản quá ngắn (tối thiểu {min_len} ký tự)!"
        )
    if len(text) > max_len:
        raise ValidationError(
            f"Text too long (max {max_len} characters)",
            f"❌ Văn bản quá dài (tối đa {max_len} ký tự)!"
        )
    return text


def validate_member_hierarchy(
    moderator: discord.Member,
    target: discord.Member,
    bot_member: discord.Member
) -> tuple[bool, Optional[str]]:
    """
    Validate hierarchy cho moderation actions
    Returns: (is_valid, error_message)
    """
    # Check moderator hierarchy
    if target.top_role >= moderator.top_role:
        return False, "❌ Bạn không thể thực hiện hành động này với member có role cao hơn hoặc bằng bạn!"
    
    # Check bot hierarchy
    if target.top_role >= bot_member.top_role:
        return False, "❌ Bot không thể thực hiện hành động này với member có role cao hơn hoặc bằng bot!"
    
    return True, None


def validate_number_range(
    value: int,
    min_val: int,
    max_val: int,
    param_name: str = "Giá trị"
) -> int:
    """Validate số trong khoảng cho phép"""
    if value < min_val or value > max_val:
        raise ValidationError(
            f"Value {value} out of range [{min_val}, {max_val}]",
            f"❌ {param_name} phải từ {min_val} đến {max_val}!"
        )
    return value
