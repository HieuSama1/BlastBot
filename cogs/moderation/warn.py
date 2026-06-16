import discord
from discord import app_commands
from discord.ext import commands

from .base import BaseModerationCog


class WarnCommand(BaseModerationCog):
    @app_commands.command(name="warn", description="Cảnh cáo một thành viên")
    @app_commands.describe(member="Thành viên cần cảnh cáo", reason="Lý do")
    @app_commands.default_permissions(moderate_members=True)
    @app_commands.guild_only()
    async def warn(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        reason: str = "Không có lý do",
    ):
        await interaction.response.defer(ephemeral=True)

        if not await self.validate_permissions(interaction, "moderate_members"):
            return

        is_valid, error_msg = await self.validate_hierarchy(interaction, member)
        if not is_valid:
            await self.send_error(interaction, error_msg or "Không hợp lệ", use_followup=True)
            return

        count = await self.bot.db.add_warning(interaction.guild.id, member.id)

        await self.log_moderation_action(
            interaction.guild,
            interaction.user,
            "warn",
            target=member,
            reason=reason,
        )
        await interaction.followup.send(
            f"✅ Đã cảnh cáo {member.mention}. Tổng cảnh cáo: **{count}**.",
            ephemeral=True,
        )

    @app_commands.command(name="warnings", description="Xem số cảnh cáo của thành viên")
    @app_commands.describe(member="Thành viên")
    @app_commands.default_permissions(moderate_members=True)
    @app_commands.guild_only()
    async def warnings(self, interaction: discord.Interaction, member: discord.Member):
        count = await self.bot.db.get_warnings(interaction.guild.id, member.id)
        await interaction.response.send_message(
            f"{member.mention} có **{count}** cảnh cáo.", ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(WarnCommand(bot))