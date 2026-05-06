"""
RDP Honeypot Trap - asyncio TCP listener simulating RDP

Uses asyncio.start_server() for fully async operation.
"""
import asyncio
import logging
import os
from typing import Optional

from app.deception.event_logger import event_logger

logger = logging.getLogger(__name__)

# Real RDP negotiation response
RDP_NEGO_RESPONSE = bytes([
    0x03, 0x00, 0x00, 0x13, 0x0e, 0xd0, 0x00, 0x00,
    0x12, 0x34, 0x00, 0x02, 0x00, 0x08, 0x00, 0x02,
    0x00, 0x00, 0x00
])


async def handle_rdp_client(
    reader: asyncio.StreamReader,
    writer: asyncio.StreamWriter
):
    """Handle a single RDP connection"""
    client_ip = "unknown"
    try:
        # Get client IP
        peer = writer.get_extra_info('peername')
        if peer:
            client_ip = peer[0]

        logger.info(f"RDP connection from {client_ip}")

        # Read initial data (up to 1024 bytes, 10 second timeout)
        try:
            data = await asyncio.wait_for(
                reader.read(1024),
                timeout=10.0
            )
        except asyncio.TimeoutError:
            logger.debug(f"RDP timeout reading initial data from {client_ip}")
            return

        if data:
            # Log connection attempt
            await event_logger.log_event(
                trap_type="rdp",
                attacker_ip=client_ip,
                event_type="connection_attempt",
                data={"bytes_received": len(data)}
            )

            # Send RDP negotiation response
            writer.write(RDP_NEGO_RESPONSE)
            await writer.drain()

            # Read more data (negotiation data)
            try:
                nego_data = await asyncio.wait_for(
                    reader.read(4096),
                    timeout=15.0
                )

                if nego_data:
                    # Log negotiation data
                    await event_logger.log_event(
                        trap_type="rdp",
                        attacker_ip=client_ip,
                        event_type="negotiation_data",
                        data={"bytes_received": len(nego_data)}
                    )
            except asyncio.TimeoutError:
                logger.debug(f"RDP timeout reading negotiation data from {client_ip}")

    except ConnectionResetError:
        logger.debug(f"RDP connection reset by {client_ip}")
    except Exception as e:
        logger.error(f"RDP client handling error: {e}")
    finally:
        try:
            writer.close()
            await writer.wait_closed()
        except:
            pass


async def start_rdp_trap(port: Optional[int] = None) -> asyncio.Server:
    """
    Start the RDP trap server.

    Returns the server object which can be used to stop the server.
    """
    listen_port = port or int(os.environ.get("RDP_TRAP_PORT", 3389))

    server = await asyncio.start_server(
        handle_rdp_client,
        host="0.0.0.0",
        port=listen_port
    )

    logger.info(f"RDP trap started on port {listen_port}")

    return server
