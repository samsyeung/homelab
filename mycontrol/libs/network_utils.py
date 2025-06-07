#!/usr/bin/env python3

import subprocess
import logging

logger = logging.getLogger(__name__)

def check_host_ping(hostname):
    """Check if a host is reachable via ping"""
    try:
        # Use ping command (works on both Linux and macOS)
        # -c 1: send only 1 packet
        # -W 3: timeout after 3 seconds
        cmd = ['ping', '-c', '1', '-W', '3', hostname]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        
        if result.returncode == 0:
            return {'success': True, 'status': 'online', 'message': 'Host is reachable'}
        else:
            return {'success': True, 'status': 'offline', 'message': 'Host is not reachable'}
            
    except subprocess.TimeoutExpired:
        return {'success': True, 'status': 'offline', 'message': 'Ping timeout'}
    except Exception as e:
        logger.error(f"Error pinging {hostname}: {e}")
        return {'success': False, 'status': 'error', 'message': f'Ping error: {str(e)}'}