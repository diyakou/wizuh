from datetime import datetime, timedelta
import asyncio
import logging
from typing import Optional
from database.models import XUIConfig, XUIServer
from database.db import session
from api.xui import XUIClient
from sqlalchemy import text, select

logger = logging.getLogger(__name__)

def get_server_credentials(server: XUIServer) -> tuple[str, Optional[str], Optional[str], Optional[str]]:
    """Get server credentials from SQLAlchemy model."""
    url = session.scalar(select(server.url))
    username = session.scalar(select(server.username))
    password = session.scalar(select(server.password))
    token = session.scalar(select(server.token))
    
    if not url:
        raise ValueError("Server URL cannot be None")
    
    return url, username, password, token

def get_config_details(config: XUIConfig) -> tuple[str, int, int]:
    """Get config details from SQLAlchemy model."""
    uuid = session.scalar(select(config.uuid))
    inbound_id = session.scalar(select(config.inbound_id))
    total_gb = session.scalar(select(config.total_gb))
    
    if not uuid or not inbound_id or not total_gb:
        raise ValueError("Config details cannot be None")
    
    return uuid, inbound_id, total_gb

async def cleanup_expired_configs():
    """Cleanup expired configs and notify users."""
    try:
        # Get expired configs
        expired_configs = XUIConfig.get_expired_configs()
        
        for config in expired_configs:
            try:
                # Get server
                server = session.get(XUIServer, config.server_id.scalar())
                if not server:
                    logger.error(f"Server not found for config {config.id}")
                    continue
                
                try:
                    # Get server credentials
                    url, username, password, token = get_server_credentials(server)
                    
                    # Create X-UI client
                    client = XUIClient(
                        url=url,
                        username=username,
                        password=password,
                        token=token
                    )
                    
                    # Get config details
                    uuid, inbound_id, _ = get_config_details(config)
                    
                    # Delete config from X-UI panel
                    if client.delete_config(uuid, inbound_id):
                        # Delete config from database
                        session.delete(config)
                        session.commit()
                        
                        logger.info(f"Deleted expired config {config.id} for user {config.user_id}")
                    else:
                        logger.error(f"Failed to delete config {config.id} from X-UI panel")
                    
                except ValueError as e:
                    logger.error(f"Invalid server/config data: {e}")
                    continue
                
            except Exception as e:
                logger.error(f"Error cleaning up config {config.id}: {e}")
                continue
        
    except Exception as e:
        logger.error(f"Error in cleanup task: {e}")

async def sync_server_configs():
    """Synchronize configs with X-UI panels."""
    try:
        # Get all active servers
        servers = XUIServer.get_active_servers()
        
        for server in servers:
            try:
                try:
                    # Get server credentials
                    url, username, password, token = get_server_credentials(server)
                    
                    # Create X-UI client
                    client = XUIClient(
                        url=url,
                        username=username,
                        password=password,
                        token=token
                    )
                    
                    # Check connection
                    if not client.check_connection():
                        logger.error(f"Failed to connect to server {server.id}")
                        continue
                    
                    # Get configs from database
                    configs = session.query(XUIConfig).filter(
                        XUIConfig.server_id == server.id,
                        XUIConfig.expiry_time > datetime.now()
                    ).all()
                    
                    for config in configs:
                        try:
                            # Get config details
                            uuid, inbound_id, total_gb = get_config_details(config)
                            
                            # Update config in X-UI panel
                            remaining_days = (config.expiry_time - datetime.now()).days
                            if remaining_days > 0:
                                client.update_config(
                                    uuid=uuid,
                                    inbound_id=inbound_id,
                                    total_gb=total_gb,
                                    expiry_days=remaining_days
                                )
                                logger.info(f"Synced config {config.id} for user {config.user_id}")
                            
                        except ValueError as e:
                            logger.error(f"Invalid config data: {e}")
                            continue
                        except Exception as e:
                            logger.error(f"Error syncing config {config.id}: {e}")
                            continue
                    
                except ValueError as e:
                    logger.error(f"Invalid server data: {e}")
                    continue
                
            except Exception as e:
                logger.error(f"Error syncing server {server.id}: {e}")
                continue
        
    except Exception as e:
        logger.error(f"Error in sync task: {e}")

async def notify_expiring_configs():
    """Notify users about configs expiring soon."""
    try:
        # Get configs expiring in the next 24 hours
        expiring_soon = session.query(XUIConfig).filter(
            XUIConfig.expiry_time > datetime.now(),
            XUIConfig.expiry_time <= datetime.now() + timedelta(days=1)
        ).all()
        
        for config in expiring_soon:
            try:
                # Calculate remaining time
                remaining = config.expiry_time - datetime.now()
                hours = int(remaining.total_seconds() / 3600)
                
                # Format message
                message = (
                    f"⚠️ اخطار انقضای سرویس\n\n"
                    f"کاربر گرامی، سرویس شما تا {hours} ساعت دیگر منقضی خواهد شد.\n"
                    f"لطفاً نسبت به تمدید سرویس خود اقدام نمایید."
                )
                
                # TODO: Send notification to user (implement in bot.py)
                # await bot.send_message(config.user.telegram_id, message)
                
                logger.info(f"Sent expiry notification for config {config.id} to user {config.user_id}")
                
            except Exception as e:
                logger.error(f"Error notifying user about config {config.id}: {e}")
                continue
        
    except Exception as e:
        logger.error(f"Error in notification task: {e}")

async def cleanup_task(interval: int = 3600):
    """Background task for cleanup and synchronization."""
    while True:
        try:
            # Run cleanup
            await cleanup_expired_configs()
            
            # Run sync
            await sync_server_configs()
            
            # Send notifications
            await notify_expiring_configs()
            
        except Exception as e:
            logger.error(f"Error in cleanup task: {e}")
        
        # Wait for next iteration
        await asyncio.sleep(interval) 