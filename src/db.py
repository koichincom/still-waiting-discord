import asyncpg
import os
from dotenv import load_dotenv
import logging
from config import config

logger = logging.getLogger(__name__)
load_dotenv()

# Global connection pool
_pool = None

async def get_pool():
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_DATABASE"), 
            host=os.getenv("DB_HOST"),
            port=int(os.getenv("DB_PORT")),
            ssl='require',  # Supabase requires SSL
            min_size=config.DB_MIN_POOL_SIZE,
            max_size=config.DB_MAX_POOL_SIZE
        )
    return _pool

async def init_db_discord(pool):
    async with pool.acquire() as conn:
        await conn.execute(f"""
            CREATE TABLE IF NOT EXISTS {config.DB_TABLE_NAME_DISCORD} (
                id SERIAL PRIMARY KEY,
                message_id BIGINT NOT NULL,
                channel_id BIGINT NOT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                mentioned_user_id BIGINT NOT NULL,
                ignore BOOLEAN NOT NULL DEFAULT FALSE,
                UNIQUE(message_id, mentioned_user_id)
            )
        """)
        logger.info(f"Table {config.DB_TABLE_NAME_DISCORD} initialized")

async def init_db_stats(pool):
    async with pool.acquire() as conn:
        await conn.execute(f"""
            CREATE TABLE IF NOT EXISTS {config.DB_TABLE_NAME_STATS} (
                id SERIAL PRIMARY KEY,
                platform TEXT NOT NULL,
                metric TEXT NOT NULL,
                value BIGINT NOT NULL,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(platform, metric) -- Ensure unique constraint on platform and metric
            )
        """)
        logger.info(f"Table {config.DB_TABLE_NAME_STATS} initialized")

async def save_message(pool, message_id, channel_id, mentioned_user_id):
    async with pool.acquire() as conn:
        try:
            return await conn.fetchrow(f"""
                INSERT INTO {config.DB_TABLE_NAME_DISCORD} 
                (message_id, channel_id, mentioned_user_id)
                VALUES ($1, $2, $3)
                RETURNING id, message_id, channel_id, created_at, mentioned_user_id
            """, message_id, channel_id, mentioned_user_id)
        
        except asyncpg.UniqueViolationError:
            logger.warning(f"Duplicate message: {message_id}")
            return None
        
        except Exception as e:
            logger.error(f"Failed to save message: {e}")
            raise

async def if_message_exists(pool, message_id, user_id):
    async with pool.acquire() as conn:
        row = await conn.fetchrow(f"""
            SELECT * FROM {config.DB_TABLE_NAME_DISCORD} 
            WHERE message_id = $1 AND mentioned_user_id = $2
        """, message_id, user_id)
        return row is not None
    
async def delete_message(pool, message_id, user_id):
    async with pool.acquire() as conn:
        try:
            await conn.execute(f"""
                DELETE FROM {config.DB_TABLE_NAME_DISCORD} 
                WHERE message_id = $1 AND mentioned_user_id = $2
            """, message_id, user_id)
        except Exception as e:
            logger.error(f"Failed to delete message {message_id} for user {user_id}: {e}")
            raise

async def has_message_expires(pool, threshold):
    async with pool.acquire() as conn:
        rows = await conn.fetch(f"""
            SELECT * FROM {config.DB_TABLE_NAME_DISCORD} 
            WHERE created_at < NOW() - INTERVAL '{threshold} seconds'
        """)
        return rows

async def update_guild_count(pool, count):
    async with pool.acquire() as conn:
        # Use a separate query approach for more reliable update
        result = await conn.fetchrow(f"""
            SELECT value FROM {config.DB_TABLE_NAME_STATS} 
            WHERE platform = 'discord' AND metric = 'guild_count'
        """)
        
        if result:
            # Update existing record
            await conn.execute(f"""
                UPDATE {config.DB_TABLE_NAME_STATS} 
                SET value = $1, updated_at = NOW()
                WHERE platform = 'discord' AND metric = 'guild_count'
            """, count)
        else:
            # Insert new record
            await conn.execute(f"""
                INSERT INTO {config.DB_TABLE_NAME_STATS} (platform, metric, value, updated_at)
                VALUES ('discord', 'guild_count', $1, NOW())
            """, count)

async def update_user_count(pool, count):
    async with pool.acquire() as conn:
        # Use a separate query approach for more reliable update
        result = await conn.fetchrow(f"""
            SELECT value FROM {config.DB_TABLE_NAME_STATS} 
            WHERE platform = 'discord' AND metric = 'user_count'
        """)
        
        if result:
            # Update existing record
            await conn.execute(f"""
                UPDATE {config.DB_TABLE_NAME_STATS} 
                SET value = $1, updated_at = NOW()
                WHERE platform = 'discord' AND metric = 'user_count'
            """, count)
        else:
            # Insert new record
            await conn.execute(f"""
                INSERT INTO {config.DB_TABLE_NAME_STATS} (platform, metric, value, updated_at)
                VALUES ('discord', 'user_count', $1, NOW())
            """, count)

async def increment_message_count(pool):
    async with pool.acquire() as conn:
        # Use a separate query approach for more reliable increment
        result = await conn.fetchrow(f"""
            SELECT value FROM {config.DB_TABLE_NAME_STATS} 
            WHERE platform = 'discord' AND metric = 'message_count'
        """)
        
        if result:
            # Update existing record
            new_value = result['value'] + 1
            await conn.execute(f"""
                UPDATE {config.DB_TABLE_NAME_STATS} 
                SET value = $1, updated_at = NOW()
                WHERE platform = 'discord' AND metric = 'message_count'
            """, new_value)
        else:
            # Insert new record
            await conn.execute(f"""
                INSERT INTO {config.DB_TABLE_NAME_STATS} (platform, metric, value, updated_at)
                VALUES ('discord', 'message_count', 1, NOW())
            """)