
import json
import os
import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime
from bot.models import Quest, QuestProgress, UserStats, ChannelConfig
import subprocess

class JSONDatabase:
    """JSON file-based database interface for the quest bot"""
    
    def __init__(self):
        self.data_dir = "data"
        self.quests_file = os.path.join(self.data_dir, "quests.json")
        self.progress_file = os.path.join(self.data_dir, "quest_progress.json")
        self.stats_file = os.path.join(self.data_dir, "user_stats.json")
        self.config_file = os.path.join(self.data_dir, "channel_config.json")
        
        # Initialize data structures
        self.quests = {}
        self.quest_progress = {}
        self.user_stats = {}
        self.channel_config = {}
        
    async def initialize(self):
        """Initialize the database and load existing data"""
        # Create data directory if it doesn't exist
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Load existing data
        await self._load_data()
        
    async def _load_data(self):
        """Load data from JSON files"""
        for file_path, data_attr in [
            (self.quests_file, 'quests'),
            (self.progress_file, 'quest_progress'),
            (self.stats_file, 'user_stats'),
            (self.config_file, 'channel_config')
        ]:
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r') as f:
                        setattr(self, data_attr, json.load(f))
                except (json.JSONDecodeError, FileNotFoundError):
                    setattr(self, data_attr, {})
            else:
                setattr(self, data_attr, {})
    
    async def _save_data(self):
        """Save all data to JSON files and commit to git"""
        # Save each data structure to its respective file
        data_files = [
            (self.quests_file, self.quests),
            (self.progress_file, self.quest_progress),
            (self.stats_file, self.user_stats),
            (self.config_file, self.channel_config)
        ]
        
        for file_path, data in data_files:
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        
        # Auto-commit to git
        await self._git_commit()
    
    async def _git_commit(self):
        """Automatically commit changes to git"""
        try:
            # Add all data files
            subprocess.run(['git', 'add', 'data/'], check=False, capture_output=True)
            
            # Commit with timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            commit_msg = f"Auto-update bot data - {timestamp}"
            subprocess.run(['git', 'commit', '-m', commit_msg], check=False, capture_output=True)
            
            # Push to remote (if configured)
            subprocess.run(['git', 'push'], check=False, capture_output=True)
            
        except Exception as e:
            print(f"Git commit failed: {e}")
    
    async def save_quest(self, quest: Quest):
        """Save a quest to the database"""
        quest_data = {
            'quest_id': quest.quest_id,
            'title': quest.title,
            'description': quest.description,
            'creator_id': quest.creator_id,
            'guild_id': quest.guild_id,
            'requirements': quest.requirements,
            'reward': quest.reward,
            'rank': quest.rank,
            'category': quest.category,
            'status': quest.status,
            'created_at': quest.created_at.isoformat() if quest.created_at else datetime.now().isoformat(),
            'required_role_ids': quest.required_role_ids
        }
        
        self.quests[quest.quest_id] = quest_data
        await self._save_data()
    
    async def get_quest(self, quest_id: str) -> Optional[Quest]:
        """Get a quest by ID"""
        if quest_id in self.quests:
            data = self.quests[quest_id]
            return Quest(
                quest_id=data['quest_id'],
                title=data['title'],
                description=data['description'],
                creator_id=data['creator_id'],
                guild_id=data['guild_id'],
                requirements=data.get('requirements', ''),
                reward=data.get('reward', ''),
                rank=data.get('rank', 'normal'),
                category=data.get('category', 'other'),
                status=data.get('status', 'available'),
                created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else None,
                required_role_ids=data.get('required_role_ids', [])
            )
        return None
    
    async def get_guild_quests(self, guild_id: int, status: str = None) -> List[Quest]:
        """Get all quests for a guild, optionally filtered by status"""
        quests = []
        for quest_data in self.quests.values():
            if quest_data['guild_id'] == guild_id:
                if status is None or quest_data.get('status') == status:
                    quest = Quest(
                        quest_id=quest_data['quest_id'],
                        title=quest_data['title'],
                        description=quest_data['description'],
                        creator_id=quest_data['creator_id'],
                        guild_id=quest_data['guild_id'],
                        requirements=quest_data.get('requirements', ''),
                        reward=quest_data.get('reward', ''),
                        rank=quest_data.get('rank', 'normal'),
                        category=quest_data.get('category', 'other'),
                        status=quest_data.get('status', 'available'),
                        created_at=datetime.fromisoformat(quest_data['created_at']) if quest_data.get('created_at') else None,
                        required_role_ids=quest_data.get('required_role_ids', [])
                    )
                    quests.append(quest)
        return quests
    
    async def delete_quest(self, quest_id: str):
        """Delete a quest"""
        if quest_id in self.quests:
            del self.quests[quest_id]
            
            # Also remove related progress entries
            to_remove = []
            for key, progress in self.quest_progress.items():
                if progress.get('quest_id') == quest_id:
                    to_remove.append(key)
            
            for key in to_remove:
                del self.quest_progress[key]
                
            await self._save_data()
    
    async def save_quest_progress(self, progress: QuestProgress):
        """Save quest progress to the database"""
        key = f"{progress.user_id}_{progress.quest_id}"
        
        progress_data = {
            'quest_id': progress.quest_id,
            'user_id': progress.user_id,
            'guild_id': progress.guild_id,
            'status': progress.status,
            'accepted_at': progress.accepted_at.isoformat() if progress.accepted_at else None,
            'completed_at': progress.completed_at.isoformat() if progress.completed_at else None,
            'proof_text': progress.proof_text,
            'proof_image_urls': progress.proof_image_urls,
            'approval_status': progress.approval_status,
            'accepted_channel_id': progress.accepted_channel_id
        }
        
        self.quest_progress[key] = progress_data
        await self._save_data()
    
    async def get_user_quest_progress(self, user_id: int, quest_id: str) -> Optional[QuestProgress]:
        """Get most recent progress for a specific user and quest"""
        key = f"{user_id}_{quest_id}"
        
        if key in self.quest_progress:
            data = self.quest_progress[key]
            return QuestProgress(
                quest_id=data['quest_id'],
                user_id=data['user_id'],
                guild_id=data['guild_id'],
                status=data['status'],
                accepted_at=datetime.fromisoformat(data['accepted_at']) if data.get('accepted_at') else None,
                completed_at=datetime.fromisoformat(data['completed_at']) if data.get('completed_at') else None,
                proof_text=data.get('proof_text', ''),
                proof_image_urls=data.get('proof_image_urls', []),
                approval_status=data.get('approval_status', ''),
                accepted_channel_id=data.get('accepted_channel_id')
            )
        return None
    
    async def get_user_quests(self, user_id: int, guild_id: int = None) -> List[QuestProgress]:
        """Get all quests for a user"""
        progresses = []
        
        for data in self.quest_progress.values():
            if data['user_id'] == user_id:
                if guild_id is None or data['guild_id'] == guild_id:
                    progress = QuestProgress(
                        quest_id=data['quest_id'],
                        user_id=data['user_id'],
                        guild_id=data['guild_id'],
                        status=data['status'],
                        accepted_at=datetime.fromisoformat(data['accepted_at']) if data.get('accepted_at') else None,
                        completed_at=datetime.fromisoformat(data['completed_at']) if data.get('completed_at') else None,
                        proof_text=data.get('proof_text', ''),
                        proof_image_urls=data.get('proof_image_urls', []),
                        approval_status=data.get('approval_status', ''),
                        accepted_channel_id=data.get('accepted_channel_id')
                    )
                    progresses.append(progress)
        
        return sorted(progresses, key=lambda x: x.accepted_at or datetime.min, reverse=True)
    
    async def get_pending_approvals(self, creator_id: int, guild_id: int) -> List[tuple]:
        """Get quests pending approval for a quest creator"""
        pending = []
        
        for progress_data in self.quest_progress.values():
            if progress_data['guild_id'] == guild_id and progress_data['status'] == 'completed':
                quest_id = progress_data['quest_id']
                if quest_id in self.quests and self.quests[quest_id]['creator_id'] == creator_id:
                    quest_title = self.quests[quest_id]['title']
                    pending.append((
                        quest_id,
                        progress_data['user_id'],
                        progress_data.get('proof_text', ''),
                        progress_data.get('proof_image_urls', []),
                        quest_title
                    ))
        
        return pending
    
    async def save_user_stats(self, stats: UserStats):
        """Save user statistics"""
        key = f"{stats.user_id}_{stats.guild_id}"
        
        stats_data = {
            'user_id': stats.user_id,
            'guild_id': stats.guild_id,
            'quests_completed': stats.quests_completed,
            'quests_accepted': stats.quests_accepted,
            'quests_rejected': stats.quests_rejected,
            'first_quest_date': stats.first_quest_date.isoformat() if stats.first_quest_date else None,
            'last_quest_date': stats.last_quest_date.isoformat() if stats.last_quest_date else None
        }
        
        self.user_stats[key] = stats_data
        await self._save_data()
    
    async def get_user_stats(self, user_id: int, guild_id: int) -> Optional[UserStats]:
        """Get user statistics"""
        key = f"{user_id}_{guild_id}"
        
        if key in self.user_stats:
            data = self.user_stats[key]
            return UserStats(
                user_id=data['user_id'],
                guild_id=data['guild_id'],
                quests_completed=data.get('quests_completed', 0),
                quests_accepted=data.get('quests_accepted', 0),
                quests_rejected=data.get('quests_rejected', 0),
                first_quest_date=datetime.fromisoformat(data['first_quest_date']) if data.get('first_quest_date') else None,
                last_quest_date=datetime.fromisoformat(data['last_quest_date']) if data.get('last_quest_date') else None
            )
        return None
    
    async def get_guild_leaderboard(self, guild_id: int, limit: int = 10) -> List[UserStats]:
        """Get guild leaderboard"""
        stats = []
        
        for data in self.user_stats.values():
            if data['guild_id'] == guild_id:
                stat = UserStats(
                    user_id=data['user_id'],
                    guild_id=data['guild_id'],
                    quests_completed=data.get('quests_completed', 0),
                    quests_accepted=data.get('quests_accepted', 0),
                    quests_rejected=data.get('quests_rejected', 0),
                    first_quest_date=datetime.fromisoformat(data['first_quest_date']) if data.get('first_quest_date') else None,
                    last_quest_date=datetime.fromisoformat(data['last_quest_date']) if data.get('last_quest_date') else None
                )
                stats.append(stat)
        
        # Sort by completed quests, then by accepted quests
        stats.sort(key=lambda x: (x.quests_completed, x.quests_accepted), reverse=True)
        return stats[:limit]
    
    async def get_total_guild_stats(self, guild_id: int) -> Dict[str, int]:
        """Get total guild statistics"""
        total_completed = 0
        total_accepted = 0
        active_users = 0
        
        for data in self.user_stats.values():
            if data['guild_id'] == guild_id:
                total_completed += data.get('quests_completed', 0)
                total_accepted += data.get('quests_accepted', 0)
                active_users += 1
        
        return {
            'total_completed': total_completed,
            'total_accepted': total_accepted,
            'active_users': active_users
        }
    
    async def save_channel_config(self, config: ChannelConfig):
        """Save channel configuration"""
        config_data = {
            'guild_id': config.guild_id,
            'quest_list_channel': config.quest_list_channel,
            'quest_accept_channel': config.quest_accept_channel,
            'quest_submit_channel': config.quest_submit_channel,
            'quest_approval_channel': config.quest_approval_channel,
            'notification_channel': config.notification_channel
        }
        
        self.channel_config[str(config.guild_id)] = config_data
        await self._save_data()
    
    async def get_channel_config(self, guild_id: int) -> Optional[ChannelConfig]:
        """Get channel configuration for a guild"""
        if str(guild_id) in self.channel_config:
            data = self.channel_config[str(guild_id)]
            return ChannelConfig(
                guild_id=data['guild_id'],
                quest_list_channel=data.get('quest_list_channel'),
                quest_accept_channel=data.get('quest_accept_channel'),
                quest_submit_channel=data.get('quest_submit_channel'),
                quest_approval_channel=data.get('quest_approval_channel'),
                notification_channel=data.get('notification_channel')
            )
        return None
    
    async def close(self):
        """Close database connection (no-op for JSON)"""
        pass
