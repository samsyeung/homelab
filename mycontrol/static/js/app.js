// Initialize page
document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('timestamp').textContent = new Date().toLocaleString();
    initializeRefreshTimer();
    loadUptimes();
    loadPingStatus();
});

// Auto-refresh management
let refreshTimeout;
let currentRefreshInterval;

function initializeRefreshTimer() {
    // Get initial refresh interval from template
    currentRefreshInterval = window.initialRefreshInterval || 30;
    
    // Load saved preference on page load
    const savedInterval = localStorage.getItem('refreshInterval');
    if (savedInterval !== null) {
        const select = document.getElementById('refresh-interval');
        if (select) {
            select.value = savedInterval;
            currentRefreshInterval = parseInt(savedInterval);
        }
    }
    
    // Start initial refresh timer
    startRefreshTimer(currentRefreshInterval);
}

function startRefreshTimer(interval) {
    if (refreshTimeout) {
        clearTimeout(refreshTimeout);
    }
    if (interval > 0) {
        refreshTimeout = setTimeout(function() {
            window.location.reload();
        }, interval * 1000);
    }
}

function updateRefreshInterval() {
    const select = document.getElementById('refresh-interval');
    const newInterval = parseInt(select.value);
    currentRefreshInterval = newInterval;
    
    // Store the preference in localStorage
    localStorage.setItem('refreshInterval', newInterval);
    
    // Start new timer with selected interval
    startRefreshTimer(newInterval);
}

function powerOnHost(hostname, button) {
    // Disable button and show loading state
    button.disabled = true;
    button.textContent = 'Powering On...';
    
    fetch('/api/power-on/' + encodeURIComponent(hostname), {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            button.textContent = 'Power On Sent';
            button.style.backgroundColor = '#007bff';
            // Refresh page after 3 seconds to show updated status
            setTimeout(() => {
                window.location.reload();
            }, 3000);
        } else {
            button.textContent = 'Failed';
            button.style.backgroundColor = '#dc3545';
            // Re-enable after 3 seconds
            setTimeout(() => {
                button.disabled = false;
                button.textContent = 'Power On';
                button.style.backgroundColor = '#28a745';
            }, 3000);
            console.error('Power on failed:', data.message);
        }
    })
    .catch(error => {
        button.textContent = 'Error';
        button.style.backgroundColor = '#dc3545';
        // Re-enable after 3 seconds
        setTimeout(() => {
            button.disabled = false;
            button.textContent = 'Power On';
            button.style.backgroundColor = '#28a745';
        }, 3000);
        console.error('Error:', error);
    });
}

function openSSHTerminal(hostname, button) {
    // Disable button and show loading state
    button.disabled = true;
    button.textContent = 'Starting Terminal...';
    
    // Open window immediately to avoid popup blockers (especially Safari)
    const terminalWindow = window.open('about:blank', '_blank');
    
    // Show loading message in the new window
    if (terminalWindow) {
        terminalWindow.document.write(`
            <html>
                <head><title>Starting SSH Terminal...</title></head>
                <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
                    <h2>Starting SSH Terminal</h2>
                    <p>Please wait while we establish the connection...</p>
                    <div style="margin: 20px;">⏳</div>
                </body>
            </html>
        `);
    }
    
    fetch('/api/ssh-terminal/' + encodeURIComponent(hostname), {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            button.textContent = 'Terminal Started';
            button.style.backgroundColor = '#28a745';
            
            // Create a wrapper page with close button and terminal iframe
            if (terminalWindow && !terminalWindow.closed) {
                const wrapperHtml = `
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <title>SSH Terminal - ${hostname}</title>
                        <style>
                            body { margin: 0; padding: 0; overflow: hidden; font-family: Arial, sans-serif; }
                            .terminal-header { 
                                background: #343a40; 
                                color: white; 
                                padding: 8px 15px; 
                                display: flex; 
                                justify-content: space-between; 
                                align-items: center;
                                border-bottom: 1px solid #495057;
                            }
                            .terminal-title { font-size: 14px; font-weight: 500; }
                            .close-btn { 
                                background: #dc3545; 
                                color: white; 
                                border: none; 
                                padding: 6px 12px; 
                                border-radius: 4px; 
                                cursor: pointer; 
                                font-size: 12px;
                                font-weight: 500;
                            }
                            .close-btn:hover { background: #c82333; }
                            .terminal-frame { 
                                width: 100%; 
                                height: calc(100vh - 45px); 
                                border: none; 
                                display: block;
                            }
                        </style>
                    </head>
                    <body>
                        <div class="terminal-header">
                            <div class="terminal-title">SSH Terminal - ${hostname}</div>
                            <button class="close-btn" onclick="window.close()">✕ Close</button>
                        </div>
                        <iframe class="terminal-frame" src="${data.terminal_url}"></iframe>
                    </body>
                    </html>
                `;
                
                terminalWindow.document.open();
                terminalWindow.document.write(wrapperHtml);
                terminalWindow.document.close();
            } else {
                // Fallback: try to open in current window if popup was blocked
                window.open(data.terminal_url, '_blank');
            }
            
            // Reset button after 3 seconds
            setTimeout(() => {
                button.disabled = false;
                button.textContent = 'SSH Terminal';
                button.style.backgroundColor = '#17a2b8';
            }, 3000);
        } else {
            button.textContent = 'Failed';
            button.style.backgroundColor = '#dc3545';
            
            // Close the loading window and show error
            if (terminalWindow && !terminalWindow.closed) {
                terminalWindow.close();
            }
            alert('Failed to start SSH terminal: ' + data.message);
            
            // Reset button after 3 seconds
            setTimeout(() => {
                button.disabled = false;
                button.textContent = 'SSH Terminal';
                button.style.backgroundColor = '#17a2b8';
            }, 3000);
            console.error('SSH terminal failed:', data.message);
        }
    })
    .catch(error => {
        button.textContent = 'Error';
        button.style.backgroundColor = '#dc3545';
        
        // Close the loading window and show error
        if (terminalWindow && !terminalWindow.closed) {
            terminalWindow.close();
        }
        alert('Error starting SSH terminal: ' + error.message);
        
        // Reset button after 3 seconds
        setTimeout(() => {
            button.disabled = false;
            button.textContent = 'SSH Terminal';
            button.style.backgroundColor = '#17a2b8';
        }, 3000);
        console.error('Error:', error);
    });
}

function toggleGpuInfo(hostname, button) {
    const gpuSection = document.getElementById('gpu-' + hostname);
    const gpuOutput = gpuSection.querySelector('.gpu-output');
    const gpuLoading = gpuSection.querySelector('.gpu-loading');
    
    if (gpuSection.style.display === 'none') {
        // Show GPU section
        gpuSection.style.display = 'block';
        button.textContent = 'Hide';
        button.classList.add('expanded');
        
        // Show loading state
        gpuLoading.style.display = 'block';
        gpuOutput.style.display = 'none';
        
        // Fetch GPU information
        fetch('/api/gpu-info/' + encodeURIComponent(hostname), {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            }
        })
        .then(response => response.json())
        .then(data => {
            gpuLoading.style.display = 'none';
            gpuOutput.style.display = 'block';
            
            if (data.success) {
                gpuOutput.textContent = data.output;
                gpuOutput.classList.remove('gpu-error');
            } else {
                gpuOutput.textContent = 'Error: ' + data.message;
                gpuOutput.classList.add('gpu-error');
            }
        })
        .catch(error => {
            gpuLoading.style.display = 'none';
            gpuOutput.style.display = 'block';
            gpuOutput.textContent = 'Error fetching GPU information: ' + error.message;
            gpuOutput.classList.add('gpu-error');
            console.error('Error:', error);
        });
    } else {
        // Hide GPU section
        gpuSection.style.display = 'none';
        button.textContent = 'nvidia-smi';
        button.classList.remove('expanded');
    }
}

