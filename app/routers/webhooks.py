from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
import logging
from datetime import datetime
from typing import List

from app.database import get_db, MediaRequest, EpisodeTracking, Notification
from app.schemas import SonarrWebhook, RadarrWebhook, WebhookResponse
from app.services.email_service import EmailService
from app.services.sonarr_service import SonarrService

logger = logging.getLogger(__name__)
router = APIRouter()
email_service = EmailService()


@router.post("/sonarr", response_model=WebhookResponse)
async def sonarr_webhook(
    webhook: SonarrWebhook,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Handle webhooks from Sonarr
    Supported events: Download, Test
    """
    logger.info(f"Received Sonarr webhook: {webhook.eventType}")
    
    if webhook.eventType == "Test":
        return WebhookResponse(success=True, message="Sonarr webhook test successful")
    
    if webhook.eventType != "Download":
        return WebhookResponse(success=False, message=f"Unsupported event type: {webhook.eventType}")
    
    try:
        # Get series TMDB ID
        tmdb_id = webhook.series.tmdbId
        if not tmdb_id:
            logger.warning(f"Series {webhook.series.title} has no TMDB ID")
            return WebhookResponse(success=False, message="Series has no TMDB ID")
        
        # Find all requests for this series
        requests = db.query(MediaRequest).filter(
            MediaRequest.media_type == "tv",
            MediaRequest.tmdb_id == tmdb_id
        ).all()
        
        if not requests:
            logger.info(f"No requests found for series TMDB ID {tmdb_id}")
            return WebhookResponse(success=True, message="No matching requests found")
        
        # Process each episode
        notifications_created = 0
        for episode in webhook.episodes or []:
            for request in requests:
                # Track this episode
                episode_tracking = db.query(EpisodeTracking).filter(
                    EpisodeTracking.series_id == webhook.series.id,
                    EpisodeTracking.season_number == episode.seasonNumber,
                    EpisodeTracking.episode_number == episode.episodeNumber
                ).first()
                
                if not episode_tracking:
                    # Create new episode tracking
                    episode_tracking = EpisodeTracking(
                        request_id=request.id,
                        series_id=webhook.series.id,
                        season_number=episode.seasonNumber,
                        episode_number=episode.episodeNumber,
                        episode_title=episode.title,
                        air_date=datetime.fromisoformat(episode.airDateUtc.replace('Z', '+00:00')) if episode.airDateUtc else None,
                        notified=False,
                        available_in_plex=True
                    )
                    db.add(episode_tracking)
                else:
                    # Update existing tracking
                    episode_tracking.available_in_plex = True
                    episode_tracking.episode_title = episode.title
                
                # Create notification if not already notified
                if not episode_tracking.notified:
                    # Check if notification already exists
                    existing_notification = db.query(Notification).filter(
                        Notification.user_id == request.user_id,
                        Notification.request_id == request.id,
                        Notification.notification_type == "episode",
                        Notification.subject.contains(f"S{episode.seasonNumber:02d}E{episode.episodeNumber:02d}")
                    ).first()
                    
                    if not existing_notification:
                        # Get poster URL
                        from app.services.tmdb_service import TMDBService
                        from app.config import settings
                        tmdb_service = TMDBService(settings.jellyseerr_url, settings.jellyseerr_api_key)
                        poster_url = await tmdb_service.get_tv_poster(request.tmdb_id)
                        
                        # Render email
                        html_body = email_service.render_episode_notification(
                            series_title=webhook.series.title,
                            episodes=[{
                                'season': episode.seasonNumber,
                                'episode': episode.episodeNumber,
                                'title': episode.title,
                                'air_date': episode.airDate
                            }],
                            poster_url=poster_url
                        )
                        
                        notification = Notification(
                            user_id=request.user_id,
                            request_id=request.id,
                            notification_type="episode",
                            subject=f"New Episode: {webhook.series.title} S{episode.seasonNumber:02d}E{episode.episodeNumber:02d}",
                            body=html_body
                        )
                        db.add(notification)
                        notifications_created += 1
                        episode_tracking.notified = True
        
        db.commit()
        
        # Send pending notifications in background
        background_tasks.add_task(email_service.process_pending_notifications, db)
        
        return WebhookResponse(
            success=True,
            message=f"Processed {len(webhook.episodes or [])} episodes",
            processed_items=notifications_created
        )
        
    except Exception as e:
        logger.error(f"Error processing Sonarr webhook: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/radarr", response_model=WebhookResponse)
async def radarr_webhook(
    webhook: RadarrWebhook,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Handle webhooks from Radarr
    Supported events: Download, Test
    """
    logger.info(f"Received Radarr webhook: {webhook.eventType}")
    
    if webhook.eventType == "Test":
        return WebhookResponse(success=True, message="Radarr webhook test successful")
    
    if webhook.eventType != "Download":
        return WebhookResponse(success=False, message=f"Unsupported event type: {webhook.eventType}")
    
    try:
        tmdb_id = webhook.movie.tmdbId
        
        # Find all requests for this movie
        requests = db.query(MediaRequest).filter(
            MediaRequest.media_type == "movie",
            MediaRequest.tmdb_id == tmdb_id
        ).all()
        
        if not requests:
            logger.info(f"No requests found for movie TMDB ID {tmdb_id}")
            return WebhookResponse(success=True, message="No matching requests found")
        
        notifications_created = 0
        for request in requests:
            # Check if already notified
            existing_notification = db.query(Notification).filter(
                Notification.user_id == request.user_id,
                Notification.request_id == request.id,
                Notification.notification_type == "movie"
            ).first()
            
            if not existing_notification:
                # Get poster URL
                from app.services.tmdb_service import TMDBService
                from app.config import settings
                tmdb_service = TMDBService(settings.jellyseerr_url, settings.jellyseerr_api_key)
                poster_url = await tmdb_service.get_movie_poster(tmdb_id)
                
                # Render email
                html_body = email_service.render_movie_notification(
                    movie_title=webhook.movie.title,
                    poster_url=poster_url
                )
                
                notification = Notification(
                    user_id=request.user_id,
                    request_id=request.id,
                    notification_type="movie",
                    subject=f"Movie Available: {webhook.movie.title}",
                    body=html_body
                )
                db.add(notification)
                notifications_created += 1
                
                # Update request status
                request.status = "available"
        
        db.commit()
        
        # Send pending notifications in background
        background_tasks.add_task(email_service.process_pending_notifications, db)
        
        return WebhookResponse(
            success=True,
            message=f"Processed movie: {webhook.movie.title}",
            processed_items=notifications_created
        )
        
    except Exception as e:
        logger.error(f"Error processing Radarr webhook: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
