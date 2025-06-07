#!/usr/bin/env python3

import subprocess
import logging

logger = logging.getLogger(__name__)

def get_power_status(hostname, username, password, ipmitool_path='ipmitool'):
    """Check the power status of a host via IPMI"""
    try:
        cmd = [
            ipmitool_path, '-I', 'lanplus', 
            '-H', hostname,
            '-U', username,
            '-P', password,
            'chassis', 'power', 'status'
        ]
        
        logger.info(f"Checking power status for {hostname}")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            output = result.stdout.strip()
            if 'Chassis Power is on' in output:
                logger.info(f"{hostname}: Power is ON")
                return 'on'
            elif 'Chassis Power is off' in output:
                logger.info(f"{hostname}: Power is OFF")
                return 'off'
            else:
                logger.warning(f"{hostname}: Unknown power status: {output}")
                return 'unknown'
        else:
            logger.error(f"IPMI command failed for {hostname}: {result.stderr}")
            return 'error'
            
    except subprocess.TimeoutExpired:
        logger.error(f"IPMI timeout for {hostname}")
        return 'timeout'
    except FileNotFoundError:
        logger.error(f"ipmitool not found at path: {ipmitool_path}")
        return 'error'
    except Exception as e:
        logger.error(f"Error checking power status for {hostname}: {e}")
        return 'error'

def power_on_host(hostname, username, password, ipmitool_path='ipmitool'):
    """Power on a host via IPMI"""
    try:
        cmd = [
            ipmitool_path, '-I', 'lanplus', 
            '-H', hostname,
            '-U', username,
            '-P', password,
            'chassis', 'power', 'on'
        ]
        
        logger.info(f"Powering on {hostname}")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        
        if result.returncode == 0:
            logger.info(f"{hostname}: Power on command successful")
            return {'success': True, 'message': 'Power on command sent successfully'}
        else:
            logger.error(f"Power on command failed for {hostname}: {result.stderr}")
            return {'success': False, 'message': f'Power on failed: {result.stderr}'}
            
    except subprocess.TimeoutExpired:
        logger.error(f"Power on timeout for {hostname}")
        return {'success': False, 'message': 'Command timeout'}
    except FileNotFoundError:
        logger.error(f"ipmitool not found at path: {ipmitool_path}")
        return {'success': False, 'message': 'ipmitool not found'}
    except Exception as e:
        logger.error(f"Error powering on {hostname}: {e}")
        return {'success': False, 'message': f'Error: {str(e)}'}