#!/bin/bash

# MyControl startup script
# Creates/activates Python venv, installs requirements, and starts the application

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/venv"
LOGS_DIR="$SCRIPT_DIR/logs"
PID_FILE="$SCRIPT_DIR/mycontrol.pid"
LOG_FILE="$LOGS_DIR/mycontrol.log"
CONFIG_FILE="$SCRIPT_DIR/config.json"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1"
}

error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1"
    exit 1
}

get_port() {
    if [ -f "$CONFIG_FILE" ]; then
        # Extract port from config.json, default to 5010 if not found
        PORT=$(python3 -c "import json; config=json.load(open('$CONFIG_FILE')); print(config.get('port', 5010))" 2>/dev/null || echo "5010")
    else
        PORT=5010
    fi
    echo "$PORT"
}

check_running() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            return 0  # Running
        else
            rm -f "$PID_FILE"
            return 1  # Not running
        fi
    fi
    return 1  # Not running
}

stop_app() {
    if check_running; then
        PID=$(cat "$PID_FILE")
        log "Stopping MyControl (PID: $PID)..."
        kill "$PID"
        rm -f "$PID_FILE"
        log "MyControl stopped"
    else
        warn "MyControl is not running"
    fi
}

start_app() {
    if check_running; then
        warn "MyControl is already running (PID: $(cat "$PID_FILE"))"
        exit 1
    fi

    log "Starting MyControl..."
    
    # Create logs directory
    mkdir -p "$LOGS_DIR"
    
    # Create or activate virtual environment
    if [ ! -d "$VENV_DIR" ]; then
        log "Creating Python virtual environment..."
        python3 -m venv "$VENV_DIR"
    fi
    
    log "Activating virtual environment..."
    source "$VENV_DIR/bin/activate"
    
    # Install/upgrade requirements
    log "Installing requirements..."
    pip install --upgrade pip
    pip install -r "$SCRIPT_DIR/requirements.txt"
    
    # Check if config exists
    if [ ! -f "$SCRIPT_DIR/config.json" ]; then
        warn "config.json not found. Please create it before starting the application."
        exit 1
    fi
    
    # Get configured port
    PORT=$(get_port)
    
    # Start the application in background
    log "Starting Flask application on port $PORT..."
    cd "$SCRIPT_DIR"
    nohup python app.py >> "$LOG_FILE" 2>&1 &
    APP_PID=$!
    
    # Save PID
    echo "$APP_PID" > "$PID_FILE"
    
    # Wait a moment and check if it's still running
    sleep 2
    if ps -p "$APP_PID" > /dev/null 2>&1; then
        log "MyControl started successfully (PID: $APP_PID)"
        log "Application running at: http://localhost:$PORT"
        log "Logs available at: $LOG_FILE"
    else
        error "Failed to start MyControl. Check logs: $LOG_FILE"
    fi
}

status_app() {
    if check_running; then
        PID=$(cat "$PID_FILE")
        PORT=$(get_port)
        log "MyControl is running (PID: $PID)"
        log "Application URL: http://localhost:$PORT"
        log "Log file: $LOG_FILE"
    else
        log "MyControl is not running"
    fi
}

show_logs() {
    if [ -f "$LOG_FILE" ]; then
        tail -f "$LOG_FILE"
    else
        warn "Log file not found: $LOG_FILE"
    fi
}

case "${1:-start}" in
    start)
        start_app
        ;;
    stop)
        stop_app
        ;;
    restart)
        stop_app
        sleep 1
        start_app
        ;;
    status)
        status_app
        ;;
    logs)
        show_logs
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|logs}"
        echo ""
        echo "Commands:"
        echo "  start   - Start the MyControl application (default)"
        echo "  stop    - Stop the MyControl application"
        echo "  restart - Restart the MyControl application"
        echo "  status  - Show application status"
        echo "  logs    - Show and follow application logs"
        exit 1
        ;;
esac