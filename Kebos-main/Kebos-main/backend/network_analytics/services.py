"""Network Analytics Services - Modernized with async database operations"""

import asyncio
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, desc, func, text
from sqlalchemy.orm import selectinload
import uuid
import logging

from common.db import get_db
from common.audit_logger import audit_logger
from network_analytics.models import (
    # ORM Models
    NetworkFlowORM, TrafficPatternORM, NetworkAnomalyORM, 
    AnalyticsJobORM, NetworkTopologyORM,
    
    # Pydantic Models
    AnalyticsQueryCreate, AnalyticsResult, TimeSeriesDataPoint,
    CategoryDataPoint, NetworkNode, NetworkEdge, NetworkGraph, GeoPoint,
    TrafficPatternResponse, NetworkAnomalyResponse, NetworkFlowResponse,
    NetworkTopologyResponse, AnalyticsJobResponse, NetworkStatsResponse,
    
    # Enums
    TimeRange, VisualizationType, MetricType, TrafficDirection,
    ProtocolType, TrafficPatternType, AnomalyType, AnalysisStatus
)

logger = logging.getLogger(__name__)


class NetworkAnalyticsService:
    """Comprehensive network analytics service with async database operations"""
    
    def __init__(self):
        self.initialized = False
        
    def initialize(self):
        """Initialize the analytics service"""
        if not self.initialized:
            logger.info("Initializing Network Analytics Service")
            self.initialized = True
    
    def cleanup(self):
        """Cleanup resources"""
        logger.info("Cleaning up Network Analytics Service")
        self.initialized = False
    
    # =============================================================================
    # ANALYTICS QUERY PROCESSING
    # =============================================================================
    
    def query_analytics(
        self,
        query: AnalyticsQueryCreate,
        user_id: str,
        db: Session
    ) -> AnalyticsResult:
        """Process analytics query and generate visualizations"""
        start_time = datetime.utcnow()
        query_id = str(uuid.uuid4())
        
        try:
            # Create analytics job record
            job = AnalyticsJobORM(
                job_id=query_id,
                job_type="analytics_query",
                job_name=query.query_name or f"Analytics Query {query_id[:8]}",
                query_parameters=query.dict(),
                status=AnalysisStatus.PROCESSING.value,
                created_by=user_id
            )
            db.add(job)
            db.commit()
            
            # Resolve time range
            start_time_range, end_time_range = self._resolve_time_range(query)
            
            # Execute query based on visualization type
            result_data = self._execute_analytics_query(
                query, start_time_range, end_time_range, db
            )
            
            # Calculate processing time
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            # Update job status
            job.status = AnalysisStatus.COMPLETED.value
            job.completed_at = datetime.utcnow()
            job.processing_time_seconds = processing_time / 1000
            job.result_summary = {
                "data_points": result_data.get("data_points_count", 0),
                "visualization_type": query.visualization_type.value
            }
            db.commit()
            
            # Log analytics query
            audit_logger.log_event(
                "network_analytics_query",
                user_id=user_id,
                details={
                    "query_id": query_id,
                    "visualization_type": query.visualization_type.value,
                    "metrics": [m.value for m in query.metrics],
                    "processing_time_ms": processing_time
                }
            )
            
            return AnalyticsResult(
                query_id=query_id,
                query_name=query.query_name,
                visualization_type=query.visualization_type,
                **result_data,
                processing_time_ms=processing_time,
                data_time_range={
                    "start": start_time_range,
                    "end": end_time_range
                }
            )
            
        except Exception as e:
            # Update job with error
            if 'job' in locals():
                job.status = AnalysisStatus.FAILED.value
                job.error_message = str(e)
                job.completed_at = datetime.utcnow()
                db.commit()
            
            logger.error(f"Error processing analytics query: {e}")
            raise
    
    def _execute_analytics_query(
        self,
        query: AnalyticsQueryCreate,
        start_time: datetime,
        end_time: datetime,
        db: Session
    ) -> Dict[str, Any]:
        """Execute the actual analytics query based on visualization type"""
        
        if query.visualization_type == VisualizationType.TIME_SERIES:
            return self._generate_time_series(query, start_time, end_time, db)
        elif query.visualization_type in [VisualizationType.BAR_CHART, VisualizationType.PIE_CHART]:
            return self._generate_category_chart(query, start_time, end_time, db)
        elif query.visualization_type == VisualizationType.NETWORK_GRAPH:
            return self._generate_network_graph(query, start_time, end_time, db)
        elif query.visualization_type == VisualizationType.GEO_MAP:
            return self._generate_geo_map(query, start_time, end_time, db)
        elif query.visualization_type == VisualizationType.HEATMAP:
            return self._generate_heatmap(query, start_time, end_time, db)
        else:
            return self._generate_raw_data(query, start_time, end_time, db)
    
    def _resolve_time_range(self, query: AnalyticsQueryCreate) -> Tuple[datetime, datetime]:
        """Resolve time range from query parameters"""
        end_time = datetime.utcnow()
        
        if query.time_range == TimeRange.CUSTOM and query.start_time and query.end_time:
            return query.start_time, query.end_time
        
        time_deltas = {
            TimeRange.LAST_HOUR: timedelta(hours=1),
            TimeRange.LAST_DAY: timedelta(days=1),
            TimeRange.LAST_WEEK: timedelta(weeks=1),
            TimeRange.LAST_MONTH: timedelta(days=30),
            TimeRange.LAST_3_MONTHS: timedelta(days=90),
            TimeRange.LAST_YEAR: timedelta(days=365)
        }
        
        delta = time_deltas.get(query.time_range, timedelta(days=1))
        start_time = end_time - delta
        
        return start_time, end_time
    
    def _generate_time_series(
        self,
        query: AnalyticsQueryCreate,
        start_time: datetime,
        end_time: datetime,
        db: Session
    ) -> Dict[str, Any]:
        """Generate time series visualization data"""
        
        # Calculate time bucket size based on time range
        time_diff = end_time - start_time
        if time_diff <= timedelta(hours=1):
            bucket_size = "1 minute"
            time_format = "YYYY-MM-DD HH24:MI"
        elif time_diff <= timedelta(days=1):
            bucket_size = "5 minutes"
            time_format = "YYYY-MM-DD HH24:MI"
        elif time_diff <= timedelta(days=7):
            bucket_size = "1 hour"
            time_format = "YYYY-MM-DD HH24"
        else:
            bucket_size = "1 day"
            time_format = "YYYY-MM-DD"
        
        time_series_data = []
        summary_metrics = {}
        
        for metric in query.metrics:
            if metric == MetricType.PACKET_COUNT:
                # Query packet count over time
                query_sql = text(f"""
                    SELECT 
                        time_bucket('{bucket_size}', first_seen) AS time_bucket,
                        SUM(packet_count) AS total_packets
                    FROM network_flows 
                    WHERE first_seen >= :start_time AND first_seen <= :end_time
                    GROUP BY time_bucket
                    ORDER BY time_bucket
                """)
                
                result = db.execute(query_sql, {
                    "start_time": start_time,
                    "end_time": end_time
                })
                
                for row in result:
                    time_series_data.append(TimeSeriesDataPoint(
                        timestamp=row.time_bucket,
                        value=float(row.total_packets),
                        metric_type=metric.value,
                        label="Packet Count"
                    ))
                
                # Calculate summary
                total_packets = sum(point.value for point in time_series_data if point.metric_type == metric.value)
                summary_metrics[metric.value] = {
                    "total": total_packets,
                    "average": total_packets / max(len([p for p in time_series_data if p.metric_type == metric.value]), 1)
                }
            
            elif metric == MetricType.BYTE_COUNT:
                # Query byte count over time
                query_sql = text(f"""
                    SELECT 
                        time_bucket('{bucket_size}', first_seen) AS time_bucket,
                        SUM(byte_count) AS total_bytes
                    FROM network_flows 
                    WHERE first_seen >= :start_time AND first_seen <= :end_time
                    GROUP BY time_bucket
                    ORDER BY time_bucket
                """)
                
                result = db.execute(query_sql, {
                    "start_time": start_time,
                    "end_time": end_time
                })
                
                for row in result:
                    time_series_data.append(TimeSeriesDataPoint(
                        timestamp=row.time_bucket,
                        value=float(row.total_bytes),
                        metric_type=metric.value,
                        label="Byte Count"
                    ))
            
            elif metric == MetricType.UNIQUE_IPS:
                # Query unique IPs over time
                query_sql = text(f"""
                    SELECT 
                        time_bucket('{bucket_size}', first_seen) AS time_bucket,
                        COUNT(DISTINCT source_ip) + COUNT(DISTINCT destination_ip) AS unique_ips
                    FROM network_flows 
                    WHERE first_seen >= :start_time AND first_seen <= :end_time
                    GROUP BY time_bucket
                    ORDER BY time_bucket
                """)
                
                result = db.execute(query_sql, {
                    "start_time": start_time,
                    "end_time": end_time
                })
                
                for row in result:
                    time_series_data.append(TimeSeriesDataPoint(
                        timestamp=row.time_bucket,
                        value=float(row.unique_ips),
                        metric_type=metric.value,
                        label="Unique IPs"
                    ))
            
            elif metric == MetricType.ANOMALY_SCORE:
                # Query anomaly scores over time
                query_sql = text(f"""
                    SELECT 
                        time_bucket('{bucket_size}', first_seen) AS time_bucket,
                        AVG(anomaly_score) AS avg_anomaly_score
                    FROM network_flows 
                    WHERE first_seen >= :start_time AND first_seen <= :end_time
                    GROUP BY time_bucket
                    ORDER BY time_bucket
                """)
                
                result = db.execute(query_sql, {
                    "start_time": start_time,
                    "end_time": end_time
                })
                
                for row in result:
                    time_series_data.append(TimeSeriesDataPoint(
                        timestamp=row.time_bucket,
                        value=float(row.avg_anomaly_score or 0),
                        metric_type=metric.value,
                        label="Anomaly Score"
                    ))
        
        return {
            "time_series_data": time_series_data,
            "summary_metrics": summary_metrics,
            "data_points_count": len(time_series_data)
        }
    
    def _generate_category_chart(
        self,
        query: AnalyticsQueryCreate,
        start_time: datetime,
        end_time: datetime,
        db: Session
    ) -> Dict[str, Any]:
        """Generate categorical chart data (bar/pie charts)"""
        
        category_data = []
        summary_metrics = {}
        
        for metric in query.metrics:
            if metric == MetricType.PROTOCOL_DISTRIBUTION:
                # Query protocol distribution
                query_sql = text("""
                    SELECT protocol, COUNT(*) as count, SUM(packet_count) as total_packets
                    FROM network_flows 
                    WHERE first_seen >= :start_time AND first_seen <= :end_time
                    GROUP BY protocol
                    ORDER BY count DESC
                    LIMIT :limit
                """)
                
                result = db.execute(query_sql, {
                    "start_time": start_time,
                    "end_time": end_time,
                    "limit": query.limit
                })
                
                total_count = 0
                for row in result:
                    total_count += row.count
                
                # Second pass to calculate percentages
                result = db.execute(query_sql, {
                    "start_time": start_time,
                    "end_time": end_time,
                    "limit": query.limit
                })
                
                for row in result:
                    percentage = (row.count / total_count * 100) if total_count > 0 else 0
                    category_data.append(CategoryDataPoint(
                        category=row.protocol,
                        value=float(row.count),
                        percentage=percentage,
                        count=row.count
                    ))
            
            elif metric == MetricType.PORT_DISTRIBUTION:
                # Query port distribution
                query_sql = text("""
                    SELECT destination_port, COUNT(*) as count
                    FROM network_flows 
                    WHERE first_seen >= :start_time AND first_seen <= :end_time
                      AND destination_port IS NOT NULL
                    GROUP BY destination_port
                    ORDER BY count DESC
                    LIMIT :limit
                """)
                
                result = db.execute(query_sql, {
                    "start_time": start_time,
                    "end_time": end_time,
                    "limit": query.limit
                })
                
                for row in result:
                    category_data.append(CategoryDataPoint(
                        category=f"Port {row.destination_port}",
                        value=float(row.count),
                        count=row.count
                    ))
        
        return {
            "category_data": category_data,
            "summary_metrics": summary_metrics,
            "data_points_count": len(category_data)
        }
    
    def _generate_network_graph(
        self,
        query: AnalyticsQueryCreate,
        start_time: datetime,
        end_time: datetime,
        db: Session
    ) -> Dict[str, Any]:
        """Generate network graph visualization"""
        
        # Query top communicating IPs
        query_sql = text("""
            SELECT 
                source_ip, destination_ip, 
                COUNT(*) as connection_count,
                SUM(packet_count) as total_packets,
                SUM(byte_count) as total_bytes
            FROM network_flows 
            WHERE first_seen >= :start_time AND first_seen <= :end_time
            GROUP BY source_ip, destination_ip
            HAVING COUNT(*) > 1
            ORDER BY connection_count DESC
            LIMIT :limit
        """)
        
        result = db.execute(query_sql, {
            "start_time": start_time,
            "end_time": end_time,
            "limit": query.limit
        })
        
        # Build nodes and edges
        nodes = {}
        edges = []
        
        for row in result:
            source_ip = str(row.source_ip)
            dest_ip = str(row.destination_ip)
            
            # Add nodes
            if source_ip not in nodes:
                nodes[source_ip] = NetworkNode(
                    id=source_ip,
                    label=source_ip,
                    node_type="ip",
                    size=1.0,
                    metrics={"connections": 0, "packets": 0, "bytes": 0}
                )
            
            if dest_ip not in nodes:
                nodes[dest_ip] = NetworkNode(
                    id=dest_ip,
                    label=dest_ip,
                    node_type="ip",
                    size=1.0,
                    metrics={"connections": 0, "packets": 0, "bytes": 0}
                )
            
            # Update node metrics
            nodes[source_ip].metrics["connections"] += row.connection_count
            nodes[source_ip].metrics["packets"] += row.total_packets
            nodes[source_ip].metrics["bytes"] += row.total_bytes
            
            nodes[dest_ip].metrics["connections"] += row.connection_count
            nodes[dest_ip].metrics["packets"] += row.total_packets
            nodes[dest_ip].metrics["bytes"] += row.total_bytes
            
            # Add edge
            edges.append(NetworkEdge(
                source=source_ip,
                target=dest_ip,
                weight=float(row.connection_count),
                edge_type="communication",
                label=f"{row.connection_count} connections",
                metrics={
                    "connections": row.connection_count,
                    "packets": row.total_packets,
                    "bytes": row.total_bytes
                }
            ))
        
        # Update node sizes based on connection count
        max_connections = max((node.metrics["connections"] for node in nodes.values()), default=1)
        for node in nodes.values():
            node.size = 1.0 + (node.metrics["connections"] / max_connections) * 3.0
        
        network_graph = NetworkGraph(
            nodes=list(nodes.values()),
            edges=edges,
            layout_algorithm="force_directed"
        )
        
        return {
            "network_graph": network_graph,
            "summary_metrics": {
                "total_nodes": len(nodes),
                "total_edges": len(edges),
                "max_connections": max_connections
            },
            "data_points_count": len(nodes) + len(edges)
        }
    
    def _generate_geo_map(
        self,
        query: AnalyticsQueryCreate,
        start_time: datetime,
        end_time: datetime,
        db: Session
    ) -> Dict[str, Any]:
        """Generate geographic map visualization"""
        
        # Query by source/destination countries
        query_sql = text("""
            SELECT 
                source_country, destination_country,
                COUNT(*) as connection_count,
                SUM(packet_count) as total_packets
            FROM network_flows 
            WHERE first_seen >= :start_time AND first_seen <= :end_time
              AND source_country IS NOT NULL 
              AND destination_country IS NOT NULL
            GROUP BY source_country, destination_country
            ORDER BY connection_count DESC
            LIMIT :limit
        """)
        
        result = db.execute(query_sql, {
            "start_time": start_time,
            "end_time": end_time,
            "limit": query.limit
        })
        
        # For demo purposes, generate mock geo coordinates
        # In production, this would use a GeoIP database
        geo_data = []
        country_coords = {
            "US": (39.8283, -98.5795),
            "CN": (35.8617, 104.1954),
            "DE": (51.1657, 10.4515),
            "GB": (55.3781, -3.4360),
            "JP": (36.2048, 138.2529),
            "FR": (46.6034, 1.8883),
            "CA": (56.1304, -106.3468),
            "AU": (-25.2744, 133.7751)
        }
        
        for row in result:
            source_coords = country_coords.get(row.source_country, (0, 0))
            dest_coords = country_coords.get(row.destination_country, (0, 0))
            
            # Add source point
            geo_data.append(GeoPoint(
                latitude=source_coords[0],
                longitude=source_coords[1],
                label=f"{row.source_country} (Source)",
                value=float(row.connection_count),
                popup_content=f"Country: {row.source_country}<br>Connections: {row.connection_count}"
            ))
            
            # Add destination point
            geo_data.append(GeoPoint(
                latitude=dest_coords[0],
                longitude=dest_coords[1],
                label=f"{row.destination_country} (Destination)",
                value=float(row.connection_count),
                popup_content=f"Country: {row.destination_country}<br>Connections: {row.connection_count}"
            ))
        
        return {
            "geo_data": geo_data,
            "summary_metrics": {
                "unique_countries": len(set(row.source_country for row in result) | 
                                      set(row.destination_country for row in result))
            },
            "data_points_count": len(geo_data)
        }
    
    def _generate_heatmap(
        self,
        query: AnalyticsQueryCreate,
        start_time: datetime,
        end_time: datetime,
        db: Session
    ) -> Dict[str, Any]:
        """Generate heatmap visualization data"""
        
        # Generate time vs protocol heatmap
        query_sql = text("""
            SELECT 
                DATE_TRUNC('hour', first_seen) as hour_bucket,
                protocol,
                COUNT(*) as activity_count
            FROM network_flows 
            WHERE first_seen >= :start_time AND first_seen <= :end_time
            GROUP BY hour_bucket, protocol
            ORDER BY hour_bucket, protocol
        """)
        
        result = db.execute(query_sql, {
            "start_time": start_time,
            "end_time": end_time
        })
        
        # Convert to heatmap format (will be processed by frontend)
        heatmap_data = []
        for row in result:
            heatmap_data.append({
                "x": row.hour_bucket.isoformat(),
                "y": row.protocol,
                "value": row.activity_count
            })
        
        return {
            "raw_data": heatmap_data,
            "summary_metrics": {
                "data_type": "heatmap",
                "x_axis": "time",
                "y_axis": "protocol"
            },
            "data_points_count": len(heatmap_data)
        }
    
    def _generate_raw_data(
        self,
        query: AnalyticsQueryCreate,
        start_time: datetime,
        end_time: datetime,
        db: Session
    ) -> Dict[str, Any]:
        """Generate raw data export"""
        
        # Query raw flow data
        query_obj = select(NetworkFlowORM).where(
            and_(
                NetworkFlowORM.first_seen >= start_time,
                NetworkFlowORM.first_seen <= end_time
            )
        ).limit(query.limit)
        
        result = db.execute(query_obj)
        flows = result.scalars().all()
        
        raw_data = []
        for flow in flows:
            raw_data.append({
                "flow_id": flow.flow_id,
                "source_ip": str(flow.source_ip),
                "destination_ip": str(flow.destination_ip),
                "source_port": flow.source_port,
                "destination_port": flow.destination_port,
                "protocol": flow.protocol,
                "packet_count": flow.packet_count,
                "byte_count": flow.byte_count,
                "duration_seconds": flow.duration_seconds,
                "first_seen": flow.first_seen.isoformat(),
                "last_seen": flow.last_seen.isoformat(),
                "threat_score": flow.threat_score,
                "anomaly_score": flow.anomaly_score
            })
        
        return {
            "raw_data": raw_data,
            "summary_metrics": {
                "total_flows": len(raw_data),
                "data_format": "tabular"
            },
            "data_points_count": len(raw_data)
        }
    
    # =============================================================================
    # TRAFFIC PATTERN ANALYSIS
    # =============================================================================
    
    def detect_traffic_patterns(
        self,
        time_range: TimeRange,
        db: Session,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[TrafficPatternResponse]:
        """Detect patterns in network traffic"""
        
        # Use provided time range or resolve from enum
        if time_range == TimeRange.CUSTOM and start_time and end_time:
            query_start, query_end = start_time, end_time
        else:
            query_obj = AnalyticsQueryCreate(
                time_range=time_range,
                metrics=[MetricType.PACKET_COUNT],
                visualization_type=VisualizationType.TIME_SERIES
            )
            query_start, query_end = self._resolve_time_range(query_obj)
        
        # Query existing patterns
        result = db.execute(
            select(TrafficPatternORM).where(
                and_(
                    TrafficPatternORM.first_detected >= query_start,
                    TrafficPatternORM.last_detected <= query_end,
                    TrafficPatternORM.is_active == True
                )
            ).order_by(desc(TrafficPatternORM.confidence_score))
        )
        
        patterns = result.scalars().all()
        
        return [TrafficPatternResponse.from_orm(pattern) for pattern in patterns]
    
    def create_traffic_pattern(
        self,
        pattern_data: Dict[str, Any],
        user_id: str,
        db: Session
    ) -> TrafficPatternResponse:
        """Create a new traffic pattern record"""
        
        pattern = TrafficPatternORM(
            pattern_id=str(uuid.uuid4()),
            pattern_type=pattern_data.get("pattern_type"),
            pattern_name=pattern_data.get("pattern_name"),
            description=pattern_data.get("description"),
            confidence_score=pattern_data.get("confidence_score", 0.0),
            frequency=pattern_data.get("frequency"),
            duration_minutes=pattern_data.get("duration_minutes"),
            affected_ips=pattern_data.get("affected_ips", []),
            affected_ports=pattern_data.get("affected_ports", []),
            protocols=pattern_data.get("protocols", []),
            first_detected=pattern_data.get("first_detected", datetime.utcnow()),
            last_detected=pattern_data.get("last_detected", datetime.utcnow()),
            detection_algorithm=pattern_data.get("detection_algorithm"),
            parameters=pattern_data.get("parameters", {}),
            baseline_data=pattern_data.get("baseline_data", {})
        )
        
        db.add(pattern)
        db.commit()
        db.refresh(pattern)
        
        # Log pattern creation
        audit_logger.log_event(
            "traffic_pattern_created",
            user_id=user_id,
            details={
                "pattern_id": pattern.pattern_id,
                "pattern_type": pattern.pattern_type,
                "confidence_score": pattern.confidence_score
            }
        )
        
        return TrafficPatternResponse.from_orm(pattern)
    
    # =============================================================================
    # ANOMALY DETECTION
    # =============================================================================
    
    def get_network_anomalies(
        self,
        db: Session,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        anomaly_type: Optional[AnomalyType] = None,
        min_severity: Optional[float] = None,
        limit: int = 100
    ) -> List[NetworkAnomalyResponse]:
        """Get network anomalies with filters"""
        
        query = select(NetworkAnomalyORM)
        filters = []
        
        if start_time:
            filters.append(NetworkAnomalyORM.detected_at >= start_time)
        if end_time:
            filters.append(NetworkAnomalyORM.detected_at <= end_time)
        if anomaly_type:
            filters.append(NetworkAnomalyORM.anomaly_type == anomaly_type.value)
        if min_severity:
            filters.append(NetworkAnomalyORM.severity_score >= min_severity)
        
        if filters:
            query = query.where(and_(*filters))
        
        query = query.order_by(desc(NetworkAnomalyORM.detected_at)).limit(limit)
        
        result = db.execute(query)
        anomalies = result.scalars().all()
        
        return [NetworkAnomalyResponse.from_orm(anomaly) for anomaly in anomalies]
    
    # =============================================================================
    # NETWORK FLOWS
    # =============================================================================
    
    def get_network_flows(
        self,
        db: Session,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        source_ip: Optional[str] = None,
        destination_ip: Optional[str] = None,
        protocol: Optional[str] = None,
        min_threat_score: Optional[float] = None,
        limit: int = 1000
    ) -> List[NetworkFlowResponse]:
        """Get network flows with filters"""
        
        query = select(NetworkFlowORM)
        filters = []
        
        if start_time:
            filters.append(NetworkFlowORM.first_seen >= start_time)
        if end_time:
            filters.append(NetworkFlowORM.first_seen <= end_time)
        if source_ip:
            filters.append(NetworkFlowORM.source_ip == source_ip)
        if destination_ip:
            filters.append(NetworkFlowORM.destination_ip == destination_ip)
        if protocol:
            filters.append(NetworkFlowORM.protocol == protocol)
        if min_threat_score:
            filters.append(NetworkFlowORM.threat_score >= min_threat_score)
        
        if filters:
            query = query.where(and_(*filters))
        
        query = query.order_by(desc(NetworkFlowORM.first_seen)).limit(limit)
        
        result = db.execute(query)
        flows = result.scalars().all()
        
        return [NetworkFlowResponse.from_orm(flow) for flow in flows]
    
    # =============================================================================
    # NETWORK TOPOLOGY
    # =============================================================================
    
    def get_network_topology(
        self,
        db: Session,
        subnet: Optional[str] = None,
        asset_type: Optional[str] = None,
        is_active: Optional[bool] = None,
        limit: int = 1000
    ) -> List[NetworkTopologyResponse]:
        """Get network topology information"""
        
        query = select(NetworkTopologyORM)
        filters = []
        
        if subnet:
            filters.append(NetworkTopologyORM.subnet == subnet)
        if asset_type:
            filters.append(NetworkTopologyORM.asset_type == asset_type)
        if is_active is not None:
            filters.append(NetworkTopologyORM.is_active == is_active)
        
        if filters:
            query = query.where(and_(*filters))
        
        query = query.order_by(NetworkTopologyORM.ip_address).limit(limit)
        
        result = db.execute(query)
        topology = result.scalars().all()
        
        return [NetworkTopologyResponse.from_orm(topo) for topo in topology]
    
    # =============================================================================
    # STATISTICS
    # =============================================================================
    
    def get_network_stats(
        self,
        db: Session,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> NetworkStatsResponse:
        """Get comprehensive network statistics"""
        
        # Default to last 24 hours if no time range provided
        if not start_time:
            start_time = datetime.utcnow() - timedelta(hours=24)
        if not end_time:
            end_time = datetime.utcnow()
        
        # Total flows
        total_flows_result = db.execute(
            select(func.count(NetworkFlowORM.id)).where(
                and_(
                    NetworkFlowORM.first_seen >= start_time,
                    NetworkFlowORM.first_seen <= end_time
                )
            )
        )
        total_flows = total_flows_result.scalar() or 0
        
        # Unique IPs
        unique_ips_result = db.execute(
            text("""
                SELECT COUNT(DISTINCT ip) FROM (
                    SELECT source_ip as ip FROM network_flows 
                    WHERE first_seen >= :start_time AND first_seen <= :end_time
                    UNION
                    SELECT destination_ip as ip FROM network_flows 
                    WHERE first_seen >= :start_time AND first_seen <= :end_time
                ) unique_ips_query
            """),
            {"start_time": start_time, "end_time": end_time}
        )
        unique_ips = unique_ips_result.scalar() or 0
        
        # Protocol distribution
        protocol_result = db.execute(
            text("""
                SELECT protocol, COUNT(*) as count
                FROM network_flows 
                WHERE first_seen >= :start_time AND first_seen <= :end_time
                GROUP BY protocol
                ORDER BY count DESC
            """),
            {"start_time": start_time, "end_time": end_time}
        )
        
        protocol_distribution = {}
        for row in protocol_result:
            protocol_distribution[row.protocol] = row.count
        
        # Top talkers (by byte count)
        top_talkers_result = db.execute(
            text("""
                SELECT 
                    source_ip,
                    SUM(byte_count) as total_bytes,
                    COUNT(*) as flow_count
                FROM network_flows 
                WHERE first_seen >= :start_time AND first_seen <= :end_time
                GROUP BY source_ip
                ORDER BY total_bytes DESC
                LIMIT 10
            """),
            {"start_time": start_time, "end_time": end_time}
        )
        
        top_talkers = []
        for row in top_talkers_result:
            top_talkers.append({
                "ip": str(row.source_ip),
                "total_bytes": row.total_bytes,
                "flow_count": row.flow_count
            })
        
        # Anomaly and threat counts
        anomaly_count_result = db.execute(
            select(func.count(NetworkAnomalyORM.id)).where(
                and_(
                    NetworkAnomalyORM.detected_at >= start_time,
                    NetworkAnomalyORM.detected_at <= end_time
                )
            )
        )
        anomaly_count = anomaly_count_result.scalar() or 0
        
        threat_count_result = db.execute(
            select(func.count(NetworkFlowORM.id)).where(
                and_(
                    NetworkFlowORM.first_seen >= start_time,
                    NetworkFlowORM.first_seen <= end_time,
                    NetworkFlowORM.is_malicious == True
                )
            )
        )
        threat_count = threat_count_result.scalar() or 0
        
        # Active patterns count
        active_patterns_result = db.execute(
            select(func.count(TrafficPatternORM.id)).where(
                TrafficPatternORM.is_active == True
            )
        )
        active_patterns = active_patterns_result.scalar() or 0
        
        # Calculate totals
        total_bytes_result = db.execute(
            select(func.sum(NetworkFlowORM.byte_count)).where(
                and_(
                    NetworkFlowORM.first_seen >= start_time,
                    NetworkFlowORM.first_seen <= end_time
                )
            )
        )
        total_bytes = total_bytes_result.scalar() or 0
        
        total_packets_result = db.execute(
            select(func.sum(NetworkFlowORM.packet_count)).where(
                and_(
                    NetworkFlowORM.first_seen >= start_time,
                    NetworkFlowORM.first_seen <= end_time
                )
            )
        )
        total_packets = total_packets_result.scalar() or 0
        
        unique_ports_result = db.execute(
            text("""
                SELECT COUNT(DISTINCT port) FROM (
                    SELECT source_port as port FROM network_flows 
                    WHERE first_seen >= :start_time AND first_seen <= :end_time
                      AND source_port IS NOT NULL
                    UNION
                    SELECT destination_port as port FROM network_flows 
                    WHERE first_seen >= :start_time AND first_seen <= :end_time
                      AND destination_port IS NOT NULL
                ) unique_ports_query
            """),
            {"start_time": start_time, "end_time": end_time}
        )
        unique_ports = unique_ports_result.scalar() or 0
        
        return NetworkStatsResponse(
            total_flows=total_flows,
            unique_ips=unique_ips,
            unique_ports=unique_ports,
            total_bytes=total_bytes,
            total_packets=total_packets,
            protocol_distribution=protocol_distribution,
            top_talkers=top_talkers,
            anomaly_count=anomaly_count,
            threat_count=threat_count,
            active_patterns=active_patterns,
            time_range={
                "start": start_time,
                "end": end_time
            }
        )


# Create singleton instance
network_analytics_service = NetworkAnalyticsService()
