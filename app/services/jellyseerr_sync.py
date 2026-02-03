import httpx
import logging
from typing import List, Optional
from sqlalchemy.orm import Session

from app.config import settings
from app.database import User, MediaRequest, get_db
from app.schemas import JellyseerrUser, JellyseerrRequest

logger = logging.getLogger(__name__)


class JellyseerrSyncService:
    def __init__(self):
        self.base_url = settings.jellyseerr_url.rstrip('/')
        self.api_key = settings.jellyseerr_api_key
        self.headers = {
            "X-Api-Key": self.api_key,
            "Content-Type": "application/json"
        }
    
    async def _get(self, endpoint: str) -> dict:
        """Make GET request to Jellyseerr API"""
        url = f"{self.base_url}/api/v1{endpoint}"
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
    
    async def get_users(self) -> List[dict]:
        """Fetch all users from Jellyseerr"""
        try:
            data = await self._get("/user")
            return data.get("results", [])
        except Exception as e:
            logger.error(f"Failed to fetch users from Jellyseerr: {e}")
            return []
    
    async def get_requests(self, take: int = 100, skip: int = 0) -> List[dict]:
        """Fetch requests from Jellyseerr"""
        try:
            data = await self._get(f"/request?take={take}&skip={skip}")
            return data.get("results", [])
        except Exception as e:
            logger.error(f"Failed to fetch requests from Jellyseerr: {e}")
            return []
    
    async def sync_users(self):
        """Sync users from Jellyseerr to local database"""
        logger.info("Starting user sync from Jellyseerr...")
        users_data = await self.get_users()
        
        db = next(get_db())
        synced_count = 0
        
        try:
            for user_data in users_data:
                # Skip users without email
                if not user_data.get("email"):
                    continue
                
                jellyseerr_id = user_data.get("id")
                existing_user = db.query(User).filter(User.jellyseerr_id == jellyseerr_id).first()
                
                if existing_user:
                    # Update existing user
                    existing_user.email = user_data.get("email")
                    existing_user.username = user_data.get("username", user_data.get("email"))
                    existing_user.plex_id = user_data.get("plexId")
                else:
                    # Create new user
                    new_user = User(
                        jellyseerr_id=jellyseerr_id,
                        email=user_data.get("email"),
                        username=user_data.get("username", user_data.get("email")),
                        plex_id=user_data.get("plexId")
                    )
                    db.add(new_user)
                
                synced_count += 1
            
            db.commit()
            logger.info(f"Synced {synced_count} users from Jellyseerr")
        except Exception as e:
            db.rollback()
            logger.error(f"Error syncing users: {e}")
        finally:
            db.close()
    
    async def sync_requests(self):
        """Sync media requests from Jellyseerr to local database"""
        logger.info("Starting request sync from Jellyseerr...")
        requests_data = await self.get_requests(take=200)
        
        db = next(get_db())
        synced_count = 0
        
        try:
            for request_data in requests_data:
                jellyseerr_request_id = request_data.get("id")
                existing_request = db.query(MediaRequest).filter(
                    MediaRequest.jellyseerr_request_id == jellyseerr_request_id
                ).first()
                
                # Get user
                requested_by = request_data.get("requestedBy", {})
                user = db.query(User).filter(
                    User.jellyseerr_id == requested_by.get("id")
                ).first()
                
                if not user:
                    logger.warning(f"User not found for request {jellyseerr_request_id}")
                    continue
                
                media = request_data.get("media", {})
                media_type = request_data.get("type", "").lower()
                
                # Map Jellyseerr status codes
                status_code = request_data.get("status", 1)
                status_map = {1: "pending", 2: "approved", 3: "declined", 4: "available"}
                status = status_map.get(status_code, "pending")
                
                if existing_request:
                    # Update existing request
                    existing_request.status = status
                else:
                    # Create new request
                    season_count = None
                    if media_type == "tv" and "seasons" in request_data:
                        season_count = len(request_data["seasons"])
                    
                    new_request = MediaRequest(
                        user_id=user.id,
                        jellyseerr_request_id=jellyseerr_request_id,
                        media_type=media_type,
                        tmdb_id=media.get("tmdbId"),
                        title=media.get("title", "Unknown"),
                        status=status,
                        season_count=season_count
                    )
                    db.add(new_request)
                
                synced_count += 1
            
            db.commit()
            logger.info(f"Synced {synced_count} requests from Jellyseerr")
        except Exception as e:
            db.rollback()
            logger.error(f"Error syncing requests: {e}")
        finally:
            db.close()
