import discord
from discord import app_commands
from discord.ext import commands

from utils.modals import SuggestionModal


class Feedback(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="suggest", description="Gửi một góp ý cho server")
    @app_commands.guild_only()
    async def suggest(self, interaction: discord.Interaction):
        await interaction.response.send_modal(SuggestionModal(self.bot))


async def setup(bot: commands.Bot):
    await bot.add_cog(Feedback(bot))