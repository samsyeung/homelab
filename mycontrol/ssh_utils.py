#!/usr/bin/env python3

import asyncio
import asyncssh
from concurrent.futures import ThreadPoolExecutor
import logging

logger = logging.getLogger(__name__)

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

def get_host_uptimes(hosts, ssh_timeout=10):
    """Get uptime for multiple hosts in parallel"""
    if not hosts:
        return []
    
    with ThreadPoolExecutor(max_workers=len(hosts)) as executor:
        futures = []
        
        for host in hosts:
            ssh_host = host.get('ssh_host')
            ssh_username = host.get('ssh_username')
            ssh_password = host.get('ssh_password')
            
            if ssh_host and ssh_username and ssh_password:
                uptime_future = executor.submit(get_uptime_sync, ssh_host, ssh_username, ssh_password, ssh_timeout)
            else:
                uptime_future = None
            
            futures.append((host, uptime_future))
        
        # Collect results
        results = []
        for host, uptime_future in futures:
            if uptime_future:
                try:
                    uptime = uptime_future.result(timeout=ssh_timeout + 1)
                except Exception as e:
                    uptime = f'Error: {str(e)}'
            else:
                uptime = 'No SSH config'
            
            results.append((host, uptime))
        
        return results