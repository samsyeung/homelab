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
from utils.ssh_utils import get_host_uptimes
from utils.grafana_utils import process_dashboards

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


def load_config():
    config_path = Path(__file__).parent / 'config.json'
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        app.logger.error(f"Config file not found: {config_path}")
        return {}
    except json.JSONDecodeError:
        app.logger.error(f"Invalid JSON in config file: {config_path}")
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

# Global dict to track ttyd processes
ttyd_processes = {}

@app.route('/api/ssh-terminal/<hostname>', methods=['POST'])
def start_ssh_terminal(hostname):
    """Start a ttyd SSH terminal for the specified host"""
    config = load_config()
    hosts = config.get('hosts', [])
    ttyd_base_port = config.get('ttyd_base_port', 7681)
    
    # Find the host in config
    target_host = None
    for host in hosts:
        if host.get('ipmi_host') == hostname or host.get('ssh_host') == hostname:
            target_host = host
            break
    
    if not target_host:
        return jsonify({'success': False, 'message': 'Host not found in configuration'}), 404
    
    ssh_host = target_host.get('ssh_host')
    if not ssh_host:
        return jsonify({'success': False, 'message': 'No SSH host configured for this server'}), 400
    
    # Check if ttyd is available
    try:
        subprocess.run(['ttyd', '--version'], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return jsonify({'success': False, 'message': 'ttyd not installed. Please install ttyd to use SSH terminals.'}), 500
    
    # Generate a unique port for this terminal session
    terminal_port = ttyd_base_port + hash(hostname) % 1000
    
    # Kill any existing ttyd process for this host
    if hostname in ttyd_processes:
        try:
            os.kill(ttyd_processes[hostname]['pid'], signal.SIGTERM)
            time.sleep(0.5)  # Give it time to shutdown
        except ProcessLookupError:
            pass  # Process already dead
    
    try:
        # Start ttyd with SSH to the target host
        # ttyd will prompt user for SSH credentials
        cmd = [
            'ttyd',
            '--port', str(terminal_port),
            '--interface', '127.0.0.1',  # Only bind to localhost for security
            '--once',  # Close after one client disconnects
            '--writable',  # Allow keyboard input
            'ssh', 
            '-o', 'StrictHostKeyChecking=no',
            '-o', 'UserKnownHostsFile=/dev/null',
            '-o', 'LogLevel=ERROR',
            ssh_host
        ]
        
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Store process info
        ttyd_processes[hostname] = {
            'pid': process.pid,
            'port': terminal_port,
            'host': ssh_host,
            'started': time.time()
        }
        
        # Give ttyd a moment to start up
        time.sleep(1)
        
        # Check if process is still running
        if process.poll() is not None:
            # Process died, get error output
            _, stderr = process.communicate()
            return jsonify({
                'success': False, 
                'message': f'Failed to start terminal: {stderr.decode()}'
            }), 500
        
        app.logger.info(f"Started SSH terminal for {hostname} on port {terminal_port}")
        
        return jsonify({
            'success': True,
            'terminal_url': f'http://localhost:{terminal_port}',
            'message': 'SSH terminal started successfully'
        }), 200
        
    except Exception as e:
        app.logger.error(f"Error starting SSH terminal for {hostname}: {e}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@app.route('/api/ssh-terminals')
def list_ssh_terminals():
    """List active SSH terminals"""
    active_terminals = []
    current_time = time.time()
    
    # Clean up dead processes
    for hostname in list(ttyd_processes.keys()):
        try:
            # Check if process is still alive
            os.kill(ttyd_processes[hostname]['pid'], 0)
            # Add to active list if it's been running for less than 1 hour
            if current_time - ttyd_processes[hostname]['started'] < 3600:
                active_terminals.append({
                    'hostname': hostname,
                    'port': ttyd_processes[hostname]['port'],
                    'host': ttyd_processes[hostname]['host'],
                    'url': f"http://localhost:{ttyd_processes[hostname]['port']}"
                })
        except ProcessLookupError:
            # Process is dead, remove it
            del ttyd_processes[hostname]
    
    return jsonify({'terminals': active_terminals})

@app.route('/api/gpu-info/<hostname>')
def get_gpu_info(hostname):
    """Get GPU information via SSH by running nvidia-smi"""
    config = load_config()
    hosts = config.get('hosts', [])
    ssh_timeout = config.get('ssh_timeout', 10)
    
    # Find the host in config
    target_host = None
    for host in hosts:
        if host.get('ipmi_host') == hostname or host.get('ssh_host') == hostname:
            target_host = host
            break
    
    if not target_host:
        return jsonify({'success': False, 'message': 'Host not found in configuration'}), 404
    
    ssh_host = target_host.get('ssh_host')
    ssh_username = target_host.get('ssh_username')
    ssh_password = target_host.get('ssh_password')
    
    if not ssh_host:
        return jsonify({'success': False, 'message': 'No SSH host configured for this server'}), 400
    
    if not ssh_username:
        return jsonify({'success': False, 'message': 'No SSH username configured for this server'}), 400
    
    try:
        import asyncio
        import asyncssh
        
        async def run_nvidia_smi():
            try:
                async with asyncssh.connect(
                    ssh_host,
                    username=ssh_username,
                    password=ssh_password,
                    known_hosts=None,
                    client_keys=None
                ) as conn:
                    result = await asyncio.wait_for(
                        conn.run('nvidia-smi', check=False),
                        timeout=15
                    )
                    
                    if result.exit_status == 0:
                        return {'success': True, 'output': result.stdout}
                    else:
                        # Command failed, could be no nvidia-smi installed
                        error_msg = result.stderr or 'nvidia-smi command failed'
                        return {'success': False, 'message': f'Command failed: {error_msg}'}
                        
            except asyncio.TimeoutError:
                return {'success': False, 'message': 'Command timed out'}
            except asyncssh.Error as e:
                return {'success': False, 'message': f'SSH connection failed: {str(e)}'}
            except Exception as e:
                return {'success': False, 'message': f'Unexpected error: {str(e)}'}
        
        # Run the async function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(run_nvidia_smi())
            return jsonify(result)
        finally:
            loop.close()
            
    except ImportError:
        return jsonify({'success': False, 'message': 'asyncssh module not available'}), 500
    except Exception as e:
        app.logger.error(f"Error getting GPU info for {hostname}: {e}")
        return jsonify({'success': False, 'message': f'Server error: {str(e)}'}), 500

# Global dict to track nvtop processes
nvtop_processes = {}

@app.route('/api/nvtop-stream/<hostname>')
def nvtop_stream(hostname):
    """Stream nvtop output via Server-Sent Events"""
    config = load_config()
    hosts = config.get('hosts', [])
    
    # Find the host in config
    target_host = None
    for host in hosts:
        if host.get('ipmi_host') == hostname or host.get('ssh_host') == hostname:
            target_host = host
            break
    
    if not target_host:
        return "data: " + json.dumps({"type": "error", "message": "Host not found"}) + "\n\n"
    
    ssh_host = target_host.get('ssh_host')
    ssh_username = target_host.get('ssh_username')
    ssh_password = target_host.get('ssh_password')
    
    if not ssh_host or not ssh_username:
        return "data: " + json.dumps({"type": "error", "message": "SSH configuration missing"}) + "\n\n"
    
    def generate():
        import subprocess
        import select
        import os
        import signal
        
        try:
            # Start SSH connection with nvtop
            ssh_cmd = [
                'ssh',
                '-o', 'StrictHostKeyChecking=no',
                '-o', 'UserKnownHostsFile=/dev/null',
                '-o', 'LogLevel=ERROR',
                f'{ssh_username}@{ssh_host}',
                'nvtop', '--color=never'  # Disable colors for clean output
            ]
            
            # Use sshpass if password is provided
            if ssh_password:
                ssh_cmd = ['sshpass', '-p', ssh_password] + ssh_cmd
            
            process = subprocess.Popen(
                ssh_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                bufsize=0
            )
            
            # Store process for cleanup
            nvtop_processes[hostname] = process
            
            yield "data: " + json.dumps({"type": "status", "message": "Connected"}) + "\n\n"
            
            # Read output in real-time
            while True:
                # Check if process is still running
                if process.poll() is not None:
                    break
                
                # Use select to check for available data
                ready, _, _ = select.select([process.stdout], [], [], 1.0)
                
                if ready:
                    output = process.stdout.read(1024)
                    if output:
                        yield "data: " + json.dumps({"type": "output", "content": output}) + "\n\n"
                else:
                    # Send keepalive
                    yield "data: " + json.dumps({"type": "keepalive"}) + "\n\n"
                
                # Check if client disconnected
                if hostname not in nvtop_processes:
                    break
            
        except FileNotFoundError:
            yield "data: " + json.dumps({"type": "error", "message": "sshpass not found. Please install sshpass for password authentication."}) + "\n\n"
        except Exception as e:
            yield "data: " + json.dumps({"type": "error", "message": str(e)}) + "\n\n"
        finally:
            # Cleanup
            if hostname in nvtop_processes:
                try:
                    nvtop_processes[hostname].terminate()
                    nvtop_processes[hostname].wait(timeout=5)
                except:
                    try:
                        nvtop_processes[hostname].kill()
                    except:
                        pass
                del nvtop_processes[hostname]
    
    return app.response_class(
        generate(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Access-Control-Allow-Origin': '*'
        }
    )

@app.route('/api/nvtop-stop/<hostname>', methods=['POST'])
def stop_nvtop(hostname):
    """Stop nvtop stream for a specific host"""
    if hostname in nvtop_processes:
        try:
            process = nvtop_processes[hostname]
            process.terminate()
            process.wait(timeout=5)
        except:
            try:
                process.kill()
            except:
                pass
        finally:
            del nvtop_processes[hostname]
        
        return jsonify({'success': True, 'message': 'nvtop stream stopped'})
    else:
        return jsonify({'success': False, 'message': 'No active nvtop stream found'})

if __name__ == '__main__':
    config = load_config()
    port = config.get('port', 5010)
    
    app.logger.info(f"Starting MyControl application on port {port}")
    app.run(debug=False, host='0.0.0.0', port=port)