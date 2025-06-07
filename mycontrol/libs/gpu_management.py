#!/usr/bin/env python3

import asyncio
import asyncssh
import logging

logger = logging.getLogger(__name__)

def get_gpu_info_sync(ssh_host, ssh_username, ssh_password, ssh_timeout=10):
    """Get GPU information via SSH by running nvidia-smi"""
    try:
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
            return result
        finally:
            loop.close()
            
    except ImportError:
        return {'success': False, 'message': 'asyncssh module not available'}
    except Exception as e:
        logger.error(f"Error getting GPU info for {ssh_host}: {e}")
        return {'success': False, 'message': f'Server error: {str(e)}'}

def get_gpu_topo_info_sync(ssh_host, ssh_username, ssh_password, ssh_timeout=10):
    """Get GPU topology information via SSH by running nvidia-smi topo -m"""
    try:
        async def run_nvidia_smi_topo():
            try:
                async with asyncssh.connect(
                    ssh_host,
                    username=ssh_username,
                    password=ssh_password,
                    known_hosts=None,
                    client_keys=None
                ) as conn:
                    result = await asyncio.wait_for(
                        conn.run('nvidia-smi topo -m', check=False),
                        timeout=15
                    )
                    
                    if result.exit_status == 0:
                        return {'success': True, 'output': result.stdout}
                    else:
                        # Command failed, could be no nvidia-smi installed or topo not supported
                        error_msg = result.stderr or 'nvidia-smi topo -m command failed'
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
            result = loop.run_until_complete(run_nvidia_smi_topo())
            return result
        finally:
            loop.close()
            
    except ImportError:
        return {'success': False, 'message': 'asyncssh module not available'}
    except Exception as e:
        logger.error(f"Error getting GPU topology info for {ssh_host}: {e}")
        return {'success': False, 'message': f'Server error: {str(e)}'}

def get_docker_info_sync(ssh_host, ssh_username, ssh_password, ssh_timeout=10):
    """Get Docker containers information via SSH by running docker ps -a"""
    try:
        async def run_docker_ps():
            try:
                async with asyncssh.connect(
                    ssh_host,
                    username=ssh_username,
                    password=ssh_password,
                    known_hosts=None,
                    client_keys=None
                ) as conn:
                    result = await asyncio.wait_for(
                        conn.run('docker ps -a --format json', check=False),
                        timeout=15
                    )
                    
                    if result.exit_status == 0:
                        return {'success': True, 'output': result.stdout}
                    else:
                        # Command failed, could be no docker installed or permission denied
                        error_msg = result.stderr or 'docker ps -a command failed'
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
            result = loop.run_until_complete(run_docker_ps())
            return result
        finally:
            loop.close()
            
    except ImportError:
        return {'success': False, 'message': 'asyncssh module not available'}
    except Exception as e:
        logger.error(f"Error getting Docker info for {ssh_host}: {e}")
        return {'success': False, 'message': f'Server error: {str(e)}'}

def parse_docker_output_to_html(docker_output, hostname):
    """Parse docker ps -a JSON output and convert to HTML table"""
    import json
    try:
        lines = docker_output.strip().split('\n')
        if not lines or (len(lines) == 1 and not lines[0].strip()):
            return '<div style="text-align: center; color: #666; padding: 20px;">No Docker containers found</div>'
        
        containers = []
        for line in lines:
            if line.strip():
                try:
                    container = json.loads(line)
                    containers.append(container)
                except json.JSONDecodeError:
                    continue
        
        if not containers:
            return '<div style="text-align: center; color: #666; padding: 20px;">No Docker containers found</div>'
        
        html = '<table class="docker-table">'
        html += '''
        <thead>
            <tr>
                <th>Container ID</th>
                <th>Name</th>
                <th>Image</th>
                <th>Status</th>
                <th>Ports</th>
                <th>Created</th>
                <th>Actions</th>
            </tr>
        </thead>
        <tbody>
        '''
        
        for container in containers:
            container_id = container.get('ID', '')[:12]  # Truncate to 12 chars
            name = container.get('Names', 'Unknown')
            image = container.get('Image', 'Unknown')
            status = container.get('Status', 'Unknown')
            ports = container.get('Ports', '') or '-'
            created = container.get('CreatedAt', 'Unknown')
            
            # Determine status class and available actions
            status_class = 'status-running'
            is_running = False
            if 'Up' in status:
                status_class = 'status-running'
                is_running = True
            elif 'Exited' in status:
                status_class = 'status-exited'
            elif 'Created' in status:
                status_class = 'status-created'
            elif 'Paused' in status:
                status_class = 'status-paused'
            
            # Generate action buttons based on container status
            actions = ''
            if is_running:
                actions = f'<button class="docker-action-btn docker-stop-btn" onclick="dockerAction(\'{hostname}\', \'{container_id}\', \'stop\', this)" title="Stop container">Stop</button>'
            else:
                actions = f'<button class="docker-action-btn docker-start-btn" onclick="dockerAction(\'{hostname}\', \'{container_id}\', \'start\', this)" title="Start container">Start</button>'
            
            html += f'''
            <tr>
                <td><code>{container_id}</code></td>
                <td><span class="container-name">{name}</span></td>
                <td>{image}</td>
                <td><span class="container-status {status_class}">{status}</span></td>
                <td><span class="container-ports">{ports}</span></td>
                <td>{created}</td>
                <td>{actions}</td>
            </tr>
            '''
        
        html += '</tbody></table>'
        return html
        
    except Exception as e:
        return f'<div class="gpu-error">Error parsing Docker output: {str(e)}</div>'

def docker_action_sync(ssh_host, ssh_username, ssh_password, container_id, action, ssh_timeout=10):
    """Perform Docker action (start/stop) on a container via SSH"""
    try:
        async def run_docker_action():
            try:
                async with asyncssh.connect(
                    ssh_host,
                    username=ssh_username,
                    password=ssh_password,
                    known_hosts=None,
                    client_keys=None
                ) as conn:
                    command = f'docker {action} {container_id}'
                    result = await asyncio.wait_for(
                        conn.run(command, check=False),
                        timeout=30  # Longer timeout for start/stop operations
                    )
                    
                    if result.exit_status == 0:
                        return {'success': True, 'message': f'Container {action} successful'}
                    else:
                        # Command failed
                        error_msg = result.stderr or f'docker {action} command failed'
                        return {'success': False, 'message': f'Command failed: {error_msg}'}
                        
            except asyncio.TimeoutError:
                return {'success': False, 'message': f'Docker {action} command timed out'}
            except asyncssh.Error as e:
                return {'success': False, 'message': f'SSH connection failed: {str(e)}'}
            except Exception as e:
                return {'success': False, 'message': f'Unexpected error: {str(e)}'}
        
        # Run the async function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(run_docker_action())
            return result
        finally:
            loop.close()
            
    except ImportError:
        return {'success': False, 'message': 'asyncssh module not available'}
    except Exception as e:
        logger.error(f"Error performing Docker {action} on {ssh_host}: {e}")
        return {'success': False, 'message': f'Server error: {str(e)}'}