"""Utilities module - Role management commands"""

from .roles import RolesCommand
from .feedback import Feedback


async def setup(bot):
	"""Load all utility commands"""
	await bot.add_cog(RolesCommand(bot))
	await bot.add_cog(Feedback(bot))
