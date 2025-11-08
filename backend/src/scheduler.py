"""
Background job scheduler for periodic task syncing
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from datetime import datetime
from typing import List
from sqlalchemy.orm import Session
from models import DataFetcher, get_db, SessionLocal
from src.integrations import IntegrationManager
from schema import SourceType
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TaskScheduler:
    """Manages background jobs for task syncing"""
    
    def __init__(self):
        self.running = False
        self.sync_interval = 3600  # 1 hour in seconds
    
    async def sync_all_users_tasks(self):
        """Sync tasks for all users with connected integrations"""
        db = SessionLocal()
        try:
            users = DataFetcher.get_users(db)
            logger.info(f"Syncing tasks for {len(users)} users")
            
            for user in users:
                try:
                    # Sync from all sources
                    count = await IntegrationManager.sync_user_tasks(user.id, db)
                    logger.info(f"Synced {count} tasks for user {user.id} ({user.email})")
                except Exception as e:
                    logger.error(f"Error syncing tasks for user {user.id}: {e}")
        finally:
            db.close()
    
    async def sync_user_tasks(self, user_id: int, source_type: SourceType = None):
        """Sync tasks for a specific user"""
        db = SessionLocal()
        try:
            count = await IntegrationManager.sync_user_tasks(user_id, db, source_type)
            logger.info(f"Synced {count} tasks for user {user_id}")
            return count
        finally:
            db.close()
    
    async def run_periodic_sync(self):
        """Run periodic sync in background"""
        self.running = True
        logger.info("Starting periodic task sync scheduler")
        
        while self.running:
            try:
                await self.sync_all_users_tasks()
                await asyncio.sleep(self.sync_interval)
            except Exception as e:
                logger.error(f"Error in periodic sync: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying
    
    def stop(self):
        """Stop the periodic sync"""
        self.running = False
        logger.info("Stopping periodic task sync scheduler")


# Global scheduler instance
scheduler = TaskScheduler()


async def start_background_sync():
    """Start background sync (to be called on app startup)"""
    # Run initial sync
    await scheduler.sync_all_users_tasks()
    # Start periodic sync in background
    asyncio.create_task(scheduler.run_periodic_sync())


def sync_user_tasks_sync(user_id: int, source_type: SourceType = None):
    """Synchronous wrapper for syncing user tasks (for use in endpoints)"""
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(scheduler.sync_user_tasks(user_id, source_type))

