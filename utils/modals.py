"""Modal forms cho input phức tạp"""

import discord
import logging

logger = logging.getLogger('BlastBot.Modals')


class ReportModal(discord.ui.Modal, title="Báo cáo người dùng/tin nhắn"):
    """Modal để report user hoặc message"""
    
    reason = discord.ui.TextInput(
        label="Lý do báo cáo",
        placeholder="Spam, vi phạm quy tắc, nội dung không phù hợp...",
        required=True,
        max_length=100,
        style=discord.TextStyle.short
    )
    
    details = discord.ui.TextInput(
        label="Chi tiết",
        placeholder="Mô tả chi tiết về vấn đề...",
        required=True,
        max_length=1000,
        style=discord.TextStyle.paragraph
    )
    
    def __init__(self, target_id: int, target_type: str = "user", **kwargs):
        super().__init__(**kwargs)
        self.target_id = target_id
        self.target_type = target_type  # "user" or "message"
    
    async def on_submit(self, interaction: discord.Interaction):
        """Xử lý khi submit report"""
        from utils.embeds import success_embed, create_embed
        from utils.constants import COLORS
        
        # Tạo report embed
        report_embed = create_embed(
            title=f"📢 Báo cáo mới - {self.target_type.title()}",
            description=f"**Người báo cáo:** {interaction.user.mention}\n"
                       f"**Target ID:** {self.target_id}",
            color=COLORS['warning']
        )
        report_embed.add_field(name="Lý do", value=self.reason.value, inline=False)
        report_embed.add_field(name="Chi tiết", value=self.details.value, inline=False)
        report_embed.set_footer(text=f"Report ID: {interaction.id}")
        
        # Gửi vào log channel nếu có
        if interaction.guild:
            try:
                from utils.database import Database
                db = getattr(interaction.client, 'db', None)
                created_local_db = False
                if db is None:
                    db = Database()
                    await db.connect()
                    created_local_db = True

                config = await db.get_guild_config(interaction.guild.id)
                
                if config.get('log_channel_id'):
                    log_channel = interaction.guild.get_channel(config['log_channel_id'])
                    if log_channel and isinstance(log_channel, (discord.TextChannel, discord.Thread)):
                        await log_channel.send(embed=report_embed)
            except Exception as e:
                logger.error(f"Failed to send report to log channel: {e}")
            finally:
                if 'created_local_db' in locals() and created_local_db:
                    await db.close()
        
        # Xác nhận với user
        await interaction.response.send_message(
            embed=success_embed(
                "Báo cáo đã gửi",
                "Cảm ơn bạn đã báo cáo. Đội ngũ quản lý sẽ xem xét sớm nhất."
            ),
            ephemeral=True
        )
        
        logger.info(f"Report submitted by {interaction.user} for {self.target_type} {self.target_id}")


class SuggestionModal(discord.ui.Modal, title="Gửi góp ý"):
    """Modal để gửi suggestion"""

    suggestion = discord.ui.TextInput(
        label="Góp ý",
        placeholder="Chia sẻ góp ý của bạn...",
        required=True,
        max_length=1000,
        style=discord.TextStyle.paragraph,
    )

    def __init__(self, bot: discord.Client):
        super().__init__()
        self.bot = bot

    async def on_submit(self, interaction: discord.Interaction):
        """Post suggestion với voting buttons"""
        suggestion_embed = discord.Embed(
            title="💡 Góp ý mới",
            description=self.suggestion.value,
            color=discord.Color.blurple(),
        )
        suggestion_embed.set_author(
            name=str(interaction.user),
            icon_url=interaction.user.display_avatar.url,
        )
        suggestion_embed.set_footer(text=f"Suggestion ID: {interaction.id}")

        view = SuggestionVotingView(getattr(self.bot, 'db', None))
        await interaction.response.send_message(embed=suggestion_embed, view=view)

        if interaction.guild and getattr(self.bot, 'db', None):
            message = await interaction.original_response()
            await self.bot.db.register_suggestion_message(interaction.guild.id, message.id)

        logger.info(f"Suggestion posted by {interaction.user}: {self.suggestion.value}")


class SuggestionVotingView(discord.ui.View):
    """Persistent view voting suggestion, lưu vote vào DB."""

    def __init__(self, db=None):
        super().__init__(timeout=None)
        self.db = db

    def _update_labels(self, up: int, down: int):
        for child in self.children:
            if getattr(child, "custom_id", "") == "suggestion_upvote":
                child.label = f"👍 {up}"
            elif getattr(child, "custom_id", "") == "suggestion_downvote":
                child.label = f"👎 {down}"

    async def _handle_vote(self, interaction: discord.Interaction, vote: int):
        if interaction.message is None:
            await interaction.response.send_message(
                "❌ Không xác định được tin nhắn suggestion. Vui lòng thử lại.",
                ephemeral=True,
            )
            return

        db = self.db or getattr(interaction.client, 'db', None)
        if db is None:
            await interaction.response.send_message(
                "❌ Hệ thống vote tạm thời không khả dụng.", ephemeral=True
            )
            return

        message_id = interaction.message.id
        user_id = interaction.user.id
        current = await db.get_user_vote(message_id, user_id)

        if current == vote:
            await db.remove_vote(message_id, user_id)
        else:
            await db.set_vote(message_id, user_id, vote)

        up, down = await db.get_vote_counts(message_id)

        self._update_labels(up, down)

        await interaction.response.edit_message(view=self)

    @discord.ui.button(label="👍 0", style=discord.ButtonStyle.success, emoji="👍", custom_id="suggestion_upvote")
    async def upvote_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._handle_vote(interaction, 1)

    @discord.ui.button(label="👎 0", style=discord.ButtonStyle.danger, emoji="👎", custom_id="suggestion_downvote")
    async def downvote_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._handle_vote(interaction, -1)
