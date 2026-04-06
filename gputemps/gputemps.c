#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/mman.h>
#include <pci/pci.h>
#include <nvml.h>
#include <errno.h>
#include <string.h>
#include <stdarg.h>
#include <signal.h>
#include <termios.h>
#include <time.h>
#include <sys/ioctl.h>

#define REFRESH_DURATION 1
#define BUFFER_SIZE 2048

#define HOTSPOT_REGISTER_OFFSET 0x0002046C
#define VRAM_REGISTER_OFFSET 0x0000E2A8
#define PG_SZ sysconf(_SC_PAGE_SIZE)
#define MEM_PATH "/dev/mem"

#define SEPARATOR     "\xE2\x94\x82"
#define CURSOR_HIDE   "\x1B[?25l"
#define CURSOR_SHOW   "\x1B[?25h"
#define COLOR_RESET   "\x1B[0m"
#define COLOR_GREEN   "\x1B[32m"
#define COLOR_YELLOW  "\x1B[33m"
#define COLOR_RED     "\x1B[31m"

const uint32_t GPU_TEMP_WARN = 70;
const uint32_t GPU_TEMP_DANGER = 85;
const uint32_t JUNCTION_TEMP_WARN = 80;
const uint32_t JUNCTION_TEMP_DANGER = 95;
const uint32_t VRAM_TEMP_WARN = 80;
const uint32_t VRAM_TEMP_DANGER = 95;

#define ELAPSED_BLANK ((uint32_t)-1)

static volatile sig_atomic_t running = 1;
static struct termios orig_termios;

typedef enum {
    FORMAT_TABLE,
    FORMAT_JSON
} OutputFormat;

typedef enum {
    MODE_CONTINUOUS,
    MODE_ONCE,
    MODE_APPEND
} OutputMode;

typedef struct {
    nvmlReturn_t result;
    unsigned int device_count;
    int initialized;
    struct pci_access *pacc;
    char output_buffer[BUFFER_SIZE];
    size_t buffer_pos;
    OutputMode output_mode;
    OutputFormat output_format;
    int duration;
} Context;

typedef struct {
    nvmlDevice_t device;
    nvmlPciInfo_t pci_info;
    uint32_t gpu_temp;
    uint32_t junction_temp;
    uint32_t vram_temp;
    uint32_t fan_speed;
    uint32_t power_w;
    uint32_t gpu_util;
    uint32_t mem_util;
    float vram_used_gb;
} GpuDevice;

static int check_root_privileges(void) {
    if (geteuid() != 0) {
        fprintf(stderr, "This program requires root privileges\n");
        return -1;
    }
    return 0;
}

static void cleanup_context(Context *ctx) {
    if (!ctx) return;

    if (ctx->initialized) {
        nvmlShutdown();
        ctx->initialized = 0;
    }

    if (ctx->pacc) {
        pci_cleanup(ctx->pacc);
        ctx->pacc = NULL;
    }
}

static void signal_handler(int signum) {
    running = 0;
}

static void restore_cursor(void) {
    printf(CURSOR_SHOW);
    fflush(stdout);
}

static void reset_terminal(void) {
    tcsetattr(STDIN_FILENO, TCSANOW, &orig_termios);
}

static int setup_terminal(void) {
    struct termios new_termios;

    if (tcgetattr(STDIN_FILENO, &orig_termios) < 0) return -1;
    atexit(reset_terminal);
    new_termios = orig_termios;
    new_termios.c_lflag &= ~(ICANON | ECHO);
    new_termios.c_cc[VMIN] = 0;
    new_termios.c_cc[VTIME] = 0;
    if (tcsetattr(STDIN_FILENO, TCSANOW, &new_termios) < 0) return -1;
    return 0;
}

static void buffer_append(Context *ctx, const char *format, ...) {
    va_list args;
    va_start(args, format);
    int remaining = BUFFER_SIZE - ctx->buffer_pos;
    int written = vsnprintf(ctx->output_buffer + ctx->buffer_pos, remaining, format, args);
    if (written > 0 && written < remaining) ctx->buffer_pos += written;
    va_end(args);
}

static const char* get_temp_color(uint32_t temp, uint32_t warn, uint32_t danger) {
    if (temp >= danger) return COLOR_RED;
    if (temp >= warn) return COLOR_YELLOW;
    return COLOR_GREEN;
}

