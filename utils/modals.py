"""Modal forms cho input phức tạp"""

import discord
from typing import Optional
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
    
    title_field = discord.ui.TextInput(
        label="Tiêu đề",
        placeholder="Tóm tắt ý tưởng của bạn...",
        required=True,
        max_length=100,
        style=discord.TextStyle.short
    )
    
    description = discord.ui.TextInput(
        label="Mô tả chi tiết",
        placeholder="Giải thích ý tưởng của bạn...",
        required=True,
        max_length=1000,
        style=discord.TextStyle.paragraph
    )
    
    reason = discord.ui.TextInput(
        label="Tại sao feature này hữu ích?",
        placeholder="Lợi ích cho server/community...",
        required=False,
        max_length=500,
        style=discord.TextStyle.paragraph
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        """Post suggestion với voting buttons"""
        from utils.embeds import create_embed
        from utils.constants import COLORS
        
        suggestion_embed = create_embed(
            title=f"💡 {self.title_field.value}",
            description=self.description.value,
            color=COLORS['info']
        )
        
        if self.reason.value:
            suggestion_embed.add_field(
                name="Lý do",
                value=self.reason.value,
                inline=False
            )
        
        suggestion_embed.set_author(
            name=f"Suggestion từ {interaction.user.display_name}",
            icon_url=interaction.user.display_avatar.url
        )
        suggestion_embed.set_footer(text=f"Suggestion ID: {interaction.id}")
        
        # Tạo voting view
        view = SuggestionVotingView()
        
        # Gửi suggestion
        await interaction.response.send_message(
            embed=suggestion_embed,
            view=view
        )
        
        # Add reactions cho voting
        message = await interaction.original_response()
        await message.add_reaction("👍")
        await message.add_reaction("👎")
        
        logger.info(f"Suggestion posted by {interaction.user}: {self.title_field.value}")


class BugReportModal(discord.ui.Modal, title="Báo cáo lỗi"):
    """Modal để report bug"""
    
    bug_title = discord.ui.TextInput(
        label="Lỗi gì?",
        placeholder="Tóm tắt lỗi...",
        required=True,
        max_length=100,
        style=discord.TextStyle.short
    )
    
    steps = discord.ui.TextInput(
        label="Các bước tái hiện",
        placeholder="1. Gõ lệnh...\n2. Click vào...\n3. Lỗi xảy ra...",
        required=True,
        max_length=500,
        style=discord.TextStyle.paragraph
    )
    
    expected = discord.ui.TextInput(
        label="Kết quả mong đợi",
        placeholder="Bot nên làm gì...",
        required=True,
        max_length=300,
        style=discord.TextStyle.short
    )
    
    actual = discord.ui.TextInput(
        label="Kết quả thực tế",
        placeholder="Bot đã làm gì...",
        required=True,
        max_length=300,
        style=discord.TextStyle.short
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        """Gửi bug report"""
        from utils.embeds import create_embed
        from utils.constants import COLORS
        
        bug_embed = create_embed(
            title=f"🐛 Bug Report: {self.bug_title.value}",
            color=COLORS['error']
        )
        
        bug_embed.add_field(name="Các bước tái hiện", value=self.steps.value, inline=False)
        bug_embed.add_field(name="Mong đợi", value=self.expected.value, inline=True)
        bug_embed.add_field(name="Thực tế", value=self.actual.value, inline=True)
        
        bug_embed.set_author(
            name=f"Reported by {interaction.user.display_name}",
            icon_url=interaction.user.display_avatar.url
        )
        bug_embed.set_footer(text=f"Bug ID: {interaction.id}")
        
        # Gửi vào log channel
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
                        await log_channel.send(embed=bug_embed)
            except Exception as e:
                logger.error(f"Failed to send bug report: {e}")
            finally:
                if 'created_local_db' in locals() and created_local_db:
                    await db.close()
        
        from utils.embeds import success_embed
        await interaction.response.send_message(
            embed=success_embed(
                "Bug report đã gửi",
                "Cảm ơn bạn! Chúng tôi sẽ xem xét và sửa lỗi sớm nhất."
            ),
            ephemeral=True
        )
        
        logger.info(f"Bug report from {interaction.user}: {self.bug_title.value}")


class SuggestionVotingView(discord.ui.View):
    """View cho voting suggestion"""
    
    def __init__(self):
        super().__init__(timeout=None)  # Persistent view
        self.upvotes = 0
        self.downvotes = 0
    
    @discord.ui.button(label="0", style=discord.ButtonStyle.success, emoji="👍", custom_id="suggestion_upvote")
    async def upvote_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Upvote suggestion"""
        self.upvotes += 1
        button.label = str(self.upvotes)
        await interaction.response.edit_message(view=self)
        await interaction.followup.send("Đã upvote! 👍", ephemeral=True)
    
    @discord.ui.button(label="0", style=discord.ButtonStyle.danger, emoji="👎", custom_id="suggestion_downvote")
    async def downvote_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Downvote suggestion"""
        self.downvotes += 1
        button.label = str(self.downvotes)
        await interaction.response.edit_message(view=self)
        await interaction.followup.send("Đã downvote! 👎", ephemeral=True)


class CustomEmbedModal(discord.ui.Modal, title="Tạo Custom Embed"):
    """Modal để tạo custom embed"""
    
    title_field = discord.ui.TextInput(
        label="Tiêu đề",
        placeholder="Tiêu đề của embed...",
        required=True,
        max_length=256,
        style=discord.TextStyle.short
    )
    
    description = discord.ui.TextInput(
        label="Nội dung",
        placeholder="Nội dung chính của embed...",
        required=True,
        max_length=4000,
        style=discord.TextStyle.paragraph
    )
    
    color = discord.ui.TextInput(
        label="Màu (hex code)",
        placeholder="Ví dụ: #5865F2 hoặc 5865F2",
        required=False,
        max_length=7,
        default="#5865F2",
        style=discord.TextStyle.short
    )
    
    footer = discord.ui.TextInput(
        label="Footer (tùy chọn)",
        placeholder="Text ở cuối embed...",
        required=False,
        max_length=2048,
        style=discord.TextStyle.short
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        """Tạo và gửi custom embed"""
        # Parse color
        color_value = self.color.value.replace('#', '')
        try:
            color_int = int(color_value, 16)
        except ValueError:
            color_int = 0x5865F2  # Default to blurple
        
        embed = discord.Embed(
            title=self.title_field.value,
            description=self.description.value,
            color=color_int
        )
        
        if self.footer.value:
            embed.set_footer(text=self.footer.value)
        
        await interaction.response.send_message(embed=embed)
        logger.info(f"Custom embed created by {interaction.user}")
