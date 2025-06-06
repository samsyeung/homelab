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

### Application Interface

![MyControl Application Screenshot](docs/images/app-screenshot.png)

The application provides a clean, modern web interface featuring:
- **Host Status Cards**: Display server name, power state, and system uptime with load averages
- **Real-time Monitoring**: Auto-refresh functionality keeps information current
- **Integrated Dashboards**: Embedded Grafana charts for GPU utilization, temperature monitoring, and other system metrics
- **Responsive Design**: Clean 2-column layout that adapts to different screen sizes

## Setup

1. **Create your configuration file**:
```bash
cp config.json.example config.json
# Edit config.json with your actual host details and credentials
```

2. **Start the application** (recommended):
```bash
./control.sh
```

3. **Manual setup** (alternative):
```bash
pip install -r requirements.txt
python app.py
```

## Configuration

The application uses `config.json` for configuration. Start by copying the example:

```bash
cp config.json.example config.json
```

Then edit `config.json` with your actual server details. See `config.json.example` for a complete configuration template with multiple hosts and dashboard examples.

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
├── config.json.example # Example configuration file
├── config.json         # Your configuration (create from example)
├── control.sh          # Service control script
├── requirements.txt    # Python dependencies
├── .gitignore          # Git ignore rules
├── templates/          # HTML templates
│   └── index.html
├── utils/              # Utility modules
│   ├── ssh_utils.py    # SSH functionality
│   └── grafana_utils.py # Grafana dashboard processing
├── docs/               # Documentation and assets
│   └── images/         # Screenshots and images
├── logs/               # Application logs (auto-created)
└── venv/               # Python virtual environment (auto-created)
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

## Security Notes

- **Never commit `config.json`** to version control as it contains sensitive credentials
- Update all default passwords and usernames in your `config.json`
- Use strong, unique passwords for IPMI and SSH access
- Consider using SSH keys instead of passwords for SSH connections
- Restrict network access to the MyControl web interface (port 5010 by default)