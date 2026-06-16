"""Interactive views với buttons và select menus"""

import discord
import asyncio
from typing import Optional, Callable, Any, List


class PersistentView(discord.ui.View):
    """Base class cho persistent views (survive bot restart)"""
    
    def __init__(self):
        super().__init__(timeout=None)  # Never timeout
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Override trong subclass để check permissions"""
        return True


class ConfirmView(discord.ui.View):
    """View với nút Confirm/Cancel"""
    
    def __init__(
        self,
        user: discord.User | discord.Member,
        timeout: float = 60.0,
        confirm_label: str = "Xác nhận",
        cancel_label: str = "Hủy"
    ):
        super().__init__(timeout=timeout)
        self.user = user
        self.value: Optional[bool] = None
        
        # Customize button labels
        self.confirm_button.label = confirm_label
        self.cancel_button.label = cancel_label
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Chỉ cho phép user đã gọi command tương tác"""
        if interaction.user.id != self.user.id:
            await interaction.response.send_message(
                "Bạn không thể sử dụng nút này!",
                ephemeral=True
            )
            return False
        return True
    
    @discord.ui.button(label="Xác nhận", style=discord.ButtonStyle.green, emoji="✅")
    async def confirm_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        self.value = True
        await interaction.response.defer()
        self.stop()
    
    @discord.ui.button(label="Hủy", style=discord.ButtonStyle.red, emoji="❌")
    async def cancel_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        self.value = False
        await interaction.response.defer()
        self.stop()


