# Changelog

All notable changes to the MyControl project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.7.1] - 2025-01-07

### Added
- **Enhanced documentation** - Comprehensive visual showcase of application features
  - Added 6 new screenshots demonstrating all major functionality
  - Main dashboard overview showing host status and monitoring tools
  - GPU Summary monitoring with nvidia-smi output display
  - GPU Topology analysis for multi-GPU system interconnects
  - Docker container management interface with start/stop controls
  - Web-based SSH terminal access demonstration
  - Real-time nvtop monitoring interface showcase
- **Improved README structure** - Better organization and visual presentation
  - Detailed feature descriptions with accompanying screenshots
  - Step-by-step visual guide through application capabilities
  - Enhanced user onboarding experience with clear feature explanations

### Enhanced
- **Documentation quality** - More comprehensive and user-friendly documentation
  - Visual documentation of all monitoring and management features
  - Clear explanations of GPU monitoring, Docker management, and terminal access
  - Better presentation of multi-host management capabilities

## [0.7.0] - 2025-01-07

### Added
- **Docker container management** - Complete Docker monitoring and control capabilities
  - Docker containers table showing all containers with formatted information
  - Start/Stop buttons for individual container management
  - Real-time container status with color-coded indicators (running=green, exited=red, etc.)
  - Container details including ID, name, image, status, ports, and creation date
  - JSON-based parsing for reliable data extraction from `docker ps -a --format json`
- **Enhanced GPU monitoring interface** - Improved button layout and organization
  - GPU Summary button (renamed from nvidia-smi for clarity)
  - GPU Topology button showing `nvidia-smi topo -m` output for multi-GPU systems
  - Docker button integrated with GPU monitoring section
  - Consistent button styling across all monitoring tools
- **Terminal interface improvements** - Better organization of SSH and monitoring tools
  - nvtop button moved to header next to SSH button for logical grouping
  - Terminal buttons container with proper spacing and alignment
  - Improved visual hierarchy for host management actions

### Enhanced
- **User interface refinements** - Better visual organization and usability
  - Reorganized button layout for improved workflow
  - Enhanced table styling with hover effects and alternating row colors
  - Responsive action buttons with loading states and visual feedback
  - Consistent color scheme across different monitoring sections
- **API endpoints expansion** - Extended functionality for container management
  - `/api/docker-info/<hostname>` - Retrieve Docker container information
  - `/api/docker-action/<hostname>` - Start/stop Docker containers remotely
  - JSON response format for structured data handling
  - Comprehensive error handling and validation

### Technical Improvements
- Enhanced SSH command execution for Docker operations with proper timeout handling
- Improved HTML table generation with structured data parsing
- Better error messaging and user feedback for all Docker operations
- Optimized refresh mechanism for real-time status updates

## [0.6.0] - 2025-01-07

### Added
- **Configurable tool paths** - Support for custom binary paths in configuration
  - `sshpass_path` configuration option for custom sshpass binary location
  - Enhanced flexibility for different system configurations and installations
- **Improved ping-based connectivity checks** - Smarter uptime monitoring
  - Uptime requests now check host connectivity via ping before attempting SSH
  - Prevents unnecessary SSH connection timeouts to unreachable hosts
  - Faster response times and better user experience

### Fixed
- **nvtop terminal functionality** - Resolved critical terminal execution issues
  - Fixed "execvp failed" errors in nvtop popup terminals
  - Added pseudo-terminal allocation (`-t` flag) for proper nvtop execution
  - Set proper terminal environment (`TERM=xterm-256color`) for display compatibility
  - Removed unsupported ttyd options (`--title-format`, `--readonly`) causing failures
  - nvtop terminals now work reliably across different system configurations
- **Git repository cleanup** - Removed unnecessary tracked files
  - Removed log files and PID files from version control
  - Improved .gitignore patterns for cleaner repository management

### Technical Improvements
- Enhanced error handling and debugging capabilities for terminal management
- Improved SSH connection reliability with proper terminal allocation
- Better integration between configuration system and library modules
- Streamlined terminal command construction and execution

## [0.5.0-alpha] - 2025-01-07

