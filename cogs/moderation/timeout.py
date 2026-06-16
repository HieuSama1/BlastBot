"""Timeout command"""

import discord
from discord import app_commands
from discord.ext import commands
from datetime import timedelta
import logging
from utils.embeds import success_embed, error_embed, warning_embed
from utils.views import ConfirmView
from utils.constants import COMMAND_COOLDOWNS
from .base import BaseModerationCog, validate_duration


TIMEOUT_REASONS = [
    "Spam nhẹ",
    "Off-topic liên tục",
    "Cãi vã",
    "Cần cooldown",
    "Vi phạm nhỏ",
]


async def timeout_reason_autocomplete(
    interaction: discord.Interaction,
    current: str,
) -> list[app_commands.Choice[str]]:
    """Autocomplete cho timeout reason"""
    filtered = [r for r in TIMEOUT_REASONS if current.lower() in r.lower()]
    return [
        app_commands.Choice(name=reason, value=reason)
        for reason in filtered[:25]
    ]


class TimeoutCommand(BaseModerationCog):
    """Timeout command cog"""
    
    def __init__(self, bot):
        super().__init__(bot)
    
    @app_commands.command(
        name="timeout",
        description="⏱️ Timeout member tạm thời (1 phút - 7 ngày)"
    )
    @app_commands.describe(
        member="Member cần timeout",
        duration="Thời gian timeout (phút)",
        reason="Lý do timeout"
    )
    @app_commands.autocomplete(reason=timeout_reason_autocomplete)
    @app_commands.guild_only()
    @app_commands.default_permissions(moderate_members=True)
    @app_commands.checks.cooldown(1, COMMAND_COOLDOWNS['timeout'], key=lambda i: i.user.id)
    async def timeout(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        duration: int,
        reason: str = "Không có lý do"
    ):
        """Timeout member"""
        try:
            # Validate permissions
            if not await self.validate_permissions(interaction, 'moderate_members'):
                return
            
            # Validate target
            is_valid, error_msg = await self.validate_target(interaction, member)
            if not is_valid:
                await self.send_error(interaction, error_msg or "Invalid target")
                return
            
            # Validate hierarchy
            is_valid, error_msg = await self.validate_hierarchy(interaction, member, "timeout member này")
            if not is_valid:
                await self.send_error(interaction, error_msg or "Hierarchy check failed")
                return
            
            # Validate duration (1-10080 phút = 7 ngày)
            is_valid, error_msg = validate_duration(duration, 1, 10080)
            if not is_valid:
                await self.send_error(interaction, f"Thời gian timeout phải từ 1 phút đến 7 ngày (10080 phút)!")
                return
            
            # Xác nhận
            view = ConfirmView(interaction.user)
            await interaction.response.send_message(
                embed=warning_embed(
                    "Xác nhận timeout",
                    f"Bạn có chắc muốn timeout {member.mention}?\n"
                    f"**Thời gian:** {duration} phút\n"
                    f"**Lý do:** {reason}"
                ),
                view=view,
                ephemeral=True
            )
            
            await view.wait()
            
            if not view.value:
                await interaction.edit_original_response(
                    embed=error_embed("Đã hủy", "Đã hủy thao tác timeout."),
                    view=None
                )
                return
            
            # Thực hiện timeout
            timeout_until = timedelta(minutes=duration)
            await member.timeout(timeout_until, reason=f"{interaction.user}: {reason}")
            
            self.logger.info(f"{interaction.user} timed out {member} for {duration}m - Reason: {reason}")
            
            # Log moderation action
            if interaction.guild and isinstance(interaction.user, discord.Member):
                await self.log_moderation_action(
                    interaction.guild,
                    interaction.user,
                    "timeout",
                    member,
                    reason,
                    f"Duration: {duration} minutes"
                )
            
            await interaction.edit_original_response(
                embed=success_embed(
                    "Đã timeout",
                    f"{member.mention} đã bị timeout {duration} phút.\n**Lý do:** {reason}"
                ),
                view=None
            )
        except Exception as e:
            self.logger.error(f"Error in timeout command: {e}", exc_info=True)
            await self.safe_error_response(interaction, "Lỗi", f"Không thể timeout: {str(e)}")
