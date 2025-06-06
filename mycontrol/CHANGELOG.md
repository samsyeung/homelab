# Changelog

All notable changes to the MyControl project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Application screenshot in README showing interface and features
- Documentation images directory structure
- `config.json.example` template with sample configuration
- `.gitignore` file to protect sensitive configuration
- Enhanced security documentation

### Changed
- Improved project structure by moving utility modules to `utils/` subdirectory
- Cleaner root directory with better organization
- Enhanced README with visual application preview
- Setup process now uses example configuration file for security
- Removed actual configuration file from version control

### Security
- **BREAKING**: `config.json` is no longer tracked in git for security
- Users must create `config.json` from the provided example template
- Added comprehensive security notes and best practices

### Added
- SSH uptime monitoring functionality
- Asynchronous SSH connections for fast uptime retrieval
- Configurable dashboard iframe heights per dashboard
- Configurable auto-refresh interval (default 30 seconds)
- Configurable SSH timeout (default 10 seconds)
- Optional dashboard headers (omit name to hide header)
- Power-on functionality for hosts via IPMI when powered off
- Comprehensive configuration validation
- Modular code structure with separate utility modules

### Changed
- **BREAKING**: Configuration structure updated with prefixed keys:
  - `hostname` → `ipmi_host`
  - `username` → `ipmi_username` 
  - `password` → `ipmi_password`
- Reorganized Grafana dashboards to display below host status in 2-column grid
- Improved configuration format for better organization
- Enhanced README with detailed configuration options
- Refactored codebase into separate modules for better maintainability

### Fixed
- **Major**: Eliminated duplicate log entries that were appearing twice in log files
- Improved logging configuration to prevent handler conflicts
- Fixed dashboard header display when no name is configured

### Technical Improvements
- Split SSH functionality into `ssh_utils.py` module
- Split Grafana functionality into `grafana_utils.py` module
- Simplified main `app.py` by using utility modules
- Added deduplication logic to prevent duplicate logging
- Implemented environment variable option for console logging during development
- Disabled propagation to root logger to prevent conflicts
- Added ThreadPoolExecutor for parallel SSH connections
- Enhanced error handling and timeout management

### Dependencies
- Added `asyncssh` for SSH connectivity

## Configuration Migration Guide

If upgrading from a previous version, update your `config.json`:

```json
{
  "hosts": [
    {
      "name": "Server Name",
      "ipmi_host": "192.168.1.100",      // was: "hostname"
      "ipmi_username": "ipmi_user",      // was: "username" 
      "ipmi_password": "ipmi_password",  // was: "password"
      "ssh_host": "192.168.1.100",      // new: for uptime monitoring
      "ssh_username": "user",           // new: for SSH access
      "ssh_password": "password"        // new: for SSH access
    }
  ],
  "grafana_dashboard_urls": [           // enhanced structure
    {
      "name": "Dashboard Name",         // optional: omit to hide header
      "url": "https://grafana.example.com/...",
      "height": 400                     // new: configurable height
    }
  ],
  "refresh_interval": 30,               // new: configurable refresh
  "ssh_timeout": 10                     // new: SSH timeout setting
}
```