### Added
- **Network connectivity monitoring** - Real-time ping status indicators
  - Ping status indicator next to power status showing online/offline/error states
  - Non-blocking ping checks after page load for better performance
  - Visual indicators with colored badges (green=online, red=offline, yellow=error)
- **Compact UI improvements** - Streamlined interface design
  - Smaller power status badges and buttons for cleaner layout
  - Reduced padding and font sizes for better space utilization
  - More compact status indicators while maintaining readability

### Changed
- **nvtop implementation** - Switched to popup terminal approach
  - nvtop now opens in popup window using SSH terminal (like SSH feature)
  - Changed from page-embedded streaming to dedicated terminal window
  - Button renamed from "GPU Stream" to "nvtop" for clarity
  - Read-only SSH terminal session specifically for nvtop monitoring
  - Uses configured SSH credentials instead of requiring sshpass
- **Major code refactoring** - Improved maintainability and organization
  - Renamed `utils/` directory to `libs/` for better naming convention
  - Split large `app.py` into focused library modules:
    - `libs/power_management.py` - IPMI power control functions
    - `libs/network_utils.py` - Ping and network connectivity
    - `libs/gpu_management.py` - GPU information retrieval
    - `libs/terminal_management.py` - SSH and nvtop terminal management
    - `libs/config_utils.py` - Configuration loading and utilities
  - Reduced main application file by ~300 lines
  - Better separation of concerns and reusable components

### Fixed
- nvtop streaming connection errors with proper SSH credential handling
- DOM element selection issues with hostnames containing special characters
- Terminal management now properly uses configured SSH credentials

### Technical Improvements
- Class-based terminal management for better process lifecycle control
- Centralized configuration loading and host lookup utilities
- Improved error handling and resource cleanup
- More maintainable codebase with clear module boundaries

## [0.3.0] - 2025-01-07

### Added
- **Real-time nvtop streaming** - Live GPU monitoring with expandable sections
  - nvtop button positioned next to nvidia-smi for easy access
  - Server-Sent Events (SSE) for real-time streaming output
  - Black terminal-style interface with auto-scrolling
  - Manual stop controls and automatic cleanup
  - Proper SSH process management and error handling
- **Enhanced SSH terminal interface** - Improved user experience
  - Custom wrapper with close button in terminal header
  - Professional dark header design with hostname display
  - Always-visible close button for easy session termination
  - Safari popup blocker compatibility maintained
- **Improved GPU monitoring layout** - Better button organization
  - Side-by-side placement of nvidia-smi and nvtop buttons
  - Consistent styling and responsive design
  - Enhanced error handling and user feedback

### Fixed
- SSH terminal connection issues with host key algorithms
- Popup blocking in Safari browser for SSH terminals
- Improved SSH connection reliability with proper options

### Technical Improvements
- Server-Sent Events implementation for real-time data streaming
- Process lifecycle management for nvtop SSH sessions
- Enhanced error handling and connection management
- Better resource cleanup and memory management

## [0.2.0] - 2025-01-07

### Added
- **Web-based SSH terminals** - Direct SSH access to servers through the browser
  - Browser-based SSH terminal sessions using ttyd
  - SSH Terminal button on each host card
  - Secure localhost-only terminal binding
  - Automatic terminal cleanup after client disconnect
  - Unique port allocation per host to prevent conflicts
  - Manual SSH authentication required (no auto-login)
- New API endpoints for SSH terminal management:
  - `POST /api/ssh-terminal/<hostname>` - Start SSH terminal for a host
  - `GET /api/ssh-terminals` - List active SSH terminals
- `ttyd_base_port` configuration option for SSH terminal port management
- **GPU Status Monitoring** - Expandable sections showing nvidia-smi output
  - GPU Status button appears on powered-on hosts
  - Fetches real-time GPU information via SSH
  - Expandable/collapsible interface with loading states
  - Formatted output in monospace font for readability
  - Error handling for hosts without nvidia-smi
- New API endpoint: `GET /api/gpu-info/<hostname>` - Get GPU information via nvidia-smi

## [0.1.0] - 2025-06-06

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