#!/usr/bin/env python3

from flask import Flask, render_template, jsonify
import subprocess
import json
import logging
import os
from pathlib import Path
from logging.handlers import RotatingFileHandler
from ssh_utils import get_host_uptimes
from grafana_utils import process_dashboards

app = Flask(__name__)

def setup_logging():
    logs_dir = Path(__file__).parent / 'logs'
    logs_dir.mkdir(exist_ok=True)
    
    log_file = logs_dir / 'mycontrol.log'
    
    # Create a custom formatter that prevents duplicates
    formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')
    
    # File handler
    file_handler = RotatingFileHandler(
        log_file, 
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(formatter)
    
    # Console handler  
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    # Clear ALL existing loggers to start fresh
    for logger_name in logging.Logger.manager.loggerDict:
        logger = logging.getLogger(logger_name)
        logger.handlers.clear()
        logger.propagate = True
    
    # Configure root logger only
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)  
    root_logger.setLevel(logging.INFO)
    
    # Make sure Flask app logger doesn't have its own handlers
    app.logger.handlers.clear()
    app.logger.propagate = True
    app.logger.setLevel(logging.INFO)
    
    # Quiet noisy loggers
    logging.getLogger('asyncssh').setLevel(logging.WARNING)
    logging.getLogger('werkzeug').setLevel(logging.WARNING)

setup_logging()


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


@app.route('/')
def index():
    config = load_config()
    hosts = config.get('hosts', [])
    ipmitool_path = config.get('ipmitool_path', 'ipmitool')
    ssh_timeout = config.get('ssh_timeout', 10)
    grafana_dashboards = config.get('grafana_dashboard_urls', [])
    
    # Process Grafana dashboards
    updated_dashboards = process_dashboards(grafana_dashboards)
    
    # Get SSH uptimes in parallel
    ssh_results = get_host_uptimes(hosts, ssh_timeout)
    
    # Build host status list
    host_status = []
    for (host, uptime) in ssh_results:
        ipmi_host = host.get('ipmi_host')
        ipmi_username = host.get('ipmi_username')
        ipmi_password = host.get('ipmi_password')
        ssh_host = host.get('ssh_host')
        name = host.get('name', ipmi_host or ssh_host)
        
        # Get power status
        if ipmi_host and ipmi_username and ipmi_password:
            power_status = get_power_status(ipmi_host, ipmi_username, ipmi_password, ipmitool_path)
        else:
            power_status = 'config_error'
        
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
    
    # Get SSH uptimes in parallel
    ssh_results = get_host_uptimes(hosts, ssh_timeout)
    
    # Build host status list
    host_status = []
    for (host, uptime) in ssh_results:
        ipmi_host = host.get('ipmi_host')
        ipmi_username = host.get('ipmi_username')
        ipmi_password = host.get('ipmi_password')
        ssh_host = host.get('ssh_host')
        name = host.get('name', ipmi_host or ssh_host)
        
        # Get power status
        if ipmi_host and ipmi_username and ipmi_password:
            power_status = get_power_status(ipmi_host, ipmi_username, ipmi_password, ipmitool_path)
        else:
            power_status = 'config_error'
        
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