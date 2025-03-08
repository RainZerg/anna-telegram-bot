#!/usr/bin/env python3

import shutil
from datetime import datetime
import os
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def create_backup():
    """Create a backup of the database and media files"""
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    backup_dir = Path('backups')
    data_dir = Path('data')
    media_dir = Path('media')
    
    try:
        # Create backups directory if it doesn't exist
        backup_dir.mkdir(exist_ok=True)
        
        # Backup database
        db_file = data_dir / 'course_bot.db'
        if db_file.exists():
            backup_db = backup_dir / f'course_bot_{timestamp}.db'
            shutil.copy2(db_file, backup_db)
            logger.info(f"Database backed up to {backup_db}")
        else:
            logger.warning("Database file not found, skipping database backup")
        
        # Backup media files
        if media_dir.exists() and any(media_dir.iterdir()):
            backup_media = backup_dir / f'media_{timestamp}.zip'
            shutil.make_archive(
                str(backup_media).replace('.zip', ''),
                'zip',
                media_dir
            )
            logger.info(f"Media files backed up to {backup_media}")
        else:
            logger.warning("No media files found, skipping media backup")

        # Clean up old backups (keep last 5)
        cleanup_old_backups(backup_dir)
        
        logger.info("Backup completed successfully!")
        return True
    
    except Exception as e:
        logger.error(f"Backup failed: {e}")
        return False

def cleanup_old_backups(backup_dir: Path, keep_last: int = 5):
    """Clean up old backups, keeping only the specified number of most recent ones"""
    try:
        # Group files by type
        db_backups = sorted(backup_dir.glob('course_bot_*.db'))
        media_backups = sorted(backup_dir.glob('media_*.zip'))
        
        # Remove old database backups
        if len(db_backups) > keep_last:
            for old_backup in db_backups[:-keep_last]:
                old_backup.unlink()
                logger.info(f"Removed old database backup: {old_backup}")
        
        # Remove old media backups
        if len(media_backups) > keep_last:
            for old_backup in media_backups[:-keep_last]:
                old_backup.unlink()
                logger.info(f"Removed old media backup: {old_backup}")
    
    except Exception as e:
        logger.error(f"Error cleaning up old backups: {e}")

if __name__ == '__main__':
    create_backup()