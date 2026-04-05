# gputemps

Displays real-time NVIDIA GPU core, junction, and VRAM temperatures.

## Credits

This tool is based entirely on the work of **ThomasBaruzier**:
https://github.com/ThomasBaruzier/gddr6-core-junction-vram-temps

All credit for the original implementation goes to them. Local modifications:
- Added `--duration <secs>` argument to run for a fixed number of seconds then exit
- Fixed 1-second refresh interval when running non-interactively (e.g. backgrounded)

## Usage

```
Usage: gputemps [OPTIONS]

Options:
  --json              Output temperatures in JSON format
  --once              Output temperatures once
  --duration <secs>   Run for a fixed number of seconds then exit
  --help              Show this help message and exit

Examples:
  gputemps                      Display and update table of GPU temperatures
  gputemps --json               Continuously output GPU temperatures in JSON format
  gputemps --once               Output temperatures once in table format
  gputemps --json --once        Output temperatures once in JSON format
  gputemps --json --duration 60 Output JSON temperatures for 60 seconds
```

## Build & Install

```bash
make
sudo make install
```

Requires `libnvidia-ml` and `libpci`. Must be run as root.
