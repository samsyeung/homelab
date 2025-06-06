#!/usr/bin/env python3

from flask import Flask, render_template, jsonify
import subprocess
import json
import logging
import os
import time
import asyncio
import asyncssh
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from pathlib import Path
from logging.handlers import RotatingFileHandler

app = Flask(__name__)

def setup_logging():
    logs_dir = Path(__file__).parent / 'logs'
    logs_dir.mkdir(exist_ok=True)
    
    log_file = logs_dir / 'mycontrol.log'
    
    file_handler = RotatingFileHandler(
        log_file, 
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s'
    ))
    
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s'
    ))
    
    app.logger.addHandler(file_handler)
    app.logger.addHandler(console_handler)
    app.logger.setLevel(logging.INFO)
    
    # Also set up root logger for other modules
    logging.basicConfig(
        level=logging.INFO,
        handlers=[file_handler, console_handler],
        format='%(asctime)s %(levelname)s: %(message)s'
    )

setup_logging()

def update_grafana_time_params(url, minutes_ago=30):
    """
    Update Grafana URL time parameters to show data from X minutes ago to now.
    
    Args:
        url (str): The Grafana URL to update
        minutes_ago (int): How many minutes back to set the 'from' parameter
        
    Returns:
        str: Updated URL with new time parameters
    """
    if not url:
        return url
        
    now_ms = int(time.time() * 1000)
    from_ms = now_ms - (minutes_ago * 60 * 1000)
    
    # Parse the URL
    parsed = urlparse(url)
    query_params = parse_qs(parsed.query)
    
    # Update time parameters
    query_params['from'] = [str(from_ms)]
    query_params['to'] = [str(now_ms)]
    
    # Rebuild the URL
    new_query = urlencode(query_params, doseq=True)
    updated_url = urlunparse((
        parsed.scheme,
        parsed.netloc,
        parsed.path,
        parsed.params,
        new_query,
        parsed.fragment
    ))
    
    return updated_url

def load_config():
    config_path = Path(__file__).parent / 'config.json'
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logging.error(f"Config file not found: {config_path}")
        return {}
    except json.JSONDecodeError:
        logging.error(f"Invalid JSON in config file: {config_path}")
        return {}

def get_power_status(hostname, username, password, ipmitool_path='ipmitool'):
    try:
        cmd = [
            ipmitool_path, '-I', 'lanplus', 
            '-H', hostname,
            '-U', username,
            '-P', password,
            'chassis', 'power', 'status'
        ]
        
        app.logger.info(f"Checking power status for {hostname}")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            output = result.stdout.strip()
            if 'Chassis Power is on' in output:
                app.logger.info(f"{hostname}: Power is ON")
                return 'on'
            elif 'Chassis Power is off' in output:
                app.logger.info(f"{hostname}: Power is OFF")
                return 'off'
            else:
                app.logger.warning(f"{hostname}: Unknown power status: {output}")
                return 'unknown'
        else:
            app.logger.error(f"IPMI command failed for {hostname}: {result.stderr}")
            return 'error'
            
    except subprocess.TimeoutExpired:
        app.logger.error(f"IPMI timeout for {hostname}")
        return 'timeout'
    except FileNotFoundError:
        app.logger.error(f"ipmitool not found at path: {ipmitool_path}")
        return 'error'
    except Exception as e:
        app.logger.error(f"Error checking power status for {hostname}: {e}")
        return 'error'

def power_on_host(hostname, username, password, ipmitool_path='ipmitool'):
    try:
        cmd = [
            ipmitool_path, '-I', 'lanplus', 
            '-H', hostname,
            '-U', username,
            '-P', password,
            'chassis', 'power', 'on'
        ]
        
        app.logger.info(f"Powering on {hostname}")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        
        if result.returncode == 0:
            app.logger.info(f"{hostname}: Power on command successful")
            return {'success': True, 'message': 'Power on command sent successfully'}
        else:
            app.logger.error(f"Power on command failed for {hostname}: {result.stderr}")
            return {'success': False, 'message': f'Power on failed: {result.stderr}'}
            
    except subprocess.TimeoutExpired:
        app.logger.error(f"Power on timeout for {hostname}")
        return {'success': False, 'message': 'Command timeout'}
    except FileNotFoundError:
        app.logger.error(f"ipmitool not found at path: {ipmitool_path}")
        return {'success': False, 'message': 'ipmitool not found'}
    except Exception as e:
        app.logger.error(f"Error powering on {hostname}: {e}")
        return {'success': False, 'message': f'Error: {str(e)}'}

async def get_ssh_uptime(ssh_host, ssh_username, ssh_password, timeout=10):
    """Get uptime via SSH connection"""
    try:
        async with asyncssh.connect(
            ssh_host,
            username=ssh_username,
            password=ssh_password,
            known_hosts=None,
            client_keys=None
        ) as conn:
            result = await asyncio.wait_for(
                conn.run('uptime', check=True),
                timeout=timeout
            )
            return result.stdout.strip()
    except asyncio.TimeoutError:
        return 'SSH timeout'
    except asyncssh.Error as e:
        return f'SSH error: {str(e)}'
    except Exception as e:
        return f'Error: {str(e)}'

