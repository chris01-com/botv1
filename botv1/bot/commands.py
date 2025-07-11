import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional, List
from datetime import datetime

from bot.models import QuestRank, QuestCategory, QuestStatus
from bot.quest_manager import QuestManager
from bot.config import ChannelConfig
from bot.user_stats import UserStatsManager
from bot.permissions import has_quest_creation_permission, can_manage_quest, user_has_required_roles


class QuestCommands(commands.Cog):
    """Quest command handlers"""

    def __init__(self, bot: commands.Bot, quest_manager: QuestManager,
                 channel_config: ChannelConfig,
                 user_stats_manager: UserStatsManager):
        self.bot = bot
        self.quest_manager = quest_manager
        self.channel_config = channel_config
        self.user_stats_manager = user_stats_manager

    def _get_rank_color(self, rank: str) -> discord.Color:
        """Get color based on quest rank"""
        colors = {
            QuestRank.EASY: discord.Color.green(),
            QuestRank.NORMAL: discord.Color.blue(),
            QuestRank.MEDIUM: discord.Color.orange(),
            QuestRank.HARD: discord.Color.red(),
            QuestRank.IMPOSSIBLE: discord.Color.purple()
        }
        return colors.get(rank, discord.Color.light_grey())

    @app_commands.command(name="setup_channels", description="Setup quest channels for the server")
    @app_commands.describe(
        quest_list_channel="Channel for quest listings",
        quest_accept_channel="Channel for quest acceptance",
        quest_submit_channel="Channel for quest submissions",
        quest_approval_channel="Channel for quest approvals",
        notification_channel="Channel for notifications"
    )
    async def setup_channels(self, interaction: discord.Interaction,
                             quest_list_channel: discord.TextChannel,
                             quest_accept_channel: discord.TextChannel,
                             quest_submit_channel: discord.TextChannel,
                             quest_approval_channel: discord.TextChannel,
                             notification_channel: discord.TextChannel):
        """Setup quest channels for the server"""
        if not has_quest_creation_permission(interaction.user, interaction.guild):
            await interaction.response.send_message("You don't have permission to setup channels!", ephemeral=True)
            return

        # Respond immediately to prevent timeout
        embed = discord.Embed(
            title="Channels Setup Complete",
            description="Quest channels have been configured successfully",
            color=discord.Color.green()
        )
        embed.add_field(name="Quest List", value=quest_list_channel.mention, inline=True)
        embed.add_field(name="Accept Quests", value=quest_accept_channel.mention, inline=True)
        embed.add_field(name="Submit Quests", value=quest_submit_channel.mention, inline=True)
        embed.add_field(name="Approval", value=quest_approval_channel.mention, inline=True)
        embed.add_field(name="Notifications", value=notification_channel.mention, inline=True)

        await interaction.response.send_message(embed=embed)

        # Set channels in database after responding
        await self.channel_config.set_guild_channels(
            interaction.guild.id,
            quest_list_channel.id,
            quest_accept_channel.id,
            quest_submit_channel.id,
            quest_approval_channel.id,
            notification_channel.id
        )

    @app_commands.command(name="create_quest", description="Create a new quest")
    @app_commands.describe(
        title="Quest title",
        description="Quest description",
        rank="Quest difficulty rank",
        category="Quest category",
        requirements="Quest requirements",
        reward="Quest reward",
        required_roles="Required roles (mention roles like @Role1 @Role2, or use role names)"
    )
    @app_commands.choices(rank=[
        app_commands.Choice(name="Easy", value=QuestRank.EASY),
        app_commands.Choice(name="Normal", value=QuestRank.NORMAL),
        app_commands.Choice(name="Medium", value=QuestRank.MEDIUM),
        app_commands.Choice(name="Hard", value=QuestRank.HARD),
        app_commands.Choice(name="Impossible", value=QuestRank.IMPOSSIBLE)
    ])
    @app_commands.choices(category=[
        app_commands.Choice(name="Hunting", value=QuestCategory.HUNTING),
        app_commands.Choice(name="Gathering", value=QuestCategory.GATHERING),
        app_commands.Choice(name="Collecting", value=QuestCategory.COLLECTING),
        app_commands.Choice(name="Crafting", value=QuestCategory.CRAFTING),
        app_commands.Choice(name="Exploration", value=QuestCategory.EXPLORATION),
        app_commands.Choice(name="Combat", value=QuestCategory.COMBAT),
        app_commands.Choice(name="Social", value=QuestCategory.SOCIAL),
        app_commands.Choice(name="Building", value=QuestCategory.BUILDING),
        app_commands.Choice(name="Trading", value=QuestCategory.TRADING),
        app_commands.Choice(name="Puzzle", value=QuestCategory.PUZZLE),
        app_commands.Choice(name="Survival", value=QuestCategory.SURVIVAL),
        app_commands.Choice(name="Other", value=QuestCategory.OTHER)
    ])
    async def create_quest(self,
                           interaction: discord.Interaction,
                           title: str,
                           description: str,
                           rank: str = QuestRank.NORMAL,
                           category: str = QuestCategory.OTHER,
                           requirements: str = "",
                           reward: str = "",
                           required_roles: str = ""):
        """Create a new quest"""
        if not has_quest_creation_permission(interaction.user, interaction.guild):
            await interaction.response.send_message("You don't have permission to create quests!", ephemeral=True)
            return

        # Respond immediately to prevent timeout
        await interaction.response.defer()

        # Parse required roles - handle both role mentions and role names
        required_role_ids = []
        if required_roles:
            import re
            # Extract role IDs from mentions like <@&123456789>
            role_mention_pattern = r'<@&(\d+)>'
            role_ids = re.findall(role_mention_pattern, required_roles)
            for role_id in role_ids:
                role = interaction.guild.get_role(int(role_id))
                if role:
                    required_role_ids.append(role.id)
                    print(f"DEBUG: Found role '{role.name}' with ID {role.id}")

            # If no mentions found, try parsing as comma-separated role names
            if not required_role_ids:
                role_names = [name.strip() for name in required_roles.split(',')]
                for role_name in role_names:
                    role = discord.utils.get(interaction.guild.roles, name=role_name)
                    if role:
                        required_role_ids.append(role.id)
                        print(f"DEBUG: Found role '{role_name}' with ID {role.id}")
                    else:
                        print(f"DEBUG: Role '{role_name}' not found in guild")

        quest = await self.quest_manager.create_quest(
            title=title,
            description=description,
            creator_id=interaction.user.id,
            guild_id=interaction.guild.id,
            requirements=requirements,
            reward=reward,
            rank=rank,
            category=category,
            required_role_ids=required_role_ids
        )

        # Create enhanced quest embed with beautiful design for quest list channel
        rank_symbols = {
            QuestRank.EASY: "⭐",
            QuestRank.NORMAL: "⭐⭐", 
            QuestRank.MEDIUM: "⭐⭐⭐",
            QuestRank.HARD: "⭐⭐⭐⭐",
            QuestRank.IMPOSSIBLE: "⭐⭐⭐⭐⭐"
        }

        category_emojis = {
            QuestCategory.HUNTING: "🏹",
            QuestCategory.GATHERING: "🌾",
            QuestCategory.COLLECTING: "📦",
            QuestCategory.CRAFTING: "🔨",
            QuestCategory.EXPLORATION: "🗺️",
            QuestCategory.COMBAT: "⚔️",
            QuestCategory.SOCIAL: "🤝",
            QuestCategory.BUILDING: "🏗️",
            QuestCategory.TRADING: "💰",
            QuestCategory.PUZZLE: "🧩",
            QuestCategory.SURVIVAL: "🛡️",
            QuestCategory.OTHER: "❓"
        }

        public_embed = discord.Embed(
            title=f"QUEST | {quest.rank.upper()} | {quest.category.upper()}",
            description=f"**{quest.title}**\n\n{quest.description}",
            color=self._get_rank_color(quest.rank)
        )

        # Add main quest info in a beautiful layout
        public_embed.add_field(
            name="Quest ID", 
            value=f"`{quest.quest_id}`", 
            inline=True
        )
        public_embed.add_field(
            name="Rank", 
            value=f"{quest.rank.upper()}", 
            inline=True
        )
        public_embed.add_field(
            name="Category", 
            value=f"{quest.category.title()}", 
            inline=True
        )

        # Add requirements with beautiful formatting
        if quest.requirements:
            public_embed.add_field(
                name="Requirements", 
                value=f"```{quest.requirements}```", 
                inline=False
            )

        # Add reward with beautiful formatting
        if quest.reward:
            public_embed.add_field(
                name="Reward", 
                value=f"```{quest.reward}```", 
                inline=False
            )

        # Add required roles with beautiful formatting
        if quest.required_role_ids:
            role_mentions = []
            for role_id in quest.required_role_ids:
                role = interaction.guild.get_role(role_id)
                if role:
                    role_mentions.append(role.mention)
            if role_mentions:
                public_embed.add_field(
                    name="Required Roles", 
                    value=" ".join(role_mentions), 
                    inline=False
                )

        # Add how to accept with beautiful formatting
        accept_channel = await self.channel_config.get_quest_accept_channel(interaction.guild.id)
        if accept_channel:
            public_embed.add_field(
                name="How to Accept", 
                value=f"Use `/accept_quest` in <#{accept_channel}>", 
                inline=False
            )

        # Set author with enhanced styling
        public_embed.set_author(
            name=f"Created by {interaction.user.display_name}", 
            icon_url=interaction.user.display_avatar.url if interaction.user.display_avatar else None
        )

        # Add footer with timestamp
        public_embed.set_footer(
            text=f"Quest created on {quest.created_at.strftime('%B %d, %Y at %I:%M %p')}",
            icon_url=interaction.guild.icon.url if interaction.guild.icon else None
        )

        # Create a simpler embed for the private response
        private_embed = discord.Embed(
            title="Quest Created Successfully!",
            description=f"Your quest **{quest.title}** has been created and posted to the quest list channel!",
            color=self._get_rank_color(quest.rank)
        )
        private_embed.add_field(name="Quest ID", value=f"`{quest.quest_id}`", inline=True)
        private_embed.add_field(name="Rank", value=quest.rank.title(), inline=True)
        private_embed.add_field(name="Category", value=quest.category.title(), inline=True)

        # Send private response to user
        await interaction.followup.send(embed=private_embed)

        # Send the beautiful quest embed to quest list channel
        quest_list_channel_id = await self.channel_config.get_quest_list_channel(interaction.guild.id)
        if quest_list_channel_id:
            quest_list_channel = interaction.guild.get_channel(quest_list_channel_id)
            if quest_list_channel:
                await quest_list_channel.send(embed=public_embed)

    @app_commands.command(name="list_quests", description="List all available quests")
    @app_commands.describe(
        rank_filter="Filter by quest rank",
        category_filter="Filter by quest category"
    )
    @app_commands.choices(rank_filter=[
        app_commands.Choice(name="Easy", value=QuestRank.EASY),
        app_commands.Choice(name="Normal", value=QuestRank.NORMAL),
        app_commands.Choice(name="Medium", value=QuestRank.MEDIUM),
        app_commands.Choice(name="Hard", value=QuestRank.HARD),
        app_commands.Choice(name="Impossible", value=QuestRank.IMPOSSIBLE)
    ])
    @app_commands.choices(category_filter=[
        app_commands.Choice(name="Hunting", value=QuestCategory.HUNTING),
        app_commands.Choice(name="Gathering", value=QuestCategory.GATHERING),
        app_commands.Choice(name="Collecting", value=QuestCategory.COLLECTING),
        app_commands.Choice(name="Crafting", value=QuestCategory.CRAFTING),
        app_commands.Choice(name="Exploration", value=QuestCategory.EXPLORATION),
        app_commands.Choice(name="Combat", value=QuestCategory.COMBAT),
        app_commands.Choice(name="Social", value=QuestCategory.SOCIAL),
        app_commands.Choice(name="Building", value=QuestCategory.BUILDING),
        app_commands.Choice(name="Trading", value=QuestCategory.TRADING),
        app_commands.Choice(name="Puzzle", value=QuestCategory.PUZZLE),
        app_commands.Choice(name="Survival", value=QuestCategory.SURVIVAL),
        app_commands.Choice(name="Other", value=QuestCategory.OTHER)
    ])
    async def list_quests(self,
                          interaction: discord.Interaction,
                          rank_filter: Optional[str] = None,
                          category_filter: Optional[str] = None):
        """List all available quests"""
        # Respond immediately to prevent timeout
        await interaction.response.defer()

        quests = await self.quest_manager.get_available_quests(interaction.guild.id)

        # Apply filters
        if rank_filter:
            quests = [q for q in quests if q.rank == rank_filter]
        if category_filter:
            quests = [q for q in quests if q.category == category_filter]

        # Sort by rank and creation date
        quest_order = {QuestRank.EASY: 0, QuestRank.NORMAL: 1, QuestRank.MEDIUM: 2, QuestRank.HARD: 3, QuestRank.IMPOSSIBLE: 4}
        quests.sort(key=lambda q: (quest_order.get(q.rank, 1), q.created_at))

        if not quests:
            # Create a beautiful "no quests" embed
            filter_parts = []
            if rank_filter:
                filter_parts.append(f"**{rank_filter.upper()}** rank")
            if category_filter:
                filter_parts.append(f"**{category_filter.title()}** category")

            filter_text = f" matching {' and '.join(filter_parts)}" if filter_parts else ""

            no_quests_embed = discord.Embed(
                title="No Quests Found",
                description=f"There are currently no available quests{filter_text}.",
                color=discord.Color.orange()
            )
            no_quests_embed.add_field(
                name="Tip", 
                value="Try removing filters or check back later for new quests!", 
                inline=False
            )

            await interaction.followup.send(embed=no_quests_embed)
            return

        # Define symbols and emojis for better visual appeal
        rank_symbols = {
            QuestRank.EASY: "⭐",
            QuestRank.NORMAL: "⭐⭐", 
            QuestRank.MEDIUM: "⭐⭐⭐",
            QuestRank.HARD: "⭐⭐⭐⭐",
            QuestRank.IMPOSSIBLE: "⭐⭐⭐⭐⭐"
        }

        category_emojis = {
            QuestCategory.HUNTING: "🏹",
            QuestCategory.GATHERING: "🌾",
            QuestCategory.COLLECTING: "📦",
            QuestCategory.CRAFTING: "🔨",
            QuestCategory.EXPLORATION: "🗺️",
            QuestCategory.COMBAT: "⚔️",
            QuestCategory.SOCIAL: "🤝",
            QuestCategory.BUILDING: "🏗️",
            QuestCategory.TRADING: "💰",
            QuestCategory.PUZZLE: "🧩",
            QuestCategory.SURVIVAL: "🛡️",
            QuestCategory.OTHER: "❓"
        }

        # Split into pages of 6 quests each for better readability
        pages = []
        quests_per_page = 6
        total_pages = (len(quests) + quests_per_page - 1) // quests_per_page

        for page_num in range(total_pages):
            start_idx = page_num * quests_per_page
            end_idx = min(start_idx + quests_per_page, len(quests))
            page_quests = quests[start_idx:end_idx]

            # Create title based on filters
            title_parts = ["AVAILABLE QUESTS"]
            if rank_filter:
                title_parts.append(f"| {rank_filter.upper()} RANK")
            if category_filter:
                title_parts.append(f"| {category_filter.upper()}")

            embed = discord.Embed(
                title=" ".join(title_parts),
                description=f"**Found {len(quests)} quest{('s' if len(quests) != 1 else '')}** • Page {page_num + 1} of {total_pages}",
                color=discord.Color.blue()
            )

            for quest in page_quests:
                # Get role requirements
                role_display = ""
                if quest.required_role_ids:
                    required_roles = []
                    for role_id in quest.required_role_ids:
                        role = interaction.guild.get_role(role_id)
                        if role:
                            required_roles.append(f"`{role.name}`")
                    if required_roles:
                        role_display = f"\n**Requires:** {', '.join(required_roles)}"

                # Build quest info with beautiful formatting
                quest_header = f"**{quest.title}**"

                quest_info = f"**{quest.description[:120]}{'...' if len(quest.description) > 120 else ''}**\n"
                quest_info += f"\n**ID:** `{quest.quest_id}`"
                quest_info += f"\n**Rank:** {quest.rank.upper()}"
                quest_info += f"\n**Category:** {quest.category.title()}"

                if quest.requirements:
                    quest_info += f"\n**Requirements:** {quest.requirements[:80]}{'...' if len(quest.requirements) > 80 else ''}"

                if quest.reward:
                    quest_info += f"\n**Reward:** {quest.reward[:80]}{'...' if len(quest.reward) > 80 else ''}"

                quest_info += role_display

                # Get accept channel info
                accept_channel = await self.channel_config.get_quest_accept_channel(interaction.guild.id)
                if accept_channel:
                    quest_info += f"\n\n**Accept with:** `/accept_quest {quest.quest_id}` in <#{accept_channel}>"

                embed.add_field(
                    name=quest_header,
                    value=quest_info,
                    inline=False
                )

                # Add a subtle separator between quests (except for the last one)
                if quest != page_quests[-1]:
                    embed.add_field(name="\u200b", value="─" * 40, inline=False)

            # Add navigation hint for multiple pages
            if total_pages > 1:
                embed.set_footer(
                    text=f"Use the navigation buttons to view other pages • Quest List",
                    icon_url=interaction.guild.icon.url if interaction.guild.icon else None
                )
            else:
                embed.set_footer(
                    text="Quest List",
                    icon_url=interaction.guild.icon.url if interaction.guild.icon else None
                )

            pages.append(embed)

        # Send first page (for now, just sending the first page - you can add pagination buttons later)
        await interaction.followup.send(embed=pages[0])

    @app_commands.command(name="accept_quest", description="Accept a quest")
    @app_commands.describe(quest_id="The ID of the quest to accept")
    async def accept_quest(self, interaction: discord.Interaction, quest_id: str):
        """Accept a quest"""
        quest_accept_channel_id = await self.channel_config.get_quest_accept_channel(interaction.guild.id)
        if quest_accept_channel_id and interaction.channel.id != quest_accept_channel_id:
            accept_channel = interaction.guild.get_channel(quest_accept_channel_id)
            if accept_channel:
                await interaction.response.send_message(
                    f"Please use {accept_channel.mention} to accept quests!",
                    ephemeral=True
                )
                return

        # Get user's role IDs
        user_role_ids = [role.id for role in interaction.user.roles] if hasattr(interaction.user, 'roles') else []

        progress, error = await self.quest_manager.accept_quest(
            quest_id, interaction.user.id, user_role_ids, interaction.channel.id
        )

        if error:
            await interaction.response.send_message(f"{error}", ephemeral=True)
            return

        quest = await self.quest_manager.get_quest(quest_id)
        if not quest:
            await interaction.response.send_message("Quest not found!", ephemeral=True)
            return

        embed = discord.Embed(
            title="Quest Accepted",
            description=f"You have accepted the quest: **{quest.title}**",
            color=self._get_rank_color(quest.rank)
        )
        embed.add_field(name="Quest ID", value=quest.quest_id, inline=True)
        embed.add_field(name="Description", value=quest.description, inline=False)

        if quest.requirements:
            embed.add_field(name="Requirements", value=quest.requirements, inline=False)

        if quest.reward:
            embed.add_field(name="Reward", value=quest.reward, inline=False)

        # Send to quest submit channel
        quest_submit_channel_id = await self.channel_config.get_quest_submit_channel(interaction.guild.id)
        if quest_submit_channel_id:
            submit_channel = interaction.guild.get_channel(quest_submit_channel_id)
            if submit_channel:
                embed.add_field(name="Next Step", value=f"Use `/complete_quest {quest_id}` in {submit_channel.mention} when ready to submit!", inline=False)

        await interaction.response.send_message(embed=embed)

        # Update user stats
        await self.user_stats_manager.update_quest_accepted(interaction.user.id, interaction.guild.id)

    @app_commands.command(name="complete_quest", description="Complete a quest with proof")
    @app_commands.describe(
        quest_id="The ID of the quest to complete",
        proof_text="Text proof of completion",
        proof_image1="Image proof 1",
        proof_image2="Image proof 2",
        proof_image3="Image proof 3",
        proof_image4="Image proof 4",
        proof_image5="Image proof 5",
        proof_image6="Image proof 6",
        proof_image7="Image proof 7",
        proof_image8="Image proof 8",
        proof_image9="Image proof 9",
        proof_image10="Image proof 10",
        proof_image11="Image proof 11",
        proof_image12="Image proof 12",
        proof_image13="Image proof 13",
        proof_image14="Image proof 14",
        proof_image15="Image proof 15"
    )
    async def complete_quest(self,
                             interaction: discord.Interaction,
                             quest_id: str,
                             proof_text: str,
                             proof_image1: Optional[discord.Attachment] = None,
                             proof_image2: Optional[discord.Attachment] = None,
                             proof_image3: Optional[discord.Attachment] = None,
                             proof_image4: Optional[discord.Attachment] = None,
                             proof_image5: Optional[discord.Attachment] = None,
                             proof_image6: Optional[discord.Attachment] = None,
                             proof_image7: Optional[discord.Attachment] = None,
                             proof_image8: Optional[discord.Attachment] = None,
                             proof_image9: Optional[discord.Attachment] = None,
                             proof_image10: Optional[discord.Attachment] = None,
                             proof_image11: Optional[discord.Attachment] = None,
                             proof_image12: Optional[discord.Attachment] = None,
                             proof_image13: Optional[discord.Attachment] = None,
                             proof_image14: Optional[discord.Attachment] = None,
                             proof_image15: Optional[discord.Attachment] = None):
        """Complete a quest with proof"""
        quest_submit_channel_id = await self.channel_config.get_quest_submit_channel(interaction.guild.id)
        if quest_submit_channel_id and interaction.channel.id != quest_submit_channel_id:
            submit_channel = interaction.guild.get_channel(quest_submit_channel_id)
            if submit_channel:
                await interaction.response.send_message(
                    f"Please use {submit_channel.mention} to submit quest completions!",
                    ephemeral=True
                )
                return

        # Collect proof images
        proof_images = [proof_image1, proof_image2, proof_image3, proof_image4, proof_image5,
                       proof_image6, proof_image7, proof_image8, proof_image9, proof_image10,
                       proof_image11, proof_image12, proof_image13, proof_image14, proof_image15]
        proof_image_urls = []

        for image in proof_images:
            if image:
                proof_image_urls.append(image.url)

        progress = await self.quest_manager.complete_quest(
            quest_id, interaction.user.id, proof_text, proof_image_urls
        )

        if not progress:
            await interaction.response.send_message("Quest not found or not accepted by you!", ephemeral=True)
            return

        quest = await self.quest_manager.get_quest(quest_id)
        if not quest:
            await interaction.response.send_message("Quest not found!", ephemeral=True)
            return

        embed = discord.Embed(
            title="Quest Completed!",
            description=f"You have completed the quest: **{quest.title}**",
            color=self._get_rank_color(quest.rank)
        )
        embed.add_field(name="Quest ID", value=quest.quest_id, inline=True)
        embed.add_field(name="Status", value="Pending Approval", inline=True)
        embed.add_field(name="Proof Text", value=proof_text[:1000] if proof_text else "No text proof", inline=False)

        if quest.reward:
            embed.add_field(name="Reward", value=quest.reward, inline=False)

        # Send to approval channel
        quest_approval_channel_id = await self.channel_config.get_quest_approval_channel(interaction.guild.id)
        if quest_approval_channel_id:
            approval_channel = interaction.guild.get_channel(quest_approval_channel_id)
            if approval_channel:
                approval_embed = discord.Embed(
                    title="Quest Approval Required",
                    description=f"User {interaction.user.mention} completed quest: **{quest.title}**",
                    color=discord.Color.orange()
                )
                approval_embed.add_field(name="Quest ID", value=quest.quest_id, inline=True)
                approval_embed.add_field(name="User", value=interaction.user.mention, inline=True)
                approval_embed.add_field(name="Proof Text", value=proof_text[:1000] if proof_text else "No text proof", inline=False)

                if quest.reward:
                    approval_embed.add_field(name="Reward", value=quest.reward, inline=False)

                approval_embed.add_field(name="Actions", value=f"Use `/approve_quest {quest_id} {interaction.user.id}` or `/reject_quest {quest_id} {interaction.user.id}`", inline=False)

                # Add image proofs
                if proof_image_urls:
                    approval_embed.set_image(url=proof_image_urls[0])
                    if len(proof_image_urls) > 1:
                        approval_embed.add_field(name="Additional Images", value="\n".join(proof_image_urls[1:]), inline=False)

                await approval_channel.send(embed=approval_embed)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="my_quests", description="View your accepted quests")
    async def my_quests(self, interaction: discord.Interaction):
        """View user's accepted quests"""
        user_quests = await self.quest_manager.get_user_quests(interaction.user.id, interaction.guild.id)

        if not user_quests:
            await interaction.response.send_message("You have no active quests!", ephemeral=True)
            return

        embed = discord.Embed(
            title="Your Quests",
            description=f"You have {len(user_quests)} active quests",
            color=discord.Color.blue()
        )

        for progress in user_quests:
            quest = await self.quest_manager.get_quest(progress.quest_id)
            if quest:
                embed.add_field(
                    name=f"{quest.title} (ID: {quest.quest_id})",
                    value=f"Status: {progress.status.title()}\n{quest.description[:100]}{'...' if len(quest.description) > 100 else ''}",
                    inline=False
                )

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="pending_approvals", description="View quests pending approval")
    async def pending_approvals(self, interaction: discord.Interaction):
        """View quests pending approval"""
        if not has_quest_creation_permission(interaction.user, interaction.guild):
            await interaction.response.send_message("You don't have permission to view pending approvals!", ephemeral=True)
            return

        pending = await self.quest_manager.get_pending_approvals(interaction.user.id, interaction.guild.id)

        if not pending:
            await interaction.response.send_message("No quests pending approval!", ephemeral=True)
            return

        embed = discord.Embed(
            title="Pending Approvals",
            description=f"You have {len(pending)} quests pending approval",
            color=discord.Color.orange()
        )

        for quest_id, user_id, proof_text, proof_images, quest_title in pending:
            user = interaction.guild.get_member(user_id)
            user_display = user.display_name if user else f"User {user_id}"

            embed.add_field(
                name=f"{quest_title} (ID: {quest_id})",
                value=f"User: {user_display}\nProof: {proof_text[:100]}{'...' if len(proof_text) > 100 else ''}",
                inline=False
            )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="quest_approval", description="Comprehensive quest approval management")
    @app_commands.describe(
        quest_id="The ID of the quest",
        user_id="The user ID who completed it",
        action="Action to perform"
    )
    @app_commands.choices(action=[
        app_commands.Choice(name="View Details", value="view"),
        app_commands.Choice(name="Approve", value="approve"),
        app_commands.Choice(name="Reject", value="reject")
    ])
    async def quest_approval(self, interaction: discord.Interaction, quest_id: str, user_id: str, action: str):
        """Comprehensive quest approval management"""
        # Check permissions first
        if not has_quest_creation_permission(interaction.user, interaction.guild):
            await interaction.response.send_message("You don't have permission to manage quest approvals!", ephemeral=True)
            return

        # Defer response immediately to prevent timeout
        await interaction.response.defer()

        # Validate inputs
        try:
            user_id_int = int(user_id)
        except ValueError:
            await interaction.followup.send("Invalid user ID format!", ephemeral=True)
            return

        # Get quest and validate
        quest = await self.quest_manager.get_quest(quest_id)
        if not quest:
            await interaction.followup.send("Quest not found!", ephemeral=True)
            return

        # Check quest ownership permissions
        if not can_manage_quest(interaction.user, interaction.guild, quest.creator_id):
            await interaction.followup.send("You don't have permission to manage this quest!", ephemeral=True)
            return

        # Get quest progress
        progress = await self.quest_manager.database.get_user_quest_progress(user_id_int, quest_id)
        if not progress:
            await interaction.followup.send("No quest progress found for this user!", ephemeral=True)
            return

        # Get user object
        user = interaction.guild.get_member(user_id_int)
        user_display = user.display_name if user else f"User {user_id}"

        if action == "view":
            # Create detailed review embed
            embed = discord.Embed(
                title="Quest Approval Review",
                description=f"**{quest.title}**\nSubmitted by {user.mention if user else f'User {user_id}'}",
                color=self._get_rank_color(quest.rank)
            )

            # Quest information
            embed.add_field(name="Quest ID", value=f"`{quest.quest_id}`", inline=True)
            embed.add_field(name="Rank", value=quest.rank.upper(), inline=True)
            embed.add_field(name="Category", value=quest.category.title(), inline=True)

            embed.add_field(name="Quest Description", value=quest.description, inline=False)

            if quest.requirements:
                embed.add_field(name="Requirements", value=quest.requirements, inline=False)

            if quest.reward:
                embed.add_field(name="Reward", value=quest.reward, inline=False)

            # User submission details
            embed.add_field(name="User", value=user.mention if user else f"User {user_id}", inline=True)
            embed.add_field(name="Status", value=progress.status.title(), inline=True)
            embed.add_field(name="Submitted At", value=f"<t:{int(progress.completed_at.timestamp())}:f>" if progress.completed_at else "N/A", inline=True)

            # Proof details
            if progress.proof_text:
                proof_preview = progress.proof_text[:500] + "..." if len(progress.proof_text) > 500 else progress.proof_text
                embed.add_field(name="Proof Text", value=f"```{proof_preview}```", inline=False)

            if progress.proof_image_urls:
                embed.add_field(name="Images Submitted", value=f"{len(progress.proof_image_urls)} image(s) attached", inline=True)
                # Set first image as main image
                embed.set_image(url=progress.proof_image_urls[0])

            # Action instructions
            embed.add_field(
                name="Actions",
                value=f"Use `/quest_approval {quest_id} {user_id} approve` to approve\nUse `/quest_approval {quest_id} {user_id} reject` to reject",
                inline=False
            )

            embed.set_footer(text=f"Quest created by {interaction.guild.get_member(quest.creator_id).display_name if interaction.guild.get_member(quest.creator_id) else 'Unknown'}")

            await interaction.followup.send(embed=embed)

            # Send additional images if there are more than one
            if progress.proof_image_urls and len(progress.proof_image_urls) > 1:
                additional_embed = discord.Embed(
                    title="Additional Proof Images",
                    description=f"Additional images for quest `{quest_id}` by {user.display_name if user else f'User {user_id}'}",
                    color=discord.Color.blue()
                )
                for i, url in enumerate(progress.proof_image_urls[1:], 2):
                    additional_embed.add_field(name=f"Image {i}", value=f"[View Image]({url})", inline=True)

                await interaction.followup.send(embed=additional_embed)

        elif action == "approve":
            # Validate quest can be approved
            if progress.status != "completed":
                await interaction.followup.send("Quest is not ready for approval!", ephemeral=True)
                return

            # Approve the quest
            approved_progress = await self.quest_manager.approve_quest(quest_id, user_id_int, approved=True)
            if not approved_progress:
                await interaction.followup.send("Failed to approve quest!", ephemeral=True)
                return

            # Create approval confirmation embed
            embed = discord.Embed(
                title="Quest Approved!",
                description=f"Quest **{quest.title}** has been approved for {user.mention if user else f'User {user_id}'}",
                color=discord.Color.green()
            )

            embed.add_field(name="Quest ID", value=f"`{quest.quest_id}`", inline=True)
            embed.add_field(name="User", value=user.mention if user else f"User {user_id}", inline=True)

            if quest.reward:
                embed.add_field(name="Reward", value=quest.reward, inline=False)

            embed.set_footer(text=f"Approved by {interaction.user.display_name}")

            await interaction.followup.send(embed=embed)

            # Send notification to user
            notification_channel_id = await self.channel_config.get_notification_channel(interaction.guild.id)
            if notification_channel_id:
                notification_channel = interaction.guild.get_channel(notification_channel_id)
                if notification_channel:
                    user_embed = discord.Embed(
                        title="Quest Approved!",
                        description=f"Congratulations! Your quest **{quest.title}** has been approved!",
                        color=discord.Color.green()
                    )

                    if quest.reward:
                        user_embed.add_field(name="Reward", value=quest.reward, inline=False)

                    user_embed.set_footer(text=f"Approved by {interaction.user.display_name}")

                    await notification_channel.send(f"{user.mention if user else f'<@{user_id}>'}", embed=user_embed)

            # Update user stats
            await self.user_stats_manager.update_quest_completed(user_id_int, interaction.guild.id)

        elif action == "reject":
            # Validate quest can be rejected
            if progress.status != "completed":
                await interaction.followup.send("Quest is not ready for rejection!", ephemeral=True)
                return

            # Reject the quest
            rejected_progress = await self.quest_manager.approve_quest(quest_id, user_id_int, approved=False)
            if not rejected_progress:
                await interaction.followup.send("Failed to reject quest!", ephemeral=True)
                return

            # Create rejection confirmation embed
            embed = discord.Embed(
                title="Quest Rejected",
                description=f"Quest **{quest.title}** has been rejected for {user.mention if user else f'User {user_id}'}",
                color=discord.Color.red()
            )

            embed.add_field(name="Quest ID", value=f"`{quest.quest_id}`", inline=True)
            embed.add_field(name="User", value=user.mention if user else f"User {user_id}", inline=True)
            embed.add_field(name="Note", value="User can attempt again in 24 hours", inline=False)

            embed.set_footer(text=f"Rejected by {interaction.user.display_name}")

            await interaction.followup.send(embed=embed)

            # Send notification to user
            notification_channel_id = await self.channel_config.get_notification_channel(interaction.guild.id)
            if notification_channel_id:
                notification_channel = interaction.guild.get_channel(notification_channel_id)
                if notification_channel:
                    user_embed = discord.Embed(
                        title="Quest Rejected",
                        description=f"Your quest **{quest.title}** has been rejected. You can try again in 24 hours.",
                        color=discord.Color.red()
                    )

                    user_embed.set_footer(text=f"Rejected by {interaction.user.display_name}")

                    await notification_channel.send(f"{user.mention if user else f'<@{user_id}>'}", embed=user_embed)

            # Update user stats
            await self.user_stats_manager.update_quest_rejected(user_id_int, interaction.guild.id)

    @app_commands.command(name="delete_quest", description="Delete a quest")
    @app_commands.describe(quest_id="The ID of the quest to delete")
    async def delete_quest(self, interaction: discord.Interaction, quest_id: str):
        """Delete a quest"""
        quest = await self.quest_manager.get_quest(quest_id)
        if not quest:
            await interaction.response.send_message("Quest not found!", ephemeral=True)
            return

        if not can_manage_quest(interaction.user, interaction.guild, quest.creator_id):
            await interaction.response.send_message("You don't have permission to delete this quest!", ephemeral=True)
            return

        success = await self.quest_manager.delete_quest(quest_id)
        if success:
            await interaction.response.send_message(f"Quest '{quest.title}' has been deleted!", ephemeral=True)
        else:
            await interaction.response.send_message("Failed to delete quest!", ephemeral=True)

    @app_commands.command(name="user_stats", description="View user quest statistics")
    @app_commands.describe(user="The user to view stats for (optional)")
    async def user_stats(self, interaction: discord.Interaction, user: Optional[discord.Member] = None):
        """View user quest statistics"""
        target_user = user or interaction.user

        stats = await self.user_stats_manager.get_user_stats(target_user.id, interaction.guild.id)

        embed = discord.Embed(
            title=f"Quest Statistics for {target_user.display_name}",
            color=discord.Color.blue()
        )

        embed.add_field(name="Completed Quests", value=stats.quests_completed, inline=True)
        embed.add_field(name="Accepted Quests", value=stats.quests_accepted, inline=True)
        embed.add_field(name="Rejected Quests", value=stats.quests_rejected, inline=True)

        # Calculate completion rate
        completion_rate = 0
        if stats.quests_accepted > 0:
            completion_rate = (stats.quests_completed / stats.quests_accepted) * 100

        embed.add_field(name="Completion Rate", value=f"{completion_rate:.1f}%", inline=True)

        if stats.first_quest_date:
            embed.add_field(name="First Quest", value=f"<t:{int(datetime.fromisoformat(stats.first_quest_date).timestamp())}:D>", inline=True)

        if stats.last_quest_date:
            embed.add_field(name="Last Quest", value=f"<t:{int(datetime.fromisoformat(stats.last_quest_date).timestamp())}:D>", inline=True)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="leaderboard", description="View quest leaderboard")
    @app_commands.describe(limit="Number of users to show (default: 10)")
    async def leaderboard(self, interaction: discord.Interaction, limit: Optional[int] = 10):
        """View quest leaderboard"""
        if limit and limit > 25:
            limit = 25

        stats_list = await self.user_stats_manager.get_guild_leaderboard(interaction.guild.id, limit or 10)

        if not stats_list:
            await interaction.response.send_message("No quest statistics found!", ephemeral=True)
            return

        embed = discord.Embed(
            title="Quest Leaderboard",
            description=f"Top {len(stats_list)} quest completers",
            color=discord.Color.gold()
        )

        for i, stats in enumerate(stats_list, 1):
            user = interaction.guild.get_member(stats.user_id)
            user_display = user.display_name if user else f"User {stats.user_id}"

            embed.add_field(
                name=f"{i}. {user_display}",
                value=f"{stats.quests_completed} completed\n{stats.quests_accepted} accepted",
                inline=True
            )

        # Add guild totals
        guild_stats = await self.user_stats_manager.get_total_guild_stats(interaction.guild.id)
        embed.add_field(
            name="Guild Totals",
            value=f"Total Completed: {guild_stats['total_completed']}\nTotal Accepted: {guild_stats['total_accepted']}\nActive Users: {guild_stats['active_users']}",
            inline=False
        )

        await interaction.response.send_message(embed=embed)


async def setup(bot):
    # This will be called when the cog is loaded
    pass