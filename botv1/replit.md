# Discord Quest Bot

## Overview

This is a Discord bot that manages a quest system for gaming communities. Users can create, accept, complete, and approve quests with various ranks and categories. The bot uses PostgreSQL for data persistence and provides a comprehensive quest management system with role-based permissions.

**Status**: ✅ Successfully migrated to Replit environment and ready for deployment

## User Preferences

Preferred communication style: Simple, everyday language.

## Recent Changes

**July 11, 2025**: 
- Successfully migrated project from Replit Agent to standard Replit environment
- Fixed datetime serialization issues in database operations
- Added comprehensive deployment configurations for Render.com
- Created deployment documentation and Docker configuration
- All bot commands now working correctly with PostgreSQL database

## Recent Changes

- **July 11, 2025**: Successfully migrated project from Replit Agent to standard Replit environment
- **Database Migration**: Fixed datetime handling issues in PostgreSQL database operations
- **Deployment Setup**: Added Render.com deployment configuration files (render.yaml, runtime.txt, startup.sh)
- **Bot Status**: Discord bot successfully connected and synced 12 slash commands

## System Architecture

### Backend Architecture
- **Python Discord Bot**: Built using discord.py library with slash commands
- **PostgreSQL Database**: Relational database for persistent data storage
- **Asynchronous Programming**: Fully async/await pattern for non-blocking operations
- **Flask Web Server**: Simple HTTP server for health checks and keepalive pings

### Data Storage
- **PostgreSQL**: Primary database for all quest data, user progress, and configuration
- **Connection Pooling**: asyncpg connection pool for efficient database operations
- **Migration System**: Built-in migration tools to convert from JSON to PostgreSQL

### Authentication & Authorization
- **Discord OAuth**: Built-in Discord authentication through bot permissions
- **Role-Based Access**: Custom permission system based on Discord roles and server permissions
- **Permission Levels**: Quest creation restricted to moderators, admins, and specific roles

## Key Components

### Core Models
- **Quest**: Main quest entity with title, description, requirements, rewards, rank, and category
- **QuestProgress**: Tracks user progress through quests (accepted, completed, approved, rejected)
- **UserStats**: Aggregated statistics for user quest activity
- **Channel Configuration**: Server-specific channel mappings for quest workflow

### Quest Management
- **QuestManager**: Central orchestrator for quest lifecycle operations
- **Database Layer**: Async PostgreSQL operations with connection pooling
- **Permission System**: Role-based access control for quest creation and management

### User Interface
- **Slash Commands**: Modern Discord slash command interface
- **Rich Embeds**: Formatted Discord embeds for quest display
- **Channel Workflow**: Dedicated channels for quest listing, acceptance, submission, and approval

## Data Flow

### Quest Creation Flow
1. User with permissions creates quest via slash command
2. Quest data validated and stored in PostgreSQL
3. Quest displayed in designated quest list channel
4. Quest becomes available for acceptance by eligible users

### Quest Acceptance Flow
1. User attempts to accept quest in designated channel
2. System validates user permissions and role requirements
3. Rate limiting enforced (24-hour cooldown between attempts)
4. Quest progress record created with "accepted" status
5. User statistics updated

### Quest Completion Flow
1. User submits quest completion with proof (text/images)
2. Submission stored in quest progress with "completed" status
3. Notification sent to approval channel for moderator review
4. Moderator approves/rejects submission
5. User statistics and quest status updated accordingly

## External Dependencies

### Core Libraries
- **discord.py**: Discord API interaction and bot functionality
- **asyncpg**: PostgreSQL async database driver
- **flask**: Web server for health checks
- **requests**: HTTP client for external API calls

### Infrastructure
- **PostgreSQL**: Primary database system
- **Replit**: Hosting platform with built-in database support
- **Discord API**: Bot permissions and guild management

## Deployment Strategy

### Replit Deployment
- **Always-On**: Flask server maintains bot availability
- **Environment Variables**: Database credentials and bot token stored securely
- **Automatic Restart**: Built-in process monitoring and restart
- **Health Checks**: HTTP endpoints for monitoring bot status

### Database Setup
- **Automatic Migration**: JSON to PostgreSQL migration system
- **Connection Pooling**: Efficient database connection management
- **Error Handling**: Robust error handling with logging and fallback mechanisms

### Configuration Management
- **Environment Variables**: Sensitive data stored in environment
- **Per-Guild Configuration**: Channel mappings stored per Discord server
- **Dynamic Configuration**: Runtime configuration updates supported

The bot is designed to be scalable, maintainable, and user-friendly, with a focus on providing a smooth quest management experience for gaming communities.