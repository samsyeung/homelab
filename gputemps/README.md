# gputemps

Displays real-time NVIDIA GPU metrics including temperatures, fan speed, power draw, utilisation, and VRAM usage.

## Credits

This tool is based entirely on the work of **ThomasBaruzier**:
https://github.com/ThomasBaruzier/gddr6-core-junction-vram-temps

All credit for the original implementation goes to them. Local modifications:
- Added `--duration <secs>` argument to run for a fixed number of seconds then exit
- Fixed 1-second refresh interval when running non-interactively (e.g. backgrounded)
- Added fan speed, power draw, GPU/memory utilisation, and used VRAM columns
- Added `--append` mode for saving/logging output to a file
- Added per-page timestamps and elapsed-seconds column for tracking when readings were taken

## Metrics

| Column   | Source | Description |
|----------|--------|-------------|
| T        | —      | Seconds elapsed since the page header was printed |
| GPU      | —      | GPU index |
| CORE     | NVML   | GPU die temperature |
| JUNC     | MMIO   | Hotspot (junction) temperature, read directly from GPU register `0x0002046C` |
| VRAM     | MMIO   | VRAM temperature, read directly from GPU register `0x0000E2A8` |
| FAN      | NVML   | Overall fan speed (% of max) |
| POWER    | NVML   | Current power draw in watts |
| UTIL     | NVML   | GPU utilisation % |
| MEM      | NVML   | Memory controller utilisation % |
| VRAM GB  | NVML   | VRAM currently in use |

Junction and VRAM temperatures require direct hardware register access via `/dev/mem`, which is why root is required.

## Usage

```
Usage: gputemps [OPTIONS]

Options:
  --json              Output temperatures in JSON format
  --once              Output temperatures once
  --append            Append rows to terminal, reprinting headers every page
  --duration <secs>   Run for a fixed number of seconds then exit
  --help              Show this help message and exit

Examples:
  gputemps                      Display and update table of GPU temperatures
  gputemps --json               Continuously output GPU temperatures in JSON format
  gputemps --once               Output temperatures once in table format
  gputemps --json --once        Output temperatures once in JSON format
  gputemps --json --duration 60 Output JSON temperatures for 60 seconds
  gputemps --append             Continuously append GPU temperatures as a growing table
```

### Append mode

`--append` is useful for logging or capturing output to a file. Unlike the default mode (which updates in place), it scrolls the table downward. A timestamp and column headers are reprinted at the top of each terminal page, and the `T` column shows how many seconds each reading is after the page's header timestamp:

```
2026-04-05 14:30:00
   T │ GPU │  CORE  │  JUNC  │  VRAM  │  FAN   │ POWER  │  UTIL  │  MEM   │ VRAM GB│
   0 │   0 │  45°C  │  52°C  │  48°C  │   65%  │ 250W   │   85%  │   42%  │ 12.5GB │
     │   1 │  43°C  │  50°C  │  46°C  │   65%  │ 248W   │   82%  │   40%  │ 11.8GB │
   1 │   0 │  46°C  │  53°C  │  49°C  │   65%  │ 252W   │   87%  │   44%  │ 12.5GB │
     │   1 │  44°C  │  51°C  │  47°C  │   65%  │ 249W   │   83%  │   41%  │ 11.8GB │
```

## Build & Install

```bash
make
sudo make install
```

Requires `libnvidia-ml` and `libpci`. Must be run as root.
