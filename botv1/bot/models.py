from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime


class QuestRank:
    """Quest rank constants"""
    EASY = "easy"
    NORMAL = "normal"
    MEDIUM = "medium"
    HARD = "hard"
    IMPOSSIBLE = "impossible"


class QuestCategory:
    """Quest category constants"""
    HUNTING = "hunting"
    GATHERING = "gathering"
    COLLECTING = "collecting"
    CRAFTING = "crafting"
    EXPLORATION = "exploration"
    COMBAT = "combat"
    SOCIAL = "social"
    BUILDING = "building"
    TRADING = "trading"
    PUZZLE = "puzzle"
    SURVIVAL = "survival"
    OTHER = "other"


class QuestStatus:
    """Quest status constants"""
    AVAILABLE = "available"
    ACCEPTED = "accepted"
    COMPLETED = "completed"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


@dataclass
class Quest:
    """Quest data model"""
    quest_id: str
    title: str
    description: str
    creator_id: int
    guild_id: int
    requirements: str = ""
    reward: str = ""
    rank: str = QuestRank.NORMAL
    category: str = QuestCategory.OTHER
    status: str = QuestStatus.AVAILABLE
    created_at: datetime = None
    required_role_ids: List[int] = None
    
    def __post_init__(self):
        if self.required_role_ids is None:
            self.required_role_ids = []
        if not self.created_at:
            self.created_at = datetime.now()


@dataclass
class QuestProgress:
    """Quest progress data model"""
    quest_id: str
    user_id: int
    guild_id: int
    status: str = QuestStatus.ACCEPTED
    accepted_at: datetime = None
    completed_at: datetime = None
    proof_text: str = ""
    proof_image_urls: List[str] = None
    approval_status: str = ""
    accepted_channel_id: Optional[int] = None
    
    def __post_init__(self):
        if self.proof_image_urls is None:
            self.proof_image_urls = []
        if not self.accepted_at:
            self.accepted_at = datetime.now()


@dataclass
class UserStats:
    """User statistics data model"""
    user_id: int
    guild_id: int
    quests_completed: int = 0
    quests_accepted: int = 0
    quests_rejected: int = 0
    first_quest_date: str = ""
    last_quest_date: str = ""
    
    def __post_init__(self):
        if not self.first_quest_date:
            self.first_quest_date = datetime.now().isoformat()
        if not self.last_quest_date:
            self.last_quest_date = datetime.now().isoformat()


@dataclass
class ChannelConfig:
    """Channel configuration data model"""
    guild_id: int
    quest_list_channel: Optional[int] = None
    quest_accept_channel: Optional[int] = None
    quest_submit_channel: Optional[int] = None
    quest_approval_channel: Optional[int] = None
    notification_channel: Optional[int] = None