function openNvtopTerminal(hostname, button) {
    // Disable button and show loading state
    button.disabled = true;
    button.textContent = 'Starting nvtop...';
    
    // Open window immediately to avoid popup blockers (especially Safari)
    const nvtopWindow = window.open('about:blank', '_blank');
    
    // Show loading message in the new window
    if (nvtopWindow) {
        nvtopWindow.document.write(`
            <html>
                <head><title>Starting nvtop...</title></head>
                <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
                    <h2>Starting nvtop Terminal</h2>
                    <p>Please wait while we establish the connection...</p>
                    <div style="margin: 20px;">⏳</div>
                </body>
            </html>
        `);
    }
    
    fetch('/api/nvtop-terminal/' + encodeURIComponent(hostname), {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            button.textContent = 'nvtop Started';
            button.style.backgroundColor = '#28a745';
            
            // Create a wrapper page with close button and nvtop iframe
            if (nvtopWindow && !nvtopWindow.closed) {
                const wrapperHtml = `
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <title>nvtop - ${hostname}</title>
                        <style>
                            body { margin: 0; padding: 0; overflow: hidden; font-family: Arial, sans-serif; }
                            .terminal-header { 
                                background: #343a40; 
                                color: white; 
                                padding: 8px 15px; 
                                display: flex; 
                                justify-content: space-between; 
                                align-items: center;
                                border-bottom: 1px solid #495057;
                            }
                            .terminal-title { font-size: 14px; font-weight: 500; }
                            .close-btn { 
                                background: #dc3545; 
                                color: white; 
                                border: none; 
                                padding: 6px 12px; 
                                border-radius: 4px; 
                                cursor: pointer; 
                                font-size: 12px;
                                font-weight: 500;
                            }
                            .close-btn:hover { background: #c82333; }
                            .terminal-frame { 
                                width: 100%; 
                                height: calc(100vh - 45px); 
                                border: none; 
                                display: block;
                            }
                        </style>
                    </head>
                    <body>
                        <div class="terminal-header">
                            <div class="terminal-title">nvtop - ${hostname} (Read-Only)</div>
                            <button class="close-btn" onclick="window.close()">✕ Close</button>
                        </div>
                        <iframe class="terminal-frame" src="${data.terminal_url}"></iframe>
                    </body>
                    </html>
                `;
                
                nvtopWindow.document.open();
                nvtopWindow.document.write(wrapperHtml);
                nvtopWindow.document.close();
            } else {
                // Fallback: try to open in current window if popup was blocked
                window.open(data.terminal_url, '_blank');
            }
            
            // Reset button after 3 seconds
            setTimeout(() => {
                button.disabled = false;
                button.textContent = 'nvtop';
                button.style.backgroundColor = '#17a2b8';
            }, 3000);
        } else {
            button.textContent = 'Failed';
            button.style.backgroundColor = '#dc3545';
            
            // Close the loading window and show error
            if (nvtopWindow && !nvtopWindow.closed) {
                nvtopWindow.close();
            }
            alert('Failed to start nvtop terminal: ' + data.message);
            
            // Reset button after 3 seconds
            setTimeout(() => {
                button.disabled = false;
                button.textContent = 'nvtop';
                button.style.backgroundColor = '#17a2b8';
            }, 3000);
            console.error('nvtop terminal failed:', data.message);
        }
    })
    .catch(error => {
        button.textContent = 'Error';
        button.style.backgroundColor = '#dc3545';
        
        // Close the loading window and show error
        if (nvtopWindow && !nvtopWindow.closed) {
            nvtopWindow.close();
        }
        alert('Error starting nvtop terminal: ' + error.message);
        
        // Reset button after 3 seconds
        setTimeout(() => {
            button.disabled = false;
            button.textContent = 'nvtop';
            button.style.backgroundColor = '#17a2b8';
        }, 3000);
        console.error('Error:', error);
    });
}

function loadUptimes() {
    // Find all uptime elements and load them asynchronously
    const uptimeElements = document.querySelectorAll('.uptime');
    
    // Create array of promises for parallel execution
    const uptimePromises = Array.from(uptimeElements).map(uptimeDiv => {
        const hostCard = uptimeDiv.closest('.host-card');
        const hostname = hostCard.querySelector('.host-hostname').textContent.trim();
        
        // Skip if already loaded or if showing an error
        const currentText = uptimeDiv.textContent;
        if (!currentText.includes('Loading...')) {
            return Promise.resolve();
        }
        
        // Fetch uptime for this host
        return fetch(`/api/uptime/${encodeURIComponent(hostname)}`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    uptimeDiv.innerHTML = `<strong>Uptime:</strong> ${data.uptime}`;
                } else {
                    uptimeDiv.innerHTML = `<strong>Uptime:</strong> ${data.uptime}`;
                }
            })
            .catch(error => {
                console.error(`Error fetching uptime for ${hostname}:`, error);
                uptimeDiv.innerHTML = `<strong>Uptime:</strong> Error loading`;
            });
    });
    
    // Wait for all uptime requests to complete
    Promise.allSettled(uptimePromises).then(() => {
        console.log('All uptime information loaded');
    });
}

function loadPingStatus() {
    // Find all ping indicator elements and check connectivity
    const pingElements = document.querySelectorAll('.ping-indicator');
    
    // Create array of promises for parallel execution
    const pingPromises = Array.from(pingElements).map(pingDiv => {
        const hostCard = pingDiv.closest('.host-card');
        const hostname = hostCard.querySelector('.host-hostname').textContent.trim();
        const pingStatus = pingDiv.querySelector('.ping-status');
        
        // Fetch ping status for this host
        return fetch(`/api/ping/${encodeURIComponent(hostname)}`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    pingStatus.className = `ping-status ${data.status}`;
                    switch(data.status) {
                        case 'online':
                            pingStatus.textContent = '● ONLINE';
                            break;
                        case 'offline':
                            pingStatus.textContent = '○ OFFLINE';
                            break;
                        case 'error':
                            pingStatus.textContent = '! ERROR';
                            break;
                        default:
                            pingStatus.textContent = '? UNKNOWN';
                    }
                } else {
                    pingStatus.className = 'ping-status error';
                    pingStatus.textContent = '! ERROR';
                }
            })
            .catch(error => {
                console.error(`Error checking ping for ${hostname}:`, error);
                pingStatus.className = 'ping-status error';
                pingStatus.textContent = '! ERROR';
            });
    });
    
    // Wait for all ping requests to complete
    Promise.allSettled(pingPromises).then(() => {
        console.log('All ping status information loaded');
    });
}