class PaginationView(discord.ui.View):
    """View cho phân trang với Previous/Next buttons"""
    
    def __init__(
        self,
        user: discord.User | discord.Member,
        pages: list[discord.Embed],
        timeout: float = 180.0
    ):
        super().__init__(timeout=timeout)
        self.user = user
        self.pages = pages
        self.current_page = 0
        self.message: Optional[discord.Message] = None
        
        # Disable previous button on first page
        self.update_buttons()
    
    def update_buttons(self):
        """Cập nhật trạng thái buttons dựa trên trang hiện tại"""
        self.previous_button.disabled = self.current_page == 0
        self.next_button.disabled = self.current_page == len(self.pages) - 1
        
        # Update counter label
        self.counter_button.label = f"{self.current_page + 1}/{len(self.pages)}"
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Chỉ cho phép user đã gọi command tương tác"""
        if interaction.user != self.user:
            await interaction.response.send_message(
                "Bạn không thể sử dụng nút này!",
                ephemeral=True
            )
            return False
        return True
    
    @discord.ui.button(label="◀️", style=discord.ButtonStyle.primary)
    async def previous_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        self.current_page -= 1
        self.update_buttons()
        await interaction.response.edit_message(
            embed=self.pages[self.current_page],
            view=self
        )
    
    @discord.ui.button(label="1/1", style=discord.ButtonStyle.secondary, disabled=True)
    async def counter_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        # This button is just for display
        pass
    
    @discord.ui.button(label="▶️", style=discord.ButtonStyle.primary)
    async def next_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        self.current_page += 1
        self.update_buttons()
        await interaction.response.edit_message(
            embed=self.pages[self.current_page],
            view=self
        )
    
    async def on_timeout(self):
        """Disable buttons khi timeout"""
        for item in self.children:
            if isinstance(item, discord.ui.Button):
                item.disabled = True
        
        if self.message:
            try:
                await self.message.edit(view=self)
            except discord.HTTPException:
                # Message was deleted or we lost permissions
                pass


class LinkButton(discord.ui.View):
    """View với link button"""
    
    def __init__(self, label: str, url: str):
        super().__init__(timeout=None)
        self.add_item(discord.ui.Button(label=label, url=url))


class CustomButton(discord.ui.Button):
    """Custom button với callback tùy chỉnh"""
    
    def __init__(
        self,
        style: discord.ButtonStyle = discord.ButtonStyle.secondary,
        label: Optional[str] = None,
        emoji: Optional[str] = None,
        disabled: bool = False,
        callback_func: Optional[Callable[[discord.Interaction, discord.ui.Button], Any]] = None
    ):
        super().__init__(style=style, label=label, emoji=emoji, disabled=disabled)
        self.callback_func = callback_func
    
    async def callback(self, interaction: discord.Interaction):
        if self.callback_func:
            await self.callback_func(interaction, self)


class RoleSelectMenu(discord.ui.Select):
    """Select menu cho role selection"""
    
    def __init__(
        self,
        roles: List[discord.Role],
        placeholder: str = "Chọn roles...",
        min_values: int = 0,
        max_values: int = 1,
        custom_id: str = "role_select_menu"
    ):
        options = [
            discord.SelectOption(
                label=role.name,
                value=str(role.id),
                description=f"Role {role.name}",
                emoji="🎭"
            )
            for role in roles[:25]  # Discord limit
        ]
        
        super().__init__(
            placeholder=placeholder,
            min_values=min_values,
            max_values=min(max_values, len(options)),
            options=options,
            custom_id=custom_id
        )
        
        # Add lock to prevent race conditions
        self._lock = asyncio.Lock()
        self._processing = False
    
    async def callback(self, interaction: discord.Interaction):
        """Handle role selection"""
        # Check if already processing to prevent race condition
        async with self._lock:
            if self._processing:
                await interaction.response.send_message(
                    "⏳ Đang xử lý request trước đó, vui lòng đợi...",
                    ephemeral=True
                )
                return
            
            self._processing = True
            
            try:
                await interaction.response.defer(ephemeral=True)

                if not isinstance(interaction.user, discord.Member):
                    await interaction.followup.send(
                        "❌ Lỗi: Không thể xác định member!",
                        ephemeral=True
                    )
                    return
                
                selected_role_ids = [int(value) for value in self.values]
                guild = interaction.guild
                
                if not guild:
                    return
                
                await self._process_role_changes(interaction, selected_role_ids, guild)
            finally:
                self._processing = False
    
    async def _process_role_changes(self, interaction: discord.Interaction, selected_role_ids: List[int], guild: discord.Guild):
        """Process role additions and removals"""
        if not isinstance(interaction.user, discord.Member):
            return
        
        added_roles = []
        removed_roles = []
        errors = []
        
        # Get menu role IDs for validation
        menu_role_ids = {int(opt.value) for opt in self.options}
        current_role_ids = {role.id for role in interaction.user.roles}

        for role_id in menu_role_ids:
            role = guild.get_role(role_id)
            if not role:
                continue

            should_have_role = role_id in selected_role_ids
            has_role = role_id in current_role_ids

            if should_have_role and not has_role:
                try:
                    await interaction.user.add_roles(role, reason="Role menu selection")
                    added_roles.append(role.mention)
                except discord.Forbidden:
                    errors.append(f"Không thể thêm {role.mention}")
                except discord.HTTPException as e:
                    errors.append(f"Lỗi khi thêm {role.mention}: {str(e)[:50]}")
            elif not should_have_role and has_role:
                try:
                    await interaction.user.remove_roles(role, reason="Role menu deselection")
                    removed_roles.append(role.mention)
                except discord.Forbidden:
                    errors.append(f"Không thể xóa {role.mention}")
                except discord.HTTPException as e:
                    errors.append(f"Lỗi khi xóa {role.mention}: {str(e)[:50]}")
        
        response = []
        if added_roles:
            response.append(f"✅ Đã thêm: {', '.join(added_roles)}")
        if removed_roles:
            response.append(f"❌ Đã xóa: {', '.join(removed_roles)}")
        if errors:
            response.append(f"⚠️ Lỗi: {', '.join(errors[:3])}")
        
        if not response:
            response.append("Không có thay đổi nào.")
        
        await interaction.followup.send("\n".join(response), ephemeral=True)


class TimeoutDeleteView(discord.ui.View):
    """View tự động xóa message sau timeout"""
    
    def __init__(self, timeout: float = 60.0, delete_after: bool = True):
        super().__init__(timeout=timeout)
        self.delete_after = delete_after
        self.message: Optional[discord.Message] = None
    
    async def on_timeout(self):
        """Xóa message khi timeout"""
        if self.delete_after and self.message:
            try:
                await self.message.delete()
            except discord.HTTPException:
                pass


class DynamicButtonGrid(discord.ui.View):
    """Dynamic grid of buttons"""
    
    def __init__(self, buttons_data: List[dict], timeout: float = 180.0):
        """
        buttons_data format: [
            {
                'label': 'Button 1',
                'style': discord.ButtonStyle.primary,
                'emoji': '🔵',
                'callback': async_function,
                'custom_id': 'unique_id'  # optional
            },
            ...
        ]
        """
        super().__init__(timeout=timeout)
        
        for btn_data in buttons_data[:25]:  # Max 25 components
            button = discord.ui.Button(
                label=btn_data.get('label', 'Button'),
                style=btn_data.get('style', discord.ButtonStyle.secondary),
                emoji=btn_data.get('emoji'),
                custom_id=btn_data.get('custom_id')
            )
            
            # Attach callback
            if 'callback' in btn_data:
                button.callback = btn_data['callback']
            
            self.add_item(button)
