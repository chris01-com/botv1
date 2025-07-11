from typing import Optional, Dict
from bot.json_database import JSONDatabase
from bot.models import ChannelConfig as ChannelConfigModel


class ChannelConfig:
    """Channel configuration management"""
    
    def __init__(self, database: JSONDatabase):
        self.database = database
    
    async def initialize(self):
        """Initialize config"""
        # Database tables are created during database initialization
        pass
    
    async def set_guild_channels(self, guild_id: int, quest_list_channel: int = None, 
                                quest_accept_channel: int = None, quest_submit_channel: int = None,
                                quest_approval_channel: int = None, notification_channel: int = None):
        """Set channel configuration for a guild"""
        config = ChannelConfigModel(
            guild_id=guild_id,
            quest_list_channel=quest_list_channel,
            quest_accept_channel=quest_accept_channel,
            quest_submit_channel=quest_submit_channel,
            quest_approval_channel=quest_approval_channel,
            notification_channel=notification_channel
        )
        await self.database.save_channel_config(config)
    
    async def get_guild_config(self, guild_id: int) -> Dict[str, int]:
        """Get channel configuration for a guild"""
        config = await self.database.get_channel_config(guild_id)
        if config:
            return {
                'quest_list_channel': config.quest_list_channel,
                'quest_accept_channel': config.quest_accept_channel,
                'quest_submit_channel': config.quest_submit_channel,
                'quest_approval_channel': config.quest_approval_channel,
                'notification_channel': config.notification_channel
            }
        return {}
    
    async def get_quest_list_channel(self, guild_id: int) -> Optional[int]:
        """Get quest list channel for a guild"""
        config = await self.database.get_channel_config(guild_id)
        return config.quest_list_channel if config else None
    
    async def get_quest_accept_channel(self, guild_id: int) -> Optional[int]:
        """Get quest accept channel for a guild"""
        config = await self.database.get_channel_config(guild_id)
        return config.quest_accept_channel if config else None
    
    async def get_quest_submit_channel(self, guild_id: int) -> Optional[int]:
        """Get quest submit channel for a guild"""
        config = await self.database.get_channel_config(guild_id)
        return config.quest_submit_channel if config else None
    
    async def get_quest_approval_channel(self, guild_id: int) -> Optional[int]:
        """Get quest approval channel for a guild"""
        config = await self.database.get_channel_config(guild_id)
        return config.quest_approval_channel if config else None
    
    async def get_notification_channel(self, guild_id: int) -> Optional[int]:
        """Get notification channel for a guild"""
        config = await self.database.get_channel_config(guild_id)
        return config.notification_channel if config else None