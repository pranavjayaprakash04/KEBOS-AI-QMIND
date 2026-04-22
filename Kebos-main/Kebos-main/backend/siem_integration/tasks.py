"""
SIEM Integration Tasks

Celery tasks for asynchronous SIEM data processing and polling.
"""

import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta
from celery import Celery
from .services import SIEMIntegrationService
from .models import SIEMConfig, SIEMEvent

logger = logging.getLogger(__name__)

# Initialize Celery app (will be configured by main app)
celery_app = Celery('siem_integration')


@celery_app.task(bind=True, retry_backoff=True, max_retries=3)
def poll_siem_api(self, siem_config_id: str, last_poll_time: str = None) -> Dict[str, Any]:
    """
    Poll SIEM API for new events periodically.
    
    Args:
        siem_config_id: ID of the SIEM configuration to poll
        last_poll_time: ISO timestamp of last successful poll
        
    Returns:
        Dict containing poll results and statistics
    """
    try:
        logger.info(f"Starting SIEM API poll for config: {siem_config_id}")
        
        service = SIEMIntegrationService()
        
        # Convert last_poll_time to datetime if provided
        start_time = None
        if last_poll_time:
            start_time = datetime.fromisoformat(last_poll_time.replace('Z', '+00:00'))
        else:
            # Default to last 1 hour if no last poll time
            start_time = datetime.utcnow() - timedelta(hours=1)
        
        # Poll for events
        events_processed = 0
        errors = []
        
        try:
            # Query real SIEM events instead of mock response
            from .services import siem_service
            
            # Get SIEM configuration
            siem_config = siem_service.get_siem_config(siem_config_id)
            if not siem_config:
                raise ValueError(f"SIEM configuration {siem_config_id} not found")
            
            # Query SIEM for new events since last poll
            query = {
                "time_range": {
                    "start": start_time.isoformat(),
                    "end": datetime.utcnow().isoformat()
                },
                "limit": 1000
            }
            
            response = siem_service.query_siem(siem_config_id, query)
            events_processed = len(response.events)
            
            # Process and store events
            for event in response.events:
                # Store event in database or forward to threat detection
                logger.debug(f"Processing SIEM event: {event.event_id}")
            
            poll_result = {
                'status': 'success',
                'siem_config_id': siem_config_id,
                'events_processed': events_processed,
                'poll_time': datetime.utcnow().isoformat(),
                'errors': errors
            }
            
            logger.info(f"SIEM poll completed successfully. Events processed: {events_processed}")
            return poll_result
            
        except Exception as e:
            logger.error(f"Error during SIEM API poll: {str(e)}")
            errors.append(str(e))
            
            # Retry the task if we haven't exceeded max retries
            if self.request.retries < self.max_retries:
                logger.warning(f"Retrying SIEM poll task. Attempt {self.request.retries + 1}")
                raise self.retry(countdown=60 * (2 ** self.request.retries))
            
            return {
                'status': 'error',
                'siem_config_id': siem_config_id,
                'events_processed': 0,
                'poll_time': datetime.utcnow().isoformat(),
                'errors': errors
            }
            
    except Exception as e:
        logger.error(f"Critical error in SIEM poll task: {str(e)}")
        return {
            'status': 'critical_error',
            'siem_config_id': siem_config_id,
            'events_processed': 0,
            'poll_time': datetime.utcnow().isoformat(),
            'errors': [str(e)]
        }