static void print_gpu_info(Context *ctx, unsigned int index, GpuDevice *gpu, uint32_t elapsed) {
    char tbuf[8];
    if (elapsed == ELAPSED_BLANK)
        snprintf(tbuf, sizeof(tbuf), "    ");
    else
        snprintf(tbuf, sizeof(tbuf), "%4u", elapsed > 9999u ? 9999u : elapsed);
    buffer_append(ctx, "%s %s %3u %s %s%3u°C%s  %s %s%3u°C%s  %s %s%3u°C%s  %s  %3u%%  %s %3uW   %s  %3u%%  %s  %3u%%  %s %4.1fGB %s\n",
        tbuf, SEPARATOR, index, SEPARATOR,
        get_temp_color(gpu->gpu_temp, GPU_TEMP_WARN, GPU_TEMP_DANGER),
        gpu->gpu_temp, COLOR_RESET, SEPARATOR,
        get_temp_color(gpu->junction_temp, JUNCTION_TEMP_WARN, JUNCTION_TEMP_DANGER),
        gpu->junction_temp, COLOR_RESET, SEPARATOR,
        get_temp_color(gpu->vram_temp, VRAM_TEMP_WARN, VRAM_TEMP_DANGER),
        gpu->vram_temp, COLOR_RESET, SEPARATOR,
        gpu->fan_speed, SEPARATOR,
        gpu->power_w, SEPARATOR,
        gpu->gpu_util, SEPARATOR,
        gpu->mem_util, SEPARATOR,
        gpu->vram_used_gb, SEPARATOR);
}

static int init_pci(Context *ctx) {
    ctx->pacc = pci_alloc();
    if (!ctx->pacc) {
        fprintf(stderr, "Failed to allocate PCI structure\n");
        return -1;
    }
    pci_init(ctx->pacc);
    pci_scan_bus(ctx->pacc);
    return 0;
}

static int init_nvml(Context *ctx) {
    ctx->result = nvmlInit();
    if (NVML_SUCCESS != ctx->result) {
        fprintf(stderr, "Failed to initialize NVML: %s\n",
          nvmlErrorString(ctx->result));
        return -1;
    }
    ctx->initialized = 1;
    return 0;
}

static int get_device_count(Context *ctx) {
    ctx->result = nvmlDeviceGetCount(&ctx->device_count);
    if (NVML_SUCCESS != ctx->result) {
        fprintf(stderr, "Failed to get device count: %s\n",
          nvmlErrorString(ctx->result));
        return -1;
    }
    if (ctx->device_count == 0) {
        fprintf(stderr, "No NVIDIA GPUs found\n");
        return -1;
    }
    return 0;
}

static int get_device_handle(Context *ctx, unsigned int index, nvmlDevice_t *device) {
    ctx->result = nvmlDeviceGetHandleByIndex(index, device);
    if (NVML_SUCCESS != ctx->result) {
        fprintf(stderr, "Failed to get handle for GPU %u: %s\n",
          index, nvmlErrorString(ctx->result));
        return -1;
    }
    return 0;
}

static int get_device_pci_info(Context *ctx, nvmlDevice_t device, nvmlPciInfo_t *pci_info) {
    ctx->result = nvmlDeviceGetPciInfo(device, pci_info);
    if (NVML_SUCCESS != ctx->result) {
        fprintf(stderr, "Failed to get PCI info: %s\n",
          nvmlErrorString(ctx->result));
        return -1;
    }
    return 0;
}

static int get_gpu_temp(nvmlDevice_t device, uint32_t *temp) {
    nvmlReturn_t result = nvmlDeviceGetTemperature(device, NVML_TEMPERATURE_GPU, temp);
    if (NVML_SUCCESS != result) {
        fprintf(stderr, "Failed to get GPU temperature: %s\n",
          nvmlErrorString(result));
        return -1;
    }
    return 0;
}

