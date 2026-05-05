"""
MITRE ATT&CK Mapping

Maps Kebos threat categories to MITRE ATT&CK techniques.
"""
from typing import Dict, List

CATEGORY_TO_MITRE: Dict[str, List[str]] = {
    "Phishing": [
        "T1566.001",  # Spearphishing Attachment
        "T1566.002",  # Spearphishing Link
    ],
    "Malware": [
        "T1059.005",  # Command and Scripting Interpreter: PowerShell
        "T1053.005",  # Scheduled Task/Job: Scheduled Task
        "T1204.002",  # User Execution: Malicious File
        "T1547",      # Boot or Logon Autostart Execution
        "T1036",      # Masquerading
        "T1070",      # Indicator Removal
    ],
    "C2_Infrastructure": [
        "T1133",      # Remote Services: External Remote Services
        "T1071.001",  # Application Layer Protocol: Web Protocols
        "T1041",      # Exfiltration Over C2 Channel
        "T1486",      # Data Encrypted for Impact
        "T1560",      # Archive Collected Data
    ],
    "Botnet_IP": [
        "T1486",      # Data Encrypted for Impact
        "T1489",      # Service Stop
        "T1490",      # Inhibit System Recovery
    ],
    "Credential_Leak": [
        "T1078",      # Valid Accounts
        "T1110",      # Brute Force
        "T1003",      # OS Credential Dumping
    ],
    "Supply_Chain": [
        "T1195",      # Supply Chain Compromise
    ],
    "Insider_Threat": [
        "T1021.002",  # Remote Services: SMB/Windows Admin Shares
        "T1057",      # Process Discovery
        "T1482",      # Domain Trust Discovery
        "T1003",      # OS Credential Dumping
    ],
    "DDoS": [
        "T1498",      # Network Denial of Service
        "T1499",      # Endpoint Denial of Service
    ],
    "CVE_Exploitation": [
        "T1190",      # Exploit Public-Facing Application
    ],
    "Benign": [],
}


THREAT_ACTOR_PROFILES = {
    "SideWinder": {
        "aliases": ["APT-C-17"],
        "targets": ["Defence", "Navy", "Finance Ministry"],
        "techniques": ["T1566.001", "T1204.002", "T1059.005"],
        "description": "India-focused APT group targeting defence and government sectors"
    },
    "Lazarus Group": {
        "aliases": ["APT38", "Hidden Cobra"],
        "targets": ["BFSI", "Crypto"],
        "techniques": ["T1190", "T1133", "T1486"],
        "description": "North Korean state-sponsored group targeting financial institutions"
    },
    "Bitter": {
        "aliases": ["APT-C-08"],
        "targets": ["Defence"],
        "techniques": ["T1476", "T1444", "T1516"],
        "description": "Pakistan-based APT group targeting defence organizations"
    },
    "SilverTerrier": {
        "name": "SilverTerrier",
        "alias": None,
        "aliases": None,
        "targets": ["Indian corporates", "BEC victims", "Financial services"],
        "techniques": ["T1566.002", "T1078", "T1071", "T1036"],
        "mitre_techniques": ["T1566.002", "T1078", "T1071", "T1036"],
        "primary_ttps": "Business email compromise, banking trojans, spear-phishing",
        "description": (
            "Nigerian BEC threat group — a Nigerian threat actor targeting Indian corporates "
            "and financial institutions via Business Email Compromise. "
            "Deploys banking trojans via spear-phishing. Active since 2014."
        ),
        "region": "India",
        "threat_level": "HIGH"
    },
    "REvil Affiliates": {
        "name": "REvil Affiliates",
        "alias": "Sodinokibi",
        "aliases": "Sodinokibi",
        "targets": ["Indian SME infrastructure", "Manufacturing", "Healthcare"],
        "techniques": ["T1486", "T1490", "T1489", "T1059"],
        "mitre_techniques": ["T1486", "T1490", "T1489", "T1059"],
        "primary_ttps": "Ransomware-as-a-service, double extortion, RDP exploitation",
        "description": (
            "REvil (Sodinokibi) RaaS affiliates targeting Indian SME infrastructure "
            "for ransomware deployment and double extortion. "
            "Exploits unpatched RDP and phishing for initial access."
        ),
        "region": "India",
        "threat_level": "CRITICAL"
    },
}


def get_mitre_techniques(category: str) -> List[str]:
    """Get MITRE ATT&CK techniques for a threat category"""
    return CATEGORY_TO_MITRE.get(category, [])


def map_category_to_mitre(category: str) -> List[str]:
    """Map Kebos threat category to MITRE techniques"""
    return get_mitre_techniques(category)


def get_threat_actor_profile(actor_name: str) -> Dict:
    """Get threat actor profile by name"""
    return THREAT_ACTOR_PROFILES.get(actor_name, {})


def get_all_threat_actors() -> Dict[str, Dict]:
    """Get all threat actor profiles"""
    return THREAT_ACTOR_PROFILES
