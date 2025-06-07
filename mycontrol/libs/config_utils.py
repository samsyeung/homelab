#!/usr/bin/env python3

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def load_config():
    """Load configuration from config.json"""
    config_path = Path(__file__).parent.parent / 'config.json'
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"Config file not found: {config_path}")
        return {}
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON in config file: {config_path}")
        return {}

def find_host_by_hostname(hosts, hostname):
    """Find a host configuration by hostname (IPMI or SSH)"""
    for host in hosts:
        if host.get('ipmi_host') == hostname or host.get('ssh_host') == hostname:
            return host
    return None