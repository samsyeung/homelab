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