def get_uptime_sync(ssh_host, ssh_username, ssh_password, timeout=10):
    """Synchronous wrapper for async SSH uptime"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(
            get_ssh_uptime(ssh_host, ssh_username, ssh_password, timeout)
        )
    except Exception as e:
        return f'Error: {str(e)}'
    finally:
        loop.close()

@app.route('/')
def index():
    config = load_config()
    hosts = config.get('hosts', [])
    ipmitool_path = config.get('ipmitool_path', 'ipmitool')
    ssh_timeout = config.get('ssh_timeout', 10)
    grafana_dashboards = config.get('grafana_dashboard_urls', [])
    
    # Update Grafana URL time parameters for all dashboards
    updated_dashboards = []
    for dashboard in grafana_dashboards:
        updated_dashboard = {
            'name': dashboard.get('name'),
            'url': update_grafana_time_params(dashboard.get('url', '')),
            'height': dashboard.get('height', 400)
        }
        updated_dashboards.append(updated_dashboard)
    
    # Use ThreadPoolExecutor to run SSH commands in parallel
    with ThreadPoolExecutor(max_workers=len(hosts)) as executor:
        host_status = []
        futures = []
        
        for host in hosts:
            ipmi_host = host.get('ipmi_host')
            ipmi_username = host.get('ipmi_username')
            ipmi_password = host.get('ipmi_password')
            ssh_host = host.get('ssh_host')
            ssh_username = host.get('ssh_username')
            ssh_password = host.get('ssh_password')
            name = host.get('name', ipmi_host or ssh_host)
            
            # Get power status
            if ipmi_host and ipmi_username and ipmi_password:
                power_status = get_power_status(ipmi_host, ipmi_username, ipmi_password, ipmitool_path)
            else:
                power_status = 'config_error'
            
            # Submit SSH uptime task
            if ssh_host and ssh_username and ssh_password:
                uptime_future = executor.submit(get_uptime_sync, ssh_host, ssh_username, ssh_password, ssh_timeout)
            else:
                uptime_future = None
            
            futures.append((host, power_status, uptime_future))
        
        # Collect results
        for host, power_status, uptime_future in futures:
            ipmi_host = host.get('ipmi_host')
            ssh_host = host.get('ssh_host')
            name = host.get('name', ipmi_host or ssh_host)
            
            if uptime_future:
                try:
                    uptime = uptime_future.result(timeout=ssh_timeout + 1)
                except Exception as e:
                    uptime = f'Error: {str(e)}'
            else:
                uptime = 'No SSH config'
            
            host_status.append({
                'name': name,
                'hostname': ipmi_host or ssh_host,
                'status': power_status,
                'uptime': uptime
            })
    
    refresh_interval = config.get('refresh_interval', 30)
    
    return render_template('index.html', hosts=host_status, grafana_dashboards=updated_dashboards, refresh_interval=refresh_interval)

@app.route('/api/status')
def api_status():
    config = load_config()
    hosts = config.get('hosts', [])
    ipmitool_path = config.get('ipmitool_path', 'ipmitool')
    ssh_timeout = config.get('ssh_timeout', 10)
    
    # Use ThreadPoolExecutor to run SSH commands in parallel
    with ThreadPoolExecutor(max_workers=len(hosts)) as executor:
        host_status = []
        futures = []
        
        for host in hosts:
            ipmi_host = host.get('ipmi_host')
            ipmi_username = host.get('ipmi_username')
            ipmi_password = host.get('ipmi_password')
            ssh_host = host.get('ssh_host')
            ssh_username = host.get('ssh_username')
            ssh_password = host.get('ssh_password')
            name = host.get('name', ipmi_host or ssh_host)
            
            # Get power status
            if ipmi_host and ipmi_username and ipmi_password:
                power_status = get_power_status(ipmi_host, ipmi_username, ipmi_password, ipmitool_path)
            else:
                power_status = 'config_error'
            
            # Submit SSH uptime task
            if ssh_host and ssh_username and ssh_password:
                uptime_future = executor.submit(get_uptime_sync, ssh_host, ssh_username, ssh_password, ssh_timeout)
            else:
                uptime_future = None
            
            futures.append((host, power_status, uptime_future))
        
        # Collect results
        for host, power_status, uptime_future in futures:
            ipmi_host = host.get('ipmi_host')
            ssh_host = host.get('ssh_host')
            name = host.get('name', ipmi_host or ssh_host)
            
            if uptime_future:
                try:
                    uptime = uptime_future.result(timeout=ssh_timeout + 1)
                except Exception as e:
                    uptime = f'Error: {str(e)}'
            else:
                uptime = 'No SSH config'
            
            host_status.append({
                'name': name,
                'hostname': ipmi_host or ssh_host,
                'status': power_status,
                'uptime': uptime
            })
    
    return jsonify({'hosts': host_status})

@app.route('/api/power-on/<hostname>', methods=['POST'])
def api_power_on(hostname):
    config = load_config()
    hosts = config.get('hosts', [])
    ipmitool_path = config.get('ipmitool_path', 'ipmitool')
    
    # Find the host in config
    target_host = None
    for host in hosts:
        if host.get('ipmi_host') == hostname:
            target_host = host
            break
    
    if not target_host:
        return jsonify({'success': False, 'message': 'Host not found in configuration'}), 404
    
    # Extract credentials
    ipmi_username = target_host.get('ipmi_username')
    ipmi_password = target_host.get('ipmi_password')
    
    if not ipmi_username or not ipmi_password:
        return jsonify({'success': False, 'message': 'Missing credentials in configuration'}), 400
    
    # Attempt to power on
    result = power_on_host(hostname, ipmi_username, ipmi_password, ipmitool_path)
    
    if result['success']:
        return jsonify(result), 200
    else:
        return jsonify(result), 500

if __name__ == '__main__':
    config = load_config()
    port = config.get('port', 5010)
    
    app.logger.info(f"Starting MyControl application on port {port}")
    app.run(debug=False, host='0.0.0.0', port=port)