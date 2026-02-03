from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
import logging

from app.database import get_db, User, MediaRequest, EpisodeTracking, Notification
from app.services.jellyseerr_sync import JellyseerrSyncService
from app.services.email_service import EmailService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/sync/users")
async def sync_users():
    """Manually trigger user sync from Jellyseerr"""
    try:
        sync_service = JellyseerrSyncService()
        await sync_service.sync_users()
        return {"success": True, "message": "User sync completed"}
    except Exception as e:
        logger.error(f"User sync failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync/requests")
async def sync_requests():
    """Manually trigger request sync from Jellyseerr"""
    try:
        sync_service = JellyseerrSyncService()
        await sync_service.sync_requests()
        return {"success": True, "message": "Request sync completed"}
    except Exception as e:
        logger.error(f"Request sync failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/notifications/process")
async def process_notifications(db: Session = Depends(get_db)):
    """Manually trigger processing of pending notifications"""
    try:
        email_service = EmailService()
        await email_service.process_pending_notifications(db)
        return {"success": True, "message": "Notifications processed"}
    except Exception as e:
        logger.error(f"Notification processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_stats(db: Session = Depends(get_db)):
    """Get system statistics"""
    try:
        stats = {
            "users": db.query(func.count(User.id)).scalar(),
            "requests": {
                "total": db.query(func.count(MediaRequest.id)).scalar(),
                "movies": db.query(func.count(MediaRequest.id)).filter(MediaRequest.media_type == "movie").scalar(),
                "tv_shows": db.query(func.count(MediaRequest.id)).filter(MediaRequest.media_type == "tv").scalar(),
            },
            "episodes_tracked": db.query(func.count(EpisodeTracking.id)).scalar(),
            "notifications": {
                "total": db.query(func.count(Notification.id)).scalar(),
                "sent": db.query(func.count(Notification.id)).filter(Notification.sent == True).scalar(),
                "pending": db.query(func.count(Notification.id)).filter(Notification.sent == False).scalar(),
            }
        }
        return stats
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/users")
async def list_users(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    """List all users"""
    users = db.query(User).offset(skip).limit(limit).all()
    return {
        "users": [
            {
                "id": u.id,
                "jellyseerr_id": u.jellyseerr_id,
                "email": u.email,
                "username": u.username,
                "created_at": u.created_at
            }
            for u in users
        ]
    }


@router.get("/requests")
async def list_requests(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    """List all media requests"""
    requests = db.query(MediaRequest).offset(skip).limit(limit).all()
    return {
        "requests": [
            {
                "id": r.id,
                "user_email": r.user.email,
                "media_type": r.media_type,
                "title": r.title,
                "status": r.status,
                "created_at": r.created_at
            }
            for r in requests
        ]
    }


@router.get("/notifications")
async def list_notifications(
    skip: int = 0,
    limit: int = 50,
    sent: bool = None,
    db: Session = Depends(get_db)
):
    """List notifications"""
    query = db.query(Notification)
    
    if sent is not None:
        query = query.filter(Notification.sent == sent)
    
    notifications = query.offset(skip).limit(limit).all()
    
    return {
        "notifications": [
            {
                "id": n.id,
                "user_email": n.user.email,
                "type": n.notification_type,
                "subject": n.subject,
                "sent": n.sent,
                "sent_at": n.sent_at,
                "created_at": n.created_at
            }
            for n in notifications
        ]
    }
