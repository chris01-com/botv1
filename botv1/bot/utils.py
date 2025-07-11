import discord
from datetime import datetime
from typing import Optional, List, Dict, Any


def create_quest_embed(quest: 'Quest', creator: Optional[discord.Member] = None) -> discord.Embed:
    """Create a formatted embed for a quest without emojis"""
    embed = discord.Embed(
        title=quest.title,
        description=quest.description,
        color=get_rank_color(quest.rank),
        timestamp=quest.created_at
    )
    
    if quest.requirements:
        embed.add_field(name="Requirements", value=quest.requirements, inline=False)
    
    if quest.reward:
        embed.add_field(name="Reward", value=quest.reward, inline=False)
    
    embed.add_field(name="Quest ID", value=f"`{quest.quest_id}`", inline=True)
    embed.add_field(name="Rank", value=quest.rank.title(), inline=True)
    embed.add_field(name="Category", value=quest.category.title(), inline=True)
    embed.add_field(name="Status", value=quest.status.title(), inline=True)
    
    if creator:
        embed.set_author(name=f"Created by {creator.display_name}", 
                        icon_url=creator.display_avatar.url if creator.display_avatar else None)
    
    return embed


def create_progress_embed(progress: 'QuestProgress', quest: 'Quest', user: Optional[discord.Member] = None) -> discord.Embed:
    """Create a formatted embed for quest progress without emojis"""
    status_colors = {
        'accepted': discord.Color.yellow(),
        'completed': discord.Color.orange(),
        'approved': discord.Color.green(),
        'rejected': discord.Color.red()
    }
    
    embed = discord.Embed(
        title=f"{quest.title}",
        description=quest.description,
        color=status_colors.get(progress.status, discord.Color.grey())
    )
    
    embed.add_field(name="Status", value=progress.status.title(), inline=True)
    embed.add_field(name="Quest ID", value=f"`{quest.quest_id}`", inline=True)
    embed.add_field(name="Rank", value=quest.rank.title(), inline=True)
    
    if progress.accepted_at:
        embed.add_field(name="Accepted", value=format_timestamp(progress.accepted_at), inline=True)
    
    if progress.completed_at:
        embed.add_field(name="Completed", value=format_timestamp(progress.completed_at), inline=True)
    
    if progress.proof_text:
        embed.add_field(name="Proof", value=progress.proof_text, inline=False)
    
    if progress.proof_image_urls:
        embed.set_image(url=progress.proof_image_urls[0])
    
    if user:
        embed.set_footer(text=f"User: {user.display_name}", 
                        icon_url=user.display_avatar.url if user.display_avatar else None)
    
    return embed


def get_rank_color(rank: str) -> discord.Color:
    """Get color based on quest rank"""
    from bot.models import QuestRank
    colors = {
        QuestRank.EASY: discord.Color.green(),
        QuestRank.NORMAL: discord.Color.blue(),
        QuestRank.MEDIUM: discord.Color.orange(),
        QuestRank.HARD: discord.Color.red(),
        QuestRank.IMPOSSIBLE: discord.Color.purple()
    }
    return colors.get(rank, discord.Color.light_grey())


def format_timestamp(timestamp) -> str:
    """Format timestamp for display"""
    try:
        if isinstance(timestamp, datetime):
            return timestamp.strftime("%Y-%m-%d %H:%M")
        elif isinstance(timestamp, str) and timestamp:
            dt = datetime.fromisoformat(timestamp)
            return dt.strftime("%Y-%m-%d %H:%M")
        else:
            return "N/A"
    except:
        return str(timestamp) if timestamp else "N/A"


def truncate_text(text: str, max_length: int = 1000) -> str:
    """Truncate text to fit within Discord embed limits"""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."


def validate_quest_data(title: str, description: str, requirements: str = "", reward: str = "") -> Optional[str]:
    """Validate quest creation data"""
    if not title or len(title) > 100:
        return "Quest title must be between 1 and 100 characters"
    
    if not description or len(description) > 2000:
        return "Quest description must be between 1 and 2000 characters"
    
    if len(requirements) > 1000:
        return "Requirements must be less than 1000 characters"
    
    if len(reward) > 1000:
        return "Reward must be less than 1000 characters"
    
    return None


def format_quest_list(quests: List['Quest'], max_quests: int = 10) -> str:
    """Format a list of quests for display"""
    if not quests:
        return "No quests available"
    
    quest_list = []
    for quest in quests[:max_quests]:
        quest_list.append(f"**{quest.title}** (ID: `{quest.quest_id}`) - {quest.rank.title()}")
    
    if len(quests) > max_quests:
        quest_list.append(f"... and {len(quests) - max_quests} more")
    
    return "\n".join(quest_list)


def is_valid_quest_id(quest_id: str) -> bool:
    """Check if a quest ID has a valid format"""
    return len(quest_id) == 8 and quest_id.replace('-', '').isalnum()


def get_user_mention(user_id: int) -> str:
    """Get a user mention string"""
    return f"<@{user_id}>"


def get_role_mention(role_id: int) -> str:
    """Get a role mention string"""
    return f"<@&{role_id}>"


def create_error_embed(title: str, description: str) -> discord.Embed:
    """Create a standardized error embed"""
    return discord.Embed(
        title=title,
        description=description,
        color=discord.Color.red()
    )


def create_success_embed(title: str, description: str) -> discord.Embed:
    """Create a standardized success embed"""
    return discord.Embed(
        title=title,
        description=description,
        color=discord.Color.green()
    )


def create_info_embed(title: str, description: str) -> discord.Embed:
    """Create a standardized info embed"""
    return discord.Embed(
        title=title,
        description=description,
        color=discord.Color.blue()
    )