static int read_register_temp(struct pci_dev *dev, uint32_t offset, uint32_t *temp) {
    int fd = open(MEM_PATH, O_RDWR | O_SYNC);
    if (fd < 0) {
        fprintf(stderr, "Failed to open %s: %s\n", MEM_PATH, strerror(errno));
        return -1;
    }

    uint32_t reg_addr = (dev->base_addr[0] & 0xFFFFFFFF) + offset;
    uint32_t base_offset = reg_addr & ~(PG_SZ-1);
    void *map_base = mmap(0, PG_SZ, PROT_READ, MAP_SHARED, fd, base_offset);
    if (map_base == MAP_FAILED) {
        fprintf(stderr, "Failed to map memory: %s\n", strerror(errno));
        close(fd);
        return -1;
    }

    uint32_t reg_value = *((uint32_t *)((char *)map_base + (reg_addr - base_offset)));

    if (offset == HOTSPOT_REGISTER_OFFSET) {
        *temp = (reg_value >> 8) & 0xff;
    } else if (offset == VRAM_REGISTER_OFFSET) {
        *temp = (reg_value & 0x00000fff) / 0x20;
    }

    munmap(map_base, PG_SZ);
    close(fd);

    return (*temp < 0x7f) ? 0 : -1;
}

static int get_gpu_temps(Context *ctx, unsigned int index, GpuDevice *gpu) {
    if ((get_device_handle(ctx, index, &gpu->device) < 0) ||
        (get_gpu_temp(gpu->device, &gpu->gpu_temp) < 0) ||
        (get_device_pci_info(ctx, gpu->device, &gpu->pci_info) < 0))
        return -1;

    nvmlDeviceGetFanSpeed(gpu->device, &gpu->fan_speed);

    uint32_t power_mw = 0;
    if (nvmlDeviceGetPowerUsage(gpu->device, &power_mw) == NVML_SUCCESS)
        gpu->power_w = power_mw / 1000;

    nvmlUtilization_t util = {0};
    if (nvmlDeviceGetUtilizationRates(gpu->device, &util) == NVML_SUCCESS) {
        gpu->gpu_util = util.gpu;
        gpu->mem_util = util.memory;
    }

    nvmlMemory_t mem = {0};
    if (nvmlDeviceGetMemoryInfo(gpu->device, &mem) == NVML_SUCCESS)
        gpu->vram_used_gb = (float)mem.used / (1024.0f * 1024.0f * 1024.0f);

    for (struct pci_dev *dev = ctx->pacc->devices; dev; dev = dev->next) {
        pci_fill_info(dev, PCI_FILL_IDENT | PCI_FILL_BASES);

        if ((dev->device_id << 16 | dev->vendor_id) != gpu->pci_info.pciDeviceId ||
            (unsigned int)dev->domain != gpu->pci_info.domain ||
            dev->bus != gpu->pci_info.bus ||
            dev->dev != gpu->pci_info.device) {
            continue;
        }

        int junction_result =
          read_register_temp(dev, HOTSPOT_REGISTER_OFFSET, &gpu->junction_temp);
        if (junction_result != 0) return -1;

        int vram_result =
          read_register_temp(dev, VRAM_REGISTER_OFFSET, &gpu->vram_temp);
        if (vram_result != 0) return -1;

        return 0;
    }

    return -1;
}

static int monitor_temperatures_table(Context *ctx) {
    int valid_readings = 0;
    char timebuf[32];
    time_t now = time(NULL);
    strftime(timebuf, sizeof(timebuf), "%Y-%m-%d %H:%M:%S", localtime(&now));

    ctx->buffer_pos = 0;
    buffer_append(ctx, "\n%s\n", timebuf);
    buffer_append(ctx, "   T %s GPU %s  CORE  %s  JUNC  %s  VRAM  %s  FAN   %s POWER  %s  UTIL  %s  MEM   %s VRAM GB%s\n",
      SEPARATOR, SEPARATOR, SEPARATOR, SEPARATOR, SEPARATOR, SEPARATOR, SEPARATOR, SEPARATOR, SEPARATOR, SEPARATOR);

    for (unsigned int i = 0; i < ctx->device_count; i++) {
        GpuDevice gpu = {0};
        if (get_gpu_temps(ctx, i, &gpu) != 0) return -1;
        print_gpu_info(ctx, i, &gpu, i == 0 ? 0 : ELAPSED_BLANK);
        valid_readings++;
    }

    buffer_append(ctx, "\033[%dA", valid_readings + 3);
    printf("%s", ctx->output_buffer);
    fflush(stdout);
    return 0;
}

