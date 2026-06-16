"""Moderation module - Các lệnh quản lý server"""

from .base import BaseModerationCog, validate_duration, validate_amount
from .kick import KickCommand
from .ban import BanCommand
from .timeout import TimeoutCommand
from .clear import ClearCommand
from .warn import WarnCommand


async def setup(bot):
	"""Load all moderation commands"""
	await bot.add_cog(KickCommand(bot))
	await bot.add_cog(BanCommand(bot))
	await bot.add_cog(TimeoutCommand(bot))
	await bot.add_cog(ClearCommand(bot))
	await bot.add_cog(WarnCommand(bot))
