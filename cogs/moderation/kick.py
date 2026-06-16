"""Kick command"""

import discord
from discord import app_commands
from discord.ext import commands
import logging
from utils.embeds import success_embed, error_embed, warning_embed
from utils.views import ConfirmView
from utils.constants import COMMAND_COOLDOWNS
from .base import BaseModerationCog


KICK_REASONS = [
    "Spam",
    "Vi phạm quy tắc",
    "Hành vi độc hại",
    "Quấy rối người khác",
    "Nội dung không phù hợp",
    "Không tuân thủ cảnh báo",
]


async def kick_reason_autocomplete(
    interaction: discord.Interaction,
    current: str,
) -> list[app_commands.Choice[str]]:
    """Autocomplete cho kick reason"""
    filtered = [r for r in KICK_REASONS if current.lower() in r.lower()]
    return [
        app_commands.Choice(name=reason, value=reason)
        for reason in filtered[:25]
    ]


class KickCommand(BaseModerationCog):
    """Kick command cog"""
    
    def __init__(self, bot):
        super().__init__(bot)
    
    @app_commands.command(
        name="kick",
        description="🦵 Kick một member khỏi server (member có thể join lại)"
    )
    @app_commands.describe(
        member="Member cần kick",
        reason="Lý do kick"
    )
    @app_commands.autocomplete(reason=kick_reason_autocomplete)
    @app_commands.guild_only()
    @app_commands.default_permissions(kick_members=True)
    @app_commands.checks.cooldown(1, COMMAND_COOLDOWNS['kick'], key=lambda i: i.user.id)
    async def kick(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        reason: str = "Không có lý do"
    ):
        """Kick member khỏi server"""
        try:
            # Validate permissions
            if not await self.validate_permissions(interaction, 'kick_members'):
                return
            
            # Validate target
            is_valid, error_msg = await self.validate_target(interaction, member)
            if not is_valid:
                await self.send_error(interaction, error_msg or "Invalid target")
                return
            
            # Validate hierarchy
            is_valid, error_msg = await self.validate_hierarchy(interaction, member, "kick member này")
            if not is_valid:
                await self.send_error(interaction, error_msg or "Hierarchy check failed")
                return
            
            # Xác nhận
            view = ConfirmView(interaction.user)
            await interaction.response.send_message(
                embed=warning_embed(
                    "Xác nhận kick",
                    f"Bạn có chắc muốn kick {member.mention}?\n**Lý do:** {reason}"
                ),
                view=view,
                ephemeral=True
            )
            
            await view.wait()
            
            if not view.value:
                await interaction.edit_original_response(
                    embed=error_embed("Đã hủy", "Đã hủy thao tác kick."),
                    view=None
                )
                return
            
            # Thực hiện kick
            await member.kick(reason=f"{interaction.user}: {reason}")
            
            self.logger.info(f"{interaction.user} kicked {member} - Reason: {reason}")
            
            # Log moderation action
            if interaction.guild and isinstance(interaction.user, discord.Member):
                await self.log_moderation_action(
                    interaction.guild,
                    interaction.user,
                    "kick",
                    member,
                    reason
                )
            
            await interaction.edit_original_response(
                embed=success_embed(
                    "Đã kick",
                    f"{member.mention} đã được kick khỏi server.\n**Lý do:** {reason}"
                ),
                view=None
            )
        except Exception as e:
            self.logger.error(f"Error in kick command: {e}", exc_info=True)
            await self.safe_error_response(interaction, "Lỗi", f"Không thể kick: {str(e)}")
