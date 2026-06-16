"""Constants và messages cho bot"""

# Colors cho embeds
COLORS = {
    'primary': 0x5865F2,      # Discord Blurple
    'success': 0x57F287,      # Green
    'warning': 0xFEE75C,      # Yellow
    'error': 0xED4245,        # Red
    'info': 0x3498db,         # Blue
}

# Emojis
EMOJIS = {
    'success': '✅',
    'error': '❌',
    'warning': '⚠️',
    'info': 'ℹ️',
    'loading': '⏳',
    'wave': '👋',
    'shield': '🛡️',
    'fun': '🎉',
    'mod': '🔨',
    'role': '🎭',
    'bot': '🤖',
    '8ball': '🎱',
    'dice': '🎲',
    'coin': '🪙',
}

# Messages tiếng Việt
MESSAGES = {
    'welcome': {
        'title': 'Chào mừng đến với server!',
        'description': 'Chúc bạn có những trải nghiệm tuyệt vời! 👋',
    },
    'errors': {
        'missing_permissions': 'Bạn không có quyền thực hiện lệnh này!',
        'bot_missing_permissions': 'Bot không có đủ quyền để thực hiện hành động này!',
        'invalid_user': 'Người dùng không hợp lệ!',
        'unknown': 'Đã xảy ra lỗi không xác định!',
        'api_error': 'Lỗi kết nối với Discord API. Vui lòng thử lại sau.',
        'database_error': 'Lỗi database. Thao tác không thành công.',
        'rate_limit': 'Bạn đang dùng lệnh quá nhanh! Vui lòng đợi {remaining}s.',
        'invalid_input': 'Dữ liệu đầu vào không hợp lệ.',
        'user_not_found': 'Không tìm thấy người dùng.',
    },
    'success': {
        'operation_complete': 'Thao tác đã hoàn thành thành công!',
    }
}

# Bot info
BOT_INFO = {
    'name': 'BlastBot',
    'version': '1.0.1',
    'description': 'Discord bot hiện đại với slash commands',
    'author': 'Blast',
}

# Bot configuration constants
BOT_CONFIG = {
    'min_token_length': 50,
}

# Cache configuration
CACHE_CONFIG = {
    'guild_config_ttl_seconds': 300,  # 5 minutes
    'guild_config_maxsize': 128,
}

# Role menu configuration
ROLE_MENU_CONFIG = {
    'max_roles_per_menu': 25,  # Discord limit
}

# Clear command configuration
CLEAR_CONFIG = {
    'max_messages': 100,
    'min_messages': 1,
    'batch_size': 50,
    'batch_delay_seconds': 1,
    'old_message_delete_delay_seconds': 1,
    'message_age_limit_days': 14,
}

# Pagination configuration
PAGINATION_CONFIG = {
    'default_timeout_seconds': 180,
}

# View timeouts
VIEW_TIMEOUTS = {
    'confirm': 60.0,
    'pagination': 180.0,
    'timeout_delete': 60.0,
}

# Command cooldowns (per user, in seconds)
COMMAND_COOLDOWNS = {
    'clear': 10.0,
    'kick': 10.0,
    'ban': 15.0,
    'timeout': 10.0,
    'rolemenu': 30.0,
}

# Validation limits
VALIDATION_LIMITS = {
    'timeout_min_seconds': 60,
    'timeout_max_seconds': 2419200,  # 28 days
    'ban_delete_days_max': 7,
}
