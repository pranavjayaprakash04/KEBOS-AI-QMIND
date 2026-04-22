"""
Zeek Log Ingestor - Network Traffic Analysis

Monitors Zeek logs in real-time and extracts threat indicators.
Supports: conn.log, dns.log, http.log, ssl.log, files.log

Configuration:
- ZEEK_ENABLED: Enable/disable Zeek log monitoring
- ZEEK_LOG_DIR: Directory to monitor (default: /opt/zeek/logs/current/)
"""
import asyncio
import logging
import aiofiles
from typing import Dict, Callable, Optional
from datetime import datetime
from app.config import settings
from app.threat_detection.kafka_producer import threat_publisher

logger = logging.getLogger(__name__)


class ZeekLogIngestor:
    """Ingest Zeek logs and extract threat indicators"""
    
    LOG_TYPES = {
        "conn.log": "_parse_conn",
        "dns.log": "_parse_dns",
        "http.log": "_parse_http",
        "ssl.log": "_parse_ssl",
        "files.log": "_parse_files",
    }
    
    def __init__(self, log_dir: str = "/opt/zeek/logs/current/"):
        self.log_dir = log_dir
        self._running = False
        self._tasks = []
    
    async def start(self):
        """Start monitoring Zeek logs"""
        if not settings.ZEEK_ENABLED:
            logger.info("Zeek log monitoring disabled (ZEEK_ENABLED=False)")
            return
        
        self._running = True
        logger.info(f"Starting Zeek log ingestor for {self.log_dir}")
        
        # Start tailing each log type
        for log_type, parser_method in self.LOG_TYPES.items():
            parser = getattr(self, parser_method)
            task = asyncio.create_task(self._tail_log(self.log_dir + log_type, parser))
            task.add_done_callback(self._handle_task_error)
            self._tasks.append(task)
        
        logger.info(f"Zeek log ingestor started: monitoring {len(self.LOG_TYPES)} log types")
    
    async def stop(self):
        """Stop monitoring Zeek logs"""
        self._running = False
        for task in self._tasks:
            task.cancel()
        logger.info("Zeek log ingestor stopped")
    
    def _handle_task_error(self, task):
        """Handle task errors"""
        if not task.cancelled() and task.exception():
            logger.error(f"Zeek log ingestor task error: {task.exception()}")
    
    async def _tail_log(self, path: str, parser: Callable):
        """Tail a log file and parse new lines"""
        if not self._running:
            return
        
        try:
            async with aiofiles.open(path, mode='r') as f:
                # Seek to end of file
                await f.seek(0, 2)
                
                while self._running:
                    line = await f.readline()
                    if line:
                        try:
                            indicator = parser(line.strip())
                            if indicator:
                                await threat_publisher.publish(indicator, catboost_score=0.5)
                        except Exception as e:
                            logger.warning(f"Failed to parse log line: {e}")
                    else:
                        await asyncio.sleep(0.1)
        except FileNotFoundError:
            logger.warning(f"Log file not found: {path}")
        except Exception as e:
            logger.error(f"Error tailing log {path}: {e}")
    
    def _parse_conn(self, line: str) -> Optional[Dict]:
        """Parse connection log line"""
        # Zeek conn.log format: ts,uid,id.orig.h,id.orig.p,id.resp.h,id.resp.p,proto,service,duration,orig_bytes,resp_bytes,conn_state,local_orig,local_resp,missed_bytes,history,orig_pkts,orig_ip_bytes,resp_pkts,resp_ip_bytes,tunnel_parents
        try:
            fields = line.split('\t')
            if len(fields) < 9:
                return None
            
            src_ip = fields[2]
            dst_ip = fields[4]
            protocol = fields[6]
            
            # Detect suspicious connections
            if self._is_suspicious_ip(src_ip) or self._is_suspicious_ip(dst_ip):
                return {
                    "indicator_value": src_ip if self._is_suspicious_ip(src_ip) else dst_ip,
                    "indicator_type": "ip",
                    "source": "zeek_conn",
                    "metadata": {
                        "protocol": protocol,
                        "timestamp": fields[0],
                        "log_type": "conn"
                    }
                }
        except Exception:
            pass
        return None
    
    def _parse_dns(self, line: str) -> Optional[Dict]:
        """Parse DNS log line"""
        try:
            fields = line.split('\t')
            if len(fields) < 10:
                return None
            
            query = fields[9]
            if query and self._is_suspicious_domain(query):
                return {
                    "indicator_value": query,
                    "indicator_type": "domain",
                    "source": "zeek_dns",
                    "metadata": {
                        "timestamp": fields[0],
                        "log_type": "dns"
                    }
                }
        except Exception:
            pass
        return None
    
    def _parse_http(self, line: str) -> Optional[Dict]:
        """Parse HTTP log line"""
        try:
            fields = line.split('\t')
            if len(fields) < 10:
                return None
            
            host = fields[9]
            uri = fields[10] if len(fields) > 10 else ""
            user_agent = fields[11] if len(fields) > 11 else ""
            
            if host and self._is_suspicious_domain(host):
                return {
                    "indicator_value": host,
                    "indicator_type": "domain",
                    "source": "zeek_http",
                    "metadata": {
                        "uri": uri,
                        "user_agent": user_agent,
                        "timestamp": fields[0],
                        "log_type": "http"
                    }
                }
        except Exception:
            pass
        return None
    
    def _parse_ssl(self, line: str) -> Optional[Dict]:
        """Parse SSL/TLS log line"""
        try:
            fields = line.split('\t')
            if len(fields) < 10:
                return None
            
            server_name = fields[9] if len(fields) > 9 else ""
            if server_name and self._is_suspicious_domain(server_name):
                return {
                    "indicator_value": server_name,
                    "indicator_type": "domain",
                    "source": "zeek_ssl",
                    "metadata": {
                        "timestamp": fields[0],
                        "log_type": "ssl"
                    }
                }
        except Exception:
            pass
        return None
    
    def _parse_files(self, line: str) -> Optional[Dict]:
        """Parse files log line"""
        try:
            fields = line.split('\t')
            if len(fields) < 10:
                return None
            
            md5 = fields[9] if len(fields) > 9 else ""
            sha1 = fields[10] if len(fields) > 10 else ""
            sha256 = fields[11] if len(fields) > 11 else ""
            
            file_hash = sha256 or sha1 or md5
            if file_hash:
                return {
                    "indicator_value": file_hash,
                    "indicator_type": "hash",
                    "source": "zeek_files",
                    "metadata": {
                        "md5": md5,
                        "sha1": sha1,
                        "sha256": sha256,
                        "timestamp": fields[0],
                        "log_type": "files"
                    }
                }
        except Exception:
            pass
        return None
    
    def _is_suspicious_ip(self, ip: str) -> bool:
        """Check if IP is suspicious (placeholder - integrate with threat intel)"""
        # TODO: Integrate with threat intel feeds
        # For now, check for private IP ranges to filter
        private_ranges = [
            "10.", "172.16.", "192.168.", "127.", "169.254."
        ]
        return not any(ip.startswith(prefix) for prefix in private_ranges)
    
    def _is_suspicious_domain(self, domain: str) -> bool:
        """Check if domain is suspicious (placeholder)"""
        # TODO: Integrate with threat intel feeds
        # For now, check for common TLDs
        suspicious_tlds = [".xyz", ".top", ".tk", ".ml", ".ga"]
        return any(domain.endswith(tld) for tld in suspicious_tlds)


def get_zeek_ingestor(log_dir: str = "/opt/zeek/logs/current/") -> ZeekLogIngestor:
    """Factory function to get Zeek log ingestor instance"""
    return ZeekLogIngestor(log_dir)
