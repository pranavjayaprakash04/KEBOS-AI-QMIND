"""
Trap Manager - REST API for controlling honeypot traps

Provides endpoints to start/stop traps and view live events.
"""
import asyncio
import logging
import os
from typing import Dict, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Header
from pydantic import BaseModel

from app.auth.dependencies import get_current_user
from app.auth.services import UserProfile
from app.deception.event_logger import event_logger

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/deception", tags=["deception"])

# In-memory trap tracking
_traps: Dict[str, any] = {}
_trap_stats: Dict[str, Dict] = {
    "ssh": {"hit_count": 0, "running": False, "port": 2222},
    "http": {"hit_count": 0, "running": False, "port": 8080},
    "rdp": {"hit_count": 0, "running": False, "port": 3389},
}


def require_role(user: UserProfile, allowed_roles: list):
    """Check if user has required role"""
    if user.role not in allowed_roles:
        raise HTTPException(status_code=403, detail="Insufficient permissions")


class TrapStatusResponse(BaseModel):
    trap_type: str
    port: int
    running: bool
    hit_count: int


class TrapActionResponse(BaseModel):
    status: str
    trap_type: str


@router.get("/traps", response_model=list[TrapStatusResponse])
async def list_traps():
    """
    Get status of all traps (read-only, no auth required).
    Returns list of trap status objects.
    """
    return [
        TrapStatusResponse(
            trap_type=trap_type,
            port=stats["port"],
            running=stats["running"],
            hit_count=stats["hit_count"]
        )
        for trap_type, stats in _trap_stats.items()
    ]


@router.post("/traps/{trap_type}/start", response_model=TrapActionResponse)
async def start_trap(
    trap_type: str,
    current_user: UserProfile = Depends(get_current_user)
):
    """
    Start a trap (requires ADMIN or ANALYST role).

    trap_type must be one of: ssh, http, rdp
    """
    require_role(current_user, ["ADMIN", "ANALYST", "analyst", "admin"])

    if trap_type not in ["ssh", "http", "rdp"]:
        raise HTTPException(status_code=400, detail="Invalid trap type")

    if _trap_stats[trap_type]["running"]:
        return TrapActionResponse(status="already_running", trap_type=trap_type)

    try:
        if trap_type == "ssh":
            from app.deception.traps.ssh_trap import start_ssh_trap
            trap = await start_ssh_trap()
            _traps["ssh"] = trap
            _trap_stats["ssh"]["running"] = True

        elif trap_type == "http":
            # HTTP trap runs as a subprocess with uvicorn
            import subprocess
            process = subprocess.Popen(
                [
                    "uvicorn",
                    "app.deception.traps.http_trap:http_trap_app",
                    "--host", "0.0.0.0",
                    "--port", str(_trap_stats["http"]["port"])
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            _traps["http"] = process
            _trap_stats["http"]["running"] = True

        elif trap_type == "rdp":
            from app.deception.traps.rdp_trap import start_rdp_trap
            server = await start_rdp_trap()
            _traps["rdp"] = server
            _trap_stats["rdp"]["running"] = True

            # Add done callback for RDP server
            async def monitor_rdp():
                try:
                    await server.serve_forever()
                except asyncio.CancelledError:
                    pass
                except Exception as e:
                    logger.error(f"RDP trap crashed: {e}")
                finally:
                    _trap_stats["rdp"]["running"] = False

            rdp_task = asyncio.create_task(monitor_rdp())
            rdp_task.add_done_callback(
                lambda t: logger.error(f"RDP trap crashed: {t.exception()}")
                if t.exception() else logger.info("RDP trap stopped")
            )

        logger.info(f"Trap {trap_type} started by {current_user.username}")
        return TrapActionResponse(status="started", trap_type=trap_type)

    except Exception as e:
        logger.error(f"Failed to start {trap_type} trap: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start trap: {str(e)}")


@router.post("/traps/{trap_type}/stop", response_model=TrapActionResponse)
async def stop_trap(
    trap_type: str,
    current_user: UserProfile = Depends(get_current_user)
):
    """
    Stop a trap (requires ADMIN role only).
    """
    require_role(current_user, ["ADMIN", "admin"])

    if trap_type not in ["ssh", "http", "rdp"]:
        raise HTTPException(status_code=400, detail="Invalid trap type")

    if not _trap_stats[trap_type]["running"]:
        return TrapActionResponse(status="stopped", trap_type=trap_type)

    try:
        trap = _traps.get(trap_type)

        if trap_type == "ssh" and trap:
            await trap.stop()
        elif trap_type == "http" and trap:
            trap.terminate()
            trap.wait()
        elif trap_type == "rdp" and trap:
            trap.close()

        _traps.pop(trap_type, None)
        _trap_stats[trap_type]["running"] = False

        logger.info(f"Trap {trap_type} stopped by {current_user.username}")
        return TrapActionResponse(status="stopped", trap_type=trap_type)

    except Exception as e:
        logger.error(f"Failed to stop {trap_type} trap: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to stop trap: {str(e)}")


@router.get("/events/live")
async def get_live_events(
    limit: int = Query(default=50, ge=1, le=200),
    current_user: UserProfile = Depends(get_current_user)
):
    """
    Get recent honeypot events from InfluxDB.
    Requires authentication.
    """
    try:
        from influxdb_client import InfluxDBClient

        influx_url = os.environ.get("INFLUXDB_URL", "http://localhost:8086")
        influx_token = os.environ.get("INFLUXDB_TOKEN", "")
        influx_org = os.environ.get("INFLUXDB_ORG", "kebos")
        influx_bucket = os.environ.get("INFLUXDB_BUCKET", "honeypot")

        client = InfluxDBClient(
            url=influx_url,
            token=influx_token,
            org=influx_org
        )

        query_api = client.query_api()

        query = f'''
        from(bucket: "{influx_bucket}")
            |> range(start: -1h)
            |> filter(fn: (r) => r._measurement == "honeypot_event")
            |> sort(columns: ["_time"], desc: true)
            |> limit(n: {limit})
        '''

        tables = query_api.query(query)

        events = []
        for table in tables:
            for record in table.records:
                events.append({
                    "time": record.get_time().isoformat() if record.get_time() else None,
                    "trap_type": record.values.get("trap_type"),
                    "event_type": record.values.get("event_type"),
                    "attacker_ip": record.values.get("attacker_ip"),
                })

        client.close()

        return events

    except Exception as e:
        logger.error(f"Failed to query InfluxDB: {e}")
        # Return empty list with header indicating data source unavailable
        return []