static int monitor_temperatures_json(Context *ctx) {
    ctx->buffer_pos = 0;
    time_t now = time(NULL);
    buffer_append(ctx, "{\"timestamp\":%ld,\"gpus\":[", (long)now);

    for (unsigned int i = 0; i < ctx->device_count; i++) {
        GpuDevice gpu = {0};
        if (get_gpu_temps(ctx, i, &gpu) != 0) return -1;

        if (i > 0) {
            buffer_append(ctx, ",");
        }
        buffer_append(ctx, "{\"index\":%u,\"core\":%u,\"junction\":%u,\"vram\":%u,\"fan\":%u,\"power_w\":%u,\"gpu_util\":%u,\"mem_util\":%u,\"vram_used_gb\":%.2f}",
               i, gpu.gpu_temp, gpu.junction_temp, gpu.vram_temp,
               gpu.fan_speed, gpu.power_w, gpu.gpu_util, gpu.mem_util, gpu.vram_used_gb);
    }
    buffer_append(ctx, "]}");
    printf("%s\n", ctx->output_buffer);
    fflush(stdout);
    return 0;
}

static int init_monitoring(Context *ctx) {
    if ((check_root_privileges() < 0) ||
        (init_pci(ctx) < 0) ||
        (init_nvml(ctx) < 0) ||
        (get_device_count(ctx) < 0))
        return -1;

    signal(SIGINT, signal_handler);
    signal(SIGTERM, signal_handler);
    signal(SIGHUP, signal_handler);

    return 0;
}

static int handle_input(int duration_ms) {
    if (isatty(STDIN_FILENO)) {
        struct timeval tv = {0, duration_ms * 1000};
        fd_set fds;
        FD_ZERO(&fds);
        FD_SET(STDIN_FILENO, &fds);

        if (select(STDIN_FILENO + 1, &fds, NULL, NULL, &tv) > 0) {
            char c;
            if (read(STDIN_FILENO, &c, 1) > 0) return 1;
        }
    } else {
        struct timespec ts = {
            .tv_sec = duration_ms / 1000,
            .tv_nsec = (duration_ms % 1000) * 1000000
        };
        nanosleep(&ts, NULL);
    }
    return 0;
}

static int run_monitoring_loop(Context *ctx) {
    int elapsed = 0;
    while (running) {
        if (monitor_temperatures_table(ctx) != 0) return -1;
        if (handle_input(REFRESH_DURATION * 1000)) break;
        if (ctx->duration > 0 && ++elapsed >= ctx->duration) break;
    }

    printf("\033[%dB", ctx->device_count + 2);
    printf("\n");
    fflush(stdout);
    return 0;
}

static int run_json_loop(Context *ctx) {
    int elapsed = 0;
    while (running) {
        if (monitor_temperatures_json(ctx) != 0) return -1;
        if (handle_input(REFRESH_DURATION * 1000)) break;
        if (ctx->duration > 0 && ++elapsed >= ctx->duration) break;
    }
    return 0;
}

static int get_terminal_rows(void) {
    struct winsize ws;
    if (isatty(STDOUT_FILENO) && ioctl(STDOUT_FILENO, TIOCGWINSZ, &ws) == 0 && ws.ws_row > 0)
        return ws.ws_row;
    return 24;
}

static int monitor_temperatures_append(Context *ctx) {
    static int rows_since_header = 0;
    static time_t header_time = 0;
    int page_height = get_terminal_rows();

    time_t now = time(NULL);

    if (rows_since_header == 0) {
        header_time = now;
        char timebuf[32];
        strftime(timebuf, sizeof(timebuf), "%Y-%m-%d %H:%M:%S", localtime(&now));
        ctx->buffer_pos = 0;
        buffer_append(ctx, "%s\n", timebuf);
        buffer_append(ctx, "   T %s GPU %s  CORE  %s  JUNC  %s  VRAM  %s  FAN   %s POWER  %s  UTIL  %s  MEM   %s VRAM GB%s\n",
            SEPARATOR, SEPARATOR, SEPARATOR, SEPARATOR, SEPARATOR, SEPARATOR, SEPARATOR, SEPARATOR, SEPARATOR, SEPARATOR);
        printf("%s", ctx->output_buffer);
        fflush(stdout);
    }

    ctx->buffer_pos = 0;
    uint32_t elapsed = (uint32_t)(now - header_time);
    for (unsigned int i = 0; i < ctx->device_count; i++) {
        GpuDevice gpu = {0};
        if (get_gpu_temps(ctx, i, &gpu) != 0) return -1;
        print_gpu_info(ctx, i, &gpu, i == 0 ? elapsed : ELAPSED_BLANK);
    }
    printf("%s", ctx->output_buffer);
    fflush(stdout);

    rows_since_header += ctx->device_count;
    if (rows_since_header + (int)ctx->device_count >= page_height - 2)
        rows_since_header = 0;

    return 0;
}

