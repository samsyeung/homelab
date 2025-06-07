#!/usr/bin/env python3

import subprocess
import os
import signal
import time
import tempfile
import stat
import logging

logger = logging.getLogger(__name__)

class TerminalManager:
    """Manages ttyd terminal processes"""
    
    def __init__(self, ttyd_base_port=7681):
        self.ttyd_base_port = ttyd_base_port
        self.ssh_processes = {}
        self.nvtop_processes = {}
    
    def _check_ttyd_available(self):
        """Check if ttyd is available"""
        try:
            subprocess.run(['ttyd', '--version'], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def _kill_existing_process(self, hostname, process_dict):
        """Kill any existing process for a hostname"""
        if hostname in process_dict:
            try:
                os.kill(process_dict[hostname]['pid'], signal.SIGTERM)
                time.sleep(0.5)  # Give it time to shutdown
            except ProcessLookupError:
                pass  # Process already dead
    
    def start_ssh_terminal(self, hostname, ssh_host):
        """Start a ttyd SSH terminal"""
        if not self._check_ttyd_available():
            return {'success': False, 'message': 'ttyd not installed. Please install ttyd to use SSH terminals.'}
        
        # Generate a unique port for this terminal session
        terminal_port = self.ttyd_base_port + hash(hostname) % 1000
        
        # Kill any existing SSH process for this host
        self._kill_existing_process(hostname, self.ssh_processes)
        
        try:
            # Start ttyd with SSH to the target host
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
            self.ssh_processes[hostname] = {
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
                return {
                    'success': False, 
                    'message': f'Failed to start terminal: {stderr.decode()}'
                }
            
            logger.info(f"Started SSH terminal for {hostname} on port {terminal_port}")
            
            return {
                'success': True,
                'terminal_url': f'http://localhost:{terminal_port}',
                'message': 'SSH terminal started successfully'
            }
            
        except Exception as e:
            logger.error(f"Error starting SSH terminal for {hostname}: {e}")
            return {'success': False, 'message': f'Error: {str(e)}'}
    
    def start_nvtop_terminal(self, hostname, ssh_host, ssh_username, ssh_password=None):
        """Start a ttyd nvtop terminal"""
        if not self._check_ttyd_available():
            return {'success': False, 'message': 'ttyd not installed. Please install ttyd to use nvtop terminal.'}
        
        # Generate a unique port for this nvtop session
        nvtop_port = self.ttyd_base_port + hash(f"{hostname}_nvtop") % 1000
        
        # Kill any existing nvtop process for this host
        self._kill_existing_process(hostname, self.nvtop_processes)
        
        try:
            # Create SSH command with nvtop that uses config credentials
            if ssh_password:
                # Create a temporary script that handles SSH login with password
                with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
                    f.write(f'''#!/bin/bash
export SSHPASS='{ssh_password}'
sshpass -e ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=ERROR {ssh_username}@{ssh_host} nvtop
''')
                    script_path = f.name
                
                # Make script executable
                os.chmod(script_path, stat.S_IRWXU)
                
                # Start ttyd with the script
                ttyd_cmd = [
                    'ttyd',
                    '--port', str(nvtop_port),
                    '--interface', '127.0.0.1',  # Only bind to localhost for security
                    '--once',  # Close after one client disconnects
                    '--readonly',  # Make it read-only
                    '--title-format', f'nvtop - {hostname}',
                    'bash', script_path
                ]
            else:
                # Use key-based authentication
                ttyd_cmd = [
                    'ttyd',
                    '--port', str(nvtop_port),
                    '--interface', '127.0.0.1',  # Only bind to localhost for security
                    '--once',  # Close after one client disconnects
                    '--readonly',  # Make it read-only
                    '--title-format', f'nvtop - {hostname}',
                    'ssh',
                    '-o', 'StrictHostKeyChecking=no',
                    '-o', 'UserKnownHostsFile=/dev/null',
                    '-o', 'LogLevel=ERROR',
                    f'{ssh_username}@{ssh_host}',
                    'nvtop'
                ]
            
            process = subprocess.Popen(ttyd_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Store process info
            self.nvtop_processes[hostname] = {
                'pid': process.pid,
                'port': nvtop_port,
                'host': ssh_host,
                'started': time.time()
            }
            
            # Give ttyd a moment to start up
            time.sleep(1)
            
            # Check if process is still running
            if process.poll() is not None:
                # Process died, get error output
                _, stderr = process.communicate()
                return {
                    'success': False, 
                    'message': f'Failed to start nvtop terminal: {stderr.decode()}'
                }
            
            logger.info(f"Started nvtop terminal for {hostname} on port {nvtop_port}")
            
            return {
                'success': True,
                'terminal_url': f'http://localhost:{nvtop_port}',
                'message': 'nvtop terminal started successfully'
            }
            
        except Exception as e:
            logger.error(f"Error starting nvtop terminal for {hostname}: {e}")
            return {'success': False, 'message': f'Error: {str(e)}'}
    
    def list_ssh_terminals(self):
        """List active SSH terminals"""
        return self._list_terminals(self.ssh_processes)
    
    def list_nvtop_terminals(self):
        """List active nvtop terminals"""
        return self._list_terminals(self.nvtop_processes)
    
    def _list_terminals(self, process_dict):
        """List active terminals for a given process dictionary"""
        active_terminals = []
        current_time = time.time()
        
        # Clean up dead processes
        for hostname in list(process_dict.keys()):
            try:
                # Check if process is still alive
                os.kill(process_dict[hostname]['pid'], 0)
                # Add to active list if it's been running for less than 1 hour
                if current_time - process_dict[hostname]['started'] < 3600:
                    active_terminals.append({
                        'hostname': hostname,
                        'port': process_dict[hostname]['port'],
                        'host': process_dict[hostname]['host'],
                        'url': f"http://localhost:{process_dict[hostname]['port']}"
                    })
            except ProcessLookupError:
                # Process is dead, remove it
                del process_dict[hostname]
        
        return active_terminals
    
    def stop_ssh_terminal(self, hostname):
        """Stop SSH terminal for a specific host"""
        return self._stop_terminal(hostname, self.ssh_processes, 'SSH terminal')
    
    def stop_nvtop_terminal(self, hostname):
        """Stop nvtop terminal for a specific host"""
        return self._stop_terminal(hostname, self.nvtop_processes, 'nvtop terminal')
    
    def _stop_terminal(self, hostname, process_dict, terminal_type):
        """Stop a terminal for a specific host"""
        if hostname in process_dict:
            try:
                os.kill(process_dict[hostname]['pid'], signal.SIGTERM)
                del process_dict[hostname]
                return {'success': True, 'message': f'{terminal_type} stopped'}
            except ProcessLookupError:
                del process_dict[hostname]
                return {'success': True, 'message': f'{terminal_type} was already stopped'}
        else:
            return {'success': False, 'message': f'No active {terminal_type} found'}