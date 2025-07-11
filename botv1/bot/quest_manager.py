import uuid
from datetime import datetime, timedelta
from typing import List, Optional, Tuple
from bot.models import Quest, QuestProgress, QuestRank, QuestCategory, QuestStatus
from bot.database import Database


class QuestManager:
    """Main quest management class"""
    
    def __init__(self, database: Database):
        self.database = database
    
    async def create_quest(self, title: str, description: str, creator_id: int, 
                          guild_id: int, requirements: str = "", reward: str = "",
                          rank: str = QuestRank.NORMAL, required_role_ids: List[int] = None,
                          category: str = QuestCategory.OTHER) -> Quest:
        """Create a new quest"""
        quest_id = str(uuid.uuid4())[:8]
        
        quest = Quest(
            quest_id=quest_id,
            title=title,
            description=description,
            creator_id=creator_id,
            guild_id=guild_id,
            requirements=requirements,
            reward=reward,
            rank=rank,
            required_role_ids=required_role_ids or [],
            category=category,
            status=QuestStatus.AVAILABLE,
            created_at=datetime.now()
        )
        
        await self.database.save_quest(quest)
        return quest
    
    async def get_quest(self, quest_id: str) -> Optional[Quest]:
        """Get quest by ID"""
        return await self.database.get_quest(quest_id)
    
    async def get_guild_quests(self, guild_id: int, status: str = None) -> List[Quest]:
        """Get all quests for a guild, optionally filtered by status"""
        return await self.database.get_guild_quests(guild_id, status)
    
    async def get_available_quests(self, guild_id: int) -> List[Quest]:
        """Get all available quests for a guild"""
        return await self.database.get_guild_quests(guild_id, QuestStatus.AVAILABLE)
    
    async def accept_quest(self, quest_id: str, user_id: int, user_role_ids: List[int] = None, 
                          accepted_channel_id: int = None) -> Tuple[Optional[QuestProgress], str]:
        """Accept a quest by a user. Returns (progress, error_message)"""
        quest = await self.database.get_quest(quest_id)
        if not quest:
            return None, "Quest not found!"
        
        if quest.status != QuestStatus.AVAILABLE:
            return None, "Quest is not available for acceptance!"
        
        # Check if user already has this quest
        existing_progress = await self.database.get_user_quest_progress(user_id, quest_id)
        if existing_progress:
            # Check if it's been 24 hours since last attempt
            if existing_progress.status in [QuestStatus.ACCEPTED, QuestStatus.COMPLETED]:
                return None, "You have already accepted this quest!"
            elif existing_progress.status == QuestStatus.REJECTED:
                # Check 24-hour cooldown
                if existing_progress.accepted_at:
                    last_attempt = existing_progress.accepted_at if isinstance(existing_progress.accepted_at, datetime) else datetime.fromisoformat(existing_progress.accepted_at)
                    cooldown_end = last_attempt + timedelta(hours=24)
                    if datetime.now() < cooldown_end:
                        remaining_time = cooldown_end - datetime.now()
                        hours_remaining = int(remaining_time.total_seconds() / 3600)
                        return None, f"You must wait {hours_remaining} hours before attempting this quest again!"
        
        # Check role requirements
        if quest.required_role_ids and user_role_ids:
            from bot.permissions import user_has_required_roles
            if not user_has_required_roles(type('User', (), {'roles': [type('Role', (), {'id': rid})() for rid in user_role_ids]})(), quest.required_role_ids):
                return None, "You don't have the required roles for this quest!"
        
        # Create new progress
        progress = QuestProgress(
            quest_id=quest_id,
            user_id=user_id,
            guild_id=quest.guild_id,
            status=QuestStatus.ACCEPTED,
            accepted_at=datetime.now(),
            accepted_channel_id=accepted_channel_id
        )
        
        await self.database.save_quest_progress(progress)
        return progress, ""
    
    async def complete_quest(self, quest_id: str, user_id: int, proof_text: str = "", 
                            proof_image_urls: List[str] = None) -> Optional[QuestProgress]:
        """Complete a quest with proof"""
        progress = await self.database.get_user_quest_progress(user_id, quest_id)
        if not progress:
            return None
        
        if progress.status != QuestStatus.ACCEPTED:
            return None
        
        # Update progress
        progress.status = QuestStatus.COMPLETED
        progress.completed_at = datetime.now()
        progress.proof_text = proof_text
        progress.proof_image_urls = proof_image_urls or []
        progress.approval_status = "pending"
        
        await self.database.save_quest_progress(progress)
        return progress
    
    async def approve_quest(self, quest_id: str, user_id: int, approved: bool) -> Optional[QuestProgress]:
        """Approve or reject a completed quest"""
        progress = await self.database.get_user_quest_progress(user_id, quest_id)
        if not progress:
            return None
        
        if progress.status != QuestStatus.COMPLETED:
            return None
        
        if approved:
            progress.status = QuestStatus.APPROVED
            progress.approval_status = "approved"
        else:
            progress.status = QuestStatus.REJECTED
            progress.approval_status = "rejected"
        
        await self.database.save_quest_progress(progress)
        return progress
    
    async def get_user_quests(self, user_id: int, guild_id: int = None) -> List[QuestProgress]:
        """Get all quests for a user"""
        return await self.database.get_user_quests(user_id, guild_id)
    
    async def get_pending_approvals(self, creator_id: int, guild_id: int) -> List[tuple]:
        """Get quests pending approval for a quest creator"""
        return await self.database.get_pending_approvals(creator_id, guild_id)
    
    async def delete_quest(self, quest_id: str) -> bool:
        """Delete a quest and all associated progress"""
        try:
            await self.database.delete_quest(quest_id)
            return True
        except Exception:
            return False