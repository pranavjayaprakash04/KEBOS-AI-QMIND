#!/usr/bin/env python3
"""
Attack Simulator for Kebos Deception Layer Demo

Simulates an attacker hitting all three honeypot traps in sequence:
1. SSH trap on port 2222
2. HTTP trap on port 8080
3. RDP trap on port 3389

Usage:
    python simulate_attack.py --target localhost --delay 2
"""
import argparse
import sys
import time
import socket
from datetime import datetime

# Try to import paramiko, provide helpful error if not available
try:
    import paramiko
except ImportError:
    print("ERROR: paramiko is required. Install with: pip install paramiko>=3.4.0")
    sys.exit(1)

# Try to import requests, provide helpful error if not available
try:
    import requests
except ImportError:
    print("ERROR: requests is required. Install with: pip install requests>=2.31.0")
    sys.exit(1)


def log(message: str):
    """Print timestamped log message"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")


def simulate_ssh_attack(target: str, delay: float):
    """
    Step 1: SSH Attack
    Attempts connections with common credentials on port 2222
    """
    log("=== STEP 1: SSH ATTACK ===")
    log(f"Target: {target}:2222")

    # Common credential pairs to try
    credentials = [
        ("admin", "admin"),
        ("root", "password123"),
        ("administrator", "Admin@2024"),
        ("user", "letmein"),
        ("root", "toor"),
        ("admin", "P@ssw0rd"),
    ]

    for username, password in credentials:
        try:
            log(f"Trying {username}/{password}...")

            # Create SSH client
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            # Attempt connection with 5 second timeout
            try:
                client.connect(
                    hostname=target,
                    port=2222,
                    username=username,
                    password=password,
                    timeout=5,
                    allow_agent=False,
                    look_for_keys=False
                )
                # If we get here, auth succeeded (shouldn't happen with honeypot)
                log(f"  WARNING: Auth succeeded with {username}/{password}")
                client.close()
            except paramiko.AuthenticationException:
                log(f"  Expected: Authentication failed")
            except paramiko.SSHException as e:
                log(f"  SSH Error: {e}")
            except socket.timeout:
                log(f"  Timeout (expected)")
            except Exception as e:
                log(f"  Error: {type(e).__name__}: {e}")
            finally:
                try:
                    client.close()
                except:
                    pass

            time.sleep(0.5)  # Delay between attempts

        except Exception as e:
            log(f"  Failed to create SSH client: {e}")

    log("SSH attack complete")
    time.sleep(delay)


def simulate_http_attack(target: str, delay: float):
    """
    Step 2: HTTP Attack
    Visits fake admin panel and submits credentials
    """
    log("=== STEP 2: HTTP ATTACK ===")
    base_url = f"http://{target}:8080"
    log(f"Target: {base_url}")

    # Step 2a: Visit home page
    try:
        log("GET /")
        response = requests.get(base_url, timeout=5)
        log(f"  Status: {response.status_code}")
    except requests.exceptions.RequestException as e:
        log(f"  Error: {e}")

    time.sleep(0.5)

    # Step 2b: Visit admin page
    try:
        log("GET /admin")
        response = requests.get(f"{base_url}/admin", timeout=5)
        log(f"  Status: {response.status_code}")
    except requests.exceptions.RequestException as e:
        log(f"  Error: {e}")

    time.sleep(0.5)

    # Step 2c: Visit login page
    try:
        log("GET /login")
        response = requests.get(f"{base_url}/login", timeout=5)
        log(f"  Status: {response.status_code}")
    except requests.exceptions.RequestException as e:
        log(f"  Error: {e}")

    time.sleep(0.5)

    # Step 2d: Submit login credentials
    try:
        log("POST /login (admin/Admin@2024)")
        response = requests.post(
            f"{base_url}/login",
            data={"username": "admin", "password": "Admin@2024"},
            timeout=5
        )
        log(f"  Status: {response.status_code}")
    except requests.exceptions.RequestException as e:
        log(f"  Error: {e}")

    log("HTTP attack complete")
    time.sleep(delay)


def simulate_rdp_attack(target: str, delay: float):
    """
    Step 3: RDP Attack
    Sends RDP negotiation bytes to port 3389
    """
    log("=== STEP 3: RDP ATTACK ===")
    log(f"Target: {target}:3389")

    # RDP negotiation request bytes
    rdp_nego_bytes = bytes([
        0x03, 0x00, 0x00, 0x13, 0x0e, 0xe0, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x01, 0x00, 0x08, 0x00, 0x03,
        0x00, 0x00, 0x00
    ])

    try:
        log("Connecting to RDP port...")

        # Create socket connection
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        sock.connect((target, 3389))

        log("  Connected, sending negotiation bytes...")

        # Send RDP negotiation
        sock.send(rdp_nego_bytes)
        log(f"  Sent {len(rdp_nego_bytes)} bytes")

        # Read response (up to 64 bytes)
        sock.settimeout(5)
        try:
            response = sock.recv(64)
            log(f"  Received {len(response)} bytes")
        except socket.timeout:
            log("  No response received (timeout)")

        sock.close()
        log("RDP connection closed")

    except socket.timeout:
        log("  Connection timeout")
    except ConnectionRefusedError:
        log("  Connection refused (RDP trap may not be running)")
    except Exception as e:
        log(f"  Error: {type(e).__name__}: {e}")

    log("RDP attack complete")
    time.sleep(delay)


def main():
    parser = argparse.ArgumentParser(
        description="Simulate attack against Kebos deception layer honeypots"
    )
    parser.add_argument(
        "--target",
        default="localhost",
        help="Target hostname or IP (default: localhost)"
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=2.0,
        help="Delay in seconds between trap attacks (default: 2)"
    )
    args = parser.parse_args()

    print("=" * 60)
    print("Kebos Deception Layer - Attack Simulator")
    print("=" * 60)
    print()
    print(f"Target: {args.target}")
    print(f"Delay between attacks: {args.delay}s")
    print()

    try:
        # Execute all three attacks
        simulate_ssh_attack(args.target, args.delay)
        simulate_http_attack(args.target, args.delay)
        simulate_rdp_attack(args.target, args.delay)

        print()
        print("=" * 60)
        print("ALL ATTACKS COMPLETE")
        print("=" * 60)
        print()
        print("Check the Deception Layer dashboard at:")
        print(f"  http://{args.target}:5173/deception")
        print()
        print("You should see:")
        print("  - SSH credential attempts logged")
        print("  - HTTP page visits and login attempts logged")
        print("  - RDP connection attempts logged")
        print()

    except KeyboardInterrupt:
        print()
        log("Interrupted by user")
        sys.exit(1)
    except Exception as e:
        log(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
