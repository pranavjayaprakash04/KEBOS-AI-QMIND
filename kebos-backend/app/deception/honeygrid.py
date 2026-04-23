import docker, asyncio, ipaddress, subprocess, logging
from uuid import UUID, uuid4
from datetime import datetime
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class HoneypotDeployment:
    deployment_id: UUID
    threat_id: UUID
    container_id: str
    attacker_ip: str
    deployed_at: datetime
    network: str = "kebos_deception_net"

class HoneyGridManager:
    """
    Deploys Cowrie SSH honeypots when QMind detects CONFIRMED_THREAT.
    Connects to docker-proxy:2375 — NEVER /var/run/docker.sock directly.
    """
    def __init__(self):
        # NEVER docker.from_env() — that uses the raw socket
        self._docker = docker.DockerClient(base_url="tcp://docker-proxy:2375")

    async def deploy_honeypot(
        self, threat_id: UUID, attacker_ip: str, lead_category: str
    ) -> HoneypotDeployment:
        """Deploy Cowrie SSH honeypot and redirect attacker traffic to it."""
        # Validate IP before any subprocess call — prevent command injection
        try:
            ipaddress.ip_address(attacker_ip)
        except ValueError:
            raise ValueError(f"Invalid attacker IP: {attacker_ip}")

        deployment_id = uuid4()
        container_name = f"honeypot-{deployment_id.hex[:8]}"

        try:
            container = self._docker.containers.run(
                image="cowrie/cowrie:latest",
                name=container_name,
                detach=True,
                network="kebos_deception_net",
                environment={
                    "COWRIE_HOSTNAME": f"prod-server-{deployment_id.hex[:6]}",
                },
                labels={
                    "kebos.threat_id": str(threat_id),
                    "kebos.attacker_ip": attacker_ip,
                    "kebos.deployed_at": datetime.utcnow().isoformat(),
                },
                mem_limit="256m",
                cpu_period=100000,
                cpu_quota=25000,  # 25% CPU max
            )
            logger.info(
                f"Honeypot {container_name} deployed for attacker {attacker_ip} "
                f"(threat {threat_id})"
            )
        except docker.errors.APIError as e:
            logger.error(f"Failed to deploy honeypot: {e}")
            raise

        # Set up iptables DNAT to redirect attacker to honeypot
        await self._setup_dnat(attacker_ip, container.id)

        deployment = HoneypotDeployment(
            deployment_id=deployment_id,
            threat_id=threat_id,
            container_id=container.id,
            attacker_ip=attacker_ip,
            deployed_at=datetime.utcnow(),
        )
        return deployment

    async def extract_iocs_and_inject(self, container_id: str, tenant_id: UUID):
        """
        Parse Cowrie logs for attacker TTPs, inject high-confidence signals to QMind.
        This closes the deception intelligence feedback loop (Patent Claim 2).
        """
        try:
            container = self._docker.containers.get(container_id)
            raw_logs = container.logs(tail=500).decode("utf-8", errors="ignore")
            iocs = self._parse_cowrie_logs(raw_logs)
            for ioc in iocs:
                from app.integrations.egress_control import EgressControlledClient
                async with EgressControlledClient() as client:
                    await client.post(
                        "http://qmind:8001/signals/inject",
                        json={
                            "indicator_value": ioc["value"],
                            "indicator_type": ioc["type"],
                            "source": "honeypot",
                            "confidence": 0.95,
                            "tenant_id": str(tenant_id),
                            "metadata": {"cowrie_command": ioc.get("command", "")}
                        }
                    )
            logger.info(f"Injected {len(iocs)} IOCs from honeypot {container_id}")
        except Exception as e:
            logger.error(f"IOC extraction failed for {container_id}: {e}")

    def _parse_cowrie_logs(self, raw_logs: str) -> list[dict]:
        """Extract IPs, commands, and file hashes from Cowrie JSON logs."""
        iocs = []
        for line in raw_logs.splitlines():
            try:
                import json as _json
                entry = _json.loads(line)
                if entry.get("eventid") in ("cowrie.login.failed", "cowrie.login.success"):
                    src = entry.get("src_ip")
                    if src:
                        iocs.append({"value": src, "type": "ip"})
                if entry.get("eventid") == "cowrie.command.input":
                    cmd = entry.get("input", "")
                    if cmd:
                        iocs.append({"value": cmd[:200], "type": "command",
                                     "command": cmd})
            except Exception:
                pass
        return iocs

    async def teardown_honeypot(self, container_id: str):
        """Remove honeypot container and clean up iptables rules."""
        try:
            container = self._docker.containers.get(container_id)
            attacker_ip = container.labels.get("kebos.attacker_ip", "")
            container.stop(timeout=10)
            container.remove(force=True)
            if attacker_ip:
                await self._remove_dnat(attacker_ip)
            logger.info(f"Honeypot {container_id} torn down")
        except Exception as e:
            logger.error(f"Honeypot teardown failed: {e}")

    async def _setup_dnat(self, attacker_ip: str, container_id: str):
        """Redirect attacker traffic to honeypot via iptables DNAT."""
        # Input already validated above — safe to use in subprocess
        cmd = [
            "iptables", "-t", "nat", "-A", "PREROUTING",
            "-s", attacker_ip, "-p", "tcp", "--dport", "22",
            "-j", "REDIRECT", "--to-port", "2222"
        ]
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode != 0:
            logger.warning(f"iptables DNAT setup failed: {stderr.decode()}")

    async def _remove_dnat(self, attacker_ip: str):
        """Remove iptables DNAT rule."""
        try:
            ipaddress.ip_address(attacker_ip)
        except ValueError:
            return
        cmd = [
            "iptables", "-t", "nat", "-D", "PREROUTING",
            "-s", attacker_ip, "-p", "tcp", "--dport", "22",
            "-j", "REDIRECT", "--to-port", "2222"
        ]
        proc = await asyncio.create_subprocess_exec(*cmd)
        await proc.communicate()