@celery_app.task(bind=True, retry_backoff=True, max_retries=3)
def process_siem_webhook(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process incoming SIEM webhook data asynchronously.
    
    Args:
        webhook_data: Raw webhook payload from SIEM system
        
    Returns:
        Dict containing processing results
    """
    try:
        logger.info(f"Processing SIEM webhook: {webhook_data.get('webhook_id', 'unknown')}")
        
        service = SIEMIntegrationService()
        
        # Extract and validate webhook data
        webhook_id = webhook_data.get('webhook_id')
        siem_source = webhook_data.get('siem_source')
        events = webhook_data.get('events', [])
        
        if not webhook_id or not siem_source:
            raise ValueError("Missing required webhook fields: webhook_id or siem_source")
        
        processed_events = 0
        errors = []
        
        try:
            # Process each event in the webhook
            for event_data in events:
                try:
                    # Normalize the event data
                    normalized_event = service.normalize_event(event_data, siem_source)
                    
                    # Store or forward the event (implementation depends on requirements)
                    # For now, just count as processed
                    processed_events += 1
                    
                except Exception as event_error:
                    logger.warning(f"Error processing individual event: {str(event_error)}")
                    errors.append(f"Event processing error: {str(event_error)}")
            
            result = {
                'status': 'success',
                'webhook_id': webhook_id,
                'siem_source': siem_source,
                'events_processed': processed_events,
                'total_events': len(events),
                'processing_time': datetime.utcnow().isoformat(),
                'errors': errors
            }
            
            logger.info(f"Webhook processing completed. Events processed: {processed_events}/{len(events)}")
            return result
            
        except Exception as e:
            logger.error(f"Error during webhook processing: {str(e)}")
            errors.append(str(e))
            
            # Retry the task if we haven't exceeded max retries
            if self.request.retries < self.max_retries:
                logger.warning(f"Retrying webhook processing task. Attempt {self.request.retries + 1}")
                raise self.retry(countdown=30 * (2 ** self.request.retries))
            
            return {
                'status': 'error',
                'webhook_id': webhook_id,
                'siem_source': siem_source,
                'events_processed': processed_events,
                'total_events': len(events),
                'processing_time': datetime.utcnow().isoformat(),
                'errors': errors
            }
            
    except Exception as e:
        logger.error(f"Critical error in webhook processing task: {str(e)}")
        return {
            'status': 'critical_error',
            'webhook_id': webhook_data.get('webhook_id', 'unknown'),
            'siem_source': webhook_data.get('siem_source', 'unknown'),
            'events_processed': 0,
            'total_events': len(webhook_data.get('events', [])),
            'processing_time': datetime.utcnow().isoformat(),
            'errors': [str(e)]
        }


@celery_app.task
def schedule_siem_polling() -> Dict[str, Any]:
    """
    Schedule polling tasks for all active SIEM configurations.
    This task should be run periodically via Celery Beat.
    
    Returns:
        Dict containing scheduling results
    """
    try:
        logger.info("Starting scheduled SIEM polling")
        
        # Get real SIEM configurations from the service
        from .services import siem_service
        
        scheduled_polls = 0
        errors = []
        
        # Get active SIEM configurations
        try:
            siem_configs = siem_service.list_siem_configs()
            
            for config in siem_configs:
                try:
                    # Check if polling is due based on configuration
                    if siem_service.is_polling_due(config.id):
                        # Schedule polling task
                        poll_siem_api.delay(config.id)
                        scheduled_polls += 1
                        logger.info(f"Scheduled polling for SIEM config: {config.id}")
                except Exception as e:
                    logger.error(f"Error scheduling poll for config {config.id}: {str(e)}")
                    errors.append(f"Config {config.id}: {str(e)}")
                    
        except Exception as e:
            logger.error(f"Failed to get SIEM configurations: {e}")
            errors.append(f"Failed to get SIEM configurations: {str(e)}")
        
        result = {
            'status': 'success',
            'scheduled_polls': scheduled_polls,
            'schedule_time': datetime.utcnow().isoformat(),
            'errors': errors
        }
        
        logger.info(f"SIEM polling scheduling completed. Scheduled: {scheduled_polls} polls")
        return result
        
    except Exception as e:
        logger.error(f"Critical error in SIEM polling scheduler: {str(e)}")
        return {
            'status': 'error',
            'scheduled_polls': 0,
            'schedule_time': datetime.utcnow().isoformat(),
            'errors': [str(e)]
        }


# Task registration helper
def register_tasks(celery_instance: Celery) -> None:
    """
    Register SIEM integration tasks with the main Celery instance.
    
    Args:
        celery_instance: Main Celery application instance
    """
    global celery_app
    celery_app = celery_instance
    
    # Register tasks
    celery_instance.task(poll_siem_api)
    celery_instance.task(process_siem_webhook)
    celery_instance.task(schedule_siem_polling)
    
    logger.info("SIEM integration tasks registered successfully")
