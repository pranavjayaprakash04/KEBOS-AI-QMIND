"""SIEM Integration Service - Modernized async version"""

import asyncio
import httpx
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc, update
from sqlalchemy.orm import selectinload

from common.db import get_async_session
from common.audit_logger import audit_logger
from .models import (
    SIEMConfigORM, SIEMEventORM, SIEMQueryORM, SIEMHealthLogORM, SIEMWebhookORM,
    SIEMConfigCreate, SIEMConfigUpdate, SIEMConfigResponse,
    SIEMEventCreate, SIEMEventResponse,
    SIEMQueryRequest, SIEMQueryResponse,
    SIEMHealthStatus, SIEMWebhookPayload, SIEMStatsResponse,
    SIEMType, SIEMAuthType, SIEMEventSeverity, SIEMConnectionStatus
)

import logging
logger = logging.getLogger(__name__)


class SIEMIntegrationService:
    """Comprehensive SIEM Integration Service with async support"""
    
    def __init__(self):
        self.http_client: Optional[httpx.AsyncClient] = None
        self.health_check_running = False
        self.health_check_task: Optional[asyncio.Task] = None
        
        # Event processors for different SIEM types
        self.event_processors = {
            SIEMType.SPLUNK: self._process_splunk_event,
            SIEMType.QRADAR: self._process_qradar_event,
            SIEMType.ELASTIC_SIEM: self._process_elastic_event,
            SIEMType.AZURE_SENTINEL: self._process_azure_sentinel_event,
            SIEMType.CHRONICLE: self._process_chronicle_event,
        }
    
    async def initialize(self):
        """Initialize the service"""
        if not self.http_client:
            self.http_client = httpx.AsyncClient(timeout=30.0)
        
        # Start health check loop if not running
        if not self.health_check_running:
            self.health_check_running = True
            self.health_check_task = asyncio.create_task(self._health_check_loop())
    
    async def cleanup(self):
        """Cleanup resources"""
        self.health_check_running = False
        
        if self.health_check_task:
            self.health_check_task.cancel()
            try:
                await self.health_check_task
            except asyncio.CancelledError:
                pass
        
        if self.http_client:
            await self.http_client.aclose()
            self.http_client = None
    
    # =============================================================================
    # CONFIGURATION MANAGEMENT
    # =============================================================================
    
    async def create_siem_config(
        self,
        config_data: SIEMConfigCreate,
        user_id: str,
        db: AsyncSession
    ) -> SIEMConfigResponse:
        """Create a new SIEM configuration"""
        
        # Create ORM instance
        db_config = SIEMConfigORM(
            name=config_data.name,
            description=config_data.description,
            siem_type=config_data.siem_type.value,
            base_url=config_data.base_url,
            auth_type=config_data.auth_type.value,
            auth_config=config_data.auth_config,
            is_active=config_data.is_active,
            timeout_seconds=config_data.timeout_seconds,
            max_retries=config_data.max_retries,
            retry_delay_seconds=config_data.retry_delay_seconds,
            query_batch_size=config_data.query_batch_size,
            enable_real_time=config_data.enable_real_time,
            webhook_url=config_data.webhook_url,
            custom_headers=config_data.custom_headers,
            api_version=config_data.api_version,
            enable_ssl_verify=config_data.enable_ssl_verify,
            created_by=user_id
        )
        
        db.add(db_config)
        await db.commit()
        await db.refresh(db_config)
        
        # Log creation
        await audit_logger.log_event(
            "siem_config_created",
            user_id=user_id,
            details={"config_id": str(db_config.id), "name": config_data.name}
        )
        
        # Test connection
        try:
            response = SIEMConfigResponse.from_orm(db_config)
            health_status = await self._perform_health_check(response)
            if health_status["status"] == SIEMConnectionStatus.CONNECTED.value:
                logger.info(f"SIEM configuration {db_config.id} connection verified")
        except Exception as e:
            logger.warning(f"Initial connection test failed: {e}")
        
        return SIEMConfigResponse.from_orm(db_config)
    
    async def get_siem_config(
        self,
        config_id: str,
        db: AsyncSession
    ) -> Optional[SIEMConfigResponse]:
        """Get SIEM configuration by ID"""
        
        result = await db.execute(
            select(SIEMConfigORM).where(SIEMConfigORM.id == config_id)
        )
        config = result.scalar_one_or_none()
        
        if config:
            return SIEMConfigResponse.from_orm(config)
        return None
    
    async def list_siem_configs(
        self,
        db: AsyncSession,
        is_active: Optional[bool] = None,
        siem_type: Optional[SIEMType] = None
    ) -> List[SIEMConfigResponse]:
        """List SIEM configurations with filters"""
        
        query = select(SIEMConfigORM)
        
        filters = []
        if is_active is not None:
            filters.append(SIEMConfigORM.is_active == is_active)
        if siem_type:
            filters.append(SIEMConfigORM.siem_type == siem_type.value)
        
        if filters:
            query = query.where(and_(*filters))
        
        result = await db.execute(query)
        configs = result.scalars().all()
        
        return [SIEMConfigResponse.from_orm(config) for config in configs]
    
    async def update_siem_config(
        self,
        config_id: str,
        config_update: SIEMConfigUpdate,
        user_id: str,
        db: AsyncSession
    ) -> Optional[SIEMConfigResponse]:
        """Update SIEM configuration"""
        
        result = await db.execute(
            select(SIEMConfigORM).where(SIEMConfigORM.id == config_id)
        )
        config = result.scalar_one_or_none()
        
        if not config:
            return None
        
        # Update fields
        update_data = config_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(config, field):
                setattr(config, field, value)
        
        config.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(config)
        
        # Log update
        await audit_logger.log_event(
            "siem_config_updated",
            user_id=user_id,
            details={"config_id": config_id, "updated_fields": list(update_data.keys())}
        )
        
        return SIEMConfigResponse.from_orm(config)
    
    async def delete_siem_config(
        self,
        config_id: str,
        user_id: str,
        db: AsyncSession
    ) -> bool:
        """Delete SIEM configuration"""
        
        result = await db.execute(
            select(SIEMConfigORM).where(SIEMConfigORM.id == config_id)
        )
        config = result.scalar_one_or_none()
        
        if not config:
            return False
        
        await db.delete(config)
        await db.commit()
        
        # Log deletion
        await audit_logger.log_event(
            "siem_config_deleted",
            user_id=user_id,
            details={"config_id": config_id, "name": config.name}
        )
        
        return True
    
    # =============================================================================
    # HEALTH MONITORING
    # =============================================================================
    
    async def check_siem_health(
        self,
        config_id: str,
        db: AsyncSession
    ) -> SIEMHealthStatus:
        """Check health of a SIEM configuration"""
        
        config = await self.get_siem_config(config_id, db)
        if not config:
            return SIEMHealthStatus(
                config_id=config_id,
                status=SIEMConnectionStatus.ERROR,
                auth_success=False,
                api_success=False,
                connectivity={},
                last_check=datetime.utcnow(),
                error="Configuration not found"
            )
        
        # Perform health check
        health_result = await self._perform_health_check(config)
        
        # Create health log entry
        health_log = SIEMHealthLogORM(
            siem_config_id=config_id,
            status=health_result["status"],
            auth_success=health_result.get("auth_success", False),
            api_success=health_result.get("api_success", False),
            connectivity_info=health_result.get("connectivity", {}),
            error_message=health_result.get("error")
        )
        
        db.add(health_log)
        await db.commit()
        
        return SIEMHealthStatus(
            config_id=config_id,
            status=SIEMConnectionStatus(health_result["status"]),
            auth_success=health_result.get("auth_success", False),
            api_success=health_result.get("api_success", False),
            connectivity=health_result.get("connectivity", {}),
            last_check=datetime.utcnow(),
            error=health_result.get("error")
        )
    
    # =============================================================================
    # EVENT INGESTION
    # =============================================================================
    
    async def ingest_event(
        self,
        event_data: SIEMEventCreate,
        db: AsyncSession
    ) -> SIEMEventResponse:
        """Ingest a single SIEM event"""
        
        # Validate SIEM config exists
        config_exists = await db.execute(
            select(SIEMConfigORM).where(SIEMConfigORM.id == event_data.siem_config_id)
        )
        if not config_exists.scalar_one_or_none():
            raise ValueError(f"SIEM config {event_data.siem_config_id} not found")
        
        # Process event based on SIEM type
        config = await self.get_siem_config(event_data.siem_config_id, db)
        processed_event = await self._process_event(event_data, config.siem_type)
        
        # Create ORM instance
        db_event = SIEMEventORM(
            event_id=processed_event.event_id,
            siem_config_id=processed_event.siem_config_id,
            timestamp=processed_event.timestamp,
            event_type=processed_event.event_type,
            severity=processed_event.severity.value,
            category=processed_event.category,
            source_ip=processed_event.source_ip,
            destination_ip=processed_event.destination_ip,
            source_port=processed_event.source_port,
            destination_port=processed_event.destination_port,
            protocol=processed_event.protocol,
            source_hostname=processed_event.source_hostname,
            destination_hostname=processed_event.destination_hostname,
            user=processed_event.user,
            asset=processed_event.asset,
            title=processed_event.title,
            description=processed_event.description,
            signature=processed_event.signature,
            geo_location=processed_event.geo_location,
            threat_intelligence=processed_event.threat_intelligence,
            correlation_id=processed_event.correlation_id,
            parent_event_id=processed_event.parent_event_id,
            raw_data=processed_event.raw_data,
            normalized_data=processed_event.normalized_data,
            processing_notes=processed_event.processing_notes,
            is_processed=processed_event.is_processed,
            processing_status=processed_event.processing_status
        )
        
        db.add(db_event)
        await db.commit()
        await db.refresh(db_event)
        
        return SIEMEventResponse.from_orm(db_event)
    
    async def ingest_events_batch(
        self,
        events: List[SIEMEventCreate],
        db: AsyncSession
    ) -> List[SIEMEventResponse]:
        """Ingest multiple SIEM events in batch"""
        
        processed_events = []
        for event_data in events:
            try:
                processed_event = await self.ingest_event(event_data, db)
                processed_events.append(processed_event)
            except Exception as e:
                logger.error(f"Failed to ingest event {event_data.event_id}: {e}")
                continue
        
        return processed_events
    
    async def get_events(
        self,
        db: AsyncSession,
        siem_config_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        severity: Optional[SIEMEventSeverity] = None,
        event_type: Optional[str] = None,
        source_ip: Optional[str] = None,
        user: Optional[str] = None,
        skip: int = 0,
        limit: int = 1000
    ) -> List[SIEMEventResponse]:
        """Query SIEM events with filters"""
        
        query = select(SIEMEventORM)
        
        # Apply filters
        filters = []
        if siem_config_id:
            filters.append(SIEMEventORM.siem_config_id == siem_config_id)
        if start_time:
            filters.append(SIEMEventORM.timestamp >= start_time)
        if end_time:
            filters.append(SIEMEventORM.timestamp <= end_time)
        if severity:
            filters.append(SIEMEventORM.severity == severity.value)
        if event_type:
            filters.append(SIEMEventORM.event_type == event_type)
        if source_ip:
            filters.append(SIEMEventORM.source_ip == source_ip)
        if user:
            filters.append(SIEMEventORM.user == user)
        
        if filters:
            query = query.where(and_(*filters))
        
        query = query.offset(skip).limit(limit).order_by(desc(SIEMEventORM.timestamp))
        
        result = await db.execute(query)
        events = result.scalars().all()
        
        return [SIEMEventResponse.from_orm(event) for event in events]
    
    # =============================================================================
    # QUERY EXECUTION
    # =============================================================================
    
    async def execute_query(
        self,
        siem_id: str,
        query_request: SIEMQueryRequest,
        user_id: str,
        db: AsyncSession
    ) -> SIEMQueryResponse:
        """Execute a query against a SIEM system"""
        
        # Get SIEM config
        siem_config = await self.get_siem_config(siem_id, db)
        if not siem_config:
            raise ValueError("SIEM config not found")
        
        if not siem_config.is_active:
            raise ValueError("SIEM config is not active")
        
        # Create query record
        query_record = SIEMQueryORM(
            siem_config_id=siem_id,
            query_text=query_request.query_text,
            query_type=query_request.query_type,
            query_parameters=query_request.query_parameters,
            start_time=query_request.start_time,
            end_time=query_request.end_time,
            created_by=user_id,
            status="running"
        )
        
        db.add(query_record)
        await db.commit()
        await db.refresh(query_record)
        
        try:
            # Execute query based on SIEM type
            start_time = datetime.utcnow()
            
            if not self.http_client:
                await self.initialize()
            
            result_data = await self._execute_siem_query(siem_config, query_request)
            
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Update query record
            query_record.status = "completed"
            query_record.execution_time_seconds = execution_time
            query_record.result_count = result_data.get("total_events", 0)
            query_record.completed_at = datetime.utcnow()
            
            await db.commit()
            
            # Create response
            return SIEMQueryResponse(
                query_id=str(query_record.id),
                status="completed",
                total_events=result_data.get("total_events", 0),
                events=result_data.get("events", []),
                execution_time_seconds=execution_time,
                next_page_token=result_data.get("next_page_token")
            )
            
        except Exception as e:
            # Update query record with error
            query_record.status = "failed"
            query_record.error_message = str(e)
            query_record.completed_at = datetime.utcnow()
            
            await db.commit()
            
            logger.error(f"Query execution failed: {e}")
            raise
    
    # =============================================================================
    # WEBHOOK HANDLING
    # =============================================================================
    
    async def process_webhook(
        self,
        webhook_payload: SIEMWebhookPayload,
        db: AsyncSession
    ) -> bool:
        """Process incoming webhook from SIEM system"""
        
        try:
            # Store webhook record
            webhook_record = SIEMWebhookORM(
                siem_source=webhook_payload.siem_source,
                event_type=webhook_payload.event_type,
                payload=webhook_payload.event_data,
                signature=webhook_payload.signature,
                processing_status="processing"
            )
            
            db.add(webhook_record)
            await db.commit()
            await db.refresh(webhook_record)
            
            # Process event data
            for event_data in webhook_payload.event_data.get("events", []):
                try:
                    # Normalize event
                    normalized_event = await self._normalize_event(
                        event_data, 
                        webhook_payload.siem_source
                    )
                    
                    # Create event record
                    event_create = SIEMEventCreate(**normalized_event.dict())
                    await self.ingest_event(event_create, db)
                    
                except Exception as e:
                    logger.error(f"Failed to process webhook event: {e}")
                    continue
            
            # Update webhook status
            webhook_record.processing_status = "completed"
            webhook_record.processed_at = datetime.utcnow()
            await db.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"Webhook processing failed: {e}")
            
            # Update webhook status
            if 'webhook_record' in locals():
                webhook_record.processing_status = "failed"
                webhook_record.error_message = str(e)
                webhook_record.processed_at = datetime.utcnow()
                await db.commit()
            
            return False
    
    # =============================================================================
    # STATISTICS
    # =============================================================================
    
    async def get_stats(
        self,
        db: AsyncSession,
        config_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> SIEMStatsResponse:
        """Get SIEM integration statistics"""
        
        # Default to last 24 hours if no time range provided
        if not start_time:
            start_time = datetime.utcnow() - timedelta(hours=24)
        if not end_time:
            end_time = datetime.utcnow()
        
        # Build base query
        query = select(SIEMEventORM).where(
            SIEMEventORM.timestamp >= start_time,
            SIEMEventORM.timestamp <= end_time
        )
        
        if config_id:
            query = query.where(SIEMEventORM.siem_config_id == config_id)
        
        # Get total events
        result = await db.execute(query)
        events = result.scalars().all()
        
        # Calculate statistics
        total_events = len(events)
        
        severity_counts = {}
        for severity in SIEMEventSeverity:
            severity_events = [e for e in events if e.severity == severity.value]
            severity_counts[severity.value] = len(severity_events)
        
        event_type_counts = {}
        for event in events:
            event_type_counts[event.event_type] = event_type_counts.get(event.event_type, 0) + 1
        
        return SIEMStatsResponse(
            total_events=total_events,
            severity_breakdown=severity_counts,
            event_types=event_type_counts,
            time_range={
                "start": start_time.isoformat(),
                "end": end_time.isoformat()
            }
        )
    
    # =============================================================================
    # PRIVATE HELPER METHODS
    # =============================================================================
    
    async def _decrypt_auth_config(self, encrypted_config: Dict[str, Any]) -> Dict[str, Any]:
        """Decrypt authentication configuration"""
        # TODO: Implement encryption/decryption
        # For now, return as-is (assuming development environment)
        return encrypted_config
    
    async def _health_check_loop(self):
        """Background health check loop"""
        while self.health_check_running:
            try:
                async with get_async_session() as db:
                    # Get all active SIEM configs
                    result = await db.execute(
                        select(SIEMConfigORM).where(SIEMConfigORM.is_active == True)
                    )
                    configs = result.scalars().all()
                    
                    # Check health of each config
                    for config in configs:
                        try:
                            await self.check_siem_health(config.id, db)
                        except Exception as e:
                            logger.error(f"Health check failed for {config.id}: {e}")
                
                # Wait 5 minutes before next check
                await asyncio.sleep(300)
                
            except Exception as e:
                logger.error(f"Health check loop error: {e}")
                await asyncio.sleep(60)  # Wait 1 minute on error
    
    async def _perform_health_check(self, siem_config: SIEMConfigResponse) -> Dict[str, Any]:
        """Perform comprehensive health check"""
        try:
            if not self.http_client:
                await self.initialize()
            
            # Build health check URL based on SIEM type
            if siem_config.siem_type == SIEMType.SPLUNK:
                health_url = f"{siem_config.base_url}/services/server/info"
            elif siem_config.siem_type == SIEMType.QRADAR:
                health_url = f"{siem_config.base_url}/api/system/about"
            elif siem_config.siem_type == SIEMType.ELASTIC_SIEM:
                health_url = f"{siem_config.base_url}/_cluster/health"
            elif siem_config.siem_type == SIEMType.AZURE_SENTINEL:
                health_url = f"{siem_config.base_url}/subscriptions/health"
            else:
                health_url = f"{siem_config.base_url}/api/health"
            
            # Decrypt auth config
            auth_config = await self._decrypt_auth_config(siem_config.auth_config)
            
            # Build auth headers
            headers = await self._build_auth_headers(
                SIEMAuthType(siem_config.auth_type), 
                auth_config
            )
            
            response = await self.http_client.get(
                health_url,
                headers=headers,
                timeout=siem_config.timeout_seconds
            )
            
            if response.status_code == 200:
                return {
                    "status": SIEMConnectionStatus.CONNECTED.value,
                    "auth_success": True,
                    "api_success": True,
                    "connectivity": {"response_code": response.status_code}
                }
            else:
                return {
                    "status": SIEMConnectionStatus.ERROR.value,
                    "error": f"HTTP {response.status_code}",
                    "auth_success": False,
                    "api_success": False
                }
                
        except Exception as e:
            return {
                "status": SIEMConnectionStatus.ERROR.value,
                "error": str(e),
                "auth_success": False,
                "api_success": False
            }
    
    async def _build_auth_headers(self, auth_type: SIEMAuthType, auth_config: Dict[str, Any]) -> Dict[str, str]:
        """Build authentication headers based on auth type"""
        headers = {"Content-Type": "application/json"}
        
        if auth_type == SIEMAuthType.API_KEY:
            api_key = auth_config.get("api_key")
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"
        elif auth_type == SIEMAuthType.BASIC_AUTH:
            username = auth_config.get("username")
            password = auth_config.get("password")
            if username and password:
                import base64
                credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
                headers["Authorization"] = f"Basic {credentials}"
        elif auth_type == SIEMAuthType.BEARER_TOKEN:
            token = auth_config.get("token")
            if token:
                headers["Authorization"] = f"Bearer {token}"
        
        return headers
    
    async def _execute_siem_query(self, siem_config: SIEMConfigResponse, query_request: SIEMQueryRequest) -> Dict[str, Any]:
        """Execute query against SIEM system"""
        try:
            if not self.http_client:
                await self.initialize()
            
            # Build query URL and payload based on SIEM type
            if siem_config.siem_type == SIEMType.SPLUNK:
                return await self._execute_splunk_query(siem_config, query_request)
            elif siem_config.siem_type == SIEMType.QRADAR:
                return await self._execute_qradar_query(siem_config, query_request)
            elif siem_config.siem_type == SIEMType.ELASTIC_SIEM:
                return await self._execute_elastic_query(siem_config, query_request)
            elif siem_config.siem_type == SIEMType.AZURE_SENTINEL:
                return await self._execute_azure_sentinel_query(siem_config, query_request)
            else:
                return await self._execute_generic_query(siem_config, query_request)
                
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise
    
    async def _execute_splunk_query(self, siem_config: SIEMConfigResponse, query_request: SIEMQueryRequest) -> Dict[str, Any]:
        """Execute Splunk search query"""
        search_url = f"{siem_config.base_url}/services/search/jobs"
        
        # Decrypt auth config
        auth_config = await self._decrypt_auth_config(siem_config.auth_config)
        headers = await self._build_auth_headers(SIEMAuthType(siem_config.auth_type), auth_config)
        
        # Create search job
        search_data = {
            "search": query_request.query_text,
            "output_mode": "json"
        }
        
        if query_request.start_time:
            search_data["earliest_time"] = query_request.start_time.isoformat()
        if query_request.end_time:
            search_data["latest_time"] = query_request.end_time.isoformat()
        
        response = await self.http_client.post(search_url, headers=headers, data=search_data)
        response.raise_for_status()
        
        job_data = response.json()
        job_id = job_data.get("sid")
        
        # Wait for job completion and get results
        results_url = f"{siem_config.base_url}/services/search/jobs/{job_id}/results"
        
        # Poll for completion (simplified)
        await asyncio.sleep(2)
        
        results_response = await self.http_client.get(f"{results_url}?output_mode=json", headers=headers)
        results_response.raise_for_status()
        
        results = results_response.json()
        
        return {
            "total_events": len(results.get("results", [])),
            "events": results.get("results", [])
        }
    
    async def _execute_qradar_query(self, siem_config: SIEMConfigResponse, query_request: SIEMQueryRequest) -> Dict[str, Any]:
        """Execute QRadar AQL query"""
        search_url = f"{siem_config.base_url}/api/ariel/searches"
        
        # Decrypt auth config
        auth_config = await self._decrypt_auth_config(siem_config.auth_config)
        headers = await self._build_auth_headers(SIEMAuthType(siem_config.auth_type), auth_config)
        
        query_data = {"query_expression": query_request.query_text}
        
        response = await self.http_client.post(search_url, headers=headers, json=query_data)
        response.raise_for_status()
        
        search_data = response.json()
        search_id = search_data.get("search_id")
        
        # Poll for completion
        status_url = f"{siem_config.base_url}/api/ariel/searches/{search_id}"
        
        for _ in range(30):  # Max 30 polls
            status_response = await self.http_client.get(status_url, headers=headers)
            status_response.raise_for_status()
            
            status_data = status_response.json()
            if status_data.get("status") == "COMPLETED":
                break
            
            await asyncio.sleep(1)
        
        # Get results
        results_url = f"{siem_config.base_url}/api/ariel/searches/{search_id}/results"
        results_response = await self.http_client.get(results_url, headers=headers)
        results_response.raise_for_status()
        
        results = results_response.json()
        
        return {
            "total_events": len(results.get("events", [])),
            "events": results.get("events", [])
        }
    
    async def _execute_elastic_query(self, siem_config: SIEMConfigResponse, query_request: SIEMQueryRequest) -> Dict[str, Any]:
        """Execute Elasticsearch query"""
        search_url = f"{siem_config.base_url}/_search"
        
        # Decrypt auth config
        auth_config = await self._decrypt_auth_config(siem_config.auth_config)
        headers = await self._build_auth_headers(SIEMAuthType(siem_config.auth_type), auth_config)
        
        # Convert query to Elasticsearch format
        query_body = {
            "query": {
                "query_string": {
                    "query": query_request.query_text
                }
            },
            "size": query_request.limit
        }
        
        if query_request.start_time or query_request.end_time:
            time_range = {}
            if query_request.start_time:
                time_range["gte"] = query_request.start_time.isoformat()
            if query_request.end_time:
                time_range["lte"] = query_request.end_time.isoformat()
            
            query_body["query"] = {
                "bool": {
                    "must": [query_body["query"]],
                    "filter": [{"range": {"@timestamp": time_range}}]
                }
            }
        
        response = await self.http_client.post(search_url, headers=headers, json=query_body)
        response.raise_for_status()
        
        results = response.json()
        hits = results.get("hits", {})
        
        return {
            "total_events": hits.get("total", {}).get("value", 0),
            "events": [hit.get("_source", {}) for hit in hits.get("hits", [])]
        }
    
    async def _execute_azure_sentinel_query(self, siem_config: SIEMConfigResponse, query_request: SIEMQueryRequest) -> Dict[str, Any]:
        """Execute Azure Sentinel KQL query"""
        # Simplified implementation
        query_url = f"{siem_config.base_url}/query"
        
        # Decrypt auth config
        auth_config = await self._decrypt_auth_config(siem_config.auth_config)
        headers = await self._build_auth_headers(SIEMAuthType(siem_config.auth_type), auth_config)
        
        query_data = {
            "query": query_request.query_text,
            "timespan": "P1D"  # Last 1 day
        }
        
        response = await self.http_client.post(query_url, headers=headers, json=query_data)
        response.raise_for_status()
        
        results = response.json()
        
        return {
            "total_events": len(results.get("tables", [{}])[0].get("rows", [])),
            "events": results.get("tables", [{}])[0].get("rows", [])
        }
    
    async def _execute_generic_query(self, siem_config: SIEMConfigResponse, query_request: SIEMQueryRequest) -> Dict[str, Any]:
        """Execute generic SIEM query"""
        query_url = f"{siem_config.base_url}/api/query"
        
        # Decrypt auth config
        auth_config = await self._decrypt_auth_config(siem_config.auth_config)
        headers = await self._build_auth_headers(SIEMAuthType(siem_config.auth_type), auth_config)
        
        query_data = {
            "query": query_request.query_text,
            "start_time": query_request.start_time.isoformat() if query_request.start_time else None,
            "end_time": query_request.end_time.isoformat() if query_request.end_time else None,
            "limit": query_request.limit
        }
        
        response = await self.http_client.post(query_url, headers=headers, json=query_data)
        response.raise_for_status()
        
        results = response.json()
        
        return {
            "total_events": results.get("total", 0),
            "events": results.get("events", [])
        }
    
    async def _process_event(self, event_data: SIEMEventCreate, siem_type: str) -> SIEMEventCreate:
        """Process and normalize event based on SIEM type"""
        processor = self.event_processors.get(SIEMType(siem_type), self._process_generic_event)
        return await processor(event_data)
    
    async def _process_splunk_event(self, event_data: SIEMEventCreate) -> SIEMEventCreate:
        """Process Splunk-specific event"""
        # Add Splunk-specific processing logic
        return event_data
    
    async def _process_qradar_event(self, event_data: SIEMEventCreate) -> SIEMEventCreate:
        """Process QRadar-specific event"""
        # Add QRadar-specific processing logic
        return event_data
    
    async def _process_elastic_event(self, event_data: SIEMEventCreate) -> SIEMEventCreate:
        """Process Elasticsearch-specific event"""
        # Add Elasticsearch-specific processing logic
        return event_data
    
    async def _process_azure_sentinel_event(self, event_data: SIEMEventCreate) -> SIEMEventCreate:
        """Process Azure Sentinel-specific event"""
        # Add Azure Sentinel-specific processing logic
        return event_data
    
    async def _process_chronicle_event(self, event_data: SIEMEventCreate) -> SIEMEventCreate:
        """Process Chronicle-specific event"""
        # Add Chronicle-specific processing logic
        return event_data
    
    async def _process_generic_event(self, event_data: SIEMEventCreate) -> SIEMEventCreate:
        """Process generic event"""
        return event_data
    
    async def _normalize_event(self, raw_event: Dict[str, Any], siem_source: str) -> SIEMEventResponse:
        """Normalize raw SIEM event to standard format"""
        # This would be implemented based on each SIEM's event format
        normalized = SIEMEventResponse(
            id=str(uuid.uuid4()),
            event_id=raw_event.get("id", str(uuid.uuid4())),
            siem_config_id="",  # Will be set by caller
            timestamp=datetime.utcnow(),
            event_type=raw_event.get("event_type", "unknown"),
            severity=SIEMEventSeverity.UNKNOWN,
            category=None,
            source_ip=raw_event.get("source_ip"),
            destination_ip=raw_event.get("dest_ip"),
            source_port=raw_event.get("source_port"),
            destination_port=raw_event.get("dest_port"),
            protocol=raw_event.get("protocol"),
            source_hostname=raw_event.get("source_host"),
            destination_hostname=raw_event.get("dest_host"),
            user=raw_event.get("user"),
            asset=raw_event.get("asset"),
            title=raw_event.get("title"),
            description=raw_event.get("description"),
            signature=raw_event.get("signature"),
            geo_location=raw_event.get("geo"),
            threat_intelligence=raw_event.get("threat_intel"),
            correlation_id=raw_event.get("correlation_id"),
            parent_event_id=raw_event.get("parent_id"),
            ingested_at=datetime.utcnow(),
            processed_at=None,
            is_processed=False,
            processing_status="pending"
        )
        
        return normalized


# Create singleton instance
siem_service = SIEMIntegrationService()
