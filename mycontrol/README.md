# MyControl - Host Power Status Monitor

A Flask web application for monitoring remote host power status via IPMI.

## Features

- Display power status of multiple remote hosts
- Display host uptime via SSH connections
- Power on hosts remotely via IPMI when they are powered off
- Query IPMI using lanplus protocol
- Asynchronous SSH connections for fast uptime retrieval
- Configuration via JSON file
- Configurable auto-refresh interval and SSH timeout
- Clean web interface with status indicators
- Automated startup script with virtual environment management
- Comprehensive logging with log rotation
- Background process management

## Setup

1. Use the control script (recommended):
```bash
./control.sh
```

2. Manual setup:
```bash
pip install -r requirements.txt
python app.py
```

## Configuration

Update `config.json` with your host details:
```json
{
  "port": 5010,
  "refresh_interval": 30,
  "ssh_timeout": 10,
  "ipmitool_path": "ipmitool",
  "grafana_dashboard_urls": [
    {
      "name": "GPU Usage",
      "url": "https://grafana.yeungs.net/d-solo/dashboard-id?panelId=20",
      "height": 300
    },
    {
      "url": "https://grafana.yeungs.net/d-solo/dashboard-id?panelId=21",
      "height": 200
    }
  ],
  "hosts": [
    {
      "name": "Server Name",
      "ipmi_host": "192.168.1.100",
      "ipmi_username": "ipmi_user",
      "ipmi_password": "ipmi_password",
      "ssh_host": "192.168.1.100",
      "ssh_username": "user",
      "ssh_password": "password"
    }
  ]
}
```

### Configuration Options

- `port`: Web server listening port (default: 5010)
- `refresh_interval`: Auto-refresh interval in seconds (default: 30)
- `ssh_timeout`: SSH connection timeout in seconds (default: 10)
- `ipmitool_path`: Path to ipmitool binary (default: "ipmitool")
- `grafana_dashboard_urls`: Array of Grafana dashboard configurations (optional)
  - `name`: Display name for the dashboard (optional - if omitted, no header is shown)
  - `url`: URL to Grafana dashboard panel
  - `height`: Height of the iframe in pixels (default: 400)
- `hosts`: Array of host configurations
  - `name`: Display name for the host
  - `ipmi_host`: IPMI hostname or IP address (optional)
  - `ipmi_username`: IPMI username (optional)
  - `ipmi_password`: IPMI password (optional)
  - `ssh_host`: SSH hostname or IP address (optional)
  - `ssh_username`: SSH username (optional)
  - `ssh_password`: SSH password (optional)

## Project Structure

```
mycontrol/
├── app.py              # Main Flask application
├── config.json         # Configuration file
├── control.sh          # Service control script
├── requirements.txt    # Python dependencies
├── templates/          # HTML templates
│   └── index.html
├── utils/              # Utility modules
│   ├── ssh_utils.py    # SSH functionality
│   └── grafana_utils.py # Grafana dashboard processing
├── logs/               # Application logs
└── venv/               # Python virtual environment
```

## Prerequisites

Ensure `ipmitool` is installed on your system:
```bash
# Ubuntu/Debian
sudo apt-get install ipmitool

# CentOS/RHEL
sudo yum install ipmitool

# macOS
brew install ipmitool
```

## Usage

### Control Script Commands

```bash
./control.sh start    # Start the application (default)
./control.sh stop     # Stop the application
./control.sh restart  # Restart the application
./control.sh status   # Show application status
./control.sh logs     # Show and follow application logs
```

### Manual Usage

```bash
python app.py
```

Access the web interface at: http://localhost:5010 (or your configured port)

## Logging

Logs are stored in the `logs/` directory:
- `logs/mycontrol.log` - Application logs with rotation (10MB max, 5 backups)
- Console output also available when running manually

## API

- `GET /` - Web interface
- `GET /api/status` - JSON API for host status
- `POST /api/power-on/<hostname>` - Power on a specific host via IPMI

## Process Management

The control script:
- Creates/activates Python virtual environment automatically
- Installs/updates requirements
- Runs application in background with PID tracking
- Provides process management commands
- Logs to both file and console

## Security Note

Update the default credentials in `config.json` before use.