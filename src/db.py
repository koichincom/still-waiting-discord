import asyncpg
import os
from dotenv import load_dotenv
import logging
from .config import config

logger = logging.getLogger(__name__)
load_dotenv()

async def get_pool():
    return await asyncpg.create_pool(
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT")),
        min_size=config.DB_MIN_POOL_SIZE,
        max_size=config.DB_MAX_POOL_SIZE
    )

async def init_db(pool):
    async with pool.acquire() as conn:
        await conn.execute(f"""
            CREATE TABLE IF NOT EXISTS {config.DB_TABLE_NAME} (
                id SERIAL PRIMARY KEY,
                message_id BIGINT NOT NULL,
                channel_id BIGINT NOT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                mentioned_user_id BIGINT NOT NULL,
                UNIQUE(message_id, mentioned_user_id)
            )
        """)
        logger.info(f"Table {config.DB_TABLE_NAME} initialized")

async def save_message(pool, message_id, channel_id, mentioned_user_id):
    async with pool.acquire() as conn:
        try:
            return await conn.fetchrow(f"""
                INSERT INTO {config.DB_TABLE_NAME} 
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
            SELECT * FROM {config.DB_TABLE_NAME} 
            WHERE message_id = $1 AND mentioned_user_id = $2
        """, message_id, user_id)
        return row is not None
    
async def delete_message(pool, message_id, user_id):
    async with pool.acquire() as conn:
        try:
            await conn.execute(f"""
                DELETE FROM {config.DB_TABLE_NAME} 
                WHERE message_id = $1 AND mentioned_user_id = $2
            """, message_id, user_id)
        except Exception as e:
            logger.error(f"Failed to delete message {message_id} for user {user_id}: {e}")
            raise

async def has_message_expires(pool, threshold):
    async with pool.acquire() as conn:
        rows = await conn.fetch(f"""
            SELECT * FROM {config.DB_TABLE_NAME} 
            WHERE created_at < NOW() - INTERVAL '{threshold} seconds'
        """)
        return rows
