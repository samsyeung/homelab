#!/usr/bin/env python3

from flask import Flask, render_template, jsonify
import subprocess
import json
import logging
import os
import time
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

@app.route('/')
def index():
    config = load_config()
    hosts = config.get('hosts', [])
    ipmitool_path = config.get('ipmitool_path', 'ipmitool')
    grafana_dashboards = config.get('grafana_dashboard_urls', [])
    
    # Update Grafana URL time parameters for all dashboards
    updated_dashboards = []
    for dashboard in grafana_dashboards:
        updated_dashboard = {
            'name': dashboard.get('name', 'Dashboard'),
            'url': update_grafana_time_params(dashboard.get('url', ''))
        }
        updated_dashboards.append(updated_dashboard)
    
    host_status = []
    for host in hosts:
        hostname = host.get('hostname')
        username = host.get('username')
        password = host.get('password')
        name = host.get('name', hostname)
        
        if hostname and username and password:
            status = get_power_status(hostname, username, password, ipmitool_path)
        else:
            status = 'config_error'
            
        host_status.append({
            'name': name,
            'hostname': hostname,
            'status': status
        })
    
    return render_template('index.html', hosts=host_status, grafana_dashboards=updated_dashboards)

@app.route('/api/status')
def api_status():
    config = load_config()
    hosts = config.get('hosts', [])
    ipmitool_path = config.get('ipmitool_path', 'ipmitool')
    
    host_status = []
    for host in hosts:
        hostname = host.get('hostname')
        username = host.get('username')
        password = host.get('password')
        name = host.get('name', hostname)
        
        if hostname and username and password:
            status = get_power_status(hostname, username, password, ipmitool_path)
        else:
            status = 'config_error'
            
        host_status.append({
            'name': name,
            'hostname': hostname,
            'status': status
        })
    
    return jsonify({'hosts': host_status})

if __name__ == '__main__':
    config = load_config()
    port = config.get('port', 5010)
    
    app.logger.info(f"Starting MyControl application on port {port}")
    app.run(debug=False, host='0.0.0.0', port=port)