static int run_append_loop(Context *ctx) {
    int elapsed = 0;
    while (running) {
        if (monitor_temperatures_append(ctx) != 0) return -1;
        if (handle_input(REFRESH_DURATION * 1000)) break;
        if (ctx->duration > 0 && ++elapsed >= ctx->duration) break;
    }
    return 0;
}

static void print_usage(const char *prog) {
    fprintf(stderr,
        "Usage: %s [OPTIONS]\n"
        "\n"
        "Options:\n"
        "  --json              Output temperatures in JSON format\n"
        "  --once              Output temperatures once\n"
        "  --append            Append rows to terminal, reprinting headers every page\n"
        "  --duration <secs>   Run for a fixed number of seconds then exit\n"
        "  --help              Show this help message and exit\n"
        "\n"
        "Examples:\n"
        "  %s                      Display and update table of GPU temperatures\n"
        "  %s --json               Continuously output GPU temperatures in JSON format\n"
        "  %s --once               Output temperatures once in table format\n"
        "  %s --json --once        Output temperatures once in JSON format\n"
        "  %s --json --duration 60 Output JSON temperatures for 60 seconds\n"
        "  %s --append             Continuously append GPU temperatures as a growing table\n",
        prog, prog, prog, prog, prog, prog, prog);
}

int main(int argc, char *argv[]) {
    Context ctx = {0};
    ctx.output_format = FORMAT_TABLE;
    ctx.output_mode = MODE_CONTINUOUS;

    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "--json") == 0) {
            ctx.output_format = FORMAT_JSON;
        } else if (strcmp(argv[i], "--once") == 0) {
            ctx.output_mode = MODE_ONCE;
        } else if (strcmp(argv[i], "--append") == 0) {
            ctx.output_mode = MODE_APPEND;
        } else if (strcmp(argv[i], "--duration") == 0) {
            if (i + 1 >= argc) {
                fprintf(stderr, "--duration requires a value\n");
                return 1;
            }
            ctx.duration = atoi(argv[++i]);
            if (ctx.duration <= 0) {
                fprintf(stderr, "--duration must be a positive integer\n");
                return 1;
            }
        } else if (strcmp(argv[i], "--help") == 0) {
            print_usage(argv[0]);
            return 0;
        } else {
            fprintf(stderr, "Unknown argument: %s\n", argv[i]);
            print_usage(argv[0]);
            return 1;
        }
    }

    if (ctx.output_format == FORMAT_TABLE && ctx.output_mode == MODE_CONTINUOUS) {
        if (setup_terminal() < 0) {
            cleanup_context(&ctx);
            return 1;
        }
        printf(CURSOR_HIDE);
        fflush(stdout);
        atexit(restore_cursor);
    }

    if (init_monitoring(&ctx) < 0) {
        cleanup_context(&ctx);
        return 1;
    }

    int result;
    if (ctx.output_format == FORMAT_JSON && ctx.output_mode == MODE_ONCE) {
        result = monitor_temperatures_json(&ctx);
    } else if (ctx.output_format == FORMAT_JSON) {
        result = run_json_loop(&ctx);
    } else if (ctx.output_mode == MODE_ONCE) {
        result = monitor_temperatures_table(&ctx);
        printf("\033[%dB\n", ctx.device_count + 2);
    } else if (ctx.output_mode == MODE_APPEND) {
        result = run_append_loop(&ctx);
    } else {
        result = run_monitoring_loop(&ctx);
    }

    cleanup_context(&ctx);
    return result == 0 ? 0 : 1;
}
