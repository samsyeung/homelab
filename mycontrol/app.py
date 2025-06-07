#!/usr/bin/env python3

from flask import Flask, render_template, jsonify
import subprocess
import json
import logging
import os
import signal
import time
from pathlib import Path
from logging.handlers import RotatingFileHandler
from libs.ssh_utils import get_host_uptimes
from libs.grafana_utils import process_dashboards
from libs.power_management import get_power_status, power_on_host
from libs.network_utils import check_host_ping
from libs.gpu_management import get_gpu_info_sync
from libs.terminal_management import TerminalManager
from libs.config_utils import load_config, find_host_by_hostname

class DeduplicatingHandler(logging.Handler):
    """A logging handler that prevents duplicate log messages"""
    
    def __init__(self, target_handler):
        super().__init__()
        self.target_handler = target_handler
        self.recent_messages = {}
        self.max_age = 1.0  # Consider messages within 1 second as duplicates
        
    def emit(self, record):
        import time
        current_time = time.time()
        message_key = (record.levelno, record.getMessage())
        
        # Clean old messages
        self.recent_messages = {
            k: v for k, v in self.recent_messages.items() 
            if current_time - v < self.max_age
        }
        
        # Check if this is a duplicate
        if message_key not in self.recent_messages:
            self.recent_messages[message_key] = current_time
            self.target_handler.emit(record)
    
    def setFormatter(self, formatter):
        self.target_handler.setFormatter(formatter)
        
    def setLevel(self, level):
        super().setLevel(level)
        self.target_handler.setLevel(level)

app = Flask(__name__)

