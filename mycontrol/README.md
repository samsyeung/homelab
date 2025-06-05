# MyControl - Host Power Status Monitor

A Flask web application for monitoring remote host power status via IPMI.

## Features

- Display power status of multiple remote hosts
- Query IPMI using lanplus protocol
- Configuration via JSON file
- Auto-refresh every 30 seconds
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
  "ipmitool_path": "ipmitool",
  "grafana_dashboard_url": "https://grafana.yeungs.net/d-solo/bdl3vqwxprhtsa/nvitop-dashboard?orgId=1&timezone=browser&var-hostname=$__all&var-username=$__all&refresh=10s&panelId=20&__feature.dashboardSceneSolo",
  "hosts": [
    {
      "name": "Server Name",
      "hostname": "192.168.1.100",
      "username": "ipmi_user",
      "password": "ipmi_password"
    }
  ]
}
```

### Configuration Options

- `port`: Web server listening port (default: 5010)
- `ipmitool_path`: Path to ipmitool binary (default: "ipmitool")
- `grafana_dashboard_url`: URL to Grafana dashboard panel (optional)
- `hosts`: Array of host configurations

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

## Process Management

The control script:
- Creates/activates Python virtual environment automatically
- Installs/updates requirements
- Runs application in background with PID tracking
- Provides process management commands
- Logs to both file and console

## Security Note

Update the default credentials in `config.json` before use.