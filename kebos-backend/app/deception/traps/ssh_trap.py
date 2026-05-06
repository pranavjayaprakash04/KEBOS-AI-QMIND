"""
SSH Honeypot Trap - Paramiko-based fake SSH server

Presents a realistic Ubuntu 22.04 SSH banner and logs all attempts.
"""
import asyncio
import logging
import os
import socket
import threading
from typing import Optional

import paramiko
from paramiko.ssh_exception import SSHException

from app.deception.event_logger import event_logger

logger = logging.getLogger(__name__)

# Generate fresh host key on module load
HOST_KEY = paramiko.RSAKey.generate(2048)


class SSHTrapServer(paramiko.ServerInterface):
    """Paramiko server interface that rejects all authentication"""

    def __init__(self, client_ip: str):
        self.client_ip = client_ip
        self.username: Optional[str] = None
        self.password: Optional[str] = None

    def check_channel_request(self, kind: str, chanid: int) -> int:
        return paramiko.OPEN_SUCCEEDED

    def check_auth_password(self, username: str, password: str) -> int:
        """Log credentials and always return AUTH_FAILED"""
        self.username = username
        self.password = password

        # Log the credential attempt
        asyncio.create_task(event_logger.log_event(
            trap_type="ssh",
            attacker_ip=self.client_ip,
            event_type="credential_attempt",
            data={"username": username, "password": password}
        ))

        logger.info(f"SSH credential attempt from {self.client_ip}: {username}/{password}")

        # Always reject authentication
        return paramiko.AUTH_FAILED

    def check_auth_publickey(self, username: str, key: paramiko.PKey) -> int:
        """Reject public key authentication"""
        return paramiko.AUTH_FAILED

    def get_allowed_auths(self, username: str) -> str:
        return "password,publickey"

    def check_channel_shell_request(self, channel: paramiko.Channel) -> bool:
        return True

    def check_channel_pty_request(
        self, channel: paramiko.Channel, term: str, width: int,
        height: int, pixelwidth: int, pixelheight: int
    ) -> bool:
        return True


class SSHTrap:
    """
    SSH Honeypot Trap

    Listens on port 2222 (configurable via SSH_TRAP_PORT env var).
    Presents Ubuntu 22.04 SSH banner.
    Accepts all connections, rejects all authentication.
    """

    def __init__(self):
        self.port = int(os.environ.get("SSH_TRAP_PORT", 2222))
        self.server_socket: Optional[socket.socket] = None
        self.running = False
        self._server_task: Optional[asyncio.Task] = None

    def _run_server(self):
        """Run the SSH server in a thread (blocking operation)"""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind(("0.0.0.0", self.port))
        self.server_socket.listen(100)
        self.server_socket.settimeout(1.0)  # Allow checking for shutdown

        logger.info(f"SSH trap listening on port {self.port}")

        while self.running:
            try:
                client, addr = self.server_socket.accept()
                client_ip = addr[0]

                # Handle connection in a thread
                thread = threading.Thread(
                    target=self._handle_client,
                    args=(client, client_ip),
                    daemon=True
                )
                thread.start()
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    logger.error(f"SSH trap accept error: {e}")

    def _handle_client(self, client_socket: socket.socket, client_ip: str):
        """Handle a single SSH connection"""
        transport: Optional[paramiko.Transport] = None
        try:
            # Create transport with Ubuntu 22.04 banner
            transport = paramiko.Transport(client_socket)
            transport.local_version = "SSH-2.0-OpenSSH_8.9p1 Ubuntu-3ubuntu0.6"
            transport.add_server_key(HOST_KEY)

            server = SSHTrapServer(client_ip)
            transport.start_server(server=server)

            # Accept connection (will fail auth)
            channel = transport.accept(30)

            if channel and server.username:
                # After auth failure, send fake shell prompt
                channel.send(b"ubuntu@server:~$ ")

                # Read any command sent
                while True:
                    try:
                        data = channel.recv(1024)
                        if not data:
                            break

                        command = data.decode("utf-8", errors="ignore").strip()
                        if command:
                            # Log the command
                            asyncio.create_task(event_logger.log_event(
                                trap_type="ssh",
                                attacker_ip=client_ip,
                                event_type="command_attempt",
                                data={"command": command}
                            ))
                            logger.info(f"SSH command from {client_ip}: {command}")

                            # Send permission denied response
                            channel.send(b"bash: permission denied\r\n")
                            channel.send(b"ubuntu@server:~$ ")
                    except Exception:
                        break

        except SSHException as e:
            logger.debug(f"SSH protocol error from {client_ip}: {e}")
        except Exception as e:
            logger.error(f"SSH client handling error: {e}")
        finally:
            if transport:
                try:
                    transport.close()
                except:
                    pass
            try:
                client_socket.close()
            except:
                pass

    async def start(self, port: Optional[int] = None):
        """Start the SSH trap server"""
        if port:
            self.port = port

        self.running = True

        # Run server in executor to not block event loop
        loop = asyncio.get_event_loop()
        self._server_task = asyncio.create_task(
            loop.run_in_executor(None, self._run_server)
        )

        # Add done callback
        def on_done(task):
            if task.exception():
                logger.error(f"SSH trap crashed: {task.exception()}")
            else:
                logger.info("SSH trap stopped")

        self._server_task.add_done_callback(on_done)

        logger.info(f"SSH trap started on port {self.port}")

    async def stop(self):
        """Stop the SSH trap server"""
        self.running = False

        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
            self.server_socket = None

        if self._server_task:
            self._server_task.cancel()
            try:
                await self._server_task
            except asyncio.CancelledError:
                pass
            self._server_task = None

        logger.info("SSH trap stopped")


# Factory function for trap_manager
async def start_ssh_trap(port: int = 2222) -> SSHTrap:
    """Create and start SSH trap"""
    trap = SSHTrap()
    await trap.start(port)
    return trap