def setup_logging():
    logs_dir = Path(__file__).parent / 'logs'
    logs_dir.mkdir(exist_ok=True)
    
    log_file = logs_dir / 'mycontrol.log'
    
    # Disable all existing logging completely
    logging.disable(logging.NOTSET)  # Re-enable logging
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    
    # Clear all loggers
    for logger_name in list(logging.Logger.manager.loggerDict.keys()):
        logger = logging.getLogger(logger_name)
        logger.handlers.clear()
        logger.disabled = True
    
    # Create file handler
    file_handler = RotatingFileHandler(
        log_file, 
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s'))
    
    # Configure Flask app logger
    app.logger.handlers.clear()
    app.logger.addHandler(file_handler)
    
    # Add console handler only if running interactively (not via control script)
    if os.getenv('MYCONTROL_INTERACTIVE', '').lower() == 'true':
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s'))
        app.logger.addHandler(console_handler)
    
    app.logger.setLevel(logging.INFO)
    app.logger.propagate = False  # Critical: don't propagate
    app.logger.disabled = False
    
    # Disable werkzeug logging completely
    logging.getLogger('werkzeug').disabled = True

logger = setup_logging()


# Initialize terminal manager (will be updated with config values)
terminal_manager = None

def get_terminal_manager():
    """Get terminal manager instance with current config"""
    global terminal_manager
    if terminal_manager is None:
        config = load_config()
        ttyd_base_port = config.get('ttyd_base_port', 7681)
        terminal_manager = TerminalManager(ttyd_base_port)
    return terminal_manager


@app.route('/')
def index():
    config = load_config()
    hosts = config.get('hosts', [])
    ipmitool_path = config.get('ipmitool_path', 'ipmitool')
    ssh_timeout = config.get('ssh_timeout', 10)
    grafana_dashboards = config.get('grafana_dashboard_urls', [])
    
    # Process Grafana dashboards
    updated_dashboards = process_dashboards(grafana_dashboards)
    
    # Build host status list (without SSH uptime initially for faster page load)
    host_status = []
    for host in hosts:
        ipmi_host = host.get('ipmi_host')
        ipmi_username = host.get('ipmi_username')
        ipmi_password = host.get('ipmi_password')
        ssh_host = host.get('ssh_host')
        name = host.get('name', ipmi_host or ssh_host)
        
        # Get power status only (fast IPMI check)
        if ipmi_host and ipmi_username and ipmi_password:
            power_status = get_power_status(ipmi_host, ipmi_username, ipmi_password, ipmitool_path)
        else:
            power_status = 'config_error'
        
        host_status.append({
            'name': name,
            'hostname': ipmi_host or ssh_host,
            'status': power_status,
            'uptime': 'Loading...',  # Will be updated via AJAX
            'ssh_host': ssh_host  # Include for client-side uptime fetching
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

@app.route('/api/uptime/<hostname>')
def get_uptime(hostname):
    """Get uptime for a specific host via SSH"""
    config = load_config()
    hosts = config.get('hosts', [])
    ssh_timeout = config.get('ssh_timeout', 10)
    
    # Find the host in config
    target_host = find_host_by_hostname(hosts, hostname)
    
    if not target_host:
        return jsonify({'success': False, 'uptime': 'Host not found'})
    
    ssh_host = target_host.get('ssh_host')
    ssh_username = target_host.get('ssh_username')
    ssh_password = target_host.get('ssh_password')
    
    if not ssh_host or not ssh_username:
        return jsonify({'success': False, 'uptime': 'No SSH config'})
    
    # Get uptime using the existing SSH utility
    from libs.ssh_utils import get_uptime_sync
    uptime = get_uptime_sync(ssh_host, ssh_username, ssh_password, ssh_timeout)
    
    return jsonify({'success': True, 'uptime': uptime})

@app.route('/api/ping/<hostname>')
def check_ping(hostname):
    """Check if a host is reachable via ping"""
    config = load_config()
    hosts = config.get('hosts', [])
    
    # Find the host in config
    target_host = find_host_by_hostname(hosts, hostname)
    
    if not target_host:
        return jsonify({'success': False, 'status': 'error', 'message': 'Host not found'})
    
    # Use SSH host if available, otherwise use IPMI host
    ping_target = target_host.get('ssh_host') or target_host.get('ipmi_host')
    
    if not ping_target:
        return jsonify({'success': False, 'status': 'error', 'message': 'No host address configured'})
    
    result = check_host_ping(ping_target)
    return jsonify(result)

@app.route('/api/power-on/<hostname>', methods=['POST'])
def api_power_on(hostname):
    config = load_config()
    hosts = config.get('hosts', [])
    ipmitool_path = config.get('ipmitool_path', 'ipmitool')
    
    # Find the host in config
    target_host = find_host_by_hostname(hosts, hostname)
    
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

@app.route('/api/ssh-terminal/<hostname>', methods=['POST'])
def start_ssh_terminal(hostname):
    """Start a ttyd SSH terminal for the specified host"""
    config = load_config()
    hosts = config.get('hosts', [])
    
    # Find the host in config
    target_host = find_host_by_hostname(hosts, hostname)
    
    if not target_host:
        return jsonify({'success': False, 'message': 'Host not found in configuration'}), 404
    
    ssh_host = target_host.get('ssh_host')
    if not ssh_host:
        return jsonify({'success': False, 'message': 'No SSH host configured for this server'}), 400
    
    result = get_terminal_manager().start_ssh_terminal(hostname, ssh_host)
    
    if result['success']:
        return jsonify(result), 200
    else:
        return jsonify(result), 500

@app.route('/api/ssh-terminals')
def list_ssh_terminals():
    """List active SSH terminals"""
    terminals = get_terminal_manager().list_ssh_terminals()
    return jsonify({'terminals': terminals})

@app.route('/api/gpu-info/<hostname>')
def get_gpu_info(hostname):
    """Get GPU information via SSH by running nvidia-smi"""
    config = load_config()
    hosts = config.get('hosts', [])
    ssh_timeout = config.get('ssh_timeout', 10)
    
    # Find the host in config
    target_host = find_host_by_hostname(hosts, hostname)
    
    if not target_host:
        return jsonify({'success': False, 'message': 'Host not found in configuration'}), 404
    
    ssh_host = target_host.get('ssh_host')
    ssh_username = target_host.get('ssh_username')
    ssh_password = target_host.get('ssh_password')
    
    if not ssh_host:
        return jsonify({'success': False, 'message': 'No SSH host configured for this server'}), 400
    
    if not ssh_username:
        return jsonify({'success': False, 'message': 'No SSH username configured for this server'}), 400
    
    result = get_gpu_info_sync(ssh_host, ssh_username, ssh_password, ssh_timeout)
    return jsonify(result)

@app.route('/api/nvtop-terminal/<hostname>', methods=['POST'])
def start_nvtop_terminal(hostname):
    """Start a ttyd nvtop terminal for the specified host"""
    config = load_config()
    hosts = config.get('hosts', [])
    
    # Find the host in config
    target_host = find_host_by_hostname(hosts, hostname)
    
    if not target_host:
        return jsonify({'success': False, 'message': 'Host not found in configuration'}), 404
    
    ssh_host = target_host.get('ssh_host')
    ssh_username = target_host.get('ssh_username')
    ssh_password = target_host.get('ssh_password')
    
    if not ssh_host or not ssh_username:
        return jsonify({'success': False, 'message': 'SSH configuration missing for this server'}), 400
    
    result = get_terminal_manager().start_nvtop_terminal(hostname, ssh_host, ssh_username, ssh_password)
    
    if result['success']:
        return jsonify(result), 200
    else:
        return jsonify(result), 500

@app.route('/api/nvtop-terminals')
def list_nvtop_terminals():
    """List active nvtop terminals"""
    terminals = get_terminal_manager().list_nvtop_terminals()
    return jsonify({'terminals': terminals})

@app.route('/api/nvtop-stop/<hostname>', methods=['POST'])
def stop_nvtop_terminal(hostname):
    """Stop nvtop terminal for a specific host"""
    result = get_terminal_manager().stop_nvtop_terminal(hostname)
    return jsonify(result)

if __name__ == '__main__':
    config = load_config()
    port = config.get('port', 5010)
    
    app.logger.info(f"Starting MyControl application on port {port}")
    app.run(debug=False, host='0.0.0.0', port=port)