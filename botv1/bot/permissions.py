import discord
from typing import List


def has_quest_creation_permission(user: discord.Member, guild: discord.Guild) -> bool:
    """Check if user has permission to create quests"""
    # Server owner can always create quests
    if user.id == guild.owner_id:
        return True
    
    # Check for administrator permission
    if user.guild_permissions.administrator:
        return True
    
    # Check for manage_guild permission
    if user.guild_permissions.manage_guild:
        return True
    
    # Check for manage_channels permission
    if user.guild_permissions.manage_channels:
        return True
    
    # Check for specific roles (you can customize these role names)
    quest_creator_roles = ['Quest Master', 'Moderator', 'Admin', 'Staff']
    user_roles = [role.name for role in user.roles]
    
    return any(role in quest_creator_roles for role in user_roles)


def can_manage_quest(user: discord.Member, guild: discord.Guild, quest_creator_id: int) -> bool:
    """Check if user can manage (approve/reject/delete) a quest"""
    # Server owner can manage all quests
    if user.id == guild.owner_id:
        return True
    
    # Quest creator can manage their own quests
    if user.id == quest_creator_id:
        return True
    
    # Check for administrator permission
    if user.guild_permissions.administrator:
        return True
    
    # Check for manage_guild permission
    if user.guild_permissions.manage_guild:
        return True
    
    return False


def can_use_quest_commands(user: discord.Member, guild: discord.Guild) -> bool:
    """Check if user can use basic quest commands (accept, complete, view)"""
    # All members can use basic quest commands by default
    return True


def get_required_roles_for_quest(guild: discord.Guild, required_role_ids: List[int]) -> List[discord.Role]:
    """Get role objects from role IDs"""
    roles = []
    for role_id in required_role_ids:
        role = guild.get_role(role_id)
        if role:
            roles.append(role)
    return roles


def user_has_required_roles(user: discord.Member, required_role_ids: List[int]) -> bool:
    """Check if user has all required roles"""
    if not required_role_ids:
        return True
    
    user_role_ids = [role.id for role in user.roles]
    return any(role_id in user_role_ids for role_id in required